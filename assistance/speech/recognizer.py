"""
Speech Recognizer
Uses Whisper model to convert audio to text
"""

import numpy as np
from faster_whisper import WhisperModel
from typing import Optional
import librosa
import threading
from assistance.utils.errors import SpeechRecognitionError


class SpeechRecognizer:
    # Class-level model cache for performance optimization
    _model_cache = {}
    _cache_lock = threading.Lock()
    
    @classmethod
    def get_model(cls, model_size: str, device: str, compute_type: str):
        """Get cached model or create new one"""
        cache_key = f"{model_size}_{device}_{compute_type}"
        
        with cls._cache_lock:
            if cache_key not in cls._model_cache:
                print(f"Loading Whisper model {model_size} on {device} with {compute_type}...")
                cls._model_cache[cache_key] = WhisperModel(
                    model_size,
                    device=device,
                    compute_type=compute_type
                )
                print("Whisper model loaded and cached!")
            return cls._model_cache[cache_key]
    
    @classmethod
    def clear_cache(cls):
        """Clear model cache to free memory"""
        with cls._cache_lock:
            cls._model_cache.clear()
            print("Model cache cleared")
    
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
        self.model = self.get_model(model_size, device, compute_type)
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.target_sample_rate = target_sample_rate
        
    def transcribe(self, audio: np.ndarray, source_sample_rate: int = 16000) -> str:
        """
        Transcribe audio to text with latency optimization and peak normalization
        
        Args:
            audio: Audio data as numpy array (float32)
            source_sample_rate: Sample rate of input audio
            
        Returns:
            Transcribed text string
        """
        if audio is None:
            raise ValueError("Audio input is None")
        if len(audio) == 0:
            raise ValueError("Audio input is empty")
        if not isinstance(audio, np.ndarray):
            raise TypeError("Audio must be numpy array")

        try:
            # Ensure audio is float32
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
                
            # Resample if needed
            if source_sample_rate != self.target_sample_rate:
                audio = librosa.resample(audio, orig_sr=source_sample_rate, target_sr=self.target_sample_rate)

            # Normalize audio volume (peak normalization) to help with quiet mic input
            max_val = np.max(np.abs(audio))
            if max_val > 0.001:
                audio = audio / max_val * 0.95
                
            # Transcribe with beam_size=1 (greedy search for 3x-5x speedup) and initial prompt
            initial_prompt = "Open application, weather, battery status, system volume, time, stop, wait, Jean Max voice assistant commands."

            segments, _ = self.model.transcribe(
                audio,
                language=self.language,
                beam_size=1,
                best_of=1,
                temperature=0.0,
                initial_prompt=initial_prompt,
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 250,
                    "speech_pad_ms": 200,
                    "threshold": 0.5
                }
            )
            
            # Combine segments
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                print("⚠️ CUDA OOM, falling back to CPU")
                # Could implement fallback logic here
            raise SpeechRecognitionError(f"Speech recognition failed: {e}")
        except Exception as e:
            raise SpeechRecognitionError(f"Transcription error: {e}")
    
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
