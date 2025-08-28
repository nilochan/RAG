import streamlit as st
import requests
import json
import time

# Minimal Educational RAG Platform Frontend
st.set_page_config(
    page_title="Educational RAG Platform",
    page_icon="🎓",
    layout="wide"
)

# Get API base URL
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

st.title("🎓 Educational RAG Platform")
st.markdown("**Backend:** " + API_BASE_URL)

# Test backend connection
try:
    response = requests.get(f"{API_BASE_URL}/health", timeout=10)
    if response.status_code == 200:
        st.success("✅ Backend Connected Successfully!")
        health_data = response.json()
        st.json(health_data)
    else:
        st.error(f"❌ Backend Error: {response.status_code}")
except Exception as e:
    st.error(f"❌ Connection Error: {str(e)}")

# Document Upload Section
st.header("📁 Upload Documents")

uploaded_file = st.file_uploader(
    "Choose a file", 
    type=['pdf', 'txt', 'docx', 'csv', 'xlsx']
)

if uploaded_file is not None:
    if st.button("Process Document"):
        try:
            # Upload file to backend
            files = {"file": uploaded_file.getvalue()}
            with st.spinner("Processing document..."):
                response = requests.post(
                    f"{API_BASE_URL}/upload", 
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                    timeout=30
                )
                
            if response.status_code == 200:
                result = response.json()
                st.success("✅ Document uploaded successfully!")
                st.json(result)
            else:
                st.error(f"❌ Upload failed: {response.status_code}")
                st.text(response.text)
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Q&A Section  
st.header("🤖 Ask Questions")

question = st.text_input("Enter your question:")

if question and st.button("Ask"):
    try:
        with st.spinner("Getting answer from DeepSeek AI..."):
            payload = {
                "question": question,
                "use_uploaded_docs_only": False
            }
            response = requests.post(
                f"{API_BASE_URL}/query",
                json=payload,
                timeout=30
            )
            
        if response.status_code == 200:
            result = response.json()
            st.success("✅ Answer received!")
            st.markdown("**Answer:**")
            st.write(result["answer"])
            
            if result.get("sources"):
                st.markdown("**Sources:**")
                for source in result["sources"]:
                    st.text(f"- {source.get('source_file', 'Unknown')}")
        else:
            st.error(f"❌ Query failed: {response.status_code}")
            st.text(response.text)
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("🚀 **Educational RAG Platform** - Powered by DeepSeek AI & Railway")