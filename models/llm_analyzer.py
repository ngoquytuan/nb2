import requests
import json
import time
from datetime import datetime 
from typing import Dict 
from .llm_health import LLMHealthMonitor, LLMProviderStatus


class LLMAnalyzer:
    def __init__(self, dynamic_config):
        self.config = dynamic_config
        # FIX 1: Xóa self.provider khỏi __init__. 
        # Chúng ta sẽ lấy provider mới nhất mỗi lần gọi hàm.
        self.health_monitor = LLMHealthMonitor()
        self.error_log = []
    
    def analyze_message(self, message: str) -> dict:
        """Phân tích message với error tracking chi tiết"""
        start_time = time.time()
        
        # FIX 1: Lấy provider mới nhất trực tiếp từ config
        current_provider = self.config.LLM_PROVIDER.lower()
        
        health_status = self._check_provider_health()
        
        # FIX 2: Đảm bảo health_status có thể chuyển đổi thành JSON
        serializable_health_status = health_status.copy()
        if 'status' in serializable_health_status and isinstance(serializable_health_status['status'], LLMProviderStatus):
            serializable_health_status['status'] = serializable_health_status['status'].value

        result = {
            'provider': current_provider,
            'health_status': serializable_health_status,
            'processing_time_ms': 0,
            'error_details': None
        }
        
        try:
            if health_status['status'] != LLMProviderStatus.HEALTHY:
                analysis = self._enhanced_mock_analysis(message)
                fallback_reason = f"Provider {current_provider} is {health_status['status'].value}"
                result.update({ 'fallback_reason': fallback_reason, **analysis })
            else:
                if current_provider == 'openai':
                    analysis = self._analyze_with_openai(message)
                elif current_provider == 'groq':
                    analysis = self._analyze_with_groq(message)
                elif current_provider == 'openrouter':
                    analysis = self._analyze_with_openrouter(message)
                else:
                    analysis = self._enhanced_mock_analysis(message)
                result.update(analysis)
                
        except requests.exceptions.RequestException as e:
            self._log_error(type(e).__name__, str(e))
            result.update({
                'error_details': {'type': type(e).__name__, 'message': str(e), 'provider': current_provider},
                **self._enhanced_mock_analysis(message, fallback=True)
            })
        except Exception as e:
            self._log_error('unknown', str(e))
            result.update({
                'error_details': {'type': 'unknown', 'message': str(e), 'provider': current_provider},
                **self._enhanced_mock_analysis(message, fallback=True)
            })
        
        result['processing_time_ms'] = (time.time() - start_time) * 1000
        return result
    
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
        
    def _check_provider_health(self) -> Dict:
        """Kiểm tra health của provider hiện tại"""
        # FIX 1: Lấy provider mới nhất
        current_provider = self.config.LLM_PROVIDER.lower()
        
        cached = self.health_monitor.get_cached_status(current_provider)
        if cached:
            return cached
            
        api_key = self._get_api_key()
        if not api_key or api_key.startswith('your-'):
            return {'status': LLMProviderStatus.DOWN, 'error': 'No valid API key configured'}
            
        return self.health_monitor.check_provider_health(current_provider, api_key)
    
    def _get_api_key(self) -> str:
        """Lấy API key theo provider"""
        # FIX 1: Lấy provider mới nhất
        current_provider = self.config.LLM_PROVIDER.lower()

        if current_provider == 'openai':
            return self.config.OPENAI_API_KEY
        elif current_provider == 'groq':
            return self.config.GROQ_API_KEY
        elif current_provider == 'openrouter':
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
    
    def _create_prompt(self, message: str) -> str:
        """Tạo prompt cho LLM"""
        return f"""
Analyze the following Vietnamese message for spam/scam detection:

Message: "{message}"

Please analyze and respond in JSON format:
{{
    "is_spam": true/false,
    "confidence": 0.0-1.0,
    "reason": "explanation in Vietnamese",
    "classification": "legitimate/suspicious/spam"
}}

Consider these factors:
- Urgent money requests
- Suspicious links or downloads
- Too-good-to-be-true offers
- Requests for personal information
- Grammar and spelling patterns
- Social engineering tactics

Response (JSON only):
"""
    
    def _analyze_with_openai(self, message: str) -> dict:
        """Phân tích bằng OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": self._create_prompt(message)}
            ],
            "max_tokens": 200,
            "temperature": 0.3
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        return self._parse_llm_response(content)
    
    def _analyze_with_groq(self, message: str) -> dict:
        """Phân tích bằng Groq API"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "openai/gpt-oss-120b",
            "messages": [
                {"role": "user", "content": self._create_prompt(message)}
            ],
            "max_tokens": 200,
            "temperature": 0.3
        }
        
        print(f"🔄 Calling Groq API with model: {payload['model']}")
    
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"📡 Groq Response Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Groq Error Response: {response.text}")
                
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Groq Raw Response: {content[:200]}...")
            
            return self._parse_llm_response(content)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Groq Request Error: {e}")
            raise
        except Exception as e:
            print(f"❌ Groq Processing Error: {e}")
            raise
    
    def _analyze_with_openrouter(self, message: str) -> dict:
        """Phân tích bằng OpenRouter API"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "Spam Filter Demo"
        }
        
        payload = {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [
                {"role": "user", "content": self._create_prompt(message)}
            ],
            "max_tokens": 200,
            "temperature": 0.3
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        return self._parse_llm_response(content)
    
    def _parse_llm_response(self, content: str) -> dict:
        """Parse JSON response từ LLM"""
        try:
            # Tìm JSON trong response
            start = content.find('{')
            end = content.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = content[start:end]
                result = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['is_spam', 'confidence', 'reason', 'classification']
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Missing field: {field}")
                
                return result
            else:
                raise ValueError("No JSON found in response")
        
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw content: {content}")
            
            # Fallback response
            return {
                'is_spam': True,
                'confidence': 0.5,
                'reason': 'Không thể phân tích response từ LLM',
                'classification': 'suspicious'
            }