"""
Beautiful Colored Logging System for JeanMax
Provides Kali Linux-style terminal output with colors, icons, and formatting
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Optional


class LogLevel(Enum):
    """Log levels with corresponding colors and icons"""
    DEBUG = {"color": "\033[0;36m", "icon": "🔍", "name": "DEBUG"}
    INFO = {"color": "\033[0;34m", "icon": "ℹ", "name": "INFO"}
    SUCCESS = {"color": "\033[0;32m", "icon": "✓", "name": "SUCCESS"}
    WARNING = {"color": "\033[1;33m", "icon": "⚠", "name": "WARNING"}
    ERROR = {"color": "\033[0;31m", "icon": "✗", "name": "ERROR"}
    CRITICAL = {"color": "\033[1;31m", "icon": "💀", "name": "CRITICAL"}
    SPEECH = {"color": "\033[0;35m", "icon": "🎙️", "name": "SPEECH"}
    LISTENING = {"color": "\033[0;36m", "icon": "🎤", "name": "LISTENING"}
    TRANSCRIBING = {"color": "\033[1;33m", "icon": "⚡", "name": "TRANSCRIBING"}
    COMMAND = {"color": "\033[0;32m", "icon": "🎯", "name": "COMMAND"}
    SYSTEM = {"color": "\033[0;34m", "icon": "⚙", "name": "SYSTEM"}
    NETWORK = {"color": "\033[0;36m", "icon": "🌐", "name": "NETWORK"}
    AI = {"color": "\033[1;35m", "icon": "🧠", "name": "AI"}


class ColorFormatter:
    """Handles color formatting for terminal output"""
    
    # ANSI color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[1;37m"
    
    # Background colors
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    
    @staticmethod
    def colorize(text: str, color: str) -> str:
        """Apply color to text"""
        return f"{color}{text}{ColorFormatter.RESET}"
    
    @staticmethod
    def bold(text: str) -> str:
        """Make text bold"""
        return f"{ColorFormatter.BOLD}{text}{ColorFormatter.RESET}"
    
    @staticmethod
    def success(text: str) -> str:
        """Format as success message"""
        return f"{ColorFormatter.GREEN}✓ {text}{ColorFormatter.RESET}"
    
    @staticmethod
    def error(text: str) -> str:
        """Format as error message"""
        return f"{ColorFormatter.RED}✗ {text}{ColorFormatter.RESET}"
    
    @staticmethod
    def warning(text: str) -> str:
        """Format as warning message"""
        return f"{ColorFormatter.YELLOW}⚠ {text}{ColorFormatter.RESET}"
    
    @staticmethod
    def info(text: str) -> str:
        """Format as info message"""
        return f"{ColorFormatter.CYAN}ℹ {text}{ColorFormatter.RESET}"


class JeanMaxLogger:
    """
    Beautiful colored logger with Kali Linux-style formatting
    """
    
    def __init__(self, name: str = "jeanmax", enable_file_logging: bool = True):
        self.name = name
        self.enable_file_logging = enable_file_logging
        self.log_file = None
        
        if enable_file_logging:
            self._setup_file_logging()
    
    def _setup_file_logging(self):
        """Setup file logging for debugging"""
        try:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / f"jeanmax_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            self.log_file = open(log_file, 'a', encoding='utf-8')
        except Exception as e:
            print(f"Failed to setup file logging: {e}")
    
    def _log_to_file(self, level: str, message: str):
        """Write log message to file"""
        if self.log_file:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_file.write(f"[{timestamp}] [{level}] {message}\n")
            self.log_file.flush()
    
    def _format_message(self, level: LogLevel, message: str, module: str = "") -> str:
        """Format message with color and icon"""
        color = level.value["color"]
        icon = level.value["icon"]
        
        if module:
            return f"{color}{icon} [{module}] {message}{ColorFormatter.RESET}"
        else:
            return f"{color}{icon} {message}{ColorFormatter.RESET}"
    
    def debug(self, message: str, module: str = ""):
        """Log debug message"""
        formatted = self._format_message(LogLevel.DEBUG, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("DEBUG", message)
    
    def info(self, message: str, module: str = ""):
        """Log info message"""
        formatted = self._format_message(LogLevel.INFO, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("INFO", message)
    
    def success(self, message: str, module: str = ""):
        """Log success message"""
        formatted = self._format_message(LogLevel.SUCCESS, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("SUCCESS", message)
    
    def warning(self, message: str, module: str = ""):
        """Log warning message"""
        formatted = self._format_message(LogLevel.WARNING, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("WARNING", message)
    
    def error(self, message: str, module: str = ""):
        """Log error message"""
        formatted = self._format_message(LogLevel.ERROR, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("ERROR", message)
    
    def critical(self, message: str, module: str = ""):
        """Log critical message"""
        formatted = self._format_message(LogLevel.CRITICAL, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("CRITICAL", message)
    
    def speech(self, message: str, module: str = ""):
        """Log speech-related message"""
        formatted = self._format_message(LogLevel.SPEECH, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("SPEECH", message)
    
    def listening(self, message: str, module: str = ""):
        """Log listening-related message"""
        formatted = self._format_message(LogLevel.LISTENING, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("LISTENING", message)
    
    def transcribing(self, message: str, module: str = ""):
        """Log transcribing-related message"""
        formatted = self._format_message(LogLevel.TRANSCRIBING, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("TRANSCRIBING", message)
    
    def command(self, message: str, module: str = ""):
        """Log command-related message"""
        formatted = self._format_message(LogLevel.COMMAND, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("COMMAND", message)
    
    def system(self, message: str, module: str = ""):
        """Log system-related message"""
        formatted = self._format_message(LogLevel.SYSTEM, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("SYSTEM", message)
    
    def network(self, message: str, module: str = ""):
        """Log network-related message"""
        formatted = self._format_message(LogLevel.NETWORK, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("NETWORK", message)
    
    def ai(self, message: str, module: str = ""):
        """Log AI-related message"""
        formatted = self._format_message(LogLevel.AI, message, module)
        print(formatted)
        if self.enable_file_logging:
            self._log_to_file("AI", message)
    
    def section(self, title: str):
        """Print a section header"""
        print("")
        print(f"{ColorFormatter.BOLD}{ColorFormatter.BLUE}▶ {title}{ColorFormatter.RESET}")
        print(f"{ColorFormatter.BLUE}{'─' * 70}{ColorFormatter.RESET}")
    
    def header(self, title: str, width: int = 70):
        """Print a fancy header"""
        border = "═" * width
        print(f"{ColorFormatter.CYAN}╔{border}╗{ColorFormatter.RESET}")
        print(f"{ColorFormatter.CYAN}║{ColorFormatter.BOLD}{ColorFormatter.WHITE}{title.center(width)}{ColorFormatter.RESET}{ColorFormatter.CYAN}║{ColorFormatter.RESET}")
        print(f"{ColorFormatter.CYAN}╚{border}╝{ColorFormatter.RESET}")
    
    def separator(self, char: str = "=", width: int = 70):
        """Print a separator line"""
        print(f"{ColorFormatter.CYAN}{char * width}{ColorFormatter.RESET}")
    
    def print_raw(self, message: str):
        """Print raw message without formatting"""
        print(message)
    
    def close(self):
        """Close log file"""
        if self.log_file:
            self.log_file.close()


# Global logger instance
logger = JeanMaxLogger()
