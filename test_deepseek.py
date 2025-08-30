#!/usr/bin/env python3
"""Test script to verify DeepSeek API connectivity"""

import os
import asyncio
import httpx
from src.rag_system import DeepSeekLLM

async def test_deepseek_api():
    """Test DeepSeek API connection and functionality"""
    print("🔍 Testing DeepSeek API connectivity...")
    
    # Check API key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ DEEPSEEK_API_KEY not found in environment")
        return
    
    print(f"✅ API Key found: {api_key[:12]}...")
    
    try:
        # Test direct API call
        print("\n📡 Testing direct API call...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "Hello! This is a test."}],
                    "temperature": 0.7,
                    "max_tokens": 100
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Direct API call successful!")
                print(f"📝 Response: {result['choices'][0]['message']['content'][:100]}...")
            else:
                print(f"❌ API call failed with status {response.status_code}")
                print(f"📄 Response: {response.text}")
                return
    
    except Exception as e:
        print(f"❌ Direct API call failed: {e}")
        return
    
    # Test LangChain wrapper
    print("\n🔗 Testing LangChain wrapper...")
    try:
        llm = DeepSeekLLM()
        
        # Test sync call
        print("Testing synchronous call...")
        sync_result = llm._call("What is 2+2?")
        print(f"✅ Sync call result: {sync_result[:100]}...")
        
        # Test async call
        print("Testing asynchronous call...")
        async_result = await llm._acall("What is the capital of France?")
        print(f"✅ Async call result: {async_result[:100]}...")
        
        print("\n🎉 All DeepSeek tests passed!")
        
    except Exception as e:
        print(f"❌ LangChain wrapper test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_deepseek_api())