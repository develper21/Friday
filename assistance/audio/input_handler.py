"""
Audio Input Handler
Handles microphone input and audio recording
"""

import sounddevice as sd
import numpy as np
from typing import Optional, Callable


class AudioInputHandler:
    def __init__(self, device: Optional[str] = None, sample_rate: int = 16000):
        """
        Initialize audio input handler
        
        Args:
            device: Audio device name or index (None for default)
            sample_rate: Sample rate for recording (default 16000 for Whisper)
        """
        self.device = self._resolve_device(device)
        self.sample_rate = sample_rate
        self.is_recording = False
        
    def _resolve_device(self, device: Optional[str]) -> Optional[int]:
        """
        Resolve device name to device index
        
        Args:
            device: Device name or index
            
        Returns:
            Device index or None for default
        """
        if not device or device.lower() == "default":
            return None
            
        # If it's already an integer
        try:
            val = int(device)
            devs = sd.query_devices()
            if 0 <= val < len(devs) and devs[val]['max_input_channels'] > 0:
                return val
        except ValueError:
            pass
            
        # Search by name (only devices with >0 input channels)
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                if device.lower() in str(dev['name']).lower():
                    print(f"Found audio device: {dev['name']} (index {idx})")
                    return idx
                    
        print(f"Device '{device}' not found or has no input channels. Using default input device.")
        return None
    
    def record(self, duration: float) -> np.ndarray:
        """
        Record audio for specified duration
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Audio data as numpy array (1D)
        """
        print(f"Recording for {duration} seconds...")
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            device=self.device
        )
        sd.wait()
        return recording.flatten()
    
    def record_continuous(self, callback: Callable[[np.ndarray], None], 
                         chunk_duration: float = 0.5):
        """
        Record audio continuously and call callback for each chunk
        
        Args:
            callback: Function to call with each audio chunk
            chunk_duration: Duration of each chunk in seconds
        """
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio status: {status}")
            callback(indata.flatten())
        
        self.is_recording = True
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32,
            device=self.device,
            callback=audio_callback,
            blocksize=int(chunk_duration * self.sample_rate)
        ):
            while self.is_recording:
                sd.sleep(100)
    
    def stop_recording(self):
        """Stop continuous recording"""
        self.is_recording = False
    
    def list_devices(self):
        """List all available input devices"""
        print("\nAvailable Audio Input Devices:")
        print("-" * 60)
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                print(f"{idx}: {dev['name']}")
                print(f"   Channels: {dev['max_input_channels']}")
                print(f"   Sample Rate: {dev['default_samplerate']}")
        print("-" * 60)
