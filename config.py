import os
import time


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