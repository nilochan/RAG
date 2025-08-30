#!/usr/bin/env python3
"""Test DeepSeek API directly to verify Railway environment"""

import os
import asyncio
import httpx

async def test_deepseek_api():
    """Test DeepSeek API with your Railway environment settings"""
    
    # Use the same API key that Railway has
    api_key = "sk-73cfe16c65d14f01908d46e20fbd1a7b"  # Your configured key
    
    print("Testing DeepSeek API connection...")
    print(f"API Key: {api_key[:12]}...")
    
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
                    "messages": [{"role": "user", "content": "Hi! This is a test. Please respond with 'API connection successful!'"}],
                    "temperature": 0.7,
                    "max_tokens": 100
                }
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                print(f"✅ SUCCESS: {answer}")
                return True
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

async def test_general_question():
    """Test a general question like the user asked"""
    
    api_key = "sk-73cfe16c65d14f01908d46e20fbd1a7b"
    
    print("\nTesting general question: 'hi'")
    
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
                    "messages": [{"role": "user", "content": "Hi"}],
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                print(f"✅ General Response: {answer}")
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("=== RAILWAY DEEPSEEK API TEST ===")
        
        # Test basic API connection
        api_works = await test_deepseek_api()
        
        if api_works:
            # Test general question
            general_works = await test_general_question()
            
            if api_works and general_works:
                print("\n🎉 CONCLUSION: DeepSeek API works perfectly!")
                print("The issue is in the RAG system logic, not the API.")
                print("Need to fix the Railway fallback handling.")
            else:
                print("\n⚠️ CONCLUSION: API connection issues detected.")
        else:
            print("\n❌ CONCLUSION: DeepSeek API connection failed.")
    
    asyncio.run(main())