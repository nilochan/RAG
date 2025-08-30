#!/usr/bin/env python3
"""Simple test script to verify DeepSeek API connectivity without dependencies"""

import os
import json
try:
    import asyncio
    import httpx
except ImportError:
    print("❌ Missing httpx. Installing...")
    import subprocess
    subprocess.run(["pip", "install", "httpx"], check=True)
    import asyncio
    import httpx

async def test_deepseek_direct():
    """Test DeepSeek API with direct HTTP calls"""
    print("Testing DeepSeek API connectivity (simplified)...")
    
    # Check API key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY not found in environment")
        return False
    
    print(f"SUCCESS: API Key found: {api_key[:12]}...")
    
    try:
        # Test direct API call
        print("\nTesting direct API call...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "Hello! Answer with just 'API test successful' if you receive this."}],
                    "temperature": 0.3,
                    "max_tokens": 50
                }
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content'].strip()
                print(f"SUCCESS: API Response: {answer}")
                print("SUCCESS: DeepSeek API is working correctly!")
                return True
            else:
                print(f"ERROR: API call failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
    
    except Exception as e:
        print(f"ERROR: API call failed: {e}")
        return False

async def test_rag_query():
    """Test a RAG-style query"""
    print("\nTesting RAG-style query...")
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return False
        
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
                        "content": """You are an educational AI assistant. Answer based on the following context:

Context from documents:
Document: sample.pdf
Content: Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models.

Question: What is machine learning?

Please provide a clear, educational answer based on the context."""
                    }],
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content'].strip()
                print(f"SUCCESS: RAG Query Response: {answer[:150]}...")
                print("SUCCESS: RAG-style queries are working!")
                return True
            else:
                print(f"ERROR: RAG query failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"ERROR: RAG query failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        api_test = await test_deepseek_direct()
        if api_test:
            rag_test = await test_rag_query()
            if api_test and rag_test:
                print("\nSUMMARY: DeepSeek integration is ready for RAG system!")
            else:
                print("\nSUMMARY: Basic API works but RAG queries need attention")
        else:
            print("\nSUMMARY: DeepSeek API connection failed")
    
    asyncio.run(main())