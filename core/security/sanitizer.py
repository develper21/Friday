"""
Input Sanitization Module
Provides utilities for sanitizing user input
"""

import re
import html
import logging
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Security-related error"""
    pass


class InputSanitizer:
    """Sanitizes various types of user input"""
    
    @staticmethod
    def sanitize_string(input_str: Optional[str], max_length: int = 1000) -> str:
        """
        Sanitize string input
        
        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not input_str:
            return ""
        
        # Truncate
        input_str = input_str[:max_length]
        
        # Remove null bytes
        input_str = input_str.replace('\x00', '')
        
        # Escape HTML entities
        input_str = html.escape(input_str)
        
        # Remove dangerous control characters
        input_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)
        
        return input_str.strip()
    
    @staticmethod
    def sanitize_filename(filename: Optional[str]) -> str:
        """
        Sanitize filename
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return ""
        
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', '', filename)
        
        # Limit length
        filename = filename[:255]
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        return filename if filename else "unnamed"
    
    @staticmethod
    def sanitize_url(url: Optional[str]) -> str:
        """
        Sanitize and validate URL
        
        Args:
            url: URL to sanitize
            
        Returns:
            Sanitized URL
            
        Raises:
            SecurityError: If URL is invalid or dangerous
        """
        if not url:
            raise SecurityError("Empty URL")
        
        try:
            parsed = urlparse(url)
            
            # Only allow http/https
            if parsed.scheme not in ['http', 'https']:
                raise SecurityError("Invalid URL scheme")
            
            # Block localhost/internal IPs
            if parsed.hostname in ['localhost', '127.0.0.1', '::1', '0.0.0.0']:
                raise SecurityError("Internal URLs not allowed")
            
            # Block private IP ranges
            if parsed.hostname:
                hostname = parsed.hostname
                if hostname.startswith(('192.168.', '10.', '172.16.')):
                    raise SecurityError("Private IP addresses not allowed")
                if hostname.startswith('127.') or hostname == '::1':
                    raise SecurityError("Loopback addresses not allowed")
            
            return url
            
        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Invalid URL: {e}")
    
    @staticmethod
    def sanitize_path(path: Optional[str]) -> str:
        """
        Sanitize file path
        
        Args:
            path: Path to sanitize
            
        Returns:
            Sanitized path
        """
        if not path:
            return ""
        
        # Remove null bytes
        path = path.replace('\x00', '')
        
        # Limit length
        path = path[:4096]
        
        return path.strip()
    
    @staticmethod
    def sanitize_command_arg(arg: Optional[str]) -> str:
        """
        Sanitize command argument
        
        Args:
            arg: Command argument to sanitize
            
        Returns:
            Sanitized argument
        """
        if not arg:
            return ""
        
        # Remove shell metacharacters
        dangerous_chars = ['$', '`', ';', '&', '|', '>', '<', '(', ')']
        for char in dangerous_chars:
            arg = arg.replace(char, '')
        
        # Limit length
        arg = arg[:1000]
        
        return arg.strip()
    
    @staticmethod
    def validate_email(email: Optional[str]) -> bool:
        """
        Validate email format
        
        Args:
            email: Email to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: Optional[str]) -> bool:
        """
        Validate phone number format
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not phone:
            return False
        
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        
        # Check if it's all digits and reasonable length
        return cleaned.isdigit() and 10 <= len(cleaned) <= 15
