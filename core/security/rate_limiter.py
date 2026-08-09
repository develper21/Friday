"""
Rate Limiting Module
Provides rate limiting to prevent API abuse
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Security-related error"""
    pass


class RateLimiter:
    """Rate limiter using sliding window algorithm"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Check if request is allowed
        
        Args:
            identifier: Unique identifier (e.g., IP address, user_id)
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get number of remaining requests for identifier"""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        return max(0, self.max_requests - len(self.requests[identifier]))
    
    def reset(self, identifier: str):
        """Reset rate limit for identifier"""
        if identifier in self.requests:
            del self.requests[identifier]
    
    def cleanup_old_entries(self, max_age_hours: int = 24):
        """Clean up old entries to prevent memory leaks"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        to_delete = []
        for identifier, timestamps in self.requests.items():
            # Check if all timestamps are older than cutoff
            if all(ts < cutoff for ts in timestamps):
                to_delete.append(identifier)
        
        for identifier in to_delete:
            del self.requests[identifier]
        
        logger.debug(f"Cleaned up {len(to_delete)} old rate limit entries")
