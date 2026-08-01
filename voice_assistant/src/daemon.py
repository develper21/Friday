"""
Main Daemon
Orchestrates voice activity detection, speech recognition, TTS output, and intent execution.
"""

import sys
import time
import threading
import numpy as np
from typing import Optional

from audio.input_handler import AudioInputHandler
from audio.vad import VoiceActivityDetector
from speech.recognizer import SpeechRecognizer
from speech.tts import TextToSpeech
from nlp.parser import CommandParser, Intent
from controllers.app_manager import AppManager
from controllers.browser_controller import BrowserController
from controllers.system_controller import SystemController
from controllers.weather_controller import WeatherController
from config.settings import ConfigLoader, Config


class VoiceAssistantDaemon:
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize voice assistant daemon
        """
        if config is None:
            config_loader = ConfigLoader()
            config = config_loader.load()
            
        self.config = config
        
        print("Initializing modules...")
        
        # Audio input
        self.audio_handler = AudioInputHandler(
            device=config.audio.device,
            sample_rate=config.audio.sample_rate
        )
        
        # VAD
        if config.audio.vad_enabled:
            self.vad = VoiceActivityDetector(
                aggressiveness=config.audio.vad_aggressiveness,
                sample_rate=config.audio.sample_rate,
                frame_duration_ms=config.audio.frame_duration_ms
            )
        else:
            self.vad = None
            
        # Speech recognition
        self.speech_recognizer = SpeechRecognizer(
            model_size=config.speech.model_size,
            device=config.speech.device,
            compute_type=config.speech.compute_type,
            language=config.speech.language
        )
        
        # NLP parser
        self.parser = CommandParser()
        
        # Controllers
        self.app_manager = AppManager()
        self.browser_controller = BrowserController()
        self.system_controller = SystemController()
        self.weather_controller = WeatherController(api_key=config.weather.api_key)
        
        # TTS (Jean Max - female voice)
        self.tts = TextToSpeech(voice_name="Jean Max", gender="female")
        
        # State tracking
        self.is_listening = False
        self.stop_requested = False
        
        print("✓ All Jean Max modules initialized successfully!")

    def _is_interruption(self, text: str) -> bool:
        """
        Check if transcribed text contains interruption commands
        """
        if not text:
            return False
        text_lower = text.lower().strip()
        interruption_keywords = [
            "wait jean", "stop jean", "jean stop", "jean wait", 
            "wait please", "wait max", "stop max", "wait a minute", "hold on"
        ]
        return any(kw in text_lower for kw in interruption_keywords)

    def handle_interruption(self):
        """
        Stop current speech and ask the user why they stopped Jean Max
        """
        print("⏸ Interruption detected! Stopping speech...")
        self.tts.stop()
        response_text = "What happening, i can hear tell me why are you stopping me ?"
        print(f"[Jean Max]: {response_text}")
        self.tts.speak(response_text, blocking=True)

    def listen_and_process(self) -> bool:
        """
        Listen for voice command using optimized VAD continuous listening
        """
        try:
            if self.vad:
                return self._listen_with_vad()
            else:
                audio = self.audio_handler.record(4.0)
                return self._process_audio(audio)
        except Exception as e:
            print(f"✗ Listening error: {e}")
            return False

    def _listen_with_vad(self) -> bool:
        """
        Listen continuously using VAD to detect speech start and stop with minimal latency
        """
        import sounddevice as sd

        blocksize = 1024
        audio_buffer = []
        silence_frames = 0
        max_silence_frames = 12  # ~0.5s of silence after speech ends for fast response
        speech_detected = False
        max_duration = 15  # Maximum 15s recording

        print("🎤 Listening...")
        self.is_listening = True

        def audio_callback(indata, frames, time_info, status):
            nonlocal audio_buffer, silence_frames, speech_detected
            if status:
                pass
            
            frame = indata.flatten()
            audio_buffer.extend(frame)

            if len(frame) >= self.vad.frame_size:
                for i in range(0, len(frame) - self.vad.frame_size + 1, self.vad.frame_size):
                    vad_frame = frame[i:i + self.vad.frame_size]
                    if self.vad.is_speech(vad_frame):
                        if not speech_detected:
                            speech_detected = True
                            print("👂 Hearing voice...")
                        silence_frames = 0
                    else:
                        if speech_detected:
                            silence_frames += 1

        try:
            with sd.InputStream(
                samplerate=self.config.audio.sample_rate,
                channels=1,
                dtype=np.float32,
                device=self.audio_handler.device,
                callback=audio_callback,
                blocksize=blocksize
            ):
                start_time = time.time()
                while True:
                    if time.time() - start_time > max_duration:
                        break
                    
                    if speech_detected and silence_frames >= max_silence_frames:
                        print("🔇 Speech finished")
                        break
                    
                    sd.sleep(30)

            self.is_listening = False

            if audio_buffer and speech_detected:
                audio = np.array(audio_buffer, dtype=np.float32)
                return self._process_audio(audio)
            else:
                return False

        except Exception as e:
            self.is_listening = False
            print(f"VAD listening error: {e}")
            audio = self.audio_handler.record(4.0)
            return self._process_audio(audio)

    def _process_audio(self, audio: np.ndarray) -> bool:
        """
        Transcribe audio and execute parsed command
        """
        print("⚡ Transcribing speech...")
        text = self.speech_recognizer.transcribe(audio, source_sample_rate=self.config.audio.sample_rate)

        if not text or len(text.strip()) < 2:
            return False

        print(f"📝 Heard: \"{text}\"")

        # Check interruption command while listening
        if self._is_interruption(text):
            self.handle_interruption()
            return True

        # Parse command
        command = self.parser.parse(text)

        # Execute command
        return self._execute_command(command)

    def _execute_command(self, command) -> bool:
        """
        Execute parsed command
        """
        intent = command.intent
        entity = command.entity

        try:
            if intent == Intent.INTERRUPT:
                self.handle_interruption()
                return True

            elif intent == Intent.OPEN_APP:
                if entity:
                    print(f"Opening application: {entity}")
                    success = self.app_manager.open_app(entity)
                    if success:
                        self.tts.speak(f"Yes sir, opening {entity}")
                    else:
                        self.tts.speak(f"Sorry sir, I could not find {entity} installed on your laptop")
                    return success
                else:
                    self.tts.speak("Sir, please specify which application to open")
                    return False

            elif intent == Intent.CLOSE_APP:
                if entity:
                    print(f"Closing application: {entity}")
                    success = self.app_manager.close_app(entity)
                    if success:
                        self.tts.speak(f"Yes sir, closing {entity}")
                    else:
                        self.tts.speak(f"Sir, {entity} does not appear to be running")
                    return success
                else:
                    self.tts.speak("Sir, please specify which application to close")
                    return False

            elif intent == Intent.CLOSE_ALL_APPS:
                success = self.app_manager.close_all_apps()
                if success:
                    self.tts.speak("Yes sir, closing all applications")
                return success

            elif intent == Intent.CLOSE_ALL_TABS:
                success = self.browser_controller.close_all_tabs()
                if success:
                    self.tts.speak("Yes sir, closing browser tabs")
                return success

            elif intent == Intent.WEATHER:
                location = entity if entity else None
                print(f"Fetching weather for: {location if location else 'current location'}")
                weather_info = self.weather_controller.get_weather(location)
                if weather_info:
                    weather_response = self.weather_controller.format_weather_response(weather_info)
                    self.tts.speak(weather_response)
                    return True
                else:
                    self.tts.speak("Sorry sir, I could not fetch weather information right now")
                    return False

            elif intent == Intent.BATTERY:
                msg = self.system_controller.get_battery_info()
                self.tts.speak(msg)
                return True

            elif intent == Intent.SYSTEM_STATUS:
                msg = self.system_controller.get_system_status()
                self.tts.speak(msg)
                return True

            elif intent == Intent.TIME_DATE:
                msg = self.system_controller.get_time_date()
                self.tts.speak(msg)
                return True

            elif intent == Intent.VOLUME_UP:
                msg = self.system_controller.set_volume("up")
                self.tts.speak(msg)
                return True

            elif intent == Intent.VOLUME_DOWN:
                msg = self.system_controller.set_volume("down")
                self.tts.speak(msg)
                return True

            elif intent == Intent.VOLUME_MUTE:
                msg = self.system_controller.set_volume("mute")
                self.tts.speak(msg)
                return True

            elif intent == Intent.SEARCH_WEB:
                msg = self.system_controller.search_web(entity)
                self.tts.speak(msg)
                return True

            elif intent == Intent.GREETING:
                greeting = f"Hello sir! I am Jean Max, your voice assistant. How can I help you today?"
                self.tts.speak(greeting)
                return True

            elif intent == Intent.POWER_OFF:
                self.tts.speak("Yes sir, shutting down system")
                return self.system_controller.power_off(self.config.shutdown_delay)

            elif intent == Intent.RESTART:
                self.tts.speak("Yes sir, restarting system")
                return self.system_controller.restart(self.config.shutdown_delay)

            elif intent == Intent.UNKNOWN:
                print("✗ Command not recognized")
                self._print_help()
                return False

        except Exception as e:
            print(f"✗ Execution error: {e}")
            return False

        return False

    def _print_help(self):
        """Print available commands"""
        print("\n📖 Available Jean Max Commands:")
        print("  - open [app]             (e.g., 'open chrome', 'open vs code', 'open calculator')")
        print("  - close [app]            (e.g., 'close firefox', 'close code', 'close spotify')")
        print("  - close all apps")
        print("  - close all tabs")
        print("  - weather [location]     (e.g., 'weather', 'weather delhi')")
        print("  - wait jean / stop jean  (Interrupts Jean Max when speaking)")
        print("  - battery status")
        print("  - system status")
        print("  - what time is it / date")
        print("  - volume up / volume down / mute")
        print("  - search google for [query] / search youtube for [query]")
        print("  - power off / restart\n")

    def run(self):
        """Main event loop"""
        print("\n" + "="*60)
        print("🎙️  Jean Max Voice Assistant Active!")
        print("="*60)
        
        greeting = self.tts.get_greeting() + ". Jean Max is online."
        print(f"\n{greeting}\n")
        self.tts.speak(greeting)
        
        self._print_help()
        
        try:
            while not self.stop_requested:
                if not self.tts.is_speaking:
                    self.listen_and_process()
                else:
                    time.sleep(0.05)
                
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            self.tts.speak("Goodbye sir")
            sys.exit(0)

