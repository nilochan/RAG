"""
Simple document processor that works without OpenAI embeddings
Uses text similarity for Railway deployment
"""
import os
import json
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SimpleDocumentProcessor:
    """Document processor that works without embeddings - Railway compatible"""
    
    def __init__(self, pinecone_index_name: str = None):
        self.documents_store: Dict[int, Dict] = {}  # In-memory document storage
        logger.info("🚀 Simple document processor initialized (Railway compatible)")
    
    def register_progress_callback(self, doc_id: int, callback):
        """Register progress callback - simplified"""
        self.progress_callback = callback
    
    def update_progress(self, doc_id: int, progress: int):
        """Update progress"""
        if hasattr(self, 'progress_callback'):
            self.progress_callback(progress)
    
    def extract_text(self, file_content: bytes, file_type: str, filename: str) -> str:
        """Extract text from different file types"""
        try:
            if file_type.lower() == 'txt':
                return file_content.decode('utf-8')
            elif file_type.lower() == 'pdf':
                return self._extract_pdf_text(file_content)
            elif file_type.lower() in ['docx', 'doc']:
                return self._extract_docx_text(file_content)
            else:
                # For other types, return basic info
                return f"Document: {filename}\\nFile type: {file_type}\\nSize: {len(file_content)} bytes"
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {e}")
            return f"Error processing {filename}: {str(e)}"
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Basic PDF text extraction"""
        try:
            import PyPDF2
            import io
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\\n"
            return text
        except Exception as e:
            logger.warning(f"PDF extraction failed: {e}")
            return "PDF content could not be extracted"
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Basic DOCX text extraction"""
        try:
            import docx
            import io
            doc = docx.Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\\n"
            return text
        except Exception as e:
            logger.warning(f"DOCX extraction failed: {e}")
            return "DOCX content could not be extracted"
    
    async def process_document(self, file_content: bytes, filename: str, file_type: str, doc_id: int) -> Dict:
        """Process document and store in memory"""
        try:
            self.update_progress(doc_id, 10)
            
            # Extract text
            text_content = self.extract_text(file_content, file_type, filename)
            self.update_progress(doc_id, 50)
            
            # Simple chunking (split by paragraphs)
            chunks = self._simple_chunk(text_content)
            self.update_progress(doc_id, 80)
            
            # Store document
            self.documents_store[doc_id] = {
                'filename': filename,
                'content': text_content,
                'chunks': chunks,
                'file_type': file_type
            }
            
            self.update_progress(doc_id, 100)
            logger.info(f"✅ Document {filename} processed: {len(chunks)} chunks")
            
            return {
                "success": True,
                "chunk_count": len(chunks),
                "vector_ids": [f"simple_{doc_id}_{i}" for i in range(len(chunks))],
                "text_length": len(text_content),
                "processing_time": 0
            }
            
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            return {
                "success": False,
                "error": str(e),
                "chunk_count": 0,
                "vector_ids": []
            }
    
    def _simple_chunk(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Simple text chunking"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def search_documents(self, query: str, doc_ids: List[int] = None, k: int = 3) -> List:
        """Simple text-based document search"""
        results = []
        
        # Get relevant documents
        search_docs = doc_ids if doc_ids else list(self.documents_store.keys())
        
        for doc_id in search_docs:
            if doc_id in self.documents_store:
                doc_data = self.documents_store[doc_id]
                
                # Simple keyword matching
                query_words = query.lower().split()
                content = doc_data['content'].lower()
                
                # Calculate simple relevance score
                matches = sum(1 for word in query_words if word in content)
                if matches > 0:
                    # Create a document-like object
                    doc_result = type('Document', (), {
                        'page_content': doc_data['content'][:1000] + "..." if len(doc_data['content']) > 1000 else doc_data['content'],
                        'metadata': {
                            'source': doc_data['filename'],
                            'doc_id': doc_id,
                            'file_type': doc_data['file_type']
                        },
                        'score': matches / len(query_words)
                    })()
                    results.append(doc_result)
        
        # Sort by relevance and return top k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:k]
    
    def delete_document_vectors(self, vector_ids: List[str]) -> bool:
        """Delete document from memory storage"""
        try:
            # Extract doc_id from vector_ids
            for vector_id in vector_ids:
                if vector_id.startswith('simple_'):
                    doc_id = int(vector_id.split('_')[1])
                    if doc_id in self.documents_store:
                        del self.documents_store[doc_id]
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def get_processing_stats(self) -> Dict:
        """Get processing statistics"""
        return {
            "active_processors": 0,
            "vectorstore_status": "simple_mode",
            "embedding_model": "text_similarity",
            "documents_stored": len(self.documents_store)
        }