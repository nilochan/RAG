// Configuration
const API_BASE_URL = 'https://rag-chanchinthai.up.railway.app';

// Global state
let documents = [];
let chatMessages = [];
let isUploading = false;
let documentRefreshInterval = null;

// DOM Elements
const elements = {
    statusDot: document.getElementById('statusDot'),
    statusText: document.getElementById('statusText'),
    systemStatus: document.getElementById('systemStatus'),
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    uploadProgress: document.getElementById('uploadProgress'),
    uploadFileName: document.getElementById('uploadFileName'),
    uploadStatus: document.getElementById('uploadStatus'),
    progressFill: document.getElementById('progressFill'),
    progressDetails: document.getElementById('progressDetails'),
    documentsCard: document.getElementById('documentsCard'),
    documentsList: document.getElementById('documentsList'),
    chatContainer: document.getElementById('chatContainer'),
    questionInput: document.getElementById('questionInput'),
    askButton: document.getElementById('askButton'),
    useDocsOnly: document.getElementById('useDocsOnly'),
    charCount: document.getElementById('charCount'),
    analyticsCard: document.getElementById('analyticsCard'),
    analyticsGrid: document.getElementById('analyticsGrid'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingText: document.getElementById('loadingText'),
    toastContainer: document.getElementById('toastContainer')
};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

async function initializeApp() {
    await checkSystemStatus();
    await loadDocuments();
    await loadAnalytics();
}

function setupEventListeners() {
    // Status refresh
    document.getElementById('refreshStatus').addEventListener('click', checkSystemStatus);
    
    // File upload
    elements.uploadArea.addEventListener('click', () => elements.fileInput.click());
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleFileDrop);
    elements.fileInput.addEventListener('change', handleFileSelect);
    
    // Documents refresh
    document.getElementById('refreshDocs').addEventListener('click', loadDocuments);
    
    // Chat
    elements.questionInput.addEventListener('input', handleQuestionInput);
    elements.questionInput.addEventListener('keydown', handleQuestionKeydown);
    elements.askButton.addEventListener('click', handleAskQuestion);
    
    // Analytics refresh
    document.getElementById('refreshAnalytics').addEventListener('click', loadAnalytics);
}

// System Status Functions
async function checkSystemStatus() {
    try {
        showLoading('Checking system status...');
        
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (response.ok) {
            updateSystemStatus(data, 'online');
            showToast('System Status', 'All systems operational', 'success');
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('Status check failed:', error);
        updateSystemStatus(null, 'offline');
        showToast('Connection Error', 'Unable to connect to backend', 'error');
    } finally {
        hideLoading();
    }
}

function updateSystemStatus(data, status) {
    // Update header status
    if (status === 'online') {
        elements.statusDot.className = 'w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse';
        elements.statusText.textContent = 'Connected';
    } else {
        elements.statusDot.className = 'w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse';
        elements.statusText.textContent = 'Disconnected';
    }

    if (data && status === 'online') {
        const statusHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                ${Object.entries(data.components).map(([component, componentStatus]) => `
                    <div class="flex items-center space-x-2 p-2.5 bg-${componentStatus === 'operational' ? 'green' : 'yellow'}-50 border border-${componentStatus === 'operational' ? 'green' : 'yellow'}-200 rounded-lg">
                        <div class="bg-${componentStatus === 'operational' ? 'green' : 'yellow'}-600 p-1.5 rounded-md">
                            <i class="fas ${getComponentIcon(component)} text-white text-xs"></i>
                        </div>
                        <div>
                            <h4 class="text-sm font-semibold text-gray-900">${formatComponentName(component)}</h4>
                            <p class="text-xs text-gray-600">${componentStatus}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div class="mt-3 text-center text-xs text-gray-500">
                Last updated: ${new Date(data.timestamp).toLocaleString()}
            </div>
        `;
        elements.systemStatus.innerHTML = statusHTML;
    } else {
        elements.systemStatus.innerHTML = `
            <div class="flex items-center space-x-2 p-2.5 bg-red-50 border border-red-200 rounded-lg">
                <div class="bg-red-600 p-1.5 rounded-md">
                    <i class="fas fa-exclamation-triangle text-white text-xs"></i>
                </div>
                <div>
                    <h4 class="text-sm font-semibold text-gray-900">Connection Failed</h4>
                    <p class="text-xs text-gray-600">Unable to reach backend server</p>
                </div>
            </div>
        `;
    }
}

function getComponentIcon(component) {
    const icons = {
        database: 'fa-database',
        pinecone: 'fa-vector-square',
        deepseek: 'fa-brain',
        progress_tracking: 'fa-chart-line'
    };
    return icons[component] || 'fa-cog';
}

function formatComponentName(component) {
    return component.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

// File Upload Functions
function handleDragOver(e) {
    e.preventDefault();
    elements.uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
}

function handleFileDrop(e) {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
        if (files.length === 1) {
            handleFileUpload(files[0]);
        } else {
            handleMultipleFileUpload(files);
        }
    }
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        if (files.length === 1) {
            handleFileUpload(files[0]);
        } else {
            handleMultipleFileUpload(files);
        }
    }
}

async function handleMultipleFileUpload(files) {
    if (isUploading) {
        showToast('Upload Error', 'Another file is currently being uploaded', 'warning');
        return;
    }
    
    showToast('Batch Upload', `Processing ${files.length} files in parallel (3 at a time)...`, 'info');

    // Process files in batches of 3 for parallel upload
    const BATCH_SIZE = 3;
    const batches = [];

    for (let i = 0; i < files.length; i += BATCH_SIZE) {
        batches.push(files.slice(i, i + BATCH_SIZE));
    }

    let completed = 0;
    let failed = 0;

    for (const batch of batches) {
        // Process batch in parallel
        const batchPromises = batch.map(file =>
            handleFileUpload(file)
                .then(() => {
                    completed++;
                    showToast('File Complete', `✅ ${file.name} (${completed}/${files.length})`, 'success');
                })
                .catch(error => {
                    failed++;
                    showToast('Upload Failed', `❌ ${file.name}: ${error.message}`, 'error');
                })
        );

        // Wait for all files in this batch to complete
        await Promise.all(batchPromises);

        // Brief pause between batches
        if (batches.indexOf(batch) < batches.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }

    showToast('Batch Complete', `✅ ${completed} succeeded, ${failed} failed (Total: ${files.length})`, completed > 0 ? 'success' : 'error');
    await loadDocuments(); // Refresh the documents list
}

async function handleFileUpload(file) {
    // Allow parallel uploads - remove global lock
    // Individual files can upload simultaneously
    
    // Validate file
    const maxSize = 50 * 1024 * 1024; // 50MB
    const allowedTypes = ['pdf', 'docx', 'doc', 'txt', 'csv', 'xlsx'];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    
    if (file.size > maxSize) {
        showToast('File Too Large', 'Maximum file size is 50MB', 'error');
        return;
    }
    
    if (!allowedTypes.includes(fileExtension)) {
        showToast('Invalid File Type', `Supported types: ${allowedTypes.join(', ')}`, 'error');
        return;
    }
    
    isUploading = true;
    showUploadProgress(file.name);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showToast('Upload Successful', `${file.name} uploaded successfully`, 'success');
            
            // Start progress tracking
            const documentId = result.document_id;
            await trackUploadProgress(documentId);
            
            // Reload documents list
            await loadDocuments();
        } else {
            throw new Error(result.detail || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Upload Error', error.message, 'error');
        hideUploadProgress();
    } finally {
        isUploading = false;
        // Reset file input
        elements.fileInput.value = '';
    }
}

function showUploadProgress(fileName) {
    elements.uploadArea.classList.add('hidden');
    elements.uploadProgress.classList.remove('hidden');
    elements.uploadFileName.textContent = fileName;
    elements.uploadStatus.textContent = 'Uploading...';
    elements.progressFill.style.width = '0%';
}

function hideUploadProgress() {
    elements.uploadArea.classList.remove('hidden');
    elements.uploadProgress.classList.add('hidden');
}

// Start auto-refreshing documents list during upload
function startDocumentAutoRefresh() {
    if (documentRefreshInterval) return; // Already running

    documentRefreshInterval = setInterval(async () => {
        await loadDocuments();
    }, 3000); // Refresh every 3 seconds during upload
}

// Stop auto-refreshing documents list
function stopDocumentAutoRefresh() {
    if (documentRefreshInterval) {
        clearInterval(documentRefreshInterval);
        documentRefreshInterval = null;
    }
}

async function trackUploadProgress(documentId) {
    const maxAttempts = 120; // 10 minutes max (increased from 5)
    let attempts = 0;

    // Start auto-refreshing document list to show real-time progress
    startDocumentAutoRefresh();

    const trackProgress = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/documents/${documentId}/progress`);
            const data = await response.json();

            if (response.ok) {
                const progress = data.progress || 0;
                elements.progressFill.style.width = `${progress}%`;
                elements.uploadStatus.textContent = `Processing... ${progress}%`;

                if (data.status === 'completed') {
                    elements.progressFill.style.width = '100%';
                    elements.uploadStatus.textContent = 'Completed successfully!';
                    elements.progressDetails.innerHTML = `
                        <div style="margin-top: 1rem; color: #38a169;">
                            <i class="fas fa-check-circle"></i>
                            Document processed successfully (${data.chunk_count || 'N/A'} chunks)
                        </div>
                    `;

                    // Stop auto-refresh and do final refresh
                    stopDocumentAutoRefresh();
                    setTimeout(async () => {
                        await loadDocuments();
                        hideUploadProgress();
                    }, 2000); // Wait 2 seconds for backend to finalize
                    return;
                } else if (data.status === 'failed') {
                    throw new Error(data.error || 'Processing failed');
                }

                // Continue tracking if still processing
                if (attempts < maxAttempts) {
                    attempts++;
                    setTimeout(trackProgress, 2000); // Check every 2 seconds
                } else {
                    // Timeout reached - check database directly
                    await checkDocumentStatus(documentId);
                }
            } else {
                // Progress endpoint failed - check database directly
                await checkDocumentStatus(documentId);
            }
        } catch (error) {
            console.error('Progress tracking error:', error);
            // On error, try checking database status
            await checkDocumentStatus(documentId);
        }
    };

    // Helper function to check database status when progress tracking fails
    const checkDocumentStatus = async (docId) => {
        try {
            const statusResponse = await fetch(`${API_BASE_URL}/documents/${docId}/status`);
            const statusData = await statusResponse.json();

            if (statusData.status === 'completed') {
                stopDocumentAutoRefresh();
                elements.progressFill.style.width = '100%';
                elements.uploadStatus.textContent = 'Completed successfully!';
                elements.progressDetails.innerHTML = `
                    <div style="margin-top: 1rem; color: #38a169;">
                        <i class="fas fa-check-circle"></i>
                        Document processed successfully (${statusData.chunk_count || 'N/A'} chunks)
                    </div>
                `;
                setTimeout(async () => {
                    await loadDocuments();
                    hideUploadProgress();
                }, 2000);
            } else if (statusData.status === 'processing') {
                // Still processing - hide progress bar and show in documents list
                stopDocumentAutoRefresh();
                showToast('Still Processing', 'Document is still being processed. Check documents list for updates.', 'info');
                hideUploadProgress();
                await loadDocuments();
            } else {
                stopDocumentAutoRefresh();
                throw new Error(statusData.metadata?.error || 'Processing timeout or failed');
            }
        } catch (error) {
            stopDocumentAutoRefresh();
            elements.uploadStatus.textContent = 'Processing status unknown';
            elements.progressDetails.innerHTML = `
                <div style="margin-top: 1rem; color: #e53e3e;">
                    <i class="fas fa-exclamation-circle"></i>
                    ${error.message}
                </div>
            `;
            setTimeout(() => {
                hideUploadProgress();
                loadDocuments(); // Refresh to show actual status
            }, 3000);
        }
    };

    // Start tracking
    setTimeout(trackProgress, 1000);
}

// Documents Functions
async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE_URL}/documents`);
        const data = await response.json();
        
        if (response.ok) {
            documents = data;
            renderDocuments();
            
            if (documents.length > 0) {
                elements.documentsCard.style.display = 'block';
            }
        } else {
            throw new Error('Failed to load documents');
        }
    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

function renderDocuments() {
    if (documents.length === 0) {
        elements.documentsList.innerHTML = `
            <div style="text-align: center; color: #718096; padding: 2rem;">
                <i class="fas fa-folder-open" style="font-size: 3rem; margin-bottom: 1rem; color: #cbd5e0;"></i>
                <p>No documents uploaded yet</p>
            </div>
        `;
        return;
    }

    // Quick stats summary
    const totalDocs = documents.length;
    const completedDocs = documents.filter(d => d.status === 'completed').length;
    const processingDocs = documents.filter(d => d.status === 'processing').length;
    const failedDocs = documents.filter(d => d.status === 'failed').length;
    const totalSize = documents.reduce((sum, doc) => sum + (doc.file_size || 0), 0);

    const statsHTML = `
        <div class="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
            <div class="flex items-center space-x-6 text-sm">
                <div class="flex items-center space-x-1.5">
                    <span class="text-gray-600">Total:</span>
                    <span class="font-semibold text-gray-900">${totalDocs}</span>
                </div>
                <div class="flex items-center space-x-1.5">
                    <span class="text-gray-600">Completed:</span>
                    <span class="font-semibold text-green-600">${completedDocs}</span>
                </div>
                <div class="flex items-center space-x-1.5">
                    <span class="text-gray-600">Processing:</span>
                    <span class="font-semibold text-blue-600">${processingDocs}</span>
                </div>
                <div class="flex items-center space-x-1.5">
                    <span class="text-gray-600">Size:</span>
                    <span class="font-semibold text-gray-900">${formatFileSize(totalSize)}</span>
                </div>
            </div>
            <input type="text" class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent" id="documentSearch" placeholder="Search documents...">
        </div>
    `;

    // Enhanced table view with Tailwind styling
    const tableHTML = `
        <div class="overflow-x-auto rounded-lg border border-gray-200">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gradient-to-r from-green-50 to-emerald-50">
                    <tr>
                        <th class="px-4 py-2.5 text-left text-xs font-semibold text-gray-700">Document</th>
                        <th class="px-4 py-2.5 text-left text-xs font-semibold text-gray-700">Size</th>
                        <th class="px-4 py-2.5 text-left text-xs font-semibold text-gray-700">Chunks</th>
                        <th class="px-4 py-2.5 text-left text-xs font-semibold text-gray-700">Upload Date</th>
                        <th class="px-4 py-2.5 text-left text-xs font-semibold text-gray-700">Status</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    ${documents.map(doc => `
                        <tr class="hover:bg-green-50 transition-colors" data-status="${doc.status}" data-filename="${doc.filename.toLowerCase()}">
                            <td class="px-4 py-3 whitespace-nowrap">
                                <div class="flex items-center space-x-2.5">
                                    <div class="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-green-100 to-emerald-100 rounded-lg flex items-center justify-center">
                                        <i class="fas ${getFileIcon(doc.filename)} text-green-600 text-sm"></i>
                                    </div>
                                    <div class="font-medium text-sm text-gray-900">${doc.filename}</div>
                                    </div>
                                </div>
                            </td>
                            <td class="px-4 py-3 whitespace-nowrap">
                                <span class="text-sm text-gray-700">${formatFileSize(doc.file_size || 0)}</span>
                            </td>
                            <td class="px-4 py-3 whitespace-nowrap">
                                <span class="text-sm text-gray-700">${doc.chunk_count || 0}</span>
                            </td>
                            <td class="px-4 py-3 whitespace-nowrap">
                                <span class="text-sm text-gray-500">${formatDate(doc.upload_time)}</span>
                            </td>
                            <td class="px-4 py-3 whitespace-nowrap">
                                ${doc.status === 'completed' ?
                                    `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                                        <i class="fas fa-check-circle mr-1 text-[10px]"></i> Completed
                                    </span>` :
                                doc.status === 'processing' ?
                                    `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                                        <i class="fas fa-spinner fa-spin mr-1 text-[10px]"></i> ${doc.progress || 0}%
                                    </span>` :
                                doc.status === 'failed' ?
                                    `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                                        <i class="fas fa-exclamation-circle mr-1 text-[10px]"></i> Failed
                                    </span>` :
                                    `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700">
                                        <i class="fas fa-clock mr-1 text-[10px]"></i> Pending
                                    </span>`
                                }
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;

    elements.documentsList.innerHTML = statsHTML + tableHTML;

    // Add search functionality
    const searchInput = document.getElementById('documentSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const filename = row.dataset.filename;
                row.style.display = filename.includes(searchTerm) ? '' : 'none';
            });
        });
    }
}

function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    const iconMap = {
        pdf: 'fa-file-pdf',
        doc: 'fa-file-word',
        docx: 'fa-file-word',
        txt: 'fa-file-alt',
        csv: 'fa-file-csv',
        xlsx: 'fa-file-excel'
    };
    return iconMap[extension] || 'fa-file';
}

function getStatusIcon(status) {
    const iconMap = {
        completed: 'fa-check-circle',
        processing: 'fa-spinner fa-spin',
        failed: 'fa-exclamation-circle',
        pending: 'fa-clock'
    };
    return iconMap[status] || 'fa-question-circle';
}

function formatStatus(status) {
    const statusMap = {
        completed: 'Completed',
        processing: 'Processing',
        failed: 'Failed',
        pending: 'Pending'
    };
    return statusMap[status] || status;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

// Document filtering functionality
function setupDocumentFilters() {
    const statusFilter = document.getElementById('statusFilter');
    const searchInput = document.getElementById('documentSearch');

    if (!statusFilter || !searchInput) return;

    const filterDocuments = () => {
        const selectedStatus = statusFilter.value;
        const searchTerm = searchInput.value.toLowerCase();
        const rows = document.querySelectorAll('.documents-table tbody tr');

        rows.forEach(row => {
            const status = row.dataset.status;
            const filename = row.dataset.filename;

            const statusMatch = selectedStatus === 'all' || status === selectedStatus;
            const searchMatch = filename.includes(searchTerm);

            row.style.display = (statusMatch && searchMatch) ? '' : 'none';
        });
    };

    statusFilter.addEventListener('change', filterDocuments);
    searchInput.addEventListener('input', filterDocuments);
}

// Chat Functions
function handleQuestionInput() {
    const text = elements.questionInput.value;
    elements.charCount.textContent = text.length;
    
    // Enable/disable ask button
    elements.askButton.disabled = text.trim().length === 0 || isAsking;
}

function handleQuestionKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!elements.askButton.disabled) {
            handleAskQuestion();
        }
    }
}

let isAsking = false;

async function handleAskQuestion() {
    const question = elements.questionInput.value.trim();
    if (!question || isAsking) return;
    
    isAsking = true;
    elements.askButton.disabled = true;
    elements.askButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Thinking...</span>';
    
    // Add user message to chat
    addChatMessage(question, 'user');
    
    // Clear input
    elements.questionInput.value = '';
    elements.charCount.textContent = '0';
    
    try {
        const payload = {
            question: question,
            use_uploaded_docs_only: elements.useDocsOnly.checked,
            session_id: 'web_session_' + Date.now()
        };
        
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            addChatMessage(result.answer, 'ai', {
                sources: result.sources || [],
                processingTime: result.processing_time,
                isFromDocs: result.is_from_uploaded_docs
            });
        } else {
            throw new Error(result.detail || 'Query failed');
        }
    } catch (error) {
        console.error('Query error:', error);
        addChatMessage(
            'Sorry, I encountered an error while processing your question. Please try again.',
            'ai',
            { error: true }
        );
        showToast('Query Error', error.message, 'error');
    } finally {
        isAsking = false;
        elements.askButton.disabled = false;
        elements.askButton.innerHTML = '<i class="fas fa-paper-plane"></i> <span>Ask</span>';
    }
}

function addChatMessage(content, sender, metadata = {}) {
    // Remove welcome message if present
    const welcomeMessage = elements.chatContainer.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    let sourcesHTML = '';
    if (metadata.sources && metadata.sources.length > 0) {
        // Get unique sources (remove duplicates)
        const uniqueSources = [...new Set(metadata.sources.map(s => s.source_file || 'Unknown file'))];

        // Only show references section if there are sources
        if (uniqueSources.length > 0) {
            // Use superscript numbers for references
            const superscripts = ['¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹', '¹⁰'];

            sourcesHTML = `
                <div class="message-sources">
                    <h5><i class="fas fa-book"></i> ${uniqueSources.length === 1 ? 'Reference' : 'References'}</h5>
                    ${uniqueSources.map((source, index) => `
                        <div class="source-item">
                            <strong>${superscripts[index] || (index + 1)}.</strong> ${source}
                        </div>
                    `).join('')}
                </div>
            `;
        }
    }
    
    let metaInfo = '';
    if (sender === 'ai') {
        const sourceType = metadata.isFromDocs ? 'Documents' : 'General Knowledge';
        const responseTime = metadata.processingTime ? `${metadata.processingTime.toFixed(2)}s` : '';
        metaInfo = `
            <div class="message-meta">
                <i class="fas fa-robot"></i> DeepSeek AI • 
                Source: ${sourceType}
                ${responseTime ? ` • Response: ${responseTime}` : ''}
            </div>
        `;
    } else {
        metaInfo = `
            <div class="message-meta">
                <i class="fas fa-user"></i> You • ${new Date().toLocaleTimeString()}
            </div>
        `;
    }
    
    // Render markdown for AI messages, plain text for user messages
    const renderedContent = sender === 'ai' && typeof marked !== 'undefined'
        ? marked.parse(content)
        : content;

    messageDiv.innerHTML = `
        <div class="message-content prose prose-sm max-w-none">${renderedContent}</div>
        ${sourcesHTML}
        ${metaInfo}
    `;
    
    elements.chatContainer.appendChild(messageDiv);
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
    
    chatMessages.push({ content, sender, metadata, timestamp: Date.now() });
}

// Analytics Functions
async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/analytics`);
        const data = await response.json();
        
        if (response.ok) {
            renderAnalytics(data);
            elements.analyticsCard.style.display = 'block';
        } else {
            throw new Error('Failed to load analytics');
        }
    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

function renderAnalytics(data) {
    const analyticsHTML = `
        <div class="analytics-item blue">
            <i class="fas fa-file-alt analytics-icon"></i>
            <div class="analytics-value">${data.documents?.total || 0}</div>
            <div class="analytics-label">Total Documents</div>
        </div>
        <div class="analytics-item green">
            <i class="fas fa-check-circle analytics-icon"></i>
            <div class="analytics-value">${data.documents?.completed || 0}</div>
            <div class="analytics-label">Processed Successfully</div>
        </div>
        <div class="analytics-item purple">
            <i class="fas fa-comments analytics-icon"></i>
            <div class="analytics-value">${data.queries?.total || 0}</div>
            <div class="analytics-label">Questions Asked</div>
        </div>
        <div class="analytics-item orange">
            <i class="fas fa-clock analytics-icon"></i>
            <div class="analytics-value">${(data.queries?.average_response_time || 0).toFixed(2)}s</div>
            <div class="analytics-label">Avg Response Time</div>
        </div>
        <div class="analytics-item green">
            <i class="fas fa-chart-line analytics-icon"></i>
            <div class="analytics-value">${Math.round(data.documents?.success_rate || 0)}%</div>
            <div class="analytics-label">Success Rate</div>
        </div>
        <div class="analytics-item blue">
            <i class="fas fa-tasks analytics-icon"></i>
            <div class="analytics-value">${data.system?.active_processing_jobs || 0}</div>
            <div class="analytics-label">Active Jobs</div>
        </div>
    `;

    elements.analyticsGrid.innerHTML = analyticsHTML;
}

// Utility Functions
function showLoading(text = 'Loading...') {
    elements.loadingText.textContent = text;
    elements.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    elements.loadingOverlay.classList.add('hidden');
}

function showToast(title, message, type = 'success') {
    const toast = document.createElement('div');

    const colorMap = {
        success: 'bg-green-50 border-green-200 text-green-800',
        error: 'bg-red-50 border-red-200 text-red-800',
        warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
        info: 'bg-blue-50 border-blue-200 text-blue-800'
    };

    const iconMap = {
        success: 'fa-check-circle text-green-600',
        error: 'fa-exclamation-circle text-red-600',
        warning: 'fa-exclamation-triangle text-yellow-600',
        info: 'fa-info-circle text-blue-600'
    };

    toast.className = `${colorMap[type]} border rounded-lg shadow-lg p-4 flex items-start space-x-3 animate-fade-in`;

    toast.innerHTML = `
        <i class="fas ${iconMap[type]} text-xl mt-0.5"></i>
        <div class="flex-1">
            <div class="font-bold mb-1">${title}</div>
            <div class="text-sm">${message}</div>
        </div>
    `;

    elements.toastContainer.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 5000);

    // Remove on click
    toast.addEventListener('click', () => {
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    });
}

// Error handling for unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('Error', 'An unexpected error occurred', 'error');
});

// Page visibility change handling
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        // Page became visible, refresh status
        checkSystemStatus();
    }
});

// Clean up localStorage theme settings
if (localStorage.getItem('theme')) {
    localStorage.removeItem('theme');
}