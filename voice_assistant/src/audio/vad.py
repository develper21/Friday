"""
Voice Activity Detection
Detects when user starts/stops speaking using webrtcvad
"""

import webrtcvad
import numpy as np
from collections import deque


class VoiceActivityDetector:
    def __init__(self, aggressiveness: int = 2, sample_rate: int = 16000, 
                 frame_duration_ms: int = 30):
        """
        Initialize VAD
        
        Args:
            aggressiveness: VAD aggressiveness (0-3, higher = more sensitive)
            sample_rate: Audio sample rate
            frame_duration_ms: Duration of each frame in ms
        """
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        
        # State tracking
        self.speech_buffer = deque(maxlen=10)  # Track recent frames
        self.is_speaking = False
        self.speech_start_threshold = 3  # Frames to consider speech started
        self.speech_end_threshold = 8  # Frames of silence to consider speech ended
        
    def is_speech(self, frame: np.ndarray) -> bool:
        """
        Check if a frame contains speech
        
        Args:
            frame: Audio frame (must be of correct size)
            
        Returns:
            True if speech detected
        """
        # Convert to int16 for webrtcvad
        if frame.dtype != np.int16:
            frame = (frame * 32767).astype(np.int16)
            
        # Ensure frame is bytes
        frame_bytes = frame.tobytes()
        
        # webrtcvad requires exactly the right size
        if len(frame_bytes) != self.frame_size * 2:  # 2 bytes per sample
            return False
            
        return self.vad.is_speech(frame_bytes, self.sample_rate)
    
    def process_frame(self, frame: np.ndarray) -> bool:
        """
        Process a frame and detect speech state changes
        
        Args:
            frame: Audio frame
            
        Returns:
            True if speech state changed (started or stopped)
        """
        has_speech = self.is_speech(frame)
        self.speech_buffer.append(has_speech)
        
        state_changed = False
        
        # Check if speech started
        if not self.is_speaking and sum(self.speech_buffer) >= self.speech_start_threshold:
            self.is_speaking = True
            state_changed = True
            print("🎤 Speech detected")
            
        # Check if speech ended
        elif self.is_speaking and sum(self.speech_buffer) <= self.speech_end_threshold:
            self.is_speaking = False
            state_changed = True
            print("🔇 Speech ended")
            
        return state_changed
    
    def reset(self):
        """Reset VAD state"""
        self.speech_buffer.clear()
        self.is_speaking = False
