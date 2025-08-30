#!/usr/bin/env python3
"""Simple RAG system test without complex dependencies"""

import asyncio
import os
import json
import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Simple RAG Test", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple document storage (in-memory for testing)
documents = []

class SimpleRAG:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")
    
    async def answer_query(self, question: str, context: str = None):
        """Generate answer using DeepSeek API"""
        try:
            if context:
                prompt = f"""You are an educational AI assistant. Answer the question based on the provided context.

Context from uploaded documents:
{context}

Question: {question}

Instructions:
- Provide a clear, educational answer based on the context
- If the context doesn't fully answer the question, say so and provide what you can
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
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
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
                    return result['choices'][0]['message']['content'].strip()
                else:
                    return f"Error: API call failed with status {response.status_code}"
                    
        except Exception as e:
            return f"Error processing query: {str(e)}"

# Initialize RAG system
try:
    rag = SimpleRAG()
    print("SUCCESS: SimpleRAG initialized successfully")
except Exception as e:
    print(f"ERROR: Failed to initialize SimpleRAG: {e}")
    rag = None

@app.get("/")
async def root():
    return {
        "message": "Simple RAG System Test",
        "status": "operational" if rag else "failed",
        "endpoints": {
            "upload": "/upload",
            "query": "/query",
            "documents": "/documents",
            "health": "/health"
        }
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a document (simplified)"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Read file content
        content = await file.read()
        
        if file.filename.endswith('.txt'):
            text_content = content.decode('utf-8')
        elif file.filename.endswith('.pdf'):
            # Simple PDF handling - just save raw content for now
            text_content = f"PDF file uploaded: {file.filename} ({len(content)} bytes)"
        else:
            text_content = f"File uploaded: {file.filename} ({len(content)} bytes)"
        
        # Store document
        doc_id = len(documents) + 1
        doc_record = {
            "id": doc_id,
            "filename": file.filename,
            "content": text_content,
            "size": len(content)
        }
        documents.append(doc_record)
        
        return {
            "message": "File uploaded successfully",
            "document_id": doc_id,
            "filename": file.filename,
            "content_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_documents(request: dict):
    """Query the RAG system"""
    try:
        question = request.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        if not rag:
            raise HTTPException(status_code=500, detail="RAG system not initialized")
        
        # Prepare context from uploaded documents
        context = ""
        if documents:
            context = "\\n\\n".join([
                f"Document: {doc['filename']}\\nContent: {doc['content']}"
                for doc in documents[-3:]  # Last 3 documents
            ])
        
        # Generate answer
        answer = await rag.answer_query(question, context if documents else None)
        
        return {
            "answer": answer,
            "sources": [doc["filename"] for doc in documents[-3:]] if documents else [],
            "has_context": bool(documents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def get_documents():
    """Get uploaded documents"""
    return {
        "documents": [
            {
                "id": doc["id"],
                "filename": doc["filename"],
                "size": doc["size"],
                "preview": doc["content"][:100] + "..." if len(doc["content"]) > 100 else doc["content"]
            }
            for doc in documents
        ]
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "rag_initialized": rag is not None,
        "documents_count": len(documents),
        "deepseek_api": "configured" if os.getenv("DEEPSEEK_API_KEY") else "missing"
    }

if __name__ == "__main__":
    print("Starting Simple RAG Test Server...")
    print("DeepSeek API Key:", "Found" if os.getenv("DEEPSEEK_API_KEY") else "Missing")
    print("Server will be available at: http://localhost:8000")
    print("Health check: http://localhost:8000/health")
    print("API docs: http://localhost:8000/docs")
    
    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)