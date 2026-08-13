"""
Observable Pattern
Implements observer pattern for state change notifications
"""

from typing import List, Callable
from assistance.utils.logger import logger


class Observable:
    """Base class for observable objects"""
    
    def __init__(self):
        self._observers: List[Callable] = []
    
    def subscribe(self, observer: Callable):
        """
        Subscribe to state changes
        
        Args:
            observer: Callback function to notify on state changes
        """
        self._observers.append(observer)
    
    def unsubscribe(self, observer: Callable):
        """
        Unsubscribe from state changes
        
        Args:
            observer: Callback function to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self, *args, **kwargs):
        """
        Notify all observers of state change
        
        Args:
            *args: Positional arguments to pass to observers
            **kwargs: Keyword arguments to pass to observers
        """
        for observer in self._observers:
            try:
                observer(*args, **kwargs)
            except Exception as e:
                logger.error(f"Observer notification error: {e}", module="Observable")


class AssistantState(Observable):
    """Assistant state management with observable pattern"""
    
    def __init__(self):
        super().__init__()
        self._is_listening = False
        self._is_speaking = False
        self._is_processing = False
    
    @property
    def is_listening(self):
        """Check if assistant is listening"""
        return self._is_listening
    
    @is_listening.setter
    def is_listening(self, value):
        self._is_listening = value
        self.notify('listening_changed', value)
    
    @property
    def is_speaking(self):
        """Check if assistant is speaking"""
        return self._is_speaking
    
    @is_speaking.setter
    def is_speaking(self, value):
        self._is_speaking = value
        self.notify('speaking_changed', value)
    
    @property
    def is_processing(self):
        """Check if assistant is processing"""
        return self._is_processing
    
    @is_processing.setter
    def is_processing(self, value):
        self._is_processing = value
        self.notify('processing_changed', value)
    
    def get_state(self) -> dict:
        """Get current state as dictionary"""
        return {
            'is_listening': self._is_listening,
            'is_speaking': self._is_speaking,
            'is_processing': self._is_processing
        }
