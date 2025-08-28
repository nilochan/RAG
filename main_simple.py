#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal Educational RAG Platform for Railway deployment
"""

from fastapi import FastAPI
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Educational RAG Platform - Minimal",
    version="1.0.0",
    description="Minimal version for Railway deployment testing"
)

@app.on_startup
async def startup_event():
    """Initialize the system"""
    logger.info("🚀 Educational RAG Platform (Minimal) starting up...")
    logger.info("✅ FastAPI server ready for deployment")

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "message": "Educational RAG Platform API - Minimal Version",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "railway_deployment": "success",
        "next_step": "Add full features once basic deployment works"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "educational-rag-platform",
        "railway_deployment": "success"
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify deployment"""
    return {
        "test": "success",
        "message": "Railway deployment working!",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    # Railway provides PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)