"""
Speech Recognizer
Uses Whisper model to convert audio to text
"""

import numpy as np
from faster_whisper import WhisperModel
from typing import Optional
import librosa


class SpeechRecognizer:
    def __init__(self, model_size: str = "base", device: str = "cuda", 
                 compute_type: str = "int8", language: str = "en", 
                 target_sample_rate: int = 16000):
        """
        Initialize speech recognizer
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to use (cuda, cpu, auto)
            compute_type: Compute type (int8, float16, float32)
            language: Language code (en, hi, etc.)
            target_sample_rate: Target sample rate for Whisper (default 16000)
        """
        print(f"Loading Whisper model ({model_size}) on {device}...")
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )
        self.language = language
        self.target_sample_rate = target_sample_rate
        print("Whisper model loaded!")
        
    def transcribe(self, audio: np.ndarray, source_sample_rate: int = 16000) -> str:
        """
        Transcribe audio to text
        
        Args:
            audio: Audio data as numpy array (float32, normalized)
            source_sample_rate: Sample rate of input audio
            
        Returns:
            Transcribed text
        """
        # Ensure audio is float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
            
        # Resample if needed
        if source_sample_rate != self.target_sample_rate:
            audio = librosa.resample(audio, orig_sr=source_sample_rate, target_sr=self.target_sample_rate)
            
        # Transcribe
        segments, _ = self.model.transcribe(
            audio,
            language=self.language,
            beam_size=5,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 500,
                "speech_pad_ms": 300
            }
        )
        
        # Combine segments
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    
    def transcribe_with_timestamps(self, audio: np.ndarray):
        """
        Transcribe audio with timestamps
        
        Args:
            audio: Audio data as numpy array
            
        Returns:
            Generator of segments with text and timestamps
        """
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
            
        segments, _ = self.model.transcribe(
            audio,
            language=self.language,
            beam_size=5,
            vad_filter=True
        )
        
        return segments
