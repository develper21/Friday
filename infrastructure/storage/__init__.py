"""
Storage Module
Contains repository implementations for data access
"""

from .json_repository import JSONRepository
from .applications_repository import ApplicationsRepository

__all__ = ['JSONRepository', 'ApplicationsRepository']
