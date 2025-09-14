// WhisperEngine Desktop App JavaScript

class WhisperEngineApp {
    constructor() {
        this.ws = null;
        this.currentConversationId = null;
        this.conversations = new Map();
        this.settings = this.loadSettings();
        this.messageHistory = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initFileUpload();
        this.loadConversationsFromStorage();
        this.connectWebSocket();
        this.loadConversations();
        this.updateUI();
    }

    setupEventListeners() {
        // Message input and sending
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        
        messageInput.addEventListener('input', this.handleInputChange.bind(this));
        messageInput.addEventListener('keydown', this.handleKeyDown.bind(this));
        sendBtn.addEventListener('click', this.sendMessage.bind(this));

        // Settings
        document.getElementById('settings-btn').addEventListener('click', this.openSettings.bind(this));
        document.getElementById('close-settings').addEventListener('click', this.closeSettings.bind(this));
        document.getElementById('cancel-settings').addEventListener('click', this.closeSettings.bind(this));
        document.getElementById('save-settings').addEventListener('click', this.saveSettings.bind(this));

        // New chat
        document.getElementById('new-chat-btn').addEventListener('click', this.startNewChat.bind(this));

        // Modal close on background click
        document.getElementById('settings-modal').addEventListener('click', (e) => {
            if (e.target.id === 'settings-modal') {
                this.closeSettings();
            }
        });
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus('connected');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus('disconnected');
            // Attempt to reconnect after 3 seconds
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus('error');
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'ai_response':
                this.addMessage(data.content, 'assistant', data.metadata);
                break;
            case 'error':
                this.showError(data.message);
                break;
            case 'conversation_list':
                this.updateConversationList(data.conversations);
                break;
        }
    }

    handleInputChange() {
        const input = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        const charCount = document.getElementById('char-count');
        
        const length = input.value.length;
        charCount.textContent = `${length}/4000`;
        
        sendBtn.disabled = length === 0 || length > 4000;
        
        // Auto-resize textarea
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    }

    handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }

    async sendMessage() {
        const input = document.getElementById('message-input');
        const message = input.value.trim();
        const attachedFiles = this.getAttachedFiles();
        
        if (!message && attachedFiles.length === 0) {
            return;
        }
        
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.showError('Connection lost. Please refresh the page.');
            return;
        }

        // If files are attached, use the enhanced message format
        if (attachedFiles.length > 0) {
            return await this.sendMessageWithFiles();
        }

        // Add user message to UI
        this.addMessage(message, 'user');
        
        // Clear input
        input.value = '';
        this.handleInputChange();

        // Show typing indicator
        this.showTypingIndicator();

        // Send message via WebSocket
        try {
            this.ws.send(JSON.stringify({
                type: 'chat_message',
                content: message,
                conversation_id: this.currentConversationId,
                settings: this.settings
            }));
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.showError('Failed to send message. Please check your connection.');
        }
    }

    addMessage(content, sender, metadata = {}) {
        const container = document.getElementById('messages-container');
        const welcomeMessage = container.querySelector('.welcome-message');
        
        // Remove welcome message if it exists
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'user' ? '👤' : '🤖';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = content;
        
        const messageMeta = document.createElement('div');
        messageMeta.className = 'message-meta';
        
        const timestamp = new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        let metaContent = `<span>${timestamp}</span>`;
        
        messageMeta.innerHTML = metaContent;
        
        messageContent.appendChild(messageText);
        messageContent.appendChild(messageMeta);
        
        // Add copy button for assistant messages
        if (sender === 'assistant') {
            const messageActions = document.createElement('div');
            messageActions.className = 'message-actions';
            
            const copyBtn = document.createElement('button');
            copyBtn.className = 'btn-copy';
            copyBtn.innerHTML = '<span>📋</span> Copy';
            copyBtn.onclick = () => this.copyToClipboard(content, copyBtn);
            
            messageActions.appendChild(copyBtn);
            messageContent.appendChild(messageActions);
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        container.appendChild(messageDiv);
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
        
        // Save message to current conversation
        this.saveMessageToConversation(content, sender, metadata);
        
        // Hide typing indicator if this is an AI response
        if (sender === 'assistant') {
            this.hideTypingIndicator();
        }

        // Update conversation stats
        this.updateConversationStats();
    }

    saveMessageToConversation(content, sender, metadata = {}) {
        if (!this.currentConversationId) {
            return;
        }
        
        const conversation = this.conversations.get(this.currentConversationId);
        if (!conversation) {
            return;
        }
        
        // Add message to conversation
        const message = {
            content,
            role: sender === 'user' ? 'user' : 'assistant',
            timestamp: new Date().toISOString(),
            metadata
        };
        
        if (!conversation.messages) {
            conversation.messages = [];
        }
        
        conversation.messages.push(message);
        conversation.lastActivity = new Date().toISOString();
        
        // Set conversation title from first user message if not already set
        if (!conversation.title && sender === 'user' && conversation.messages.length <= 2) {
            conversation.title = content.length > 50 ? 
                                content.substring(0, 47) + '...' : 
                                content;
        }
        
        // Update conversation in map
        this.conversations.set(this.currentConversationId, conversation);
        
        // Save to storage and update sidebar
        this.saveConversationsToStorage();
        this.loadConversations();
    }

    showTypingIndicator() {
        const container = document.getElementById('messages-container');
        
        // Remove existing typing indicator
        this.hideTypingIndicator();
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-indicator';
        typingDiv.id = 'typing-indicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '🤖';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const text = document.createElement('div');
        text.className = 'typing-text';
        text.innerHTML = 'AI is thinking...';
        
        const dots = document.createElement('div');
        dots.className = 'typing-dots';
        dots.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        
        content.appendChild(text);
        content.appendChild(dots);
        typingDiv.appendChild(avatar);
        typingDiv.appendChild(content);
        
        container.appendChild(typingDiv);
        container.scrollTop = container.scrollHeight;
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    startNewChat() {
        this.currentConversationId = this.generateConversationId();
        
        // Create new conversation object
        const newConversation = {
            id: this.currentConversationId,
            title: null, // Will be set from first message
            messages: [],
            createdAt: new Date().toISOString(),
            lastActivity: new Date().toISOString()
        };
        
        this.conversations.set(this.currentConversationId, newConversation);
        
        // Clear messages and show welcome
        const container = document.getElementById('messages-container');
        container.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">🤖</div>
                <h3>New Conversation</h3>
                <p>Start a new conversation with your AI assistant.</p>
                <div class="welcome-features">
                    <div class="feature">
                        <span class="feature-icon">🧠</span>
                        <span>Advanced Memory Networks</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">💭</span>
                        <span>Emotional Intelligence</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">🔒</span>
                        <span>Local Privacy</span>
                    </div>
                </div>
            </div>
        `;
        
        // Update UI
        document.getElementById('chat-title').textContent = 'New Conversation';
        this.updateConversationStats();
        this.loadConversations(); // Refresh sidebar
        
        // Focus input
        document.getElementById('message-input').focus();
    }

    generateConversationId() {
        return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    updateConversationStats() {
        const messages = document.querySelectorAll('.message:not(.typing-indicator)');
        const messageCount = messages.length;
        
        document.getElementById('message-count').textContent = `${messageCount} messages`;
    }

    updateConnectionStatus(status) {
        const statusDot = document.getElementById('connection-status');
        const statusText = statusDot.nextElementSibling;
        
        statusDot.className = `status-dot status-${status}`;
        
        switch (status) {
            case 'connected':
                statusText.textContent = 'Connected';
                break;
            case 'connecting':
                statusText.textContent = 'Connecting...';
                break;
            case 'disconnected':
                statusText.textContent = 'Disconnected';
                break;
            case 'error':
                statusText.textContent = 'Connection Error';
                break;
        }
    }

    openSettings() {
        const modal = document.getElementById('settings-modal');
        modal.classList.add('active');
        
        // Load current settings into form
        document.getElementById('openrouter-key').value = this.settings.openrouter_key || '';
        document.getElementById('model-select').value = this.settings.model || 'openai/gpt-4o-mini';
        document.getElementById('local-storage').checked = this.settings.local_storage !== false;
    }

    closeSettings() {
        const modal = document.getElementById('settings-modal');
        modal.classList.remove('active');
    }

    saveSettings() {
        // Gather settings from form
        this.settings = {
            openrouter_key: document.getElementById('openrouter-key').value,
            model: document.getElementById('model-select').value,
            local_storage: document.getElementById('local-storage').checked
        };
        
        // Save to localStorage
        localStorage.setItem('whisperengine_settings', JSON.stringify(this.settings));
        
        // Update model info display
        document.getElementById('model-info').textContent = `Using: ${this.settings.model.split('/').pop()}`;
        
        this.closeSettings();
        
        // Show success message
        this.showSuccess('Settings saved successfully!');
    }

    loadSettings() {
        const saved = localStorage.getItem('whisperengine_settings');
        return saved ? JSON.parse(saved) : {
            model: 'openai/gpt-4o-mini',
            local_storage: true,
            analytics_enabled: false
        };
    }

    loadConversations() {
        const listContainer = document.getElementById('conversation-list');
        
        if (this.conversations.size === 0) {
            listContainer.innerHTML = `
                <div class="empty-conversations">
                    <div style="padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.875rem;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">💬</div>
                        No conversations yet.<br>
                        Start a new chat to begin!
                    </div>
                </div>
            `;
            return;
        }

        // Convert conversations map to array and sort by last activity
        const conversationArray = Array.from(this.conversations.entries())
            .map(([id, conv]) => ({ id, ...conv }))
            .sort((a, b) => new Date(b.lastActivity || 0) - new Date(a.lastActivity || 0));

        listContainer.innerHTML = '';
        
        conversationArray.forEach(conv => {
            const conversationItem = this.createConversationItem(conv);
            listContainer.appendChild(conversationItem);
        });
    }

    createConversationItem(conversation) {
        const item = document.createElement('div');
        item.className = `conversation-item ${conversation.id === this.currentConversationId ? 'active' : ''}`;
        item.dataset.conversationId = conversation.id;
        
        // Generate title from first message or use timestamp
        const title = conversation.title || 
                     conversation.messages?.[0]?.content?.substring(0, 30) + '...' || 
                     'New Conversation';
        
        // Generate preview from last message
        const lastMessage = conversation.messages?.[conversation.messages.length - 1];
        const preview = lastMessage ? 
                       (lastMessage.content.length > 50 ? 
                        lastMessage.content.substring(0, 50) + '...' : 
                        lastMessage.content) : 
                       'No messages yet';
        
        // Format timestamp
        const timestamp = conversation.lastActivity ? 
                         this.formatRelativeTime(new Date(conversation.lastActivity)) : 
                         'Just now';
        
        item.innerHTML = `
            <div class="conversation-title">${title}</div>
            <div class="conversation-preview">${preview}</div>
            <div class="conversation-meta">
                <span>${conversation.messages?.length || 0} messages</span>
                <span>${timestamp}</span>
            </div>
            <div class="conversation-actions">
                <button onclick="window.whisperEngineApp.renameConversation('${conversation.id}')" title="Rename">✏️</button>
                <button onclick="window.whisperEngineApp.deleteConversation('${conversation.id}')" title="Delete">🗑️</button>
            </div>
        `;
        
        // Add click handler to switch conversations
        item.addEventListener('click', (e) => {
            if (!e.target.closest('.conversation-actions')) {
                this.switchToConversation(conversation.id);
            }
        });
        
        return item;
    }

    formatRelativeTime(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        
        if (diffDays > 0) {
            return diffDays === 1 ? 'Yesterday' : `${diffDays} days ago`;
        } else if (diffHours > 0) {
            return diffHours === 1 ? '1 hour ago' : `${diffHours} hours ago`;
        } else if (diffMinutes > 0) {
            return diffMinutes === 1 ? '1 minute ago' : `${diffMinutes} minutes ago`;
        } else {
            return 'Just now';
        }
    }

    switchToConversation(conversationId) {
        if (this.currentConversationId === conversationId) {
            return;
        }
        
        this.currentConversationId = conversationId;
        
        // Update UI to show conversation as active
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeItem = document.querySelector(`[data-conversation-id="${conversationId}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
        
        // Load conversation messages
        this.loadConversationMessages(conversationId);
        
        // Update chat title
        const conversation = this.conversations.get(conversationId);
        if (conversation) {
            document.getElementById('chat-title').textContent = 
                conversation.title || conversation.messages?.[0]?.content?.substring(0, 50) + '...' || 'Conversation';
        }
    }

    loadConversationMessages(conversationId) {
        const conversation = this.conversations.get(conversationId);
        if (!conversation || !conversation.messages) {
            return;
        }
        
        // Clear current messages
        const container = document.getElementById('messages-container');
        container.innerHTML = '';
        
        // Add messages from conversation
        conversation.messages.forEach(msg => {
            this.addMessage(msg.content, msg.role === 'user' ? 'user' : 'assistant', msg.metadata);
        });
        
        this.updateConversationStats();
    }

    renameConversation(conversationId) {
        const conversation = this.conversations.get(conversationId);
        if (!conversation) return;
        
        const currentTitle = conversation.title || 
                           conversation.messages?.[0]?.content?.substring(0, 30) || 
                           'New Conversation';
        
        const newTitle = prompt('Enter new conversation title:', currentTitle);
        if (newTitle && newTitle.trim() && newTitle !== currentTitle) {
            conversation.title = newTitle.trim();
            this.conversations.set(conversationId, conversation);
            this.loadConversations();
            
            // Update chat title if this is the current conversation
            if (conversationId === this.currentConversationId) {
                document.getElementById('chat-title').textContent = newTitle;
            }
            
            this.saveConversationsToStorage();
        }
    }

    deleteConversation(conversationId) {
        const conversation = this.conversations.get(conversationId);
        if (!conversation) return;
        
        const title = conversation.title || 
                     conversation.messages?.[0]?.content?.substring(0, 30) + '...' || 
                     'this conversation';
        
        if (confirm(`Are you sure you want to delete "${title}"?`)) {
            this.conversations.delete(conversationId);
            
            // If this was the current conversation, start a new one
            if (conversationId === this.currentConversationId) {
                this.startNewChat();
            }
            
            this.loadConversations();
            this.saveConversationsToStorage();
        }
    }

    saveConversationsToStorage() {
        try {
            const conversationsData = {};
            this.conversations.forEach((conv, id) => {
                conversationsData[id] = conv;
            });
            localStorage.setItem('whisperengine_conversations', JSON.stringify(conversationsData));
        } catch (error) {
            console.error('Failed to save conversations:', error);
        }
    }

    loadConversationsFromStorage() {
        try {
            const stored = localStorage.getItem('whisperengine_conversations');
            if (stored) {
                const conversationsData = JSON.parse(stored);
                Object.entries(conversationsData).forEach(([id, conv]) => {
                    this.conversations.set(id, conv);
                });
            }
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    }

    updateUI() {
        // Update model info
        const modelName = this.settings.model ? this.settings.model.split('/').pop() : 'gpt-4o-mini';
        document.getElementById('model-info').textContent = `Using: ${modelName}`;
        
        // Set initial focus
        document.getElementById('message-input').focus();
    }

    showError(message) {
        // Simple error display - in a real app you'd want a proper notification system
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--error-color);
            color: white;
            padding: 1rem;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            z-index: 1001;
            max-width: 300px;
        `;
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    // Copy functionality
    async copyToClipboard(text, buttonElement) {
        try {
            await navigator.clipboard.writeText(text);
            
            // Visual feedback
            const originalHTML = buttonElement.innerHTML;
            buttonElement.innerHTML = '<span>✅</span> Copied!';
            buttonElement.classList.add('copied');
            
            setTimeout(() => {
                buttonElement.innerHTML = originalHTML;
                buttonElement.classList.remove('copied');
            }, 2000);
            
        } catch (err) {
            console.error('Failed to copy text: ', err);
            this.showError('Failed to copy to clipboard');
        }
    }

    // File upload functionality
    initFileUpload() {
        const attachBtn = document.getElementById('attach-btn');
        const fileInput = document.getElementById('file-input');
        const fileUploadArea = document.getElementById('file-upload-area');
        const fileDropZone = document.getElementById('file-drop-zone');
        const filePreviewArea = document.getElementById('file-preview-area');
        
        // Attach button click
        attachBtn.addEventListener('click', () => {
            if (fileUploadArea.classList.contains('hidden')) {
                this.showFileUpload();
            } else {
                this.hideFileUpload();
            }
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });
        
        // Drag and drop
        fileDropZone.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileDropZone.classList.add('dragover');
        });
        
        fileDropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            fileDropZone.classList.remove('dragover');
        });
        
        fileDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            fileDropZone.classList.remove('dragover');
            this.handleFiles(e.dataTransfer.files);
        });
    }

    showFileUpload() {
        const fileUploadArea = document.getElementById('file-upload-area');
        fileUploadArea.classList.remove('hidden');
        document.getElementById('attach-btn').classList.add('active');
    }

    hideFileUpload() {
        const fileUploadArea = document.getElementById('file-upload-area');
        fileUploadArea.classList.add('hidden');
        document.getElementById('attach-btn').classList.remove('active');
        this.clearFilePreview();
    }

    async handleFiles(files) {
        const filePreviewArea = document.getElementById('file-preview-area');
        
        for (const file of files) {
            if (file.size > 10 * 1024 * 1024) { // 10MB limit
                this.showError(`File "${file.name}" is too large. Maximum size is 10MB.`);
                continue;
            }
            
            const filePreview = await this.createFilePreview(file);
            filePreviewArea.appendChild(filePreview);
        }
    }

    async createFilePreview(file) {
        const preview = document.createElement('div');
        preview.className = 'file-preview';
        preview.dataset.fileName = file.name;
        
        // Determine file type
        const isImage = file.type.startsWith('image/');
        const isText = file.type.startsWith('text/') || file.name.endsWith('.txt') || file.name.endsWith('.md');
        
        if (isImage) {
            preview.classList.add('image');
        }
        
        preview.innerHTML = `
            <div class="file-preview-header">
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${this.formatFileSize(file.size)}</div>
                </div>
                <button class="file-remove" onclick="this.parentElement.parentElement.remove()">✕</button>
            </div>
            <div class="file-preview-content">
                <div class="spinner"></div>
            </div>
        `;
        
        // Load file content for preview
        const reader = new FileReader();
        
        if (isImage) {
            reader.onload = (e) => {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.alt = file.name;
                preview.querySelector('.file-preview-content').innerHTML = '';
                preview.querySelector('.file-preview-content').appendChild(img);
                
                // Store base64 data for OpenAI format
                preview.dataset.fileData = e.target.result;
                preview.dataset.fileType = file.type;
            };
            reader.readAsDataURL(file);
        } else if (isText && file.size < 1024 * 1024) { // 1MB limit for text preview
            reader.onload = (e) => {
                const content = e.target.result.substring(0, 200) + (e.target.result.length > 200 ? '...' : '');
                preview.querySelector('.file-preview-content').textContent = content;
                
                // Store text data
                preview.dataset.fileData = e.target.result;
                preview.dataset.fileType = file.type;
            };
            reader.readAsText(file);
        } else {
            // For other file types, just show file info
            preview.querySelector('.file-preview-content').innerHTML = `
                <div style="text-align: center; color: var(--text-secondary);">
                    📄 ${file.type || 'Unknown type'}
                </div>
            `;
            
            // Store file as base64 for upload
            reader.onload = (e) => {
                preview.dataset.fileData = e.target.result;
                preview.dataset.fileType = file.type;
            };
            reader.readAsDataURL(file);
        }
        
        return preview;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    clearFilePreview() {
        const filePreviewArea = document.getElementById('file-preview-area');
        filePreviewArea.innerHTML = '';
        document.getElementById('file-input').value = '';
    }

    getAttachedFiles() {
        const filePreviewArea = document.getElementById('file-preview-area');
        const filePreviews = filePreviewArea.querySelectorAll('.file-preview');
        const files = [];
        
        filePreviews.forEach(preview => {
            if (preview.dataset.fileData) {
                files.push({
                    name: preview.dataset.fileName,
                    type: preview.dataset.fileType,
                    data: preview.dataset.fileData
                });
            }
        });
        
        return files;
    }

    // Enhanced message sending with file support
    async sendMessageWithFiles() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        const attachedFiles = this.getAttachedFiles();
        
        if (!message && attachedFiles.length === 0) {
            return;
        }
        
        // Create OpenAI-compatible message format
        const messageData = {
            role: 'user',
            content: []
        };
        
        // Add text content
        if (message) {
            messageData.content.push({
                type: 'text',
                text: message
            });
        }
        
        // Add file content
        attachedFiles.forEach(file => {
            if (file.type.startsWith('image/')) {
                messageData.content.push({
                    type: 'image_url',
                    image_url: {
                        url: file.data
                    }
                });
            } else {
                // For text files, add as text content
                if (file.type.startsWith('text/')) {
                    messageData.content.push({
                        type: 'text',
                        text: `[File: ${file.name}]\n${file.data}`
                    });
                }
            }
        });
        
        // Send via WebSocket
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'message',
                content: messageData,
                conversation_id: this.currentConversationId,
                files: attachedFiles.map(f => ({
                    name: f.name,
                    type: f.type,
                    size: f.data.length
                }))
            }));
            
            // Display user message
            const displayMessage = message + (attachedFiles.length > 0 ? 
                `\n\n📎 ${attachedFiles.length} file(s) attached` : '');
            this.addMessage(displayMessage, 'user');
            
            // Clear input and files
            messageInput.value = '';
            this.hideFileUpload();
            this.updateUI();
            this.showTypingIndicator();
        }
    }

    showSuccess(message) {
        // Simple success display
        const successDiv = document.createElement('div');
        successDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--success-color);
            color: white;
            padding: 1rem;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            z-index: 1001;
            max-width: 300px;
        `;
        successDiv.textContent = message;
        
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.whisperEngineApp = new WhisperEngineApp();
});

// Global functions for HTML onclick handlers
window.hideFileUpload = () => {
    if (window.whisperEngineApp) {
        window.whisperEngineApp.hideFileUpload();
    }
};

window.whisperEngineApp = null;

// Additional global methods for conversation management
window.addEventListener('load', () => {
    // These will be available after app initialization
    window.renameConversation = (id) => {
        if (window.whisperEngineApp) {
            window.whisperEngineApp.renameConversation(id);
        }
    };
    
    window.deleteConversation = (id) => {
        if (window.whisperEngineApp) {
            window.whisperEngineApp.deleteConversation(id);
        }
    };
});

// Handle window/app lifecycle
window.addEventListener('beforeunload', () => {
    if (window.whisperEngineApp && window.whisperEngineApp.ws) {
        window.whisperEngineApp.ws.close();
    }
});