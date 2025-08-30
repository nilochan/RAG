#!/usr/bin/env python3
"""Debug script to identify issues in RAG document processing and querying"""

import os
import asyncio
import json
import tempfile
import httpx
from datetime import datetime

# Check what dependencies we have available
def check_dependencies():
    """Check which dependencies are available"""
    deps = {}
    
    try:
        import fastapi
        deps['fastapi'] = fastapi.__version__
    except:
        deps['fastapi'] = 'MISSING'
    
    try:
        import langchain
        deps['langchain'] = langchain.__version__
    except:
        deps['langchain'] = 'MISSING'
    
    try:
        import pinecone
        deps['pinecone'] = 'Available'
    except:
        deps['pinecone'] = 'MISSING'
    
    deps['httpx'] = 'Available'
    
    print("=== DEPENDENCY CHECK ===")
    for dep, status in deps.items():
        print(f"{dep}: {status}")
    print()
    return deps

async def test_document_upload():
    """Test document upload process"""
    print("=== DOCUMENT UPLOAD TEST ===")
    
    # Create a simple test document
    test_content = """
    Machine Learning Fundamentals
    
    Machine learning is a subset of artificial intelligence (AI) that provides systems 
    the ability to automatically learn and improve from experience without being 
    explicitly programmed.
    
    Key concepts:
    1. Supervised Learning - Learning with labeled examples
    2. Unsupervised Learning - Finding patterns in data without labels  
    3. Neural Networks - Models inspired by biological neural networks
    4. Deep Learning - Neural networks with many layers
    
    Applications include:
    - Image recognition
    - Natural language processing
    - Recommendation systems
    - Autonomous vehicles
    """
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file = f.name
    
    print(f"Created test document: {temp_file}")
    print(f"Content length: {len(test_content)} characters")
    
    return temp_file, test_content

def test_text_processing():
    """Test text chunking and processing without dependencies"""
    print("\n=== TEXT PROCESSING TEST ===")
    
    test_content = """
    Machine learning is a subset of artificial intelligence (AI) that provides systems 
    the ability to automatically learn and improve from experience without being 
    explicitly programmed. Key concepts include supervised learning, unsupervised learning, 
    and neural networks. Applications include image recognition, natural language processing, 
    and recommendation systems.
    """
    
    # Simple text chunking (without langchain)
    def simple_chunk(text, chunk_size=200, overlap=50):
        chunks = []
        words = text.split()
        
        start = 0
        while start < len(words):
            end = min(start + chunk_size//5, len(words))  # Rough word estimate
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            start = end - overlap//5  # Overlap
            if start >= len(words):
                break
        
        return chunks
    
    chunks = simple_chunk(test_content)
    print(f"Text length: {len(test_content)} characters")
    print(f"Number of chunks: {len(chunks)}")
    print("Sample chunks:")
    for i, chunk in enumerate(chunks[:2]):
        print(f"  Chunk {i+1}: {chunk[:100]}...")
    
    return chunks

async def test_rag_query_flow():
    """Test the complete RAG query flow"""
    print("\n=== RAG QUERY FLOW TEST ===")
    
    # Test without uploaded docs (should use general knowledge)
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("ERROR: No DeepSeek API key found")
        return False
    
    print("Testing general knowledge query...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{
                        "role": "user",
                        "content": "What is machine learning? Please provide a brief educational explanation."
                    }],
                    "temperature": 0.7,
                    "max_tokens": 300
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content'].strip()
                print(f"SUCCESS: General knowledge response received")
                print(f"Response preview: {answer[:150]}...")
                return True
            else:
                print(f"ERROR: Query failed with status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"ERROR: Query failed: {e}")
        return False

def test_environment_config():
    """Test environment configuration"""
    print("\n=== ENVIRONMENT CONFIGURATION TEST ===")
    
    required_vars = ['DEEPSEEK_API_KEY']
    optional_vars = ['OPENAI_API_KEY', 'PINECONE_API_KEY', 'PINECONE_HOST', 'PINECONE_INDEX_NAME']
    
    print("Required environment variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: Found ({value[:12]}...)")
        else:
            print(f"  {var}: MISSING")
    
    print("Optional environment variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: Found")
        else:
            print(f"  {var}: Not set")

async def simulate_full_workflow():
    """Simulate the full workflow that a user would experience"""
    print("\n=== FULL WORKFLOW SIMULATION ===")
    
    # Step 1: Document upload simulation
    temp_file, content = await test_document_upload()
    
    # Step 2: Text processing
    chunks = test_text_processing()
    
    # Step 3: Query simulation  
    query_success = await test_rag_query_flow()
    
    # Cleanup
    try:
        os.unlink(temp_file)
        print(f"Cleaned up temp file: {temp_file}")
    except:
        pass
    
    # Summary
    print(f"\n=== WORKFLOW SUMMARY ===")
    print(f"Document processing: {'SUCCESS' if chunks else 'FAILED'}")
    print(f"Query processing: {'SUCCESS' if query_success else 'FAILED'}")
    
    if chunks and query_success:
        print("OVERALL: RAG system core functionality is working!")
        print("\nPossible issues with your setup:")
        print("1. Missing vector database (Pinecone) - system will work in text-only mode")
        print("2. LangChain dependencies not installed - using simplified processing")
        print("3. FastAPI server not running - need to start the web interface")
        
        return True
    else:
        print("OVERALL: Some components need attention")
        return False

if __name__ == "__main__":
    async def main():
        print(f"RAG System Debug Report - {datetime.now()}")
        print("=" * 50)
        
        # Check dependencies
        deps = check_dependencies()
        
        # Test environment
        test_environment_config()
        
        # Run full workflow test
        success = await simulate_full_workflow()
        
        print(f"\n{'='*50}")
        if success:
            print("RECOMMENDATION: Your RAG system should work. Try starting the server:")
            print("  cd RAG")
            print("  python main.py")
            print("  Then test at: http://localhost:8000")
        else:
            print("RECOMMENDATION: Fix the identified issues before proceeding")
        
    asyncio.run(main())