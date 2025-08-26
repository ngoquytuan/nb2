class SpamFilterApp {
    constructor() {
        this.socket = null;
        this.currentTab = 'inbox';
        this.testMessages = {
            legitimate: [
                "Xin chào, tôi muốn hỏi về sản phẩm của công ty",
                "Cảm ơn bạn đã hỗ trợ tôi hôm qua",
                "Khi nào có meeting tiếp theo?"
            ],
            suspicious: [
                "Anh có thể chuyển khoản giúp em không? Em sẽ trả sau",
                "Link này hay lắm, bạn vào xem đi",
                "Gửi mã OTP giúp tôi, tôi đang gặp khó khăn"
            ],
            spam: [
                "CHÚC MỪNG! Bạn đã trúng giải 100 triệu VND! Click link ngay",
                "Vay tiền nhanh 24/7, không cần thế chấp! Liên hệ ngay",
                "CẢNH BÁO! Tài khoản sẽ bị khóa nếu không xác thực ngay"
            ]
        };
        
        // Chạy init khi DOM đã sẵn sàng
        document.addEventListener('DOMContentLoaded', () => this.init());
    }
    
    // PHẦN 1: KHỞI TẠO VÀ SỰ KIỆN
    // ===================================

    init() {
        this.initSocket();
        this.initEventListeners();
        this.loadInitialData();
    }
    
    initSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            this.updateConnectionStatus(true);
            this.showToast('Connected to server', 'success');
        });
        
        this.socket.on('disconnect', () => {
            this.updateConnectionStatus(false);
            this.showToast('Disconnected from server', 'error');
        });
        
        this.socket.on('message_processed', (data) => {
            this.showToast(`Message ${data.message_id} processed`, 'info');
            // Chỉ refresh nếu tab đang xem có liên quan
            if (['inbox', 'flagged', 'blocked', 'admin'].includes(this.currentTab)) {
                 this.loadTabData(this.currentTab);
            }
            this.loadStats();
        });
    }
    
    initEventListeners() {
        // Form gửi tin nhắn
        document.getElementById('messageForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });
        
        // Các nút test nhanh
        document.querySelector('.btn-success').addEventListener('click', () => this.sendTestMessage('legitimate'));
        document.querySelector('.btn-warning').addEventListener('click', () => this.sendTestMessage('suspicious'));
        document.querySelector('.btn-danger').addEventListener('click', () => this.sendTestMessage('spam'));

        // Chuyển tab
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = button.getAttribute('onclick').match(/showTab\('(.+?)'\)/)[1];
                this.showTab(tabName, e.target);
            });
        });

        // Nút trong tab Admin
        document.querySelector('.btn-info[onclick="refreshAllData()"]').addEventListener('click', () => this.refreshAllData());
        document.querySelector('.btn-secondary[onclick="exportLogs()"]').addEventListener('click', () => this.exportLogs());

        // Nút trong tab Settings
        document.querySelector('.btn-primary[onclick="saveSettings()"]').addEventListener('click', () => this.saveSettings());
        document.querySelector('.btn-info[onclick="loadSettings()"]').addEventListener('click', () => this.loadSettings());
		// FIX: Thêm event listener cho các nút test
        document.querySelector('.btn-warning[onclick="testCurrentLLM()"]').addEventListener('click', () => this.testCurrentLLM());
        // Thêm cho các nút test nhỏ bên cạnh API key
        document.querySelectorAll('button[onclick^="testLLMConnection"]').forEach(button => {
            const provider = button.getAttribute('onclick').match(/testLLMConnection\('(.+?)'\)/)[1];
            button.addEventListener('click', () => this.testLLMConnection(provider));
        });
        // Thanh trượt
        document.getElementById('naive_bayes_threshold').addEventListener('input', e => {
            document.getElementById('nb_threshold_value').textContent = e.target.value;
        });
        document.getElementById('suspicious_threshold').addEventListener('input', e => {
            document.getElementById('sus_threshold_value').textContent = e.target.value;
        });
        
        // Tự động refresh nhẹ nhàng
        setInterval(() => {
            if (document.visibilityState === 'visible') { // Chỉ refresh khi tab đang được xem
                this.loadTabData(this.currentTab);
                this.loadStats();
            }
        }, 15000); // 15 giây
    }

    // PHẦN 2: CÁC HÀM XỬ LÝ GIAO DIỆN
    // ===================================
    
    updateConnectionStatus(connected) {
        const statusIndicator = document.getElementById('connectionStatus');
        const dot = statusIndicator.querySelector('.status-dot');
        const text = statusIndicator.querySelector('span:last-child');
        
        if (connected) {
            dot.className = 'status-dot online';
            text.textContent = 'Connected';
        } else {
            dot.className = 'status-dot offline';
            text.textContent = 'Disconnected';
        }
    }

    showTab(tabName, clickedButton) {
        this.currentTab = tabName;
        
        document.querySelectorAll('.tab-button').forEach(button => button.classList.remove('active'));
        clickedButton.classList.add('active');
        
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // Chỉ load data cho các tab message, tab settings không cần
        if (['inbox', 'flagged', 'blocked', 'admin'].includes(tabName)) {
            this.loadTabData(tabName);
        }
    }

    renderMessages(messages, containerId, isAdmin = false) {
        const container = document.getElementById(containerId);
        if (!messages || messages.length === 0) {
            container.innerHTML = '<p class="empty-state">No messages found...</p>';
            return;
        }
        
        container.innerHTML = messages.map(msg => `
            <div class="message-item ${msg.classification || ''}">
                <div class="message-header">
                    <span class="message-sender">${this.escapeHtml(msg.sender)}</span>
                    <span class="message-time">${new Date(msg.created_at).toLocaleString()}</span>
                </div>
                <div class="message-content">${this.escapeHtml(msg.content)}</div>
                <div class="message-meta">
                    <span>ID: ${msg.id}</span>
                    <span>Status: ${msg.status}</span>
                    ${msg.classification ? `<span class="classification-badge ${msg.classification}">${msg.classification.toUpperCase()}</span>` : ''}
                </div>
                ${isAdmin && msg.filter_history ? `
                    <div class="filter-history">
                        <strong>History:</strong> ${msg.filter_history.replace(/\|/g, ' &rarr; ')}
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    // PHẦN 3: TƯƠNG TÁC VỚI API
    // ===================================

    async sendMessage() {
        const sender = document.getElementById('sender').value.trim();
        const content = document.getElementById('message').value.trim();
        if (!sender || !content) {
            return this.showToast('Sender and message are required.', 'warning');
        }

        document.getElementById('processingStatus').style.display = 'flex';
        try {
            const response = await fetch('/api/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sender, content })
            });
            const data = await response.json();
            if (data.success) {
                this.showToast(`Message sent! ID: ${data.message_id}`, 'success');
                document.getElementById('message').value = '';
            } else {
                this.showToast(data.error || 'Failed to send message', 'error');
            }
        } catch (error) {
            this.showToast('Network error while sending.', 'error');
        } finally {
            document.getElementById('processingStatus').style.display = 'none';
        }
    }
    
    sendTestMessage(type) {
        const messages = this.testMessages[type];
        const randomMessage = messages[Math.floor(Math.random() * messages.length)];
        document.getElementById('sender').value = `Test User (${type})`;
        document.getElementById('message').value = randomMessage;
        this.sendMessage();
    }
    
    async loadTabData(tabName) {
        const endpoints = {
            inbox: '/api/inbox?status=approved',
            flagged: '/api/inbox?status=flagged',
            blocked: '/api/inbox?status=blocked',
            admin: '/api/admin/messages'
        };
        const containerIds = {
            inbox: 'inboxMessages',
            flagged: 'flaggedMessages',
            blocked: 'blockedMessages',
            admin: 'adminMessages'
        };

        if (!endpoints[tabName]) return;

        try {
            const response = await fetch(endpoints[tabName]);
            const data = await response.json();
            this.renderMessages(data, containerIds[tabName], tabName === 'admin');
        } catch (error) {
            this.showToast(`Failed to load ${tabName} data`, 'error');
        }
    }
    
    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            document.getElementById('totalProcessed').textContent = stats.total_processed || 0;
            document.getElementById('legitimateCount').textContent = stats.legitimate || 0;
            document.getElementById('suspiciousCount').textContent = stats.suspicious || 0;
            document.getElementById('blockedCount').textContent = stats.blocked || 0;
        } catch (error) { console.error('Error loading stats:', error); }
    }
    
    // PHẦN 4: CÁC HÀM LIÊN QUAN ĐẾN SETTINGS (ĐÃ HỢP NHẤT)
    // ========================================================
    
    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const settings = await response.json();
            for (const category in settings) {
                settings[category].forEach(setting => {
                    const el = document.getElementById(setting.key);
                    if (!el) return;
					
                    // FIX: Sửa lỗi checkbox
                    if (el.type === 'checkbox') {
                        // Chuyển giá trị về chữ thường trước khi so sánh
                        el.checked = setting.value.toString().toLowerCase() === 'true';
                    } else if (el.type === 'range') {
                        el.value = setting.value;
                        const valueEl = document.getElementById(el.id.replace('_threshold', '_threshold_value'));
                        if (valueEl) valueEl.textContent = setting.value;
                    } else {
                        el.value = setting.value;
                    }
                });
            }
            this.showToast('Settings loaded successfully!', 'success');
        } catch (error) {
            this.showToast('Error loading settings.', 'error');
        }
    }

    async saveSettings() {
        const settingsData = {};
        const keys = ['llm_provider', 'openai_api_key', 'groq_api_key', 'openrouter_api_key', 'naive_bayes_threshold', 'suspicious_threshold', 'enable_mock_fallback', 'enable_health_check'];
        
        keys.forEach(key => {
            const el = document.getElementById(key);
            if (el) {
                if (el.type === 'checkbox') {
                    settingsData[key] = el.checked;
                } else if (!(el.type === 'password' && (el.value === '***masked***' || el.value === ''))) {
                    settingsData[key] = el.value;
                }
            }
        });

        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settingsData)
            });
            await response.json();
            this.showToast('Settings saved successfully!', 'success');
            setTimeout(() => this.loadSettings(), 500);
        } catch (error) {
            this.showToast('Error saving settings.', 'error');
        }
    }
	// FIX: Thêm hai hàm test LLM mới
    async testLLMConnection(provider) {
        const apiKey = document.getElementById(`${provider}_api_key`).value;
        if (!apiKey || apiKey === '***masked***') {
            return this.showToast(`Please enter an API key for ${provider} to test.`, 'warning');
        }
        
        this.showToast(`Testing ${provider}...`, 'info');

        // Thủ thuật: Tạm thời lưu provider và key, sau đó gọi test
        const originalProvider = document.getElementById('llm_provider').value;
        const payload = {
            llm_provider: provider,
            [`${provider}_api_key`]: apiKey
        };

        try {
            // Tạm thời lưu provider đang test
            await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            // Gọi hàm test chung
            await this.testCurrentLLM(true); // true = isSubTest

        } catch (e) {
            this.showToast(`Failed to test ${provider}.`, 'error');
        } finally {
            // Khôi phục lại provider ban đầu
            await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ llm_provider: originalProvider })
            });
        }
    }

    async testCurrentLLM(isSubTest = false) {
        if (!isSubTest) {
            this.showToast('Testing current LLM provider...', 'info');
        }

        try {
            const response = await fetch('/api/llm/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: 'Đây là tin nhắn kiểm tra kết nối.' })
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                const analysis = result.test_result;
                const message = `Success! Provider: ${result.provider}. Classification: ${analysis.classification} (Confidence: ${analysis.confidence})`;
                this.showToast(message, 'success');
            } else {
                throw new Error(result.error || 'Test failed.');
            }
        } catch (error) {
            this.showToast(`LLM Test Failed: ${error.message}`, 'error');
        }
    }

    // PHẦN 5: CÁC HÀM TIỆN ÍCH
    // ===================================
    
    loadInitialData() {
        this.loadTabData('inbox');
        this.loadStats();
        this.loadSettings();
    }
    
    refreshAllData() {
        this.loadTabData(this.currentTab);
        this.loadStats();
        this.showToast('Data refreshed', 'success');
    }
    
    exportLogs() {
        fetch('/api/admin/messages')
            .then(res => res.json())
            .then(data => {
                const headers = ['id', 'content', 'sender', 'status', 'classification', 'created_at', 'filter_history'];
                const rows = data.map(item => headers.map(header => `"${(item[header] || '').toString().replace(/"/g, '""')}"`).join(','));
                const csv = [headers.join(','), ...rows].join('\n');
                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'spam_filter_logs.csv';
                link.click();
                this.showToast('Logs exported', 'success');
            })
            .catch(() => this.showToast('Export failed', 'error'));
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        const icon = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' }[type];
        toast.innerHTML = `<span>${icon}</span> ${this.escapeHtml(message)}`;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = 0;
            setTimeout(() => container.removeChild(toast), 300);
        }, 3000);
    }
    
    escapeHtml(text) {
        return text.toString().replace(/[&<>"']/g, m => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'})[m]);
    }
}

// Khởi tạo ứng dụng
const app = new SpamFilterApp();