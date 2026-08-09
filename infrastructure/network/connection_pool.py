"""
HTTP Connection Pool
Manages reusable HTTP connections for better performance
"""

import aiohttp
import asyncio
from typing import Optional


class ConnectionPool:
    """Singleton HTTP connection pool for efficient HTTP requests"""
    
    _instance: Optional['ConnectionPool'] = None
    _session: Optional[aiohttp.ClientSession] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_session(self) -> aiohttp.ClientSession:
        """
        Get or create HTTP session with connection pooling
        
        Returns:
            Configured aiohttp ClientSession
        """
        async with self._lock:
            if self._session is None or self._session.closed:
                timeout = aiohttp.ClientTimeout(total=30)
                connector = aiohttp.TCPConnector(
                    limit=100,  # Max total connections
                    limit_per_host=10,  # Max connections per host
                    enable_cleanup_closed=True,
                    force_close=False,
                    keepalive_timeout=30
                )
                
                self._session = aiohttp.ClientSession(
                    timeout=timeout,
                    connector=connector
                )
            
            return self._session
    
    async def close(self):
        """Close the HTTP session"""
        async with self._lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None
    
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Perform GET request using pooled connection
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for aiohttp.ClientSession.get
            
        Returns:
            aiohttp ClientResponse
        """
        session = await self.get_session()
        return await session.get(url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Perform POST request using pooled connection
        
        Args:
            url: URL to post to
            **kwargs: Additional arguments for aiohttp.ClientSession.post
            
        Returns:
            aiohttp ClientResponse
        """
        session = await self.get_session()
        return await session.post(url, **kwargs)
    
    def is_active(self) -> bool:
        """Check if session is active"""
        return self._session is not None and not self._session.closed


# Global connection pool instance
connection_pool = ConnectionPool()
