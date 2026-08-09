"""
Audio Service Implementation
Implements IAudioService interface using existing AudioInputHandler
"""

import numpy as np
from core.interfaces.audio_service import IAudioService
from assistance.audio.input_handler import AudioInputHandler


class AudioService(IAudioService):
    """Audio service implementation"""
    
    def __init__(self, device: str = None, sample_rate: int = 16000):
        self.audio_handler = AudioInputHandler(device, sample_rate)
    
    def record(self, duration: float) -> np.ndarray:
        """Record audio for specified duration"""
        return self.audio_handler.record(duration)
    
    def get_device_info(self) -> dict:
        """Get audio device information"""
        import sounddevice as sd
        device_idx = self.audio_handler.device
        if device_idx is not None:
            device_info = sd.query_devices(device_idx)
            return {
                'name': device_info['name'],
                'index': device_idx,
                'sample_rate': self.audio_handler.sample_rate
            }
        return {'name': 'default', 'index': None, 'sample_rate': self.audio_handler.sample_rate}
