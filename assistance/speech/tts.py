"""
Text-to-Speech Module
Provides voice output for Jean Max assistant using Edge TTS (Microsoft Neural Voices)
"""

import tempfile
import os
import time
import subprocess
import asyncio
import threading
from typing import Optional
from datetime import datetime
from assistance.utils.logger import logger


class TextToSpeech:
    def __init__(self, voice_name: str = "Jean Max", gender: str = "female"):
        """
        Initialize TTS engine with Edge TTS
        """
        self.voice_name = voice_name
        self.gender = gender
        self._lock = threading.Lock()
        self._is_speaking = False
        self._stop_requested = False
        self.speech_thread = None
        self.current_process: Optional[subprocess.Popen] = None
        
        if gender == "female":
            self.voice = "en-US-AriaNeural"  # Natural female voice
        else:
            self.voice = "en-US-GuyNeural"
        
        self.edgetts_available = self._check_edgetts()
    
    @property
    def is_speaking(self) -> bool:
        with self._lock:
            return self._is_speaking
    
    @is_speaking.setter
    def is_speaking(self, value: bool):
        with self._lock:
            self._is_speaking = value
    
    @property
    def stop_requested(self) -> bool:
        with self._lock:
            return self._stop_requested
    
    @stop_requested.setter
    def stop_requested(self, value: bool):
        with self._lock:
            self._stop_requested = value

    def _check_edgetts(self) -> bool:
        """Check if edge-tts is installed"""
        try:
            import edge_tts
            return True
        except ImportError:
            logger.warning("edge-tts not found. Install with: pip install edge-tts")
            return False
    
    def speak(self, text: str, blocking: bool = False):
        """
        Speak the given text using Edge TTS
        """
        if not text:
            return

        if not self.edgetts_available:
            logger.speech(f"[{self.voice_name}]: {text}")
            return
        
        # Stop any current speech immediately
        self.stop()
        
        self.stop_requested = False
        if blocking:
            self._speak_thread(text)
        else:
            self.speech_thread = threading.Thread(target=self._speak_thread, args=(text,), daemon=True)
            self.speech_thread.start()
    
    def _speak_thread(self, text: str):
        """Speech execution in thread"""
        self.is_speaking = True
        temp_path = None
        
        try:
            import edge_tts
            
            # Generate audio using edge-tts
            communicate = edge_tts.Communicate(text, self.voice)
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            asyncio.run(communicate.save(temp_path))
            
            # Play audio if not stopped
            if not self.stop_requested:
                self._play_audio(temp_path)
            
        except Exception as e:
            if not self.stop_requested:
                logger.error(f"Error speaking: {e}")
                logger.speech(f"[{self.voice_name}]: {text}")
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            self.is_speaking = False
            self.current_process = None
    
    def stop(self):
        """
        Stop current speech immediately
        """
        self.stop_requested = True
        if self.current_process:
            try:
                self.current_process.kill()
                self.current_process.wait(timeout=0.2)
            except Exception:
                pass
            self.current_process = None
        self.is_speaking = False
    
    def _play_audio(self, audio_path: str):
        """Play audio file with process tracking for instant cancellation"""
        try:
            players = ["mpg123", "pw-play", "aplay", "ffplay"]
            
            for player in players:
                try:
                    cmd = [player, audio_path]
                    if player == "ffplay":
                        cmd = [player, "-nodisp", "-autoexit", "-loglevel", "quiet", audio_path]

                    process = subprocess.Popen(cmd,
                                             stdout=subprocess.DEVNULL, 
                                             stderr=subprocess.DEVNULL)
                    self.current_process = process
                    
                    while process.poll() is None:
                        if self.stop_requested:
                            process.kill()
                            process.wait(timeout=0.2)
                            return
                        time.sleep(0.05)
                    
                    return
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
                    
            logger.warning("No audio player found. Install mpg123: sudo apt install mpg123")
            
        except Exception as e:
            if not self.stop_requested:
                logger.error(f"Error playing audio: {e}")
    
    def get_greeting(self) -> str:
        """
        Get time-based greeting
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
