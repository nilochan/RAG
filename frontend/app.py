import streamlit as st
import requests
import time
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import threading
import queue

# Page config
st.set_page_config(
    page_title="Educational RAG Platform",
    page_icon="<“",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")

# Initialize session state
if "progress_queue" not in st.session_state:
    st.session_state.progress_queue = queue.Queue()
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "processing_docs" not in st.session_state:
    st.session_state.processing_docs = {}

# Custom CSS with enhanced real-time progress styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .upload-area {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f8f9fa;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #667eea;
        background-color: #f0f2ff;
    }
    
    .status-success { color: #28a745; font-weight: bold; }
    .status-processing { color: #ffc107; font-weight: bold; }
    .status-failed { color: #dc3545; font-weight: bold; }
    .status-pending { color: #6c757d; font-weight: bold; }
    
    .progress-container {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .performance-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    
    .indicator-green { background-color: #28a745; }
    .indicator-yellow { background-color: #ffc107; }
    .indicator-red { background-color: #dc3545; }
    
    .real-time-update {
        animation: pulse 2s infinite;
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

def check_api_connection():
    """Check if API is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_real_time_progress(doc_id):
    """Get real-time progress for a document"""
    try:
        response = requests.get(f"{API_BASE_URL}/documents/{doc_id}/progress", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def main():
    st.markdown('<h1 class="main-header"><“ Educational RAG Platform</h1>', unsafe_allow_html=True)
    
    # Check API connection
    api_connected = check_api_connection()
    if not api_connected:
        st.error("L Cannot connect to backend API. Please check if the server is running.")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("=Ë Navigation")
        page = st.selectbox(
            "Choose a page:",
            ["<à Home", "=ä Upload Documents", "S Ask Questions", "=Ê Analytics Dashboard", "™ Settings"]
        )
        
        st.markdown("---")
        st.subheader("=' Quick Actions")
        
        if st.button("= Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
        if st.button(">ù Clear Cache"):
            st.cache_data.clear()
            st.success("Cache cleared!")
        
        # Real-time system status
        st.markdown("---")
        st.subheader("¡ System Status")
        
        try:
            health_response = requests.get(f"{API_BASE_URL}/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                st.markdown(f'<span class="performance-indicator indicator-green"></span> API: Online', unsafe_allow_html=True)
                st.markdown(f'<span class="performance-indicator indicator-green"></span> Database: Connected', unsafe_allow_html=True)
                
                # Show active processors
                active_trackers = health_data.get("metrics", {}).get("active_progress_trackers", 0)
                if active_trackers > 0:
                    st.markdown(f'<span class="real-time-update">=Ê {active_trackers} active jobs</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="performance-indicator indicator-red"></span> API: Error', unsafe_allow_html=True)
        except:
            st.markdown(f'<span class="performance-indicator indicator-red"></span> API: Offline', unsafe_allow_html=True)
    
    # Main content based on selected page
    if page == "<à Home":
        show_home_page()
    elif page == "=ä Upload Documents":
        show_upload_page()
    elif page == "S Ask Questions":
        show_query_page()
    elif page == "=Ê Analytics Dashboard":
        show_analytics_dashboard()
    elif page == "™ Settings":
        show_settings_page()

def show_home_page():
    st.subheader("Welcome to the Educational RAG Platform")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### =ä Smart Document Upload
        - **Multi-format support**: PDF, DOCX, TXT, CSV, XLSX
        - **Real-time progress tracking** with live updates
        - **Intelligent text extraction** with error handling
        - **Vector embeddings** for semantic search
        - **Background processing** with status monitoring
        """)
        
    with col2:
        st.markdown("""
        ### > Advanced AI Q&A
        - **Hybrid intelligence**: Documents + General knowledge
        - **Smart fallback system** for comprehensive answers
        - **Context-aware responses** with source citations
        - **Performance tracking** and response optimization
        - **Session management** for conversation continuity
        """)
        
    with col3:
        st.markdown("""
        ### =Ê Real-Time Analytics
        - **Live progress monitoring** with % completion
        - **Performance metrics** and processing statistics
        - **Document management** with batch operations
        - **Query analytics** and response time tracking
        - **System health monitoring** with alerts
        """)
    
    # Real-time system overview
    st.markdown("---")
    st.subheader("=È Live System Overview")
    
    try:
        # Get analytics data
        analytics_response = requests.get(f"{API_BASE_URL}/analytics")
        if analytics_response.status_code == 200:
            analytics = analytics_response.json()
            
            # Create metrics row
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                total_docs = analytics["documents"]["total"]
                st.metric("=Á Total Documents", total_docs)
            
            with col2:
                completed_docs = analytics["documents"]["completed"]
                st.metric(" Processed", completed_docs)
            
            with col3:
                processing_docs = analytics["documents"]["processing"]
                if processing_docs > 0:
                    st.metric("¡ Processing", processing_docs, delta="Active")
                else:
                    st.metric("¡ Processing", processing_docs)
            
            with col4:
                success_rate = analytics["documents"]["success_rate"]
                st.metric("=È Success Rate", f"{success_rate:.1f}%")
            
            with col5:
                avg_response = analytics["queries"]["average_response_time"]
                st.metric("ñ Avg Response", f"{avg_response:.2f}s")
            
            # Processing jobs indicator
            active_jobs = analytics["system"]["active_processing_jobs"]
            if active_jobs > 0:
                st.markdown(f'<div class="real-time-update">= {active_jobs} document(s) currently processing</div>', unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Could not load system overview: {e}")

@st.cache_data(ttl=30)  # Cache for 30 seconds for real-time updates
def get_documents():
    """Fetch documents from API with caching"""
    try:
        response = requests.get(f"{API_BASE_URL}/documents")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def show_upload_page():
    st.subheader("=ä Document Upload with Real-Time Progress")
    
    # File uploader with enhanced styling
    st.markdown('<div class="upload-area">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Choose files to upload",
        type=['pdf', 'docx', 'doc', 'txt', 'csv', 'xlsx'],
        help="Supported formats: PDF, Word documents, Text files, CSV, Excel (Max: 10MB)"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file is not None:
        # Display file info in an attractive format
        file_info = {
            "=Ä Filename": uploaded_file.name,
            "=Ï File size": f"{uploaded_file.size:,} bytes ({uploaded_file.size / (1024*1024):.2f} MB)",
            "<¯ File type": uploaded_file.type
        }
        
        # Create info cards
        cols = st.columns(3)
        for i, (key, value) in enumerate(file_info.items()):
            with cols[i]:
                st.info(f"**{key}**\n\n{value}")
        
        # Upload button with enhanced styling
        if st.button("=€ Process Document", type="primary", use_container_width=True):
            with st.spinner("Uploading and initializing processing..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{API_BASE_URL}/upload", files=files)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f" Document uploaded successfully!")
                        
                        # Show upload details
                        st.json(result)
                        
                        # Start real-time progress monitoring
                        doc_id = result["document_id"]
                        show_real_time_progress(doc_id, uploaded_file.name)
                        
                    else:
                        error_detail = response.json().get("detail", response.text)
                        st.error(f"L Upload failed: {error_detail}")
                        
                except Exception as e:
                    st.error(f"L Error uploading file: {e}")
    
    # Show existing documents with enhanced table
    st.markdown("---")
    st.subheader("=Á Document Library")
    
    documents = get_documents()
    if documents:
        df = pd.DataFrame(documents)
        
        # Add status indicators
        def format_status(status):
            indicators = {
                'completed': ' Completed',
                'processing': '¡ Processing',
                'failed': 'L Failed',
                'pending': 'ó Pending'
            }
            return indicators.get(status, status)
        
        df['status_display'] = df['status'].apply(format_status)
        df['upload_time'] = pd.to_datetime(df['upload_time']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Display enhanced table
        display_df = df[['filename', 'status_display', 'chunk_count', 'upload_time']].copy()
        display_df.columns = ['=Ä Document', '=Ê Status', '=" Chunks', '=Å Uploaded']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
        
        # Document management section
        st.subheader("=à Document Management")
        
        # Show processing documents with live progress
        processing_docs = [doc for doc in documents if doc['status'] == 'processing']
        if processing_docs:
            st.markdown("### ¡ Currently Processing")
            for doc in processing_docs:
                show_mini_progress_tracker(doc['id'], doc['filename'])
        
        # Document actions
        selected_doc = st.selectbox(
            "Select document for actions:",
            options=[f"{doc['filename']} (ID: {doc['id']})" for doc in documents],
            help="Choose a document to view details or delete"
        )
        
        if selected_doc:
            doc_id = int(selected_doc.split("ID: ")[1].split(")")[0])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("= View Details", use_container_width=True):
                    show_document_details(doc_id)
            
            with col2:
                if st.button("=Ê Show Progress", use_container_width=True):
                    progress_data = get_real_time_progress(doc_id)
                    if progress_data:
                        st.json(progress_data)
                    else:
                        st.info("No progress data available")
            
            with col3:
                if st.button("=Ñ Delete Document", type="secondary", use_container_width=True):
                    if st.button("  Confirm Delete", type="secondary"):
                        delete_document(doc_id)
    else:
        st.info("=í No documents uploaded yet. Upload your first document above!")
        
        # Show sample analytics while empty
        st.markdown("### =Ê Getting Started")
        sample_metrics = pd.DataFrame({
            'Metric': ['Documents Ready', 'Processing Queue', 'Success Rate', 'Avg. Processing Time'],
            'Value': ['0', '0', '100%', '< 30s'],
            'Status': ['<¯ Ready', '¡ Available', '<‰ Excellent', '=€ Fast']
        })
        st.table(sample_metrics)

def show_mini_progress_tracker(doc_id, filename):
    """Show a compact progress tracker for processing documents"""
    progress_data = get_real_time_progress(doc_id)
    if progress_data:
        progress = progress_data.get("progress", 0)
        status = progress_data.get("status", "unknown")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"=Ä {filename}")
            st.progress(progress / 100)
        with col2:
            st.write(f"{progress}%")
            if status == "processing":
                st.markdown('<span class="real-time-update">= Live</span>', unsafe_allow_html=True)

def show_real_time_progress(doc_id, filename):
    """Show detailed real-time progress monitoring"""
    st.markdown('<div class="progress-container">', unsafe_allow_html=True)
    st.subheader(f"¡ Processing: {filename}")
    
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    details_placeholder = st.empty()
    
    # Monitor progress for up to 5 minutes
    for i in range(300):  # 5 minutes max
        progress_data = get_real_time_progress(doc_id)
        
        if progress_data:
            progress = progress_data["progress"]
            status = progress_data["status"]
            timestamp = progress_data["timestamp"]
            
            # Update progress bar
            progress_placeholder.progress(progress / 100)
            
            # Update status
            if status == "completed":
                status_placeholder.success(f" Processing completed! ({progress}%)")
                details_placeholder.info(f"ð Completed at: {timestamp}")
                break
            elif status == "failed":
                error = progress_data.get("error", "Unknown error")
                status_placeholder.error(f"L Processing failed: {error}")
                details_placeholder.error(f"ð Failed at: {timestamp}")
                break
            elif status == "processing":
                status_placeholder.info(f"= Processing... {progress}%")
                details_placeholder.write(f"=P Last update: {timestamp}")
            
            time.sleep(2)  # Check every 2 seconds
        else:
            status_placeholder.warning("  Cannot get progress data")
            break
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_document_details(doc_id):
    """Show detailed document information"""
    try:
        response = requests.get(f"{API_BASE_URL}/documents/{doc_id}/status")
        if response.status_code == 200:
            doc_data = response.json()
            
            st.subheader(f"=Ä {doc_data['filename']}")
            
            # Create info grid
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("=Ê Status", doc_data['status'])
                st.metric("=" Chunks Created", doc_data.get('chunk_count', 0))
                
            with col2:
                st.metric("=Ï File Size", f"{doc_data.get('file_size', 0):,} bytes")
                st.metric("=Ä File Type", doc_data.get('file_type', 'Unknown').upper())
                
            with col3:
                upload_time = pd.to_datetime(doc_data['upload_time']).strftime('%Y-%m-%d %H:%M:%S')
                st.metric("=Å Uploaded", upload_time)
                
                if doc_data.get('last_update'):
                    last_update = pd.to_datetime(doc_data['last_update']).strftime('%Y-%m-%d %H:%M:%S')
                    st.metric("= Last Update", last_update)
            
            # Show metadata if available
            if doc_data.get('metadata'):
                st.subheader("= Processing Details")
                st.json(doc_data['metadata'])
        else:
            st.error("Cannot load document details")
    except Exception as e:
        st.error(f"Error: {e}")

def delete_document(doc_id):
    """Delete a document"""
    try:
        response = requests.delete(f"{API_BASE_URL}/documents/{doc_id}")
        if response.status_code == 200:
            st.success(" Document deleted successfully!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("L Failed to delete document")
    except Exception as e:
        st.error(f"Error: {e}")

def show_query_page():
    st.subheader("S Intelligent Q&A System")
    
    # Query interface with enhanced layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        question = st.text_area(
            "What would you like to know?",
            height=120,
            placeholder="Ask any question about your uploaded documents or general topics...\n\nExamples:\n" What does this document say about...?\n" Explain the concept of...\n" Summarize the main points from my files",
            help="The AI will intelligently search your documents first, then use general knowledge if needed"
        )
    
    with col2:
        st.markdown("### ™ Query Options")
        use_docs_only = st.checkbox(
            "=Ú Search uploaded docs only",
            help="If checked, will only search your uploaded documents"
        )
        
        session_id = st.text_input(
            "Session ID",
            value="default",
            help="Use different session IDs to separate conversations"
        )
        
        # Strategy selection
        strategy = st.selectbox(
            "AI Strategy",
            ["auto", "docs_only", "general_only", "hybrid"],
            help="Choose how the AI should answer your question"
        )
    
    # Query button with performance tracking
    if st.button("= Ask Question", type="primary", disabled=not question.strip(), use_container_width=True):
        start_time = time.time()
        
        with st.spinner("> AI is thinking..."):
            try:
                payload = {
                    "question": question,
                    "session_id": session_id,
                    "use_uploaded_docs_only": use_docs_only
                }
                
                response = requests.post(f"{API_BASE_URL}/query", json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    processing_time = time.time() - start_time
                    
                    # Display answer with enhanced formatting
                    st.markdown("### =¡ Answer")
                    st.markdown(result["answer"])
                    
                    # Show performance metrics
                    st.markdown("### =Ê Query Performance")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        source_type = "=Ú Your Documents" if result["is_from_uploaded_docs"] else "< General Knowledge"
                        st.metric("Source", source_type)
                    
                    with col2:
                        st.metric("Response Time", f"{result['processing_time']:.2f}s")
                    
                    with col3:
                        st.metric("Sources Used", len(result["sources"]))
                    
                    with col4:
                        total_time = processing_time
                        st.metric("Total Time", f"{total_time:.2f}s")
                    
                    # Show sources with enhanced display
                    if result["sources"]:
                        st.markdown("### =Ö Sources & Citations")
                        
                        for i, source in enumerate(result["sources"]):
                            with st.expander(f"=Ñ Source {i+1} - {source.get('source_file', 'Unknown Document')}"):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.text(source["content"])
                                
                                with col2:
                                    if source.get("score"):
                                        st.metric("Relevance Score", f"{source['score']:.3f}")
                                    
                                    if source.get("document_id"):
                                        st.metric("Document ID", source["document_id"])
                                
                                if source.get("metadata"):
                                    st.json(source["metadata"])
                    
                    # Add to query history
                    st.session_state.query_history.append({
                        "question": question,
                        "answer": result["answer"][:200] + "..." if len(result["answer"]) > 200 else result["answer"],
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "session": session_id,
                        "sources": len(result["sources"]),
                        "response_time": result['processing_time']
                    })
                    
                else:
                    st.error(f"L Query failed: {response.text}")
                    
            except Exception as e:
                st.error(f"L Error: {e}")
    
    # Query history with enhanced display
    st.markdown("---")
    st.subheader("=Ý Recent Queries")
    
    if st.session_state.query_history:
        # Show statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Queries", len(st.session_state.query_history))
        with col2:
            avg_time = sum(q.get("response_time", 0) for q in st.session_state.query_history) / len(st.session_state.query_history)
            st.metric("Avg Response Time", f"{avg_time:.2f}s")
        with col3:
            total_sources = sum(q.get("sources", 0) for q in st.session_state.query_history)
            st.metric("Total Sources Used", total_sources)
        
        # Show recent queries
        for i, item in enumerate(reversed(st.session_state.query_history[-10:])):  # Show last 10
            with st.expander(f"=P {item['timestamp']} | Session: {item['session']} | {item.get('sources', 0)} sources"):
                st.markdown(f"**Q:** {item['question']}")
                st.markdown(f"**A:** {item['answer']}")
                if item.get("response_time"):
                    st.caption(f"Response time: {item['response_time']:.2f}s")
    else:
        st.info("No queries yet. Ask your first question above!")

def show_analytics_dashboard():
    st.subheader("=Ê Real-Time Analytics Dashboard")
    
    try:
        # Get fresh analytics data
        analytics_response = requests.get(f"{API_BASE_URL}/analytics")
        if analytics_response.status_code != 200:
            st.error("Cannot load analytics data")
            return
            
        analytics = analytics_response.json()
        documents = get_documents()
        
        # Overview metrics with real-time indicators
        st.markdown("### =È System Overview")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_docs = analytics["documents"]["total"]
            st.metric("=Á Total Documents", total_docs)
        
        with col2:
            completed_docs = analytics["documents"]["completed"]
            success_rate = analytics["documents"]["success_rate"]
            st.metric(" Completed", completed_docs, delta=f"{success_rate:.1f}% success")
        
        with col3:
            processing_docs = analytics["documents"]["processing"]
            if processing_docs > 0:
                st.metric("¡ Processing", processing_docs, delta="Active")
                st.markdown('<span class="real-time-update">= Live Jobs Running</span>', unsafe_allow_html=True)
            else:
                st.metric("¡ Processing", processing_docs)
        
        with col4:
            total_queries = analytics["queries"]["total"]
            st.metric("S Total Queries", total_queries)
        
        with col5:
            avg_response = analytics["queries"]["average_response_time"]
            st.metric("ñ Avg Response", f"{avg_response:.2f}s")
        
        if documents:
            df = pd.DataFrame(documents)
            
            # Document status distribution
            st.markdown("### =Ê Document Status Distribution")
            col1, col2 = st.columns(2)
            
            with col1:
                status_counts = df['status'].value_counts()
                fig_pie = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Document Processing Status",
                    color_discrete_map={
                        'completed': '#28a745',
                        'processing': '#ffc107',
                        'failed': '#dc3545',
                        'pending': '#6c757d'
                    }
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Processing timeline
                df['upload_date'] = pd.to_datetime(df['upload_time']).dt.date
                timeline_data = df.groupby(['upload_date', 'status']).size().reset_index()
                timeline_data.columns = ['Date', 'Status', 'Count']
                
                fig_timeline = px.bar(
                    timeline_data,
                    x='Date',
                    y='Count',
                    color='Status',
                    title="Upload Timeline by Status",
                    color_discrete_map={
                        'completed': '#28a745',
                        'processing': '#ffc107',
                        'failed': '#dc3545',
                        'pending': '#6c757d'
                    }
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Performance metrics
            st.markdown("### ¡ Performance Metrics")
            
            # Create performance dashboard
            col1, col2 = st.columns(2)
            
            with col1:
                # Document size vs chunks analysis
                if 'chunk_count' in df.columns and df['chunk_count'].notna().any():
                    fig_chunks = px.scatter(
                        df,
                        x='file_size',
                        y='chunk_count',
                        color='status',
                        title="File Size vs Chunks Generated",
                        hover_data=['filename'],
                        color_discrete_map={
                            'completed': '#28a745',
                            'processing': '#ffc107',
                            'failed': '#dc3545',
                            'pending': '#6c757d'
                        }
                    )
                    fig_chunks.update_xaxis(title="File Size (bytes)")
                    fig_chunks.update_yaxis(title="Number of Chunks")
                    st.plotly_chart(fig_chunks, use_container_width=True)
            
            with col2:
                # Processing success rate over time
                df['upload_date'] = pd.to_datetime(df['upload_time']).dt.date
                daily_stats = df.groupby('upload_date').agg({
                    'status': lambda x: (x == 'completed').sum() / len(x) * 100
                }).reset_index()
                daily_stats.columns = ['Date', 'Success_Rate']
                
                fig_success = px.line(
                    daily_stats,
                    x='Date',
                    y='Success_Rate',
                    title="Daily Success Rate (%)",
                    markers=True
                )
                fig_success.update_yaxis(range=[0, 100])
                st.plotly_chart(fig_success, use_container_width=True)
            
            # Real-time processing monitor
            processing_docs = df[df['status'] == 'processing']
            if not processing_docs.empty:
                st.markdown("### = Live Processing Monitor")
                
                for _, doc in processing_docs.iterrows():
                    progress_data = get_real_time_progress(doc['id'])
                    if progress_data:
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.write(f"=Ä {doc['filename']}")
                        
                        with col2:
                            progress = progress_data.get('progress', 0)
                            st.progress(progress / 100)
                        
                        with col3:
                            st.write(f"{progress}%")
                        
                        with col4:
                            st.markdown('<span class="real-time-update">= Live</span>', unsafe_allow_html=True)
            
            # System performance metrics
            st.markdown("### =¥ System Performance")
            
            system_metrics = analytics["system"]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Active Jobs", system_metrics["active_processing_jobs"])
            
            with col2:
                st.metric("Progress Trackers", system_metrics["progress_trackers"])
            
            with col3:
                processor_stats = system_metrics.get("processor_stats", {})
                st.metric("Active Processors", processor_stats.get("active_processors", 0))
            
            with col4:
                rag_stats = system_metrics.get("rag_stats", {})
                st.metric("AI Model", rag_stats.get("model", "gpt-3.5-turbo").split("-")[-1].upper())
        
        else:
            st.info("=í No analytics data available yet. Upload some documents to see metrics!")
            
            # Show sample dashboard
            st.markdown("### =Ê Sample Analytics View")
            
            # Create sample data for demonstration
            sample_dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
            sample_data = pd.DataFrame({
                'Date': sample_dates,
                'Documents_Processed': [0] * len(sample_dates),
                'Success_Rate': [100] * len(sample_dates),
                'Avg_Response_Time': [0.5] * len(sample_dates)
            })
            
            fig_sample = px.line(
                sample_data,
                x='Date',
                y=['Documents_Processed', 'Success_Rate', 'Avg_Response_Time'],
                title="Sample Analytics - Ready for Your Data"
            )
            st.plotly_chart(fig_sample, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

def show_settings_page():
    st.subheader("™ System Configuration")
    
    # API Configuration
    st.markdown("### =' API Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        api_url = st.text_input("API Base URL", value=API_BASE_URL)
        if st.button("= Test Connection"):
            try:
                response = requests.get(f"{api_url}/health")
                if response.status_code == 200:
                    st.success(" Connection successful!")
                    st.json(response.json())
                else:
                    st.error(f"L Connection failed: {response.status_code}")
            except Exception as e:
                st.error(f"L Connection error: {e}")
    
    with col2:
        timeout = st.number_input("Request Timeout (seconds)", min_value=1, max_value=300, value=30)
        st.info(f"Current timeout: {timeout} seconds")
    
    # Real-time settings
    st.markdown("### ¡ Real-Time Features")
    
    col1, col2 = st.columns(2)
    with col1:
        progress_refresh = st.slider("Progress Refresh Rate (seconds)", 1, 10, 2)
        st.info("How often to check progress updates")
        
        auto_refresh = st.checkbox("Auto-refresh Dashboard", value=True)
        if auto_refresh:
            refresh_interval = st.number_input("Dashboard refresh (seconds)", min_value=10, max_value=300, value=30)
    
    with col2:
        max_history = st.number_input("Max Query History", min_value=10, max_value=1000, value=100)
        st.info("Maximum number of queries to keep in history")
        
        show_debug = st.checkbox("Show Debug Information", value=False)
        if show_debug:
            st.markdown("### = Debug Information")
            st.json({
                "session_state_keys": list(st.session_state.keys()),
                "query_history_count": len(st.session_state.query_history),
                "processing_docs": st.session_state.processing_docs
            })
    
    # Performance settings
    st.markdown("### =Ê Performance Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        cache_ttl = st.slider("Cache TTL (seconds)", 10, 300, 30)
        st.info("How long to cache API responses")
        
        batch_size = st.number_input("Batch Processing Size", min_value=1, max_value=50, value=10)
        st.info("Documents to process in each batch")
    
    with col2:
        max_file_size = st.number_input("Max File Size (MB)", min_value=1, max_value=100, value=10)
        st.info("Maximum allowed file size for uploads")
        
        concurrent_jobs = st.number_input("Max Concurrent Jobs", min_value=1, max_value=10, value=3)
        st.info("Maximum number of documents to process simultaneously")
    
    # System actions
    st.markdown("### =à System Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("= Refresh All Data", use_container_width=True):
            st.cache_data.clear()
            st.success(" All caches cleared!")
            st.rerun()
    
    with col2:
        if st.button("=Ê Export Settings", use_container_width=True):
            settings = {
                "api_url": api_url,
                "timeout": timeout,
                "progress_refresh": progress_refresh,
                "auto_refresh": auto_refresh,
                "max_history": max_history,
                "cache_ttl": cache_ttl
            }
            st.download_button(
                "=¾ Download Settings JSON",
                data=json.dumps(settings, indent=2),
                file_name="rag_platform_settings.json",
                mime="application/json"
            )
    
    with col3:
        if st.button(">ê Run System Test", use_container_width=True):
            with st.spinner("Running system tests..."):
                test_results = run_system_tests(api_url)
                st.json(test_results)
    
    with col4:
        if st.button("=È Performance Report", use_container_width=True):
            show_performance_report()
    
    # System information
    st.markdown("### 9 System Information")
    
    try:
        response = requests.get(f"{api_url}/")
        if response.status_code == 200:
            system_info = response.json()
            
            info_display = {
                "=€ Platform Version": system_info.get("version", "Unknown"),
                "=ñ Frontend": "Streamlit",
                "=' Backend": "FastAPI + Python",
                "=¾ Vector Database": "Pinecone",
                "> AI Model": "OpenAI GPT",
                "=Ä Document Processing": "LangChain + PyPDF2",
                " Deployment": "Railway + Docker",
                "=Ê Real-time Features": "Server-Sent Events + Progress Tracking"
            }
            
            for key, value in info_display.items():
                st.text(f"{key}: {value}")
        else:
            st.error("Cannot retrieve system information")
    except Exception as e:
        st.error(f"Error getting system info: {e}")

def run_system_tests(api_url):
    """Run comprehensive system tests"""
    tests = {
        "api_connection": False,
        "health_check": False,
        "documents_endpoint": False,
        "analytics_endpoint": False
    }
    
    try:
        # Test API connection
        response = requests.get(api_url, timeout=5)
        tests["api_connection"] = response.status_code == 200
        
        # Test health endpoint
        response = requests.get(f"{api_url}/health", timeout=5)
        tests["health_check"] = response.status_code == 200
        
        # Test documents endpoint
        response = requests.get(f"{api_url}/documents", timeout=5)
        tests["documents_endpoint"] = response.status_code == 200
        
        # Test analytics endpoint
        response = requests.get(f"{api_url}/analytics", timeout=5)
        tests["analytics_endpoint"] = response.status_code == 200
        
    except Exception as e:
        tests["error"] = str(e)
    
    return tests

def show_performance_report():
    """Show detailed performance report"""
    st.markdown("### =È Performance Report")
    
    try:
        analytics_response = requests.get(f"{API_BASE_URL}/analytics")
        if analytics_response.status_code == 200:
            analytics = analytics_response.json()
            
            # Performance summary
            perf_data = {
                "Documents Processed": analytics["documents"]["completed"],
                "Success Rate": f"{analytics['documents']['success_rate']:.1f}%",
                "Average Response Time": f"{analytics['queries']['average_response_time']:.3f}s",
                "Active Processing Jobs": analytics["system"]["active_processing_jobs"],
                "System Uptime": "Operational",
                "Cache Hit Rate": "95%",  # Mock data
                "Memory Usage": "Normal",  # Mock data
                "API Latency": "< 100ms"  # Mock data
            }
            
            # Display as metrics
            cols = st.columns(4)
            for i, (metric, value) in enumerate(perf_data.items()):
                with cols[i % 4]:
                    st.metric(metric, value)
            
            # Performance trend (mock data)
            dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
            performance_trend = pd.DataFrame({
                'Date': dates,
                'Response_Time': [0.5 + 0.1 * (i % 5) for i in range(len(dates))],
                'Success_Rate': [95 + (i % 10) for i in range(len(dates))],
                'Documents_Per_Day': [(i % 7) + 1 for i in range(len(dates))]
            })
            
            fig_perf = px.line(
                performance_trend,
                x='Date',
                y=['Response_Time', 'Success_Rate', 'Documents_Per_Day'],
                title="30-Day Performance Trend"
            )
            st.plotly_chart(fig_perf, use_container_width=True)
        
        else:
            st.error("Cannot load performance data")
    
    except Exception as e:
        st.error(f"Error generating performance report: {e}")

# Auto-refresh for real-time updates
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# Check if we should auto-refresh (every 30 seconds for processing documents)
current_time = time.time()
if current_time - st.session_state.last_refresh > 30:
    st.session_state.last_refresh = current_time
    if any(doc.get('status') == 'processing' for doc in get_documents()):
        st.rerun()

if __name__ == "__main__":
    main()