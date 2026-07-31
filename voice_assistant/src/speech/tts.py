"""
Text-to-Speech Module
Provides voice output for Jean Max assistant using Edge TTS (Microsoft Neural Voices)
"""

import tempfile
import os
import subprocess
import asyncio
from typing import Optional
from datetime import datetime


class TextToSpeech:
    def __init__(self, voice_name: str = "Jean Max", gender: str = "female"):
        """
        Initialize TTS engine with Edge TTS
        
        Args:
            voice_name: Name of the assistant
            gender: Voice gender (male/female)
        """
        self.voice_name = voice_name
        self.gender = gender
        
        # Edge TTS has very natural neural voices
        # en-US-AriaNeural - Young female voice (very natural)
        # en-US-JennyNeural - Young female voice (friendly)
        # en-US-GuyNeural - Young male voice
        if gender == "female":
            self.voice = "en-US-AriaNeural"  # Young, natural female voice
        else:
            self.voice = "en-US-GuyNeural"
        
        # Check if edge-tts is available
        self.edgetts_available = self._check_edgetts()
        
    def _check_edgetts(self) -> bool:
        """Check if edge-tts is installed"""
        try:
            import edge_tts
            return True
        except ImportError:
            print("Warning: edge-tts not found. Install with: pip install edge-tts")
            return False
    
    def speak(self, text: str):
        """
        Speak the given text using Edge TTS
        
        Args:
            text: Text to speak
        """
        if not self.edgetts_available:
            print(f"[{self.voice_name}]: {text}")
            return
            
        try:
            import edge_tts
            
            # Generate audio using edge-tts
            communicate = edge_tts.Communicate(text, self.voice)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            # Save audio
            asyncio.run(communicate.save(temp_path))
            
            # Play the audio
            self._play_audio(temp_path)
            
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        except Exception as e:
            print(f"Error speaking: {e}")
            print(f"[{self.voice_name}]: {text}")
    
    def _play_audio(self, audio_path: str):
        """Play audio file"""
        try:
            # Try different audio players
            players = ["mpg123", "aplay", "paplay", "ffplay"]
            
            for player in players:
                try:
                    subprocess.run([player, audio_path], check=True, 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
                    
            print("No audio player found. Install mpg123: sudo apt install mpg123")
            
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def get_greeting(self) -> str:
        """
        Get time-based greeting
        
        Returns:
            Greeting string
        """
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "Good morning sir"
        elif 12 <= hour < 17:
            return "Good afternoon sir"
        elif 17 <= hour < 21:
            return "Good evening sir"
        else:
            return "Good night sir"
