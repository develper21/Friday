"""
Audio Input Handler
Handles microphone input and audio recording
"""

import sounddevice as sd
import numpy as np
from typing import Optional, Callable
from assistance.utils.errors import AudioInputError
from assistance.utils.logger import logger


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
        self._audio_buffer = None  # Track buffer for cleanup
        
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
                    logger.success(f"Found audio device: {dev['name']} (index {idx})")
                    return idx
                    
        logger.warning(f"Device '{device}' not found or has no input channels. Using default input device.")
        return None
    
    def record(self, duration: float) -> np.ndarray:
        """
        Record audio for specified duration
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Audio data as numpy array (1D)
        """
        logger.listening(f"Recording for {duration} seconds...")
        try:
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                device=self.device
            )
            sd.wait()
            
            # Store reference for cleanup
            self._audio_buffer = recording
            
            return recording.flatten()
        except sd.PortAudioError as e:
            logger.error(f"Audio device error: {e}")
            raise AudioInputError(f"Failed to record audio: {e}")
        except Exception as e:
            logger.error(f"Unexpected recording error: {e}")
            raise AudioInputError(f"Recording failed: {e}")
        finally:
            # Explicit cleanup
            if hasattr(self, '_audio_buffer') and self._audio_buffer is not None:
                del self._audio_buffer
                self._audio_buffer = None
    
    def record_continuous(self, callback: Callable[[np.ndarray], None], 
                         chunk_duration: float = 0.5):
        """
        Record audio continuously and call callback for each chunk
        
        Args:
            callback: Function to call with each audio chunk
            chunk_duration: Duration of each chunk in seconds
        """
        chunk_samples = int(chunk_duration * self.sample_rate)
        
        def audio_callback(indata, frames, time_info, status):
            if status:
                logger.debug(f"Audio callback status: {status}")
            callback(indata.flatten())
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                device=self.device,
                callback=audio_callback,
                blocksize=chunk_samples
            ):
                self.is_recording = True
                while self.is_recording:
                    sd.sleep(100)
        except Exception as e:
            logger.error(f"Continuous recording error: {e}")
            raise AudioInputError(f"Continuous recording failed: {e}")
        finally:
            self.is_recording = False
    
    def __del__(self):
        """Cleanup on object destruction"""
        if hasattr(self, '_audio_buffer') and self._audio_buffer is not None:
            del self._audio_buffer
    
    def stop_recording(self):
        """Stop continuous recording"""
        self.is_recording = False
    
    def list_devices(self):
        """List all available input devices"""
        logger.section("Available Audio Input Devices")
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                logger.print_raw(f"{idx}: {dev['name']}")
                logger.print_raw(f"   Channels: {dev['max_input_channels']}")
                logger.print_raw(f"   Sample Rate: {dev['default_samplerate']}")
        logger.separator("-", 60)
