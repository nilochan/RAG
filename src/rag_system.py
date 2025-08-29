# Railway deployment - robust imports with fallbacks
try:
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain.llms.base import LLM
    from langchain.schema import Document
    from pydantic import Field
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"LangChain dependencies not fully available: {e}")
    print("Falling back to simplified mode for Railway deployment")
    LANGCHAIN_AVAILABLE = False
    # Create minimal fallback classes
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
import json

logger = logging.getLogger(__name__)

class DeepSeekLLM(LLM):
    """Custom DeepSeek LLM wrapper for LangChain with Railway compatibility"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com/v1", 
                 model: str = "deepseek-chat", temperature: float = 0.7, max_tokens: int = 2000, **kwargs):
        # Initialize without Field annotations to avoid JSON serialization issues
        if LANGCHAIN_AVAILABLE:
            super().__init__(**kwargs)
        
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")
    
    @property
    def _llm_type(self) -> str:
        return "deepseek" if LANGCHAIN_AVAILABLE else "deepseek-simple"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Synchronous call to DeepSeek API"""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"
    
    async def _acall(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Asynchronous call to DeepSeek API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"

class EnhancedRAGSystem:
    def __init__(self, temperature: float = 0.7, model: str = "deepseek-chat"):
        self.temperature = temperature
        self.model = model
        self.railway_mode = True  # Default to Railway mode for safety
        
        # Try to initialize LangChain components
        if LANGCHAIN_AVAILABLE:
            try:
                self.llm = DeepSeekLLM(
                    temperature=temperature,
                    model=model,
                    api_key=os.getenv("DEEPSEEK_API_KEY", "")
                )
                # Test that the LLM can be used without JSON serialization issues
                _ = self.llm.model  # Test attribute access
                self.railway_mode = False
                logger.info("✅ RAG system initialized with full LangChain support")
            except Exception as e:
                logger.warning(f"⚠️ LangChain initialization failed: {e}")
                logger.info("🔄 Using Railway-compatible mode")
                self.llm = None
                self.railway_mode = True
                return  # Skip LangChain initialization
        else:
            logger.info("🔄 LangChain not available - using Railway-compatible mode")
            self.llm = None
            return
            
        # Prompt for answering from documents
        self.doc_prompt = PromptTemplate(
            input_variables=["question", "context"],
            template="""
            You are an educational AI assistant. Answer the question based on the provided context from uploaded documents.
            
            Context from documents:
            {context}
            
            Question: {question}
            
            Instructions:
            - Provide a clear, educational answer based on the context
            - If the context doesn't fully answer the question, say so and provide what you can
            - Use examples from the context when possible
            - Be concise but comprehensive
            - Format your answer in a student-friendly way
            - Always cite which document or source you're referencing
            
            Answer:
            """
        )
        
        # Prompt for general knowledge fallback
        self.general_prompt = PromptTemplate(
            input_variables=["question"],
            template="""
            You are an educational AI assistant. Answer this question using your general knowledge.
            
            Question: {question}
            
            Instructions:
            - Provide a clear, educational explanation
            - Use examples and analogies when helpful
            - Break down complex topics into understandable parts
            - Be encouraging and supportive
            - If it's a programming question, include code examples
            - Structure your answer with clear sections if the topic is complex
            
            Answer:
            """
        )
        
        # Prompt for hybrid answers (combining docs + general knowledge)
        self.hybrid_prompt = PromptTemplate(
            input_variables=["question", "context", "general_knowledge"],
            template="""
            You are an educational AI assistant. Answer the question by combining information from uploaded documents with your general knowledge.
            
            Context from uploaded documents:
            {context}
            
            General knowledge context:
            {general_knowledge}
            
            Question: {question}
            
            Instructions:
            - Combine information from both sources intelligently
            - Clearly distinguish between document-based info and general knowledge
            - Provide a comprehensive answer that leverages both sources
            - Use examples from documents when available
            - Fill gaps with general knowledge when documents are incomplete
            - Be educational and student-friendly
            
            Answer:
            """
        )
        
        self.doc_chain = LLMChain(llm=self.llm, prompt=self.doc_prompt)
        self.general_chain = LLMChain(llm=self.llm, prompt=self.general_prompt)
        self.hybrid_chain = LLMChain(llm=self.llm, prompt=self.hybrid_prompt)
    
    async def generate_answer_from_docs(self, question: str, documents: List[Document], 
                                      min_relevance_score: float = 0.5) -> Dict:
        """Generate answer based on retrieved documents with relevance checking"""
        try:
            start_time = time.time()
            
            # Filter documents by relevance if scores are available
            relevant_docs = []
            for doc in documents:
                score = getattr(doc, 'score', 1.0)  # Default score if not available
                if score >= min_relevance_score:
                    relevant_docs.append(doc)
            
            if not relevant_docs:
                logger.info("No sufficiently relevant documents found")
                return {
                    "answer": None,
                    "relevance": "low",
                    "sources_used": 0,
                    "processing_time": time.time() - start_time
                }
            
            # Combine document content with source information
            context_parts = []
            for i, doc in enumerate(relevant_docs):
                source_info = doc.metadata.get("source", f"Document {i+1}")
                context_parts.append(f"Source: {source_info}\nContent: {doc.page_content}\n")
            
            context = "\n---\n".join(context_parts)
            
            # Generate answer
            result = await self.doc_chain.arun(question=question, context=context)
            
            processing_time = time.time() - start_time
            
            return {
                "answer": result.strip(),
                "relevance": "high" if len(relevant_docs) >= 2 else "medium",
                "sources_used": len(relevant_docs),
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error generating answer from docs: {e}")
            return {
                "answer": None,
                "error": str(e),
                "relevance": "error",
                "sources_used": 0,
                "processing_time": 0
            }
    
    async def generate_general_answer(self, question: str) -> Dict:
        """Generate answer using general knowledge"""
        try:
            start_time = time.time()
            result = await self.general_chain.arun(question=question)
            processing_time = time.time() - start_time
            
            return {
                "answer": result.strip(),
                "source_type": "general_knowledge",
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error generating general answer: {e}")
            return {
                "answer": f"Sorry, I encountered an error while answering your question: {str(e)}",
                "source_type": "error",
                "processing_time": 0
            }
    
    async def generate_hybrid_answer(self, question: str, documents: List[Document]) -> Dict:
        """Generate answer combining documents and general knowledge"""
        try:
            start_time = time.time()
            
            # Get document-based context
            doc_context = "\n\n".join([
                f"Document: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}"
                for doc in documents[:3]  # Limit to top 3 documents
            ])
            
            # Get general knowledge context (abbreviated)
            general_result = await self.generate_general_answer(question)
            general_knowledge = general_result["answer"][:500] + "..." if len(general_result["answer"]) > 500 else general_result["answer"]
            
            # Generate hybrid answer
            result = await self.hybrid_chain.arun(
                question=question,
                context=doc_context,
                general_knowledge=general_knowledge
            )
            
            processing_time = time.time() - start_time
            
            return {
                "answer": result.strip(),
                "source_type": "hybrid",
                "sources_used": len(documents),
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error generating hybrid answer: {e}")
            return {
                "answer": f"Sorry, I encountered an error while processing your question: {str(e)}",
                "source_type": "error",
                "processing_time": 0
            }
    
    async def intelligent_answer(self, question: str, documents: Optional[List[Document]] = None,
                               strategy: str = "auto") -> Dict:
        """
        Intelligently choose the best answering strategy based on available documents and question type
        
        Strategies:
        - auto: Automatically choose the best approach
        - docs_only: Use only uploaded documents
        - general_only: Use only general knowledge
        - hybrid: Combine documents and general knowledge
        """
        # Railway deployment fallback mode
        if hasattr(self, 'railway_mode') and self.railway_mode:
            return await self._railway_fallback_answer(question, documents)
        
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
            return {
                "answer": f"I apologize, but I encountered an error processing your question: {str(e)}",
                "source_type": "error",
                "strategy_used": "error",
                "processing_time": 0
            }
    
    async def _railway_fallback_answer(self, question: str, documents: Optional[List[Document]] = None) -> Dict:
        """Railway deployment fallback - direct DeepSeek API call without LangChain"""
        try:
            # Build context from documents if available
            context = ""
            if documents:
                context_parts = []
                for i, doc in enumerate(documents[:3]):
                    if hasattr(doc, 'page_content'):
                        source = getattr(doc, 'metadata', {}).get('source', f'Document {i+1}')
                        content = doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
                        context_parts.append(f"Source: {source}\\nContent: {content}")
                context = "\\n\\n---\\n\\n".join(context_parts)
            
            # Create prompt based on whether we have context
            if context:
                prompt = f"""You are an educational AI assistant. Answer the question based on the provided context from uploaded documents.

Context from documents:
{context}

Question: {question}

Instructions:
- Provide a clear, educational answer based on the context
- If the context doesn't fully answer the question, say so and provide what you can
- Use examples from the context when possible
- Be concise but comprehensive

Answer:"""
            else:
                prompt = f"""You are an educational AI assistant. Answer this question using your general knowledge.

Question: {question}

Instructions:
- Provide a clear, educational explanation
- Use examples when helpful
- Be encouraging and supportive

Answer:"""
            
            # Direct DeepSeek API call
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                return {
                    "answer": "DeepSeek API key not configured. Please check your Railway environment variables.",
                    "source_type": "error",
                    "strategy_used": "railway_error"
                }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
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
                    answer = result['choices'][0]['message']['content'].strip()
                    return {
                        "answer": answer,
                        "source_type": "documents" if context else "general_knowledge",
                        "strategy_used": "railway_fallback",
                        "mode": "railway_compatible"
                    }
                else:
                    return {
                        "answer": f"DeepSeek API error: {response.status_code}. Please check your API key configuration.",
                        "source_type": "error",
                        "strategy_used": "railway_error"
                    }
                    
        except Exception as e:
            return {
                "answer": f"Railway fallback error: {str(e)}. Please check your environment configuration.",
                "source_type": "error",
                "strategy_used": "railway_error"
            }
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        if hasattr(self, 'railway_mode') and self.railway_mode:
            return {
                "model": getattr(self, 'model', 'deepseek-chat'),
                "temperature": getattr(self, 'temperature', 0.7),
                "available_chains": ["railway_fallback"],
                "status": "operational",
                "mode": "railway_compatible",
                "langchain_available": LANGCHAIN_AVAILABLE
            }
        else:
            return {
                "model": self.llm.model if hasattr(self.llm, 'model') else 'deepseek-chat',
                "temperature": getattr(self.llm, 'temperature', 0.7),
                "available_chains": ["document", "general", "hybrid"],
                "status": "operational",
                "mode": "langchain_full"
            }