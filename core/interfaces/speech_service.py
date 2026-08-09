"""
Speech Service Interfaces
"""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class ISpeechService(ABC):
    """Interface for speech recognition (STT)"""
    
    @abstractmethod
    def transcribe(self, audio: np.ndarray, source_sample_rate: int) -> str:
        """Transcribe audio to text"""
        pass
    
    @abstractmethod
    def load_model(self):
        """Load speech recognition model"""
        pass


class ITTSService(ABC):
    """Interface for text-to-speech"""
    
    @abstractmethod
    def speak(self, text: str, blocking: bool = False) -> bool:
        """Convert text to speech"""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop current speech"""
        pass
    
    @abstractmethod
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        pass
    
    @abstractmethod
    def get_greeting(self) -> str:
        """Get time-based greeting"""
        pass
