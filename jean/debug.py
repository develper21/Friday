"""
Debug logging compatibility module.
"""

import logging
import sys

def debug_log(message: str, context: str = ""):
    """Debug log function for compatibility"""
    if context:
        print(f"[DEBUG][{context}] {message}", flush=True)
    else:
        print(f"[DEBUG] {message}", flush=True)

__all__ = ['debug_log']
