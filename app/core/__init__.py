"""
Core application functionality.
"""

from .app import main
from .updater import check_for_updates

__all__ = ['main', 'check_for_updates']
