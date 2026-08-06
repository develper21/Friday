"""
Main Daemon
Orchestrates voice activity detection, speech recognition, TTS output, and intent execution.
"""

import sys
import time
import threading
import numpy as np
from typing import Optional

from .audio.input_handler import AudioInputHandler
from .audio.vad import VoiceActivityDetector
from .speech.recognizer import SpeechRecognizer
from .speech.tts import TextToSpeech
from .nlp.neural_engine import JeanMaxNeuralEngine
from .nlp.parser import Intent, ParsedCommand
from .controllers.app_manager import AppManager
from .controllers.browser_controller import BrowserController
from .controllers.system_controller import SystemController
from .controllers.weather_controller import WeatherController
from .controllers.spotify_controller import SpotifyController
from .controllers.terminal_controller import TerminalController
from .controllers.phone_tracking_controller import PhoneTrackingController, TrackingMode
from .controllers.phone_tracking_http_server import PhoneTrackingHTTPServer
from .config.settings import ConfigLoader, Config


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
        
        # Neural Engine for intent classification and conversational responses
        self.neural_engine = JeanMaxNeuralEngine()

        
        # Controllers
        self.app_manager = AppManager()
        self.browser_controller = BrowserController()
        self.system_controller = SystemController()
        self.weather_controller = WeatherController(api_key=config.weather.api_key)
        self.spotify_controller = SpotifyController()
        self.terminal_controller = TerminalController()
        
        # Phone Tracking Controller
        if config.phone_tracking.enabled:
            phone_tracking_config = {
                'device_id': config.phone_tracking.device_id,
                'http_server_port': config.phone_tracking.http_server_port,
                'location_change_threshold': config.phone_tracking.location_change_threshold,
                'monitoring_interval': config.phone_tracking.monitoring_interval,
                'alert_cooldown': config.phone_tracking.alert_cooldown,
                'max_location_history': config.phone_tracking.max_location_history,
                'enable_location_prediction': config.phone_tracking.enable_location_prediction
            }
            self.phone_tracking_controller = PhoneTrackingController(phone_tracking_config)
            
            # Register alert callback for TTS
            self.phone_tracking_controller.register_alert_callback(self._phone_tracking_alert_callback)
            
            # Start HTTP server for receiving location data
            self.phone_tracking_http_server = PhoneTrackingHTTPServer(
                self.phone_tracking_controller,
                port=config.phone_tracking.http_server_port,
                host=config.phone_tracking.http_server_host
            )
            
            if self.phone_tracking_http_server.start():
                print(f"✓ Phone tracking HTTP server started on {config.phone_tracking.http_server_host}:{config.phone_tracking.http_server_port}")
            else:
                print("✗ Failed to start phone tracking HTTP server")
                self.phone_tracking_http_server = None
                
            # Auto-start tracking if configured
            if config.phone_tracking.auto_start_tracking:
                mode = TrackingMode.PASSIVE
                if config.phone_tracking.default_tracking_mode == 'active':
                    mode = TrackingMode.ACTIVE
                elif config.phone_tracking.default_tracking_mode == 'continuous':
                    mode = TrackingMode.CONTINUOUS
                
                self.phone_tracking_controller.start_tracking(mode)
                print(f"✓ Phone tracking auto-started in {config.phone_tracking.default_tracking_mode} mode")
        else:
            self.phone_tracking_controller = None
            self.phone_tracking_http_server = None
        
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
    
    def _phone_tracking_alert_callback(self, alert):
        """
        Callback for phone tracking alerts
        Handles location change alerts via TTS
        """
        try:
            print(f"📱 Phone Tracking Alert: {alert.message}")
            
            # Only speak critical and warning alerts, not info alerts in continuous mode
            if alert.severity.value in ['critical', 'warning']:
                self.tts.speak(alert.message)
            elif alert.severity.value == 'info' and 'location update' not in alert.message.lower():
                self.tts.speak(alert.message)
        except Exception as e:
            print(f"Error in phone tracking alert callback: {e}")

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
        Transcribe audio and execute parsed command with conversational responses
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

        # Process input via Neural Engine (Intent + Conversational Response)
        command, conversational_response = self.neural_engine.predict(text)

        # If conversational response is available, speak it
        if conversational_response:
            print(f"[Jean Max]: {conversational_response}")
            self.tts.speak(conversational_response)
        
        # If command is available, execute it
        if command and command.intent != Intent.UNKNOWN:
            return self._execute_command(command)
        
        return True


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

            elif intent == Intent.SPOTIFY_PLAY:
                if entity:
                    print(f"Playing song on Spotify: {entity}")
                    success, msg = self.spotify_controller.play_song(entity)
                    self.tts.speak(msg)
                    return success
                else:
                    self.tts.speak("Sir, please specify which song to play")
                    return False

            elif intent == Intent.SPOTIFY_ADD_TO_PLAYLIST:
                song = entity
                playlist = command.playlist_entity
                if song and playlist:
                    print(f"Adding song '{song}' to playlist '{playlist}'")
                    success, msg = self.spotify_controller.add_to_playlist(song, playlist)
                    self.tts.speak(msg)
                    return success
                else:
                    self.tts.speak("Sir, please specify both the song and the playlist name")
                    return False

            elif intent == Intent.SPOTIFY_CREATE_PLAYLIST:
                if entity:
                    print(f"Creating Spotify playlist: {entity}")
                    success, msg = self.spotify_controller.create_playlist(entity)
                    self.tts.speak(msg)
                    return success
                else:
                    self.tts.speak("Sir, please specify a name for the new playlist")
                    return False

            elif intent == Intent.SPOTIFY_NEXT:
                success, msg = self.spotify_controller.change_track("next")
                self.tts.speak(msg)
                return success

            elif intent == Intent.SPOTIFY_PREVIOUS:
                success, msg = self.spotify_controller.change_track("previous")
                self.tts.speak(msg)
                return success

            elif intent == Intent.SPOTIFY_PAUSE:
                success, msg = self.spotify_controller.change_track("pause")
                self.tts.speak(msg)
                return success

            elif intent == Intent.SPOTIFY_RESUME:
                success, msg = self.spotify_controller.change_track("resume")
                self.tts.speak(msg)
                return success

            elif intent == Intent.GREETING:
                greeting = f"Hello sir! I am Jean Max, your voice assistant. How can I help you today?"
                self.tts.speak(greeting)
                return True

            elif intent == Intent.TERMINAL_EXEC:
                print("💻 Processing Terminal Command...")
                task_text = entity if entity else command.original_text if hasattr(command, 'original_text') else "update system"
                success, response_msg = self.terminal_controller.execute_task_by_phrase(task_text)
                self.tts.speak(response_msg)
                return success

            elif intent == Intent.POWER_OFF:
                self.tts.speak("Yes sir, shutting down system")
                return self.system_controller.power_off(self.config.shutdown_delay)

            elif intent == Intent.RESTART:
                self.tts.speak("Yes sir, restarting system")
                return self.system_controller.restart(self.config.shutdown_delay)

            elif intent == Intent.PHONE_LOCATION:
                if self.phone_tracking_controller:
                    print("📍 Fetching phone location...")
                    location = self.phone_tracking_controller.get_current_location()
                    response = self.phone_tracking_controller.format_location_response(location)
                    self.tts.speak(response)
                    return True
                else:
                    self.tts.speak("Sorry sir, phone tracking is not enabled")
                    return False

            elif intent == Intent.START_TRACKING:
                if self.phone_tracking_controller:
                    print("🚀 Starting phone tracking...")
                    # Determine tracking mode based on command
                    mode = TrackingMode.ACTIVE
                    if entity and "continuous" in entity.lower():
                        mode = TrackingMode.CONTINUOUS
                    elif entity and "passive" in entity.lower():
                        mode = TrackingMode.PASSIVE
                    
                    success = self.phone_tracking_controller.start_tracking(mode)
                    if success:
                        mode_desc = "active monitoring" if mode == TrackingMode.ACTIVE else "continuous tracking" if mode == TrackingMode.CONTINUOUS else "passive mode"
                        self.tts.speak(f"Yes sir, phone tracking started in {mode_desc}")
                    else:
                        self.tts.speak("Sorry sir, failed to start phone tracking")
                    return success
                else:
                    self.tts.speak("Sorry sir, phone tracking is not enabled")
                    return False

            elif intent == Intent.STOP_TRACKING:
                if self.phone_tracking_controller:
                    print("🛑 Stopping phone tracking...")
                    success = self.phone_tracking_controller.stop_tracking()
                    if success:
                        self.tts.speak("Yes sir, phone tracking stopped")
                    else:
                        self.tts.speak("Sorry sir, failed to stop phone tracking")
                    return success
                else:
                    self.tts.speak("Sorry sir, phone tracking is not enabled")
                    return False

            elif intent == Intent.TRACKING_STATUS:
                if self.phone_tracking_controller:
                    print("📊 Getting phone tracking status...")
                    status = self.phone_tracking_controller.get_tracking_status()
                    self.tts.speak(status)
                    return True
                else:
                    self.tts.speak("Sorry sir, phone tracking is not enabled")
                    return False

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
        print("  - open [app]             (e.g., 'open chrome', 'open vs code', 'open spotify')")
        print("  - play [song name]       (e.g., 'play Bohemian Rhapsody', 'play song Starboy')")
        print("  - add [song] to [playlist] (e.g., 'add Believer to Workout playlist')")
        print("  - create playlist [name] (e.g., 'create playlist Chill Hits')")
        print("  - next track / previous track / pause music / resume music")
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
        print("  - update system / upgrade linux (e.g., 'update system', 'upgrade packages')")
        print("  - run command [cmd]      (e.g., 'run command htop', 'run command git status')")
        print("  - install [package]      (e.g., 'install vlc', 'install htop')")
        print("  - power off / restart")
        print("  📱 Phone Tracking:")
        print("    - where is my phone / phone location / mera phone kidhar hai")
        print("    - start tracking / phone tracking start karo / track my phone")
        print("    - stop tracking / phone tracking stop karo")
        print("    - tracking status / tracking status batao\n")

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

