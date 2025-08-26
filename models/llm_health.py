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