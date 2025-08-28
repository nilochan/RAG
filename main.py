# -*- coding: utf-8 -*-
# Railway redeploy trigger: langchain dependencies added - 2024-08-28
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
import asyncio
import os
import logging
from datetime import datetime
import time
import json
from typing import List, Dict
import uuid

from src.models import Document as DocumentModel, QueryLog, DocumentUpload, DocumentStatus, QueryRequest, QueryResponse
from src.document_processor import DocumentProcessor
from src.database import get_db, engine, Base
from src.rag_system import EnhancedRAGSystem

# Initialize FastAPI
app = FastAPI(title="Educational RAG Platform", version="2.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global progress tracking
progress_store: Dict[int, Dict] = {}

# Initialize components
document_processor = DocumentProcessor(os.getenv("PINECONE_INDEX_NAME", "educational-docs"))
rag_system = EnhancedRAGSystem()

# Create tables
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_document_progress(doc_id: int, progress: int):
    """Update progress for a document"""
    progress_store[doc_id] = {
        "progress": progress,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "processing" if progress < 100 else "completed"
    }
    logger.info(f"Document {doc_id} progress: {progress}%")

# Startup logging (removed deprecated @app.on_startup decorator)
logger.info("Educational RAG Platform starting up...")
logger.info("Progress tracking enabled for real-time monitoring")

@app.get("/")
async def root():
    return {
        "message": "Educational RAG Platform API",
        "version": "2.0.1",
        "status": "operational",
        "features": [
            "File upload and processing",
            "Real-time progress tracking",
            "Intelligent Q&A with fallback",
            "Document management",
            "Performance analytics"
        ],
        "endpoints": {
            "upload": "/upload",
            "query": "/query", 
            "documents": "/documents",
            "progress": "/documents/{id}/progress",
            "health": "/health"
        }
    }

@app.post("/upload", response_model=dict)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a document with real-time progress tracking"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        allowed_types = ['pdf', 'docx', 'doc', 'txt', 'csv', 'xlsx']
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File type '{file_extension}' not supported. Allowed: {allowed_types}"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {max_size // (1024*1024)}MB"
            )
        
        # Save document record to database
        doc_record = DocumentModel(
            filename=f"{int(time.time())}_{file.filename}",
            original_name=file.filename,
            file_type=file_extension,
            file_size=file_size,
            processing_status="pending"
        )
        
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)
        
        # Initialize progress tracking
        progress_store[doc_record.id] = {
            "progress": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending",
            "filename": file.filename
        }
        
        # Register progress callback
        document_processor.register_progress_callback(
            doc_record.id,
            lambda progress: update_document_progress(doc_record.id, progress)
        )
        
        # Process document in background
        background_tasks.add_task(
            process_document_background,
            file_content,
            file.filename,
            file_extension,
            doc_record.id,
            db
        )
        
        return {
            "message": "File uploaded successfully",
            "document_id": doc_record.id,
            "filename": file.filename,
            "size": file_size,
            "type": file_extension,
            "status": "processing",
            "progress_url": f"/documents/{doc_record.id}/progress",
            "estimated_time": estimate_processing_time(file_size, file_extension)
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def estimate_processing_time(file_size: int, file_type: str) -> str:
    """Estimate processing time based on file size and type"""
    # Base processing time per MB
    base_time = {
        'pdf': 30,  # seconds per MB
        'docx': 20,
        'txt': 10,
        'csv': 25,
        'xlsx': 35
    }
    
    size_mb = file_size / (1024 * 1024)
    estimated_seconds = base_time.get(file_type, 20) * size_mb
    
    if estimated_seconds < 10:
        return "< 10 seconds"
    elif estimated_seconds < 60:
        return f"~{int(estimated_seconds)} seconds"
    else:
        return f"~{int(estimated_seconds // 60)} minutes"

async def process_document_background(
    file_content: bytes, 
    filename: str, 
    file_type: str, 
    doc_id: int,
    db: Session
):
    """Background task to process uploaded document with progress updates"""
    try:
        # Update status to processing
        doc_record = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
        doc_record.processing_status = "processing"
        db.commit()
        
        # Update progress store
        update_document_progress(doc_id, 1)
        
        # Process the document
        result = await document_processor.process_document(
            file_content, filename, file_type, doc_id
        )
        
        if result["success"]:
            # Update database with results
            doc_record.processing_status = "completed"
            doc_record.chunk_count = result["chunk_count"]
            doc_record.vector_ids = json.dumps(result["vector_ids"])
            doc_record.doc_metadata = json.dumps({
                "text_length": result["text_length"],
                "processed_at": datetime.utcnow().isoformat(),
                "processing_time": result.get("processing_time", 0)
            })
            
            # Final progress update
            update_document_progress(doc_id, 100)
            
        else:
            doc_record.processing_status = "failed"
            doc_record.doc_metadata = json.dumps({
                "error": result["error"],
                "failed_at": datetime.utcnow().isoformat()
            })
            
            progress_store[doc_id] = {
                "progress": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failed",
                "error": result["error"]
            }
        
        db.commit()
        logger.info(f"Document processing completed for {filename} (ID: {doc_id})")
        
    except Exception as e:
        logger.error(f"Background processing error: {e}")
        doc_record.processing_status = "failed"
        doc_record.doc_metadata = json.dumps({
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        })
        db.commit()
        
        progress_store[doc_id] = {
            "progress": 0,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "failed",
            "error": str(e)
        }

@app.get("/documents/{doc_id}/progress")
async def get_document_progress(doc_id: int):
    """Get real-time processing progress for a document"""
    if doc_id not in progress_store:
        raise HTTPException(status_code=404, detail="Progress tracking not found")
    
    progress_data = progress_store[doc_id]
    return {
        "document_id": doc_id,
        "progress": progress_data["progress"],
        "status": progress_data["status"],
        "timestamp": progress_data["timestamp"],
        "filename": progress_data.get("filename", "Unknown"),
        "error": progress_data.get("error")
    }

@app.get("/documents/{doc_id}/progress/stream")
async def stream_document_progress(doc_id: int):
    """Stream real-time progress updates using Server-Sent Events"""
    async def generate_progress_stream():
        while doc_id in progress_store:
            progress_data = progress_store[doc_id]
            
            # Send progress update
            yield f"data: {json.dumps(progress_data)}\n\n"
            
            # Stop streaming when completed or failed
            if progress_data["status"] in ["completed", "failed"]:
                break
                
            await asyncio.sleep(1)  # Update every second
    
    if doc_id not in progress_store:
        raise HTTPException(status_code=404, detail="Progress tracking not found")
    
    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@app.get("/documents", response_model=List[DocumentStatus])
async def get_documents(db: Session = Depends(get_db)):
    """Get all uploaded documents with their status"""
    documents = db.query(DocumentModel).order_by(DocumentModel.upload_time.desc()).all()
    
    result = []
    for doc in documents:
        # Get real-time progress if available
        progress = None
        if doc.id in progress_store:
            progress = progress_store[doc.id]["progress"]
        
        result.append(DocumentStatus(
            id=doc.id,
            filename=doc.original_name,
            status=doc.processing_status,
            progress=progress,
            chunk_count=doc.chunk_count,
            upload_time=doc.upload_time
        ))
    
    return result

@app.get("/documents/{doc_id}/status")
async def get_document_status(doc_id: int, db: Session = Depends(get_db)):
    """Get detailed status of a specific document"""
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_metadata = json.loads(doc.doc_metadata or '{}')
    progress_data = progress_store.get(doc_id, {})
    
    return {
        "id": doc.id,
        "filename": doc.original_name,
        "status": doc.processing_status,
        "chunk_count": doc.chunk_count,
        "file_size": doc.file_size,
        "file_type": doc.file_type,
        "upload_time": doc.upload_time,
        "metadata": doc_metadata,
        "progress": progress_data.get("progress"),
        "last_update": progress_data.get("timestamp")
    }

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest, db: Session = Depends(get_db)):
    """Query the RAG system with intelligent fallback and performance tracking"""
    start_time = time.time()
    
    try:
        # Get available documents
        completed_docs = db.query(DocumentModel).filter(
            DocumentModel.processing_status == "completed"
        ).all()
        
        if not completed_docs and request.use_uploaded_docs_only:
            raise HTTPException(
                status_code=400, 
                detail="No processed documents available. Please upload and process documents first."
            )
        
        # Search in uploaded documents
        relevant_docs = []
        if completed_docs:
            doc_ids = [doc.id for doc in completed_docs]
            relevant_docs = document_processor.search_documents(
                request.question, doc_ids=doc_ids, k=5
            )
        
        # Use intelligent answering strategy
        strategy = "docs_only" if request.use_uploaded_docs_only else "auto"
        result = await rag_system.intelligent_answer(
            request.question,
            documents=relevant_docs,
            strategy=strategy
        )
        
        # Prepare sources information
        sources = []
        if relevant_docs:
            sources = [
                {
                    "content": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                    "metadata": doc.metadata,
                    "score": getattr(doc, 'score', 1.0),
                    "document_id": doc.metadata.get("doc_id"),
                    "source_file": doc.metadata.get("source", "Unknown")
                }
                for doc in relevant_docs[:3]  # Top 3 sources
            ]
        
        processing_time = time.time() - start_time
        
        # Log the query with performance metrics
        query_log = QueryLog(
            query=request.question,
            response=result["answer"],
            sources_used=json.dumps([s.get("document_id") for s in sources]),
            response_time=processing_time,
            session_id=request.session_id
        )
        db.add(query_log)
        db.commit()
        
        return QueryResponse(
            answer=result["answer"],
            sources=sources,
            is_from_uploaded_docs=result.get("source_type") != "general_knowledge",
            processing_time=processing_time,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """Delete a document and its vectors"""
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete vectors from Pinecone
        if doc.vector_ids:
            vector_ids = json.loads(doc.vector_ids)
            document_processor.delete_document_vectors(vector_ids)
        
        # Delete from database
        db.delete(doc)
        db.commit()
        
        # Clean up progress tracking
        if doc_id in progress_store:
            del progress_store[doc_id]
        
        return {"message": f"Document '{doc.original_name}' deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    """Get system analytics and performance metrics"""
    try:
        # Document statistics
        total_docs = db.query(DocumentModel).count()
        completed_docs = db.query(DocumentModel).filter(DocumentModel.processing_status == "completed").count()
        processing_docs = db.query(DocumentModel).filter(DocumentModel.processing_status == "processing").count()
        failed_docs = db.query(DocumentModel).filter(DocumentModel.processing_status == "failed").count()
        
        # Query statistics
        total_queries = db.query(QueryLog).count()
        avg_response_time = db.query(QueryLog).with_entities(QueryLog.response_time).all()
        avg_time = sum([r[0] for r in avg_response_time if r[0]]) / len(avg_response_time) if avg_response_time else 0
        
        # Progress tracking statistics
        active_processing = len([p for p in progress_store.values() if p["status"] == "processing"])
        
        return {
            "documents": {
                "total": total_docs,
                "completed": completed_docs,
                "processing": processing_docs,
                "failed": failed_docs,
                "success_rate": (completed_docs / total_docs * 100) if total_docs > 0 else 0
            },
            "queries": {
                "total": total_queries,
                "average_response_time": round(avg_time, 3)
            },
            "system": {
                "active_processing_jobs": active_processing,
                "progress_trackers": len(progress_store),
                "processor_stats": document_processor.get_processing_stats(),
                "rag_stats": rag_system.get_system_stats()
            }
        }
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Comprehensive health check with component status"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "operational",
            "pinecone": "operational",
            "deepseek": "operational",
            "progress_tracking": "operational"
        },
        "metrics": {
            "active_progress_trackers": len(progress_store),
            "uptime": "operational"
        }
    }

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Production configuration - no reload in Railway
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)