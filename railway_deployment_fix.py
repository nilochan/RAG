#!/usr/bin/env python3
"""
Railway Deployment Fix - Apply minimal changes to make RAG work on Railway
"""

import shutil
import os

def apply_railway_fix():
    """Apply minimal Railway deployment fixes"""
    
    # Path to the rag_system.py file
    rag_file = "C:/Users/chanc/RAG/educational-rag-platform/src/rag_system.py"
    
    # Read current file
    with open(rag_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add try-catch around imports for Railway deployment resilience
    if 'try:' not in content[:500]:  # Check if already applied
        imports_fix = '''# Robust imports for Railway deployment
try:
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain.llms.base import LLM
    from langchain.schema import Document
    from pydantic import Field
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ LangChain not fully available: {e}")
    print("🔄 Using simplified mode for Railway deployment")
    LANGCHAIN_AVAILABLE = False
    # Create minimal classes to prevent errors
    class LLM:
        pass
    class Document:
        def __init__(self, page_content, metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}

from typing import List, Dict, Optional, Any
import logging
import time
import asyncio
import httpx
import os
import json'''
        
        # Replace the imports section
        old_imports = content[:content.find('logger = logging.getLogger(__name__)')]
        content = content.replace(old_imports, imports_fix + '\\n\\n')
    
    # Add error handling to the EnhancedRAGSystem.__init__ method
    if 'try:' not in content[content.find('class EnhancedRAGSystem:'):content.find('class EnhancedRAGSystem:') + 500]:
        # Find and wrap the initialization
        init_start = content.find('def __init__(self, temperature: float = 0.7, model: str = "deepseek-chat"):')
        init_end = content.find('self.doc_chain = LLMChain', init_start)
        
        if init_start != -1 and init_end != -1:
            # Get the initialization code
            init_code = content[init_start:init_end]
            
            # Add try-catch wrapper
            new_init = init_code.replace(
                '# Initialize DeepSeek LLM\\n        self.llm = DeepSeekLLM(',
                '''# Initialize DeepSeek LLM with error handling
        try:
            self.llm = DeepSeekLLM('''
            ) + '''        
            self.mode = "operational"
            print("✅ RAG System initialized successfully")
        except Exception as e:
            print(f"⚠️ RAG initialization error: {e}")
            print("🔄 Falling back to basic mode")
            self.llm = None
            self.mode = "error"
            # Create fallback prompts
            self.doc_template = "Answer based on context: {context}\\n\\nQuestion: {question}\\n\\nAnswer:"
            self.general_template = "Answer the question: {question}\\n\\nAnswer:"
            return  # Skip LangChain initialization
        
        # Only initialize LangChain components if successful
        if LANGCHAIN_AVAILABLE and self.mode == "operational":
            try:'''
            
            # Replace in content
            content = content.replace(init_code, new_init)
    
    # Add fallback intelligent_answer method
    if 'def simple_answer(' not in content:
        fallback_method = '''
    async def simple_answer(self, question: str, context: str = "") -> str:
        """Fallback answer method when LangChain is not available"""
        if not self.llm:
            return "Sorry, the system is not properly configured. Please check environment variables."
        
        try:
            if context:
                prompt = f"Answer based on the provided context:\\n\\nContext: {context}\\n\\nQuestion: {question}\\n\\nAnswer:"
            else:
                prompt = f"Answer this question: {question}\\n\\nAnswer:"
            
            # Use the DeepSeek API directly
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    return f"API Error: {response.status_code}"
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    '''
        
        # Add before the get_system_stats method
        stats_pos = content.find('def get_system_stats(self)')
        if stats_pos != -1:
            content = content[:stats_pos] + fallback_method + '\\n' + content[stats_pos:]
    
    # Update intelligent_answer to use fallback
    if 'if self.mode == "error":' not in content:
        intelligent_pos = content.find('async def intelligent_answer(')
        if intelligent_pos != -1:
            method_end = content.find('def get_system_stats(', intelligent_pos)
            old_method = content[intelligent_pos:method_end]
            
            new_method = '''async def intelligent_answer(self, question: str, documents: Optional[List[Document]] = None,
                               strategy: str = "auto") -> Dict:
        """
        Intelligently choose the best answering strategy with Railway deployment support
        """
        # Fallback for Railway deployment issues
        if self.mode == "error" or not LANGCHAIN_AVAILABLE:
            context = ""
            if documents:
                context = "\\n\\n".join([
                    f"Document: {getattr(doc, 'metadata', {}).get('source', 'Unknown')}\\n{getattr(doc, 'page_content', str(doc))}"
                    for doc in documents[:3]
                ])
            
            answer = await self.simple_answer(question, context)
            return {
                "answer": answer,
                "source_type": "documents" if context else "general_knowledge",
                "strategy_used": "railway_fallback"
            }
        
        # Original LangChain implementation (when available)
        try:
            start_time = time.time()
            
            # Analyze question type
            question_lower = question.lower()
            is_specific_query = any(word in question_lower for word in 
                                  ["document", "file", "uploaded", "this", "these", "according to"])
            
            # Auto strategy selection
            if strategy == "auto":
                if documents and len(documents) > 0:
                    if is_specific_query:
                        strategy = "docs_only"
                    else:
                        # Try documents first, fallback to hybrid if not relevant enough
                        doc_result = await self.generate_answer_from_docs(question, documents)
                        if doc_result.get("relevance") in ["high", "medium"]:
                            strategy = "docs_only"
                            final_result = doc_result
                        else:
                            strategy = "hybrid"
                else:
                    strategy = "general_only"
            
            # Execute chosen strategy
            if strategy == "docs_only" and documents:
                if 'final_result' not in locals():
                    final_result = await self.generate_answer_from_docs(question, documents)
                
                if not final_result.get("answer"):
                    # Fallback to general knowledge if no good answer from docs
                    logger.info("Falling back to general knowledge due to poor document relevance")
                    final_result = await self.generate_general_answer(question)
                    final_result["fallback_reason"] = "low_document_relevance"
                    
            elif strategy == "hybrid" and documents:
                final_result = await self.generate_hybrid_answer(question, documents)
                
            else:  # general_only or no documents available
                final_result = await self.generate_general_answer(question)
            
            # Add metadata
            final_result["strategy_used"] = strategy
            final_result["total_processing_time"] = time.time() - start_time
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error in intelligent_answer: {e}")
            # Fallback to simple answer
            context = ""
            if documents:
                context = "\\n\\n".join([
                    f"Document: {getattr(doc, 'metadata', {}).get('source', 'Unknown')}\\n{getattr(doc, 'page_content', str(doc))}"
                    for doc in documents[:3]
                ])
            
            answer = await self.simple_answer(question, context)
            return {
                "answer": answer,
                "source_type": "documents" if context else "general_knowledge", 
                "strategy_used": "error_fallback"
            }
    '''
            
            content = content.replace(old_method, new_method)
    
    # Write the updated file
    with open(rag_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Railway deployment fixes applied successfully!")
    print("📝 Changes made:")
    print("   - Added robust import handling")  
    print("   - Added error handling for LangChain initialization")
    print("   - Added fallback methods for Railway deployment")
    print("   - Enhanced intelligent_answer with error recovery")

if __name__ == "__main__":
    apply_railway_fix()