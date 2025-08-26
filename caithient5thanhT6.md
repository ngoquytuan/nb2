Phân tích rất tốt! Tôi sẽ đưa ra lộ trình cải thiện các vấn đề này:

## 🎯 Lộ trình cải thiện

### Phase 1: Cải thiện LLM Connection & Error Handling
### Phase 2: Dynamic Configuration UI  
### Phase 3: Enhanced Mock System với Scoring

---

## 📍 Phase 1: LLM Connection Transparency

### 1.1 Tạo LLM Health Monitor (models/llm_health.py)

```python
import time
import requests
from enum import Enum
from typing import Dict, Optional
from datetime import datetime, timedelta

class LLMProviderStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"

class LLMHealthMonitor:
    def __init__(self):
        self.last_checks = {}
        self.status_cache = {}
        self.error_counts = {}
        self.response_times = {}
        
    def check_provider_health(self, provider: str, api_key: str) -> Dict:
        """Kiểm tra health của LLM provider"""
        start_time = time.time()
        
        try:
            if provider == 'openai':
                result = self._check_openai_health(api_key)
            elif provider == 'groq':
                result = self._check_groq_health(api_key)
            elif provider == 'openrouter':
                result = self._check_openrouter_health(api_key)
            else:
                result = {
                    'status': LLMProviderStatus.UNKNOWN,
                    'error': f'Unknown provider: {provider}',
                    'details': {}
                }
                
        except Exception as e:
            result = {
                'status': LLMProviderStatus.DOWN,
                'error': str(e),
                'details': {'exception_type': type(e).__name__}
            }
        
        # Tính response time
        response_time = (time.time() - start_time) * 1000
        result['response_time_ms'] = response_time
        result['checked_at'] = datetime.now().isoformat()
        
        # Update cache
        self.status_cache[provider] = result
        self.last_checks[provider] = datetime.now()
        
        return result
    
    def _check_openai_health(self, api_key: str) -> Dict:
        """Health check cho OpenAI"""
        url = "https://api.openai.com/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            models = response.json().get('data', [])
            available_models = [m['id'] for m in models if 'gpt' in m['id']]
            
            return {
                'status': LLMProviderStatus.HEALTHY,
                'details': {
                    'available_models': available_models[:5],  # Chỉ lấy 5 model đầu
                    'total_models': len(available_models)
                }
            }
        elif response.status_code == 401:
            return {
                'status': LLMProviderStatus.DOWN,
                'error': 'Invalid API key',
                'details': {'status_code': 401}
            }
        else:
            return {
                'status': LLMProviderStatus.DEGRADED,
                'error': f'HTTP {response.status_code}: {response.text[:100]}',
                'details': {'status_code': response.status_code}
            }
    
    def _check_groq_health(self, api_key: str) -> Dict:
        """Health check cho Groq"""
        url = "https://api.groq.com/openai/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            models = response.json().get('data', [])
            return {
                'status': LLMProviderStatus.HEALTHY,
                'details': {
                    'available_models': [m['id'] for m in models][:3],
                    'total_models': len(models)
                }
            }
        elif response.status_code == 401:
            return {
                'status': LLMProviderStatus.DOWN,
                'error': 'Invalid API key',
                'details': {'status_code': 401}
            }
        else:
            return {
                'status': LLMProviderStatus.DEGRADED,
                'error': f'HTTP {response.status_code}',
                'details': {'status_code': response.status_code}
            }
    
    def _check_openrouter_health(self, api_key: str) -> Dict:
        """Health check cho OpenRouter"""
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {
                'status': LLMProviderStatus.HEALTHY,
                'details': {'models_endpoint': 'accessible'}
            }
        else:
            return {
                'status': LLMProviderStatus.DEGRADED,
                'error': f'HTTP {response.status_code}',
                'details': {'status_code': response.status_code}
            }
    
    def get_cached_status(self, provider: str) -> Optional[Dict]:
        """Lấy status đã cache (trong vòng 5 phút)"""
        if provider not in self.last_checks:
            return None
            
        if datetime.now() - self.last_checks[provider] < timedelta(minutes=5):
            return self.status_cache.get(provider)
            
        return None
```

### 1.2 Cập nhật LLM Analyzer với Error Tracking (models/llm_analyzer.py)

```python
# Thêm vào đầu file
from .llm_health import LLMHealthMonitor, LLMProviderStatus

class LLMAnalyzer:
    def __init__(self):
        self.config = Config()
        self.provider = self.config.LLM_PROVIDER.lower()
        self.health_monitor = LLMHealthMonitor()
        self.error_log = []
    
    def analyze_message(self, message: str) -> dict:
        """Phân tích message với error tracking chi tiết"""
        start_time = time.time()
        
        # Check provider health trước khi gọi
        health_status = self._check_provider_health()
        
        result = {
            'provider': self.provider,
            'health_status': health_status,
            'processing_time_ms': 0,
            'error_details': None
        }
        
        try:
            if health_status['status'] != LLMProviderStatus.HEALTHY:
                # Fallback to mock nếu provider không healthy
                analysis = self._enhanced_mock_analysis(message)
                result.update({
                    'fallback_reason': f"Provider {self.provider} is {health_status['status'].value}",
                    **analysis
                })
            else:
                # Thử gọi LLM thực
                if self.provider == 'openai':
                    analysis = self._analyze_with_openai(message)
                elif self.provider == 'groq':
                    analysis = self._analyze_with_groq(message)
                elif self.provider == 'openrouter':
                    analysis = self._analyze_with_openrouter(message)
                else:
                    analysis = self._enhanced_mock_analysis(message)
                
                result.update(analysis)
                
        except requests.exceptions.Timeout as e:
            self._log_error('timeout', str(e))
            result.update({
                'error_details': {
                    'type': 'timeout',
                    'message': 'LLM request timed out',
                    'provider': self.provider
                },
                **self._enhanced_mock_analysis(message, fallback=True)
            })
            
        except requests.exceptions.ConnectionError as e:
            self._log_error('connection', str(e))
            result.update({
                'error_details': {
                    'type': 'connection',
                    'message': 'Cannot connect to LLM provider',
                    'provider': self.provider
                },
                **self._enhanced_mock_analysis(message, fallback=True)
            })
            
        except requests.exceptions.HTTPError as e:
            self._log_error('http', str(e))
            result.update({
                'error_details': {
                    'type': 'http',
                    'message': f'HTTP error: {e.response.status_code}',
                    'provider': self.provider,
                    'status_code': e.response.status_code
                },
                **self._enhanced_mock_analysis(message, fallback=True)
            })
            
        except Exception as e:
            self._log_error('unknown', str(e))
            result.update({
                'error_details': {
                    'type': 'unknown',
                    'message': str(e),
                    'provider': self.provider
                },
                **self._enhanced_mock_analysis(message, fallback=True)
            })
        
        result['processing_time_ms'] = (time.time() - start_time) * 1000
        return result
    
    def _check_provider_health(self) -> Dict:
        """Kiểm tra health của provider hiện tại"""
        # Lấy từ cache nếu có
        cached = self.health_monitor.get_cached_status(self.provider)
        if cached:
            return cached
            
        # Kiểm tra mới
        api_key = self._get_api_key()
        if not api_key or api_key.startswith('your-'):
            return {
                'status': LLMProviderStatus.DOWN,
                'error': 'No valid API key configured'
            }
            
        return self.health_monitor.check_provider_health(self.provider, api_key)
    
    def _get_api_key(self) -> str:
        """Lấy API key theo provider"""
        if self.provider == 'openai':
            return self.config.OPENAI_API_KEY
        elif self.provider == 'groq':
            return self.config.GROQ_API_KEY
        elif self.provider == 'openrouter':
            return self.config.OPENROUTER_API_KEY
        return ""
    
    def _log_error(self, error_type: str, message: str):
        """Log lỗi để tracking"""
        self.error_log.append({
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': message,
            'provider': self.provider
        })
        
        # Chỉ giữ 50 errors gần nhất
        if len(self.error_log) > 50:
            self.error_log = self.error_log[-50:]
    
    def get_error_summary(self) -> Dict:
        """Tổng hợp lỗi trong 24h qua"""
        now = datetime.now()
        recent_errors = [
            err for err in self.error_log 
            if (now - datetime.fromisoformat(err['timestamp'])).total_seconds() < 86400
        ]
        
        error_counts = {}
        for err in recent_errors:
            error_counts[err['type']] = error_counts.get(err['type'], 0) + 1
        
        return {
            'total_errors_24h': len(recent_errors),
            'error_breakdown': error_counts,
            'recent_errors': recent_errors[-5:]  # 5 lỗi gần nhất
        }
```

### 1.3 Enhanced Mock Analysis

```python
# Thêm vào LLM Analyzer
def _enhanced_mock_analysis(self, message: str, fallback: bool = False) -> dict:
    """Mock analysis với scoring chi tiết"""
    message_lower = message.lower()
    
    # Phân tích từ khóa với trọng số
    spam_keywords = {
        'trúng giải': 0.9,
        'vay tiền': 0.8, 
        'khuyến mãi': 0.7,
        'miễn phí': 0.6,
        'click link': 0.9,
        'chuyển khoản': 0.8,
        'mã otp': 0.9,
        'xác thực': 0.7,
        'làm giàu': 0.8,
        'đầu tư': 0.6,
        'lợi nhuận': 0.7,
        'cảnh báo': 0.8,
        'tài khoản bị khóa': 0.9,
        'nhấp vào đây': 0.8
    }
    
    legitimate_keywords = {
        'xin chào': 0.3,
        'cảm ơn': 0.2,
        'meeting': 0.2,
        'dự án': 0.2,
        'báo cáo': 0.2,
        'công ty': 0.3,
        'hỗ trợ': 0.3,
        'thông tin': 0.4
    }
    
    # Tính điểm spam
    spam_score = 0.0
    matched_spam_keywords = []
    for keyword, weight in spam_keywords.items():
        if keyword in message_lower:
            spam_score += weight
            matched_spam_keywords.append(keyword)
    
    # Tính điểm legitimate  
    legit_score = 0.0
    matched_legit_keywords = []
    for keyword, weight in legitimate_keywords.items():
        if keyword in message_lower:
            legit_score += weight
            matched_legit_keywords.append(keyword)
    
    # Normalize scores
    spam_score = min(spam_score, 1.0)
    legit_score = min(legit_score, 1.0)
    
    # Final decision
    if spam_score >= 0.8:
        classification = 'spam'
        is_spam = True
        confidence = 0.85 + (spam_score - 0.8) * 0.15
    elif spam_score >= 0.5:
        classification = 'suspicious' 
        is_spam = False
        confidence = 0.6 + (spam_score - 0.5) * 0.3
    elif legit_score >= 0.4:
        classification = 'legitimate'
        is_spam = False
        confidence = 0.7 + legit_score * 0.3
    else:
        classification = 'suspicious'
        is_spam = False
        confidence = 0.5
    
    # Tạo reason chi tiết
    reason_parts = []
    if matched_spam_keywords:
        reason_parts.append(f"Phát hiện từ khóa spam: {', '.join(matched_spam_keywords)}")
    if matched_legit_keywords:
        reason_parts.append(f"Phát hiện từ khóa hợp lệ: {', '.join(matched_legit_keywords)}")
    
    reason = f"Mock Analysis: {'. '.join(reason_parts) if reason_parts else 'Không phát hiện từ khóa đặc biệt'}"
    
    if fallback:
        reason = f"LLM Fallback - {reason}"
    
    return {
        'is_spam': is_spam,
        'confidence': round(confidence, 3),
        'reason': reason,
        'classification': classification,
        'analysis_method': 'enhanced_mock',
        'scoring_details': {
            'spam_score': round(spam_score, 3),
            'legitimate_score': round(legit_score, 3),
            'matched_spam_keywords': matched_spam_keywords,
            'matched_legit_keywords': matched_legit_keywords
        }
    }
```

---

## 📍 Phase 2: Dynamic Configuration UI

### 2.1 Database Schema cho Settings (database/db_manager.py)

```python
# Thêm vào init_database()
def init_database(self):
    """Khởi tạo database và các bảng"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # ... existing tables ...
    
    # Bảng system settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            data_type TEXT DEFAULT 'string',
            description TEXT,
            category TEXT DEFAULT 'general',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default settings nếu chưa có
    default_settings = [
        ('llm_provider', 'openai', 'string', 'LLM Provider (openai/groq/openrouter)', 'llm'),
        ('openai_api_key', '', 'password', 'OpenAI API Key', 'llm'),
        ('groq_api_key', '', 'password', 'Groq API Key', 'llm'), 
        ('openrouter_api_key', '', 'password', 'OpenRouter API Key', 'llm'),
        ('naive_bayes_threshold', '0.7', 'float', 'Ngưỡng confidence cho Naive Bayes', 'filter'),
        ('suspicious_threshold', '0.5', 'float', 'Ngưỡng đánh dấu suspicious', 'filter'),
        ('enable_mock_fallback', 'true', 'boolean', 'Bật mock analysis khi LLM lỗi', 'system'),
        ('max_processing_time', '30', 'int', 'Timeout tối đa (giây)', 'system'),
        ('enable_health_check', 'true', 'boolean', 'Bật kiểm tra health LLM', 'system')
    ]
    
    for key, value, data_type, desc, category in default_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO system_settings 
            (key, value, data_type, description, category) 
            VALUES (?, ?, ?, ?, ?)
        ''', (key, value, data_type, desc, category))
    
    conn.commit()
    conn.close()

# Thêm methods cho settings
def get_setting(self, key: str, default=None):
    """Lấy giá trị setting"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT value, data_type FROM system_settings WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return default
        
    value, data_type = result
    
    # Convert theo data type
    if data_type == 'int':
        return int(value)
    elif data_type == 'float':
        return float(value)
    elif data_type == 'boolean':
        return value.lower() in ('true', '1', 'yes')
    else:
        return value

def update_setting(self, key: str, value: str):
    """Cập nhật setting"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE system_settings 
        SET value = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE key = ?
    ''', (str(value), key))
    
    conn.commit()
    conn.close()

def get_all_settings(self) -> Dict:
    """Lấy tất cả settings theo category"""
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM system_settings ORDER BY category, key")
    rows = cursor.fetchall()
    conn.close()
    
    settings = {}
    for row in rows:
        category = row['category']
        if category not in settings:
            settings[category] = []
            
        settings[category].append({
            'key': row['key'],
            'value': row['value'],
            'data_type': row['data_type'],
            'description': row['description'],
            'updated_at': row['updated_at']
        })
    
    return settings
```

### 2.2 Dynamic Config Class (config.py)

```python
class DynamicConfig:
    def __init__(self, db_manager):
        self.db = db_manager
        self._cache = {}
        self._cache_time = {}
        self.CACHE_DURATION = 300  # 5 phút
    
    def get(self, key: str, default=None):
        """Lấy config với caching"""
        now = time.time()
        
        # Check cache
        if (key in self._cache and 
            key in self._cache_time and 
            now - self._cache_time[key] < self.CACHE_DURATION):
            return self._cache[key]
        
        # Get from DB
        value = self.db.get_setting(key, default)
        
        # Cache result
        self._cache[key] = value
        self._cache_time[key] = now
        
        return value
    
    def update(self, key: str, value):
        """Update config và clear cache"""
        self.db.update_setting(key, value)
        
        # Clear cache for this key
        if key in self._cache:
            del self._cache[key]
        if key in self._cache_time:
            del self._cache_time[key]
    
    def clear_cache(self):
        """Clear toàn bộ cache"""
        self._cache = {}
        self._cache_time = {}
    
    # Properties để tương thích với code cũ
    @property
    def LLM_PROVIDER(self):
        return self.get('llm_provider', 'openai')
    
    @property
    def OPENAI_API_KEY(self):
        return self.get('openai_api_key', '')
    
    @property
    def GROQ_API_KEY(self):
        return self.get('groq_api_key', '')
        
    @property
    def OPENROUTER_API_KEY(self):
        return self.get('openrouter_api_key', '')
    
    @property
    def NAIVE_BAYES_THRESHOLD(self):
        return self.get('naive_bayes_threshold', 0.7)
    
    @property 
    def SUSPICIOUS_THRESHOLD(self):
        return self.get('suspicious_threshold', 0.5)
```

### 2.3 Settings API Routes (app.py)

```python
# Thêm vào app.py
@app.route('/api/settings')
def get_settings():
    """Lấy tất cả settings"""
    settings = db.get_all_settings()
    
    # Mask passwords
    for category in settings:
        for setting in settings[category]:
            if setting['data_type'] == 'password' and setting['value']:
                setting['value'] = '***masked***'
    
    return jsonify(settings)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Cập nhật settings"""
    data = request.json
    updated_keys = []
    
    for key, value in data.items():
        # Validate key exists
        current = db.get_setting(key)
        if current is not None:
            db.update_setting(key, value)
            updated_keys.append(key)
            
            # Clear config cache
            if hasattr(app, 'dynamic_config'):
                app.dynamic_config.clear_cache()
    
    return jsonify({
        'success': True,
        'updated_keys': updated_keys,
        'message': f'Updated {len(updated_keys)} settings'
    })

@app.route('/api/llm/health')
def check_llm_health():
    """Kiểm tra health của LLM providers"""
    provider = app.dynamic_config.LLM_PROVIDER
    
    health_result = llm_analyzer.health_monitor.check_provider_health(
        provider, 
        app.dynamic_config.get(f'{provider}_api_key', '')
    )
    
    # Thêm error summary
    error_summary = llm_analyzer.get_error_summary()
    
    return jsonify({
        'current_provider': provider,
        'health': health_result,
        'error_summary': error_summary
    })

@app.route('/api/llm/test', methods=['POST'])
def test_llm_connection():
    """Test LLM connection với message mẫu"""
    data = request.json
    test_message = data.get('message', 'This is a test message.')
    
    result = llm_analyzer.analyze_message(test_message)
    
    return jsonify({
        'success': True,
        'test_result': result,
        'provider': app.dynamic_config.LLM_PROVIDER
    })
```

### 2.4 Settings UI (static/settings.html)

```html
<!-- Thêm tab Settings vào index.html -->
<button class="tab-button" onclick="showTab('settings')">
    ⚙️ Settings
</button>

<!-- Tab content -->
<div id="settings-tab" class="tab-content">
    <h3>⚙️ System Configuration</h3>
    
    <!-- LLM Settings -->
    <div class="settings-section">
        <h4>🤖 LLM Configuration</h4>
        <div class="settings-grid">
            <div class="setting-item">
                <label for="llm_provider">Provider:</label>
                <select id="llm_provider" name="llm_provider">
                    <option value="openai">OpenAI</option>
                    <option value="groq">Groq</option>
                    <option value="openrouter">OpenRouter</option>
                </select>
            </div>
            
            <div class="setting-item">
                <label for="openai_api_key">OpenAI API Key:</label>
                <input type="password" id="openai_api_key" name="openai_api_key" 
                       placeholder="sk-...">
                <button type="button" class="btn btn-small btn-info" 
                        onclick="testLLMConnection('openai')">Test</button>
            </div>
            
            <div class="setting-item">
                <label for="groq_api_key">Groq API Key:</label>
                <input type="password" id="groq_api_key" name="groq_api_key" 
                       placeholder="gsk_...">
                <button type="button" class="btn btn-small btn-info" 
                        onclick="testLLMConnection('groq')">Test</button>
            </div>
            
            <div class="setting-item">
                <label for="openrouter_api_key">OpenRouter API Key:</label>
                <input type="password" id="openrouter_api_key" name="openrouter_api_key" 
                       placeholder="sk-or-...">
                <button type="button" class="btn btn-small btn-info" 
                        onclick="testLLMConnection('openrouter')">Test</button>
            </div>
        </div>
        
        <!-- LLM Health Status -->
        <div class="health-status" id="llmHealthStatus">
            <h5>Provider Health Status</h5>
            <div id="healthStatusContent">
                <p class="loading">Checking...</p>
            </div>
        </div>
    </div>
    
    <!-- Filter Settings -->
    <div class="settings-section">
        <h4>🔍 Filter Configuration</h4>
        <div class="settings-grid">
            <div class="setting-item">
                <label for="naive_bayes_threshold">Naive Bayes Threshold:</label>
                <input type="range" id="naive_bayes_threshold" name="naive_bayes_threshold" 
                       min="0.1" max="1.0" step="0.1">
                <span class="range-value" id="nb_threshold_value">0.7</span>
            </div>
            
            <div class="setting-item">
                <label for="suspicious_threshold">Suspicious Threshold:</label>
                <input type="range" id="suspicious_threshold" name="suspicious_threshold" 
                       min="0.1" max="1.0" step="0.1">
                <span class="range-value" id="sus_threshold_value">0.5</span>
            </div>
        </div>
    </div>
    
    <!-- System Settings -->
    <div class="settings-section">
        <h4>🔧 System Settings</h4>
        <div class="settings-grid">
            <div class="setting-item">
                <label>
                    <input type="checkbox" id="enable_mock_fallback" name="enable_mock_fallback" checked>
                    Enable Mock Fallback
                </label>
                <small>Use enhanced mock analysis when LLM fails</small>
            </div>
            
            <div class="setting-item">
                <label>
                    <input type="checkbox" id="enable_health_check" name="enable_health_check" checked>
                    Enable Health Monitoring
                </label>
                <small>Automatically check LLM provider health</small>
            </div>
        </div>
    </div>
    
    <!-- Action Buttons -->
    <div class="settings-actions">
        <button class="btn btn-primary" onclick="saveSettings()">
            💾 Save Settings
        </button>
        <button class="btn btn-info" onclick="loadSettings()">
            🔄 Reload Settings
        </button>
        <button class="btn btn-warning" onclick="testCurrentLLM()">
            🧪 Test Current LLM
        </button>
    </div>
</div>
```

Phần tiếp theo sẽ bao gồm CSS styling cho settings UI và JavaScript functions. Bạn có muốn tôi tiếp tục với Phase 3 (Enhanced Mock System) hay hoàn thiện Phase 2 trước?

Chắc chắn rồi. Dựa trên các file mã nguồn bạn đã cung cấp, chúng ta có thể phân tích và tìm ra nhiều hướng để cải thiện thuật toán xử lý spam.

Trước hết, hãy làm rõ hai nhận định của bạn:

1.  **"Hiện nay là xử lý dựa trên keyword là chính đúng không?"** -> **Chưa hoàn toàn chính xác.** Hệ thống của bạn có 2 lớp xử lý chính:
    * **Naive Bayes (NB):** Lớp này **không** chỉ dựa vào từ khóa. Nó sử dụng mô hình thống kê **TF-IDF** để tính toán "trọng số" của các từ và cụm từ (n-gram) dựa trên tần suất xuất hiện của chúng trong dữ liệu spam và không spam. Đây là phương pháp phức tạp hơn việc chỉ tìm kiếm từ khóa.
    * **LLM Analyzer:** Khi gọi đến các API thật (OpenAI, Groq), LLM sẽ phân tích **ngữ cảnh, ý định, và cấu trúc câu** chứ không chỉ từ khóa. Lớp xử lý dựa trên từ khóa (`_enhanced_mock_analysis`) thực chất chỉ là một cơ chế **dự phòng (fallback)** hoặc **demo** khi không có API key hoặc API bị lỗi.

2.  **"NB đã phát huy hết khả năng của nó chưa?"** -> **Chưa, còn rất nhiều không gian để cải thiện.** Model NB hiện tại đang dùng một bộ dữ liệu mẫu khá nhỏ và các kỹ thuật xử lý cơ bản.

---

### ## Các hướng cải thiện thuật toán

Dưới đây là những vị trí bạn có thể tập trung cải thiện, chia theo từng thành phần của hệ thống.

### 1. Cải thiện Model Naive Bayes (Lớp phòng thủ đầu tiên) 🛡️

Đây là lớp quan trọng vì nó giúp giảm tải cho LLM. Một model NB tốt sẽ xử lý được phần lớn các tin nhắn rõ ràng, chỉ để lại các ca khó cho LLM.

* **Dữ liệu, Dữ liệu và Dữ liệu:** Đây là yếu tố **quan trọng nhất**.
    * **Tăng kích thước Dataset:** Bộ dữ liệu `training_data.json` hiện tại còn khá nhỏ. Bạn cần thu thập thêm nhiều mẫu tin nhắn spam, lừa đảo, và hợp lệ trong thực tế để model "học" được nhiều trường hợp hơn. Dữ liệu càng đa dạng, model càng thông minh.
    * **Cân bằng Dữ liệu:** Đảm bảo số lượng tin nhắn trong các lớp `legitimate`, `spam`, `suspicious` không quá chênh lệch nhau để tránh model bị "thiên vị".

* **Tiền xử lý văn bản chuyên sâu (Advanced Text Preprocessing):**
    * **Word Segmentation (Tách từ tiếng Việt):** Các thư viện như `vncorenlp` hoặc `underthesea` có thể giúp tách từ tiếng Việt chính xác hơn, ví dụ "khuyếnmãi" -> "khuyến mãi". Điều này giúp `TfidfVectorizer` nhận diện từ đúng hơn.
    * **Loại bỏ Stopwords tiếng Việt:** Xây dựng một danh sách các từ dừng (stopword) phổ biến trong tiếng Việt (ví dụ: là, và, của, có,...) và loại bỏ chúng. Điều này giúp model tập trung vào những từ mang nhiều ý nghĩa hơn.
    * **Lemmatization/Stemming (Đưa từ về dạng gốc):** Chuyển các từ biến thể về cùng một dạng gốc (ví dụ: "vay", "vay mượn" -> "vay").

* **Feature Engineering (Tạo thêm đặc trưng):**
    * Thay vì chỉ dựa vào nội dung văn bản, bạn có thể bổ sung các "siêu dữ liệu" (metadata) làm đặc trưng mới cho model, ví dụ:
        * Số lượng ký tự viết hoa.
        * Số lượng ký tự đặc biệt (!, @, #, $).
        * Sự hiện diện của đường link (URL).
        * Số lượng số trong tin nhắn.

* **Tinh chỉnh siêu tham số (Hyperparameter Tuning):**
    * Sử dụng các kỹ thuật như `GridSearchCV` của scikit-learn để tìm ra bộ tham số tốt nhất cho `TfidfVectorizer` (ví dụ: `max_features`, `ngram_range`) và `MultinomialNB` (ví dụ: `alpha`).

### 2. Cải thiện LLM Analyzer (Lớp phân tích sâu) 🧠

Lớp này xử lý các ca khó mà NB không chắc chắn.

* **Prompt Engineering (Kỹ thuật tạo câu lệnh):**
    * Đây là cách cải thiện hiệu quả và ít tốn kém nhất. Câu lệnh (`prompt`) bạn gửi cho LLM quyết định rất nhiều đến chất lượng câu trả lời.
    * **Thêm ví dụ (Few-shot learning):** Thay vì chỉ đưa ra chỉ dẫn, hãy cung cấp cho LLM một vài ví dụ cụ thể về tin nhắn spam/lừa đảo và tin nhắn hợp lệ ngay trong prompt.
    * **Yêu cầu LLM "suy nghĩ từng bước" (Chain-of-thought):** Thêm vào prompt yêu cầu như: *"Hãy phân tích tin nhắn từng bước. Đầu tiên, xác định ý định chính. Thứ hai, tìm các dấu hiệu lừa đảo. Cuối cùng, đưa ra kết luận."* Điều này giúp LLM có quá trình phân tích logic và chính xác hơn.

* **Sử dụng Model LLM tốt hơn:**
    * Các model bạn đang dùng là các lựa chọn miễn phí hoặc giá rẻ (`gpt-3.5-turbo`, `llama-3.3-70b-instruct:free`). Nếu ngân sách cho phép, việc nâng cấp lên các model mạnh hơn như **GPT-4o** hoặc các phiên bản Llama trả phí có thể cải thiện đáng kể độ chính xác.

* **Kết hợp Heuristics (Luật suy nghiệm):**
    * Thêm một vài luật đơn giản để xử lý các trường hợp cực kỳ rõ ràng **trước khi** gọi LLM để tiết kiệm chi phí. Ví dụ:
        * Nếu tin nhắn chứa một số điện thoại trong danh sách đen (blacklist).
        * Nếu tin nhắn chứa một đường link đã được xác định là độc hại.

---

### ## Tóm tắt và Lộ trình đề xuất

1.  **Ngắn hạn (Dễ thực hiện):**
    * Bắt đầu **thu thập thêm dữ liệu** huấn luyện cho Naive Bayes.
    * **Cải thiện prompt** cho LLM bằng cách thêm ví dụ (few-shot).
    * Thêm bước **tách từ tiếng Việt** vào quy trình tiền xử lý của Naive Bayes.

2.  **Trung hạn:**
    * **Bổ sung Feature Engineering** (đếm ký tự viết hoa, link,...).
    * Sử dụng **GridSearchCV** để tinh chỉnh tham số cho Naive Bayes.
    * Xây dựng một vài **luật Heuristics** đơn giản.

3.  **Dài hạn:**
    * Thử nghiệm với các **model LLM trả phí** mạnh hơn.
    * Xây dựng một hệ thống để người dùng có thể "báo cáo" (report) tin nhắn sai, từ đó liên tục cập nhật và huấn luyện lại (re-train) model Naive Bayes.
	
	