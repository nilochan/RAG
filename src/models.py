from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_time = Column(DateTime, server_default=func.now())
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    chunk_count = Column(Integer, default=0)
    vector_ids = Column(Text)  # JSON list of vector IDs in Pinecone
    doc_metadata = Column(Text)  # JSON metadata

class QueryLog(Base):
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    sources_used = Column(Text)  # JSON list of document IDs
    response_time = Column(Float)
    timestamp = Column(DateTime, server_default=func.now())
    session_id = Column(String(100))

# Pydantic Models
class DocumentUpload(BaseModel):
    file_content: bytes
    filename: str
    file_type: str

class DocumentStatus(BaseModel):
    id: int
    filename: str
    status: str
    progress: Optional[int] = None
    chunk_count: Optional[int] = None
    upload_time: datetime

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = "default"
    use_uploaded_docs_only: Optional[bool] = False

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict]
    is_from_uploaded_docs: bool
    processing_time: float
    session_id: str