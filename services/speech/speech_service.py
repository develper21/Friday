"""
Speech Recognition Service Implementation
Implements ISpeechService interface using existing SpeechRecognizer
"""

import numpy as np
from core.interfaces.speech_service import ISpeechService
from assistance.speech.recognizer import SpeechRecognizer


class SpeechService(ISpeechService):
    """Speech recognition service implementation"""
    
    def __init__(self, model_size: str = "base", device: str = "cuda", 
                 compute_type: str = "int8", language: str = "en", 
                 target_sample_rate: int = 16000):
        self.recognizer = SpeechRecognizer(model_size, device, compute_type, language, target_sample_rate)
    
    def transcribe(self, audio: np.ndarray, source_sample_rate: int) -> str:
        """Transcribe audio to text"""
        return self.recognizer.transcribe(audio, source_sample_rate)
    
    def load_model(self):
        """Load speech recognition model"""
        # Model is already loaded in __init__
        pass
