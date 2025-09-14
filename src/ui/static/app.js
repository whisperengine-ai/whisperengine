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
        
        if (!message || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
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
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        container.appendChild(messageDiv);
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
        
        // Hide typing indicator if this is an AI response
        if (sender === 'assistant') {
            this.hideTypingIndicator();
        }

        // Update conversation stats
        this.updateConversationStats();
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
        
        // Clear messages
        const container = document.getElementById('messages-container');
        container.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">🤖</div>
                <h3>New Conversation</h3>
                <p>Start a new conversation with your AI assistant.</p>
            </div>
        `;
        
        // Update UI
        document.getElementById('chat-title').textContent = 'New Conversation';
        this.updateConversationStats();
        
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
        // In a real app, this would load from the database
        // For now, we'll just show a placeholder
        const listContainer = document.getElementById('conversation-list');
        
        if (this.conversations.size === 0) {
            listContainer.innerHTML = `
                <div style="padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.875rem;">
                    No conversations yet.<br>
                    Start a new chat to begin!
                </div>
            `;
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

// Handle window/app lifecycle
window.addEventListener('beforeunload', () => {
    if (window.whisperEngineApp && window.whisperEngineApp.ws) {
        window.whisperEngineApp.ws.close();
    }
});