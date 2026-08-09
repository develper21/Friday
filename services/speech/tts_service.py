"""
TTS Service Implementation
Implements ITTSService interface using existing TextToSpeech
"""

from core.interfaces.speech_service import ITTSService
from assistance.speech.tts import TextToSpeech


class TTSService(ITTSService):
    """Text-to-speech service implementation"""
    
    def __init__(self, voice_name: str = "Jean Max", gender: str = "female"):
        self.tts = TextToSpeech(voice_name, gender)
    
    def speak(self, text: str, blocking: bool = False) -> bool:
        """Convert text to speech"""
        try:
            self.tts.speak(text, blocking)
            return True
        except Exception:
            return False
    
    def stop(self):
        """Stop current speech"""
        self.tts.stop()
    
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        return self.tts.is_speaking
    
    def get_greeting(self) -> str:
        """Get time-based greeting"""
        return self.tts.get_greeting()
