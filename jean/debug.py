"""
Debug logging compatibility module.
"""

import logging
import sys
from assistance.utils.logger import logger

def debug_log(message: str, context: str = ""):
    """Debug log function for compatibility"""
    if context:
        logger.debug(message, module=context)
    else:
        logger.debug(message)

__all__ = ['debug_log']
