import streamlit as st
import requests
import json

# No Pandas Educational RAG Platform Frontend
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
st.markdown(f"**Backend:** `{API_BASE_URL}`")

# Test backend connection
st.header("🔗 Backend Connection Test")

if st.button("🧪 Test Backend Connection"):
    try:
        with st.spinner("Testing connection..."):
            response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            
        if response.status_code == 200:
            st.success("✅ Backend Connected Successfully!")
            health_data = response.json()
            
            # Display component status with colors
            st.subheader("📊 System Status")
            for component, status in health_data.get("components", {}).items():
                if status == "operational":
                    st.success(f"✅ {component.title()}: {status}")
                else:
                    st.warning(f"⚠️ {component.title()}: {status}")
                    
            st.info(f"🕐 Last checked: {health_data.get('timestamp', 'Unknown')}")
                
        else:
            st.error(f"❌ Backend Error: HTTP {response.status_code}")
            
    except requests.exceptions.Timeout:
        st.error("❌ Connection timeout - Backend may be starting up")
    except Exception as e:
        st.error(f"❌ Connection Failed: {str(e)}")

# Document upload test
st.header("📁 Document Upload Test")
uploaded_file = st.file_uploader(
    "Choose a file to test upload", 
    type=['pdf', 'txt', 'docx'],
    help="This will test the document processing pipeline"
)

if uploaded_file is not None:
    st.info(f"📄 Selected: {uploaded_file.name} ({uploaded_file.size} bytes)")
    
    if st.button("🚀 Test Upload"):
        try:
            with st.spinner("Testing document upload..."):
                files = {
                    "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                }
                response = requests.post(f"{API_BASE_URL}/upload", files=files, timeout=30)
                
            if response.status_code == 200:
                result = response.json()
                st.success("✅ Document uploaded successfully!")
                
                st.subheader("📋 Upload Results")
                st.write(f"**Document ID:** {result.get('document_id')}")
                st.write(f"**Status:** {result.get('status')}")
                st.write(f"**Size:** {result.get('size')} bytes")
                st.write(f"**Type:** {result.get('type')}")
                st.write(f"**Estimated Time:** {result.get('estimated_time')}")
                
                if result.get('progress_url'):
                    st.info(f"📈 Progress tracking: {result.get('progress_url')}")
                
            else:
                st.error(f"❌ Upload failed: HTTP {response.status_code}")
                st.code(response.text)
                
        except Exception as e:
            st.error(f"❌ Upload error: {str(e)}")

# DeepSeek AI test
st.header("🤖 DeepSeek AI Test")

question = st.text_input(
    "Enter a test question:",
    placeholder="What is artificial intelligence?",
    help="This will test your DeepSeek AI integration"
)

col1, col2 = st.columns([1, 1])
with col1:
    use_docs_only = st.checkbox("🔍 Use uploaded docs only", value=False)

if question:
    if st.button("🧠 Ask DeepSeek AI"):
        try:
            with st.spinner("Getting answer from DeepSeek..."):
                payload = {
                    "question": question,
                    "use_uploaded_docs_only": use_docs_only,
                    "session_id": "test_session"
                }
                response = requests.post(
                    f"{API_BASE_URL}/query",
                    json=payload,
                    timeout=30
                )
                
            if response.status_code == 200:
                result = response.json()
                
                st.success("✅ DeepSeek Response Received!")
                
                # Show answer
                st.subheader("💬 Answer")
                st.write(result.get("answer", "No answer received"))
                
                # Show metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("⏱️ Response Time", f"{result.get('processing_time', 0):.2f}s")
                with col2:
                    st.metric("📚 From Docs", "Yes" if result.get('is_from_uploaded_docs') else "No")
                with col3:
                    st.metric("🔗 Sources", len(result.get('sources', [])))
                
                # Show sources if available
                if result.get('sources'):
                    with st.expander("📖 View Sources"):
                        for i, source in enumerate(result.get('sources', [])):
                            st.write(f"**Source {i+1}:** {source.get('source_file', 'Unknown')}")
                            st.code(source.get('content', '')[:200] + "...")
                
            else:
                st.error(f"❌ Query Failed: HTTP {response.status_code}")
                st.code(response.text)
                
        except Exception as e:
            st.error(f"❌ DeepSeek Test Failed: {str(e)}")

# System info
st.header("ℹ️ System Information")
col1, col2 = st.columns(2)

with col1:
    st.info("🖥️ **Frontend**\n- Platform: Streamlit Cloud\n- Version: No Pandas")

with col2:
    st.info("⚙️ **Backend**\n- Platform: Railway\n- AI: DeepSeek")

# Footer
st.markdown("---")
st.markdown("🚀 **Educational RAG Platform** - Testing Interface (Pandas-Free Version)")

# Quick debug info
with st.expander("🛠️ Debug Info"):
    st.write("**API Base URL:**", API_BASE_URL)
    st.write("**Streamlit Version:**", st.__version__)
    st.write("**Python Version:** 3.13+")
    st.write("**Dependencies:** streamlit, requests only")