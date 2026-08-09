"""
Audio Service Interfaces
"""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class IAudioService(ABC):
    """Interface for audio input handling"""
    
    @abstractmethod
    def record(self, duration: float) -> np.ndarray:
        """Record audio for specified duration"""
        pass
    
    @abstractmethod
    def get_device_info(self) -> dict:
        """Get audio device information"""
        pass


class IVoiceActivityDetector(ABC):
    """Interface for voice activity detection"""
    
    @abstractmethod
    def is_speech(self, audio_frame: np.ndarray) -> bool:
        """Detect if audio frame contains speech"""
        pass
    
    @abstractmethod
    def reset(self):
        """Reset VAD state"""
        pass
