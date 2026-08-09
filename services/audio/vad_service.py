"""
VAD Service Implementation
Implements IVoiceActivityDetector interface using existing VoiceActivityDetector
"""

import numpy as np
from core.interfaces.audio_service import IVoiceActivityDetector
from assistance.audio.vad import VoiceActivityDetector


class VADService(IVoiceActivityDetector):
    """Voice activity detection service implementation"""
    
    def __init__(self, aggressiveness: int = 2, sample_rate: int = 16000, frame_duration_ms: int = 30):
        self.vad = VoiceActivityDetector(aggressiveness, sample_rate, frame_duration_ms)
        self.frame_size = self.vad.frame_size
    
    def is_speech(self, audio_frame: np.ndarray) -> bool:
        """Detect if audio frame contains speech"""
        return self.vad.is_speech(audio_frame)
    
    def reset(self):
        """Reset VAD state"""
        self.vad.reset()
