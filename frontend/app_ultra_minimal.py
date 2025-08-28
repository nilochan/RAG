import streamlit as st
import requests
import json

# Ultra Minimal Educational RAG Platform Frontend
st.set_page_config(
    page_title="Educational RAG Platform",
    page_icon="🎓",
    layout="centered"
)

# Get API base URL from secrets
try:
    API_BASE_URL = st.secrets["API_BASE_URL"]
except:
    API_BASE_URL = "http://localhost:8000"

st.title("🎓 Educational RAG Platform")
st.write(f"**Backend:** {API_BASE_URL}")

# Test backend connection
st.header("🔗 Backend Connection Test")

if st.button("Test Connection"):
    try:
        with st.spinner("Testing connection..."):
            response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            
        if response.status_code == 200:
            st.success("✅ Backend Connected Successfully!")
            health_data = response.json()
            
            # Display key info
            st.write("**Status:**", health_data.get("status", "Unknown"))
            st.write("**Components:**")
            for component, status in health_data.get("components", {}).items():
                st.write(f"- {component}: {status}")
                
        else:
            st.error(f"❌ Backend Error: HTTP {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Connection Failed: {str(e)}")

# Basic API test
st.header("🧪 API Test")

if st.button("Test Root Endpoint"):
    try:
        with st.spinner("Testing API..."):
            response = requests.get(f"{API_BASE_URL}/", timeout=10)
            
        if response.status_code == 200:
            st.success("✅ API Working!")
            data = response.json()
            st.json(data)
        else:
            st.error(f"❌ API Error: HTTP {response.status_code}")
            st.text(response.text)
            
    except Exception as e:
        st.error(f"❌ API Test Failed: {str(e)}")

# Simple Q&A test
st.header("🤖 DeepSeek AI Test")

question = st.text_input("Enter a test question:")

if question and st.button("Ask DeepSeek"):
    try:
        with st.spinner("Getting answer from DeepSeek AI..."):
            payload = {
                "question": question,
                "use_uploaded_docs_only": False,
                "session_id": "test"
            }
            response = requests.post(
                f"{API_BASE_URL}/query",
                json=payload,
                timeout=30
            )
            
        if response.status_code == 200:
            result = response.json()
            st.success("✅ DeepSeek Response:")
            st.write("**Answer:**")
            st.write(result.get("answer", "No answer received"))
            st.write(f"**Response Time:** {result.get('processing_time', 0):.2f}s")
        else:
            st.error(f"❌ Query Failed: HTTP {response.status_code}")
            st.text(response.text)
            
    except Exception as e:
        st.error(f"❌ DeepSeek Test Failed: {str(e)}")

# System info
st.header("ℹ️ System Info")
st.write("**Platform:** Streamlit Cloud")
st.write("**Backend:** Railway")
st.write("**AI:** DeepSeek")

# Footer
st.markdown("---")
st.markdown("🚀 **Educational RAG Platform** - Ultra Minimal Test Version")