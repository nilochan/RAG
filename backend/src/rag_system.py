from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms.base import LLM
from typing import List, Dict, Optional, Any
from langchain.schema import Document
import logging
import time
import asyncio
import httpx
import os
import json
from pydantic import Field

logger = logging.getLogger(__name__)

class DeepSeekLLM(LLM):
    """Custom DeepSeek LLM wrapper for LangChain"""
    
    api_key: str = Field(..., description="DeepSeek API key")
    base_url: str = Field(default="https://api.deepseek.com/v1", description="DeepSeek API base URL")
    model: str = Field(default="deepseek-chat", description="DeepSeek model name")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: int = Field(default=2000, description="Maximum tokens to generate")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.api_key:
            self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")
    
    @property
    def _llm_type(self) -> str:
        return "deepseek"
    
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
        # Initialize DeepSeek LLM
        self.llm = DeepSeekLLM(
            temperature=temperature,
            model=model,
            api_key=os.getenv("DEEPSEEK_API_KEY", "")
        )
        
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
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        return {
            "model": self.llm.model_name,
            "temperature": self.llm.temperature,
            "available_chains": ["document", "general", "hybrid"],
            "status": "operational"
        }