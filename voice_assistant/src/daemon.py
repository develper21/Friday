"""
Main Daemon
Orchestrates all modules and handles the main event loop
"""

import sys
import time
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
        
        Args:
            config: Configuration object (loads default if None)
        """
        # Load configuration
        if config is None:
            config_loader = ConfigLoader()
            config = config_loader.load()
            
        self.config = config
        
        # Initialize modules
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
        self.weather_controller = WeatherController()
        
        # TTS (Jean Max - female voice)
        self.tts = TextToSpeech(voice_name="Jean Max", gender="female")
        
        # Audio buffer for speech detection
        self.audio_buffer = []
        self.is_speaking = False
        
        print("✓ All modules initialized")
        
    def listen_and_process(self, duration: float = 5.0) -> bool:
        """
        Listen for voice command and process it
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            True if command was processed successfully
        """
        try:
            # Record audio
            audio = self.audio_handler.record(duration)
            
            # Transcribe
            print("Transcribing...")
            text = self.speech_recognizer.transcribe(audio, source_sample_rate=self.config.audio.sample_rate)
            
            if not text:
                print("No speech detected")
                return False
                
            print(f"📝 Heard: \"{text}\"")
            
            # Parse command
            command = self.parser.parse(text)
            
            # Execute command
            return self._execute_command(command)
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def _execute_command(self, command) -> bool:
        """
        Execute parsed command
        
        Args:
            command: ParsedCommand object
            
        Returns:
            True if successful
        """
        intent = command.intent
        entity = command.entity
        
        try:
            if intent == Intent.OPEN_APP:
                if entity:
                    success = self.app_manager.open_app(entity)
                    if success:
                        self.tts.speak(f"Yes sir, I am opening {entity}")
                    return success
                else:
                    print("✗ No app specified")
                    self.tts.speak("Sir, please specify which app to open")
                    return False
                    
            elif intent == Intent.CLOSE_APP:
                if entity:
                    success = self.app_manager.close_app(entity)
                    if success:
                        self.tts.speak(f"Yes sir, I am closing {entity}")
                    return success
                else:
                    print("✗ No app specified")
                    self.tts.speak("Sir, please specify which app to close")
                    return False
                    
            elif intent == Intent.CLOSE_ALL_APPS:
                success = self.app_manager.close_all_apps()
                if success:
                    self.tts.speak("Yes sir, I am closing all applications")
                return success
                
            elif intent == Intent.CLOSE_ALL_TABS:
                success = self.browser_controller.close_all_tabs()
                if success:
                    self.tts.speak("Yes sir, I am closing all browser tabs")
                return success
                
            elif intent == Intent.POWER_OFF:
                self.tts.speak("Yes sir, I am shutting down the system")
                return self.system_controller.power_off(self.config.shutdown_delay)
                
            elif intent == Intent.RESTART:
                self.tts.speak("Yes sir, I am restarting the system")
                return self.system_controller.restart(self.config.shutdown_delay)
                
            elif intent == Intent.WEATHER:
                location = entity if entity else None
                print(f"Fetching weather for: {location if location else 'current location'}")
                weather_info = self.weather_controller.get_weather(location)
                if weather_info:
                    weather_response = self.weather_controller.format_weather_response(weather_info)
                    self.tts.speak(weather_response)
                    return True
                else:
                    self.tts.speak("Sorry sir, I could not fetch the weather information")
                    return False
                
            elif intent == Intent.UNKNOWN:
                print("✗ Command not recognized")
                self._print_help()
                return False
                
        except Exception as e:
            print(f"✗ Error executing command: {e}")
            return False
            
        return False
    
    def _print_help(self):
        """Print help information"""
        print("\n📖 Available commands:")
        print("  - open [app]           (e.g., 'open chrome')")
        print("  - close [app]          (e.g., 'close firefox')")
        print("  - close all apps")
        print("  - close all tabs")
        print("  - weather [location]   (e.g., 'weather' or 'weather delhi')")
        print("  - power off / shut down")
        print("  - restart / reboot")
        print(f"\n📱 Apps are discovered dynamically")
        print()
    
    def run(self):
        """Main event loop"""
        print("\n" + "="*60)
        print("🎙️  Voice Assistant Started!")
        print("="*60)
        
        # Greeting based on time
        greeting = self.tts.get_greeting()
        print(f"\n{greeting}!")
        self.tts.speak(greeting)
        
        print("\nSay commands like:")
        print("  'open chrome'")
        print("  'close firefox'")
        print("  'close all apps'")
        print("  'close all tabs'")
        print("  'weather' or 'weather delhi'")
        print("  'power off'")
        print("  'restart'")
        print("\nPress Ctrl+C to exit\n")
        
        try:
            while True:
                # Listen and process
                self.listen_and_process(duration=5.0)
                
                # Small delay between commands
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            self.tts.speak("Goodbye sir")
            sys.exit(0)
