"""
Response Caching System
Caches function results to avoid redundant computations and API calls
"""

import hashlib
import json
import time
from typing import Any, Optional, Callable
from functools import wraps


class ResponseCache:
    """Generic response cache with TTL support"""
    
    def __init__(self, ttl: int = 300, max_size: int = 1000):
        """
        Initialize response cache
        
        Args:
            ttl: Time to live in seconds (default: 5 minutes)
            max_size: Maximum number of cached entries
        """
        self.cache = {}
        self.ttl = ttl
        self.max_size = max_size
        self._access_times = {}
    
    def _generate_key(self, func_name: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_data = {
            'func': func_name,
            'args': str(args),
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self._access_times[key] = time.time()
                return value
            else:
                del self.cache[key]
                if key in self._access_times:
                    del self._access_times[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set cached value"""
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self._access_times, key=self._access_times.get)
            del self.cache[oldest_key]
            del self._access_times[oldest_key]
        
        self.cache[key] = (value, time.time())
        self._access_times[key] = time.time()
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self._access_times.clear()
    
    def clear_expired(self):
        """Clear expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
            if key in self._access_times:
                del self._access_times[key]
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'ttl': self.ttl
        }


def cached(cache: ResponseCache):
    """Decorator for caching function results"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = cache._generate_key(func.__name__, *args, **kwargs)
            
            # Try cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(key, result)
            
            return result
        return wrapper
    return decorator


# Global cache instances
weather_cache = ResponseCache(ttl=600, max_size=100)  # 10 minutes for weather
system_cache = ResponseCache(ttl=300, max_size=500)  # 5 minutes for system info
general_cache = ResponseCache(ttl=1800, max_size=1000)  # 30 minutes for general
