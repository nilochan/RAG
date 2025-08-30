// Configuration
const API_BASE_URL = 'https://rag-chanchinthai.up.railway.app';

// Global state
let documents = [];
let chatMessages = [];
let isUploading = false;

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
    toastContainer: document.getElementById('toastContainer'),
    themeBtn: document.getElementById('themeBtn'),
    themeDropdown: document.getElementById('themeDropdown')
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
    elements.statusDot.className = `status-dot ${status}`;
    elements.statusText.textContent = status === 'online' ? 'Connected' : 'Disconnected';
    
    if (data && status === 'online') {
        const statusHTML = `
            <div class="status-grid">
                ${Object.entries(data.components).map(([component, status]) => `
                    <div class="status-item ${status !== 'operational' ? 'warning' : ''}">
                        <div class="status-icon">
                            <i class="fas ${getComponentIcon(component)}"></i>
                        </div>
                        <div class="status-info">
                            <h4>${formatComponentName(component)}</h4>
                            <p>${status}</p>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div style="margin-top: 1rem; text-align: center; font-size: 0.875rem; color: #718096;">
                Last updated: ${new Date(data.timestamp).toLocaleString()}
            </div>
        `;
        elements.systemStatus.innerHTML = statusHTML;
    } else {
        elements.systemStatus.innerHTML = `
            <div class="status-item error">
                <div class="status-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div class="status-info">
                    <h4>Connection Failed</h4>
                    <p>Unable to reach backend server</p>
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
        handleFileUpload(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFileUpload(file);
    }
}

async function handleFileUpload(file) {
    if (isUploading) {
        showToast('Upload Error', 'Another file is currently being uploaded', 'warning');
        return;
    }
    
    // Validate file
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = ['pdf', 'docx', 'doc', 'txt', 'csv', 'xlsx'];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    
    if (file.size > maxSize) {
        showToast('File Too Large', 'Maximum file size is 10MB', 'error');
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
    elements.uploadArea.style.display = 'none';
    elements.uploadProgress.style.display = 'block';
    elements.uploadFileName.textContent = fileName;
    elements.uploadStatus.textContent = 'Uploading...';
    elements.progressFill.style.width = '0%';
}

function hideUploadProgress() {
    elements.uploadArea.style.display = 'block';
    elements.uploadProgress.style.display = 'none';
}

async function trackUploadProgress(documentId) {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;
    
    const trackProgress = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/documents/${documentId}/progress`);
            const data = await response.json();
            
            if (response.ok) {
                const progress = data.progress || 0;
                elements.progressFill.style.width = `${progress}%`;
                elements.uploadStatus.textContent = `Processing... ${progress}%`;
                
                if (data.status === 'completed') {
                    elements.uploadStatus.textContent = 'Completed successfully!';
                    elements.progressDetails.innerHTML = `
                        <div style="margin-top: 1rem; color: #38a169;">
                            <i class="fas fa-check-circle"></i>
                            Document processed successfully
                        </div>
                    `;
                    setTimeout(() => hideUploadProgress(), 3000);
                    return;
                } else if (data.status === 'failed') {
                    throw new Error(data.error || 'Processing failed');
                }
                
                // Continue tracking if still processing
                if (attempts < maxAttempts) {
                    attempts++;
                    setTimeout(trackProgress, 2000); // Check every 2 seconds
                } else {
                    throw new Error('Processing timeout');
                }
            } else {
                throw new Error('Failed to get progress');
            }
        } catch (error) {
            elements.uploadStatus.textContent = 'Processing failed';
            elements.progressDetails.innerHTML = `
                <div style="margin-top: 1rem; color: #e53e3e;">
                    <i class="fas fa-exclamation-circle"></i>
                    ${error.message}
                </div>
            `;
            setTimeout(() => hideUploadProgress(), 5000);
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
    
    const documentsHTML = documents.map(doc => `
        <div class="document-item">
            <div class="document-info">
                <div class="document-icon">
                    <i class="fas ${getFileIcon(doc.filename)}"></i>
                </div>
                <div class="document-details">
                    <h4>${doc.filename}</h4>
                    <div class="document-meta">
                        ${formatFileSize(doc.file_size || 0)} • 
                        Uploaded ${formatDate(doc.upload_time)} • 
                        ${doc.chunk_count || 0} chunks
                    </div>
                </div>
            </div>
            <div class="document-status status-${doc.status}">
                <i class="fas ${getStatusIcon(doc.status)}"></i>
                <span>${formatStatus(doc.status)}</span>
                ${doc.progress !== null ? `<span>(${doc.progress}%)</span>` : ''}
            </div>
        </div>
    `).join('');
    
    elements.documentsList.innerHTML = documentsHTML;
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
        sourcesHTML = `
            <div class="message-sources">
                <h5><i class="fas fa-book"></i> Sources (${metadata.sources.length})</h5>
                ${metadata.sources.map((source, index) => `
                    <div class="source-item">
                        <strong>${index + 1}.</strong> ${source.source_file || 'Unknown file'}
                    </div>
                `).join('')}
            </div>
        `;
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
    
    messageDiv.innerHTML = `
        <div class="message-content">${content}</div>
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
        <div class="analytics-item">
            <div class="analytics-value">${data.documents?.total || 0}</div>
            <div class="analytics-label">Total Documents</div>
        </div>
        <div class="analytics-item">
            <div class="analytics-value">${data.documents?.completed || 0}</div>
            <div class="analytics-label">Processed Successfully</div>
        </div>
        <div class="analytics-item">
            <div class="analytics-value">${data.queries?.total || 0}</div>
            <div class="analytics-label">Questions Asked</div>
        </div>
        <div class="analytics-item">
            <div class="analytics-value">${data.queries?.average_response_time || 0}s</div>
            <div class="analytics-label">Avg Response Time</div>
        </div>
        <div class="analytics-item">
            <div class="analytics-value">${Math.round(data.documents?.success_rate || 0)}%</div>
            <div class="analytics-label">Success Rate</div>
        </div>
        <div class="analytics-item">
            <div class="analytics-value">${data.system?.active_processing_jobs || 0}</div>
            <div class="analytics-label">Active Jobs</div>
        </div>
    `;
    
    elements.analyticsGrid.innerHTML = analyticsHTML;
}

// Utility Functions
function showLoading(text = 'Loading...') {
    elements.loadingText.textContent = text;
    elements.loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    elements.loadingOverlay.style.display = 'none';
}

function showToast(title, message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <div class="toast-content">
            <div class="toast-icon">
                <i class="fas ${iconMap[type]}"></i>
            </div>
            <div class="toast-text">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
        </div>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
    
    // Remove on click
    toast.addEventListener('click', () => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
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

// Theme Switcher Functionality
class ThemeSwitcher {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'original';
        this.themes = {
            original: { name: 'Original', stylesheet: 'mainStyles' },
            twilio: { name: 'Twilio', stylesheet: 'twilioTheme' },
            stripe: { name: 'Stripe', stylesheet: 'stripeTheme' },
            notion: { name: 'Notion', stylesheet: 'notionTheme' },
<<<<<<< HEAD
            linear: { name: 'Linear', stylesheet: 'linearTheme' },
            cyber: { name: 'Cyber 🚀', stylesheet: 'cyberTheme' },
            luxury: { name: 'Luxury 💎', stylesheet: 'luxuryTheme' },
            energy: { name: 'Energy ⚡', stylesheet: 'energyTheme' }
        };
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadTheme();
        this.updateActiveTheme();
    }

    setupEventListeners() {
        // Theme button click
        elements.themeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });

        // Theme options click
        document.querySelectorAll('.theme-option').forEach(option => {
            option.addEventListener('click', (e) => {
                const theme = e.currentTarget.dataset.theme;
                this.switchTheme(theme);
                this.closeDropdown();
            });
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            this.closeDropdown();
        });

        // Prevent dropdown close when clicking inside
        elements.themeDropdown.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    toggleDropdown() {
        elements.themeDropdown.classList.toggle('open');
    }

    closeDropdown() {
        elements.themeDropdown.classList.remove('open');
    }

    switchTheme(theme) {
        // Disable all theme stylesheets
        Object.values(this.themes).forEach(themeObj => {
            const stylesheet = document.getElementById(themeObj.stylesheet);
            if (stylesheet) {
                stylesheet.disabled = true;
            }
        });

        // Enable selected theme
        if (theme === 'original') {
            document.getElementById('mainStyles').disabled = false;
        } else {
            const selectedStylesheet = document.getElementById(this.themes[theme].stylesheet);
            if (selectedStylesheet) {
                selectedStylesheet.disabled = false;
            }
        }

        this.currentTheme = theme;
        localStorage.setItem('theme', theme);
        this.updateActiveTheme();
        
        // Show success toast
        const themeName = theme === 'original' ? 'Original' : this.themes[theme].name;
        showToast('Theme Changed', `Switched to ${themeName} theme`, 'success');
    }

    loadTheme() {
        this.switchTheme(this.currentTheme);
    }

    updateActiveTheme() {
        // Remove active class from all options
        document.querySelectorAll('.theme-option').forEach(option => {
            option.classList.remove('active');
        });

        // Add active class to current theme
        const currentOption = document.querySelector(`[data-theme="${this.currentTheme}"]`);
        if (currentOption) {
            currentOption.classList.add('active');
        }
    }
}

// Initialize theme switcher
let themeSwitcher;
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit to ensure all elements are loaded
    setTimeout(() => {
        themeSwitcher = new ThemeSwitcher();
    }, 100);
});