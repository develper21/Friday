"""
Debug logging compatibility module.
"""

import logging
import sys

def debug_log(message: str):
    """Debug log function for compatibility"""
    print(f"[DEBUG] {message}", flush=True)

__all__ = ['debug_log']
