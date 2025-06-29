// TI-CSC Web Interface JavaScript

class TIWebInterface {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.preventTabCreation();
        this.checkStatus();
        this.updateInfo();
        
        // Check GUI status periodically
        setInterval(() => this.checkGUIStatus(), 5000);
        
        // Update timestamp periodically
        setInterval(() => this.updateTimestamp(), 1000);
    }

    setupEventListeners() {
        // Basic test buttons
        document.getElementById('test-web').addEventListener('click', () => this.testWebApp());
        document.getElementById('test-gui-status').addEventListener('click', () => this.testGUIStatus());
        document.getElementById('test-gui-ping').addEventListener('click', () => this.pingGUI());

        // GUI interaction buttons
        document.getElementById('get-gui-info').addEventListener('click', () => this.getGUIInfo());
        document.getElementById('send-message').addEventListener('click', () => this.sendMessage());

        // TI-CSC action buttons
        document.getElementById('trigger-analysis').addEventListener('click', () => this.triggerAnalysis());
        document.getElementById('get-results').addEventListener('click', () => this.getResults());

        // Utility buttons
        document.getElementById('clear-log').addEventListener('click', () => this.clearLog());

        // Enter key for message input
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    async checkStatus() {
        await this.testWebApp();
        await this.checkGUIStatus();
    }

    async testWebApp() {
        try {
            const response = await fetch('/api/test');
            const data = await response.json();
            
            this.setWebStatus('ok');
            this.log('✅ Web App Test: ' + data.message, 'success');
            
        } catch (error) {
            this.setWebStatus('error');
            this.log('❌ Web App Test Failed: ' + error.message, 'error');
        }
    }

    async checkGUIStatus() {
        try {
            const response = await fetch('/api/gui/status');
            const data = await response.json();
            
            this.setGUIStatus('ok');
            this.log('✅ GUI API Connected', 'success');
            
        } catch (error) {
            this.setGUIStatus('error');
            // Don't log every failed connection check to avoid spam
            console.log('GUI API not available:', error.message);
        }
    }

    async testGUIStatus() {
        try {
            this.log('🔍 Testing GUI API connection...', 'info');
            
            const response = await fetch('/api/gui/status');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.setGUIStatus('ok');
            this.log('✅ GUI Status: ' + JSON.stringify(data, null, 2), 'success');
            
        } catch (error) {
            this.setGUIStatus('error');
            this.log('❌ GUI Status Test Failed: ' + error.message, 'error');
        }
    }

    async pingGUI() {
        try {
            this.log('🏓 Pinging GUI...', 'info');
            
            const response = await fetch('/api/gui/ping', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: 'ping from web app', timestamp: new Date().toISOString() })
            });
            
            const data = await response.json();
            this.log('🏓 GUI Ping Response: ' + JSON.stringify(data, null, 2), 'success');
            
        } catch (error) {
            this.log('❌ GUI Ping Failed: ' + error.message, 'error');
        }
    }

    async getGUIInfo() {
        try {
            this.log('ℹ️ Getting GUI information...', 'info');
            
            const response = await fetch('/api/gui/info');
            const data = await response.json();
            this.log('ℹ️ GUI Info: ' + JSON.stringify(data, null, 2), 'info');
            
        } catch (error) {
            this.log('❌ Failed to get GUI info: ' + error.message, 'error');
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message) {
            this.log('⚠️ Please enter a message first', 'warning');
            return;
        }

        try {
            this.log(`📤 Sending message: "${message}"`, 'info');
            
            const response = await fetch('/api/gui/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message, 
                    from: 'web-interface',
                    timestamp: new Date().toISOString()
                })
            });
            
            const data = await response.json();
            this.log('📥 GUI Response: ' + JSON.stringify(data, null, 2), 'success');
            
            messageInput.value = '';
            
        } catch (error) {
            this.log('❌ Failed to send message: ' + error.message, 'error');
        }
    }

    async triggerAnalysis() {
        const analysisType = document.getElementById('analysis-type').value;
        
        try {
            this.log(`🚀 Triggering ${analysisType} analysis...`, 'info');
            
            const response = await fetch('/api/gui/analysis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    type: analysisType,
                    parameters: {
                        test_param: 'test_value',
                        timestamp: new Date().toISOString()
                    }
                })
            });
            
            const data = await response.json();
            this.log('🧪 Analysis Response: ' + JSON.stringify(data, null, 2), 'success');
            
        } catch (error) {
            this.log('❌ Failed to trigger analysis: ' + error.message, 'error');
        }
    }

    async getResults() {
        try {
            this.log('📊 Getting analysis results...', 'info');
            
            const response = await fetch('/api/gui/results');
            const data = await response.json();
            this.log('📈 Results: ' + JSON.stringify(data, null, 2), 'info');
            
        } catch (error) {
            this.log('❌ Failed to get results: ' + error.message, 'error');
        }
    }

    setWebStatus(status) {
        const element = document.getElementById('web-status');
        element.className = `status ${status}`;
        element.textContent = {
            'ok': 'Connected',
            'error': 'Error',
            'unknown': 'Unknown'
        }[status];
    }

    setGUIStatus(status) {
        const element = document.getElementById('gui-status');
        element.className = `status ${status}`;
        element.textContent = {
            'ok': 'Connected',
            'error': 'Disconnected',
            'unknown': 'Checking...'
        }[status];
    }

    log(message, type = 'info') {
        const output = document.getElementById('output');
        const timestamp = new Date().toLocaleTimeString();
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        logEntry.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${message}`;
        
        output.appendChild(logEntry);
        output.scrollTop = output.scrollHeight;
        
        // Also log to console
        console.log(`[${timestamp}] ${message}`);
    }

    clearLog() {
        document.getElementById('output').innerHTML = '';
        this.log('Log cleared', 'info');
    }

    updateInfo() {
        document.getElementById('web-url').textContent = window.location.href;
        document.getElementById('gui-url').textContent = 'http://localhost:8080/api/*';
        this.updateTimestamp();
    }

    preventTabCreation() {
        // Disable keyboard shortcuts that create new tabs/windows
        document.addEventListener('keydown', (e) => {
            // Prevent Ctrl+T (new tab)
            if (e.ctrlKey && e.key === 't') {
                e.preventDefault();
                this.log('🚫 New tab creation blocked', 'warning');
                return false;
            }
            
            // Prevent Ctrl+N (new window)
            if (e.ctrlKey && e.key === 'n') {
                e.preventDefault();
                this.log('🚫 New window creation blocked', 'warning');
                return false;
            }
            
            // Prevent Ctrl+Shift+T (restore closed tab)
            if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.log('🚫 Tab restoration blocked', 'warning');
                return false;
            }
            
            // Prevent Ctrl+Shift+N (new incognito window)
            if (e.ctrlKey && e.shiftKey && e.key === 'N') {
                e.preventDefault();
                this.log('🚫 Incognito window creation blocked', 'warning');
                return false;
            }
            
            // Allow Ctrl+W (close window) but warn user
            if (e.ctrlKey && e.key === 'w') {
                this.log('⚠️ Closing TI-CSC interface...', 'info');
                // Don't prevent this - let user close if they want
            }
        });
        
        // Override window.open to prevent programmatic new windows
        const originalOpen = window.open;
        window.open = (...args) => {
            this.log('🚫 Programmatic window.open() blocked', 'warning');
            return null;
        };
        
        // Disable right-click context menu to prevent "Open in new tab"
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.log('🚫 Context menu disabled', 'warning');
            return false;
        });
        
        this.log('🔒 Tab prevention system activated', 'info');
    }

    updateTimestamp() {
        document.getElementById('timestamp').textContent = new Date().toLocaleString();
    }
}

// Initialize the web interface when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.tiWebInterface = new TIWebInterface();
    console.log('🚀 TI-CSC Web Interface initialized');
}); 