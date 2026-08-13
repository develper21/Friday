"""
Refactored Voice Assistant Daemon
Uses modern architecture with dependency injection, event bus, and service layer
"""

import sys
import time
import threading
import signal
import atexit
import numpy as np
from typing import Optional

from core.di.service_config import configure_container, configure_phone_tracking, configure_messaging
from core.events.event_bus import EventBus, EventType
from core.observable.observable import AssistantState
from core.interfaces.audio_service import IAudioService, IVoiceActivityDetector
from core.interfaces.speech_service import ISpeechService, ITTSService
from core.interfaces.nlp_service import INeuralEngine
from core.interfaces.controller_service import (
    IAppController, ISystemController, IWeatherController,
    ISpotifyController, ITerminalController, IPhoneTrackingController
)
from core.interfaces.messaging_service import IMessagingService, IMessageMonitor
from assistance.config.settings import ConfigLoader, Config
from assistance.nlp.parser import Intent
from assistance.controllers.phone_tracking_controller import TrackingMode
from assistance.controllers.messaging_controller import MessagingController
from assistance.utils.logger import logger


class VoiceAssistantDaemonRefactored:
    """
    Refactored voice assistant daemon using modern architecture
    - Dependency injection for loose coupling
    - Event bus for component communication
    - Service layer for business logic
    - Observable pattern for state management
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize voice assistant daemon with new architecture
        """
        if config is None:
            config_loader = ConfigLoader()
            config = config_loader.load()
        
        self.config = config
        
        logger.system("Initializing JeanMax with modern architecture...")
        
        # Configure dependency injection container
        self.container = configure_container(config)
        
        # Initialize event bus
        self.event_bus = EventBus()
        
        # Initialize observable state
        self.state = AssistantState()
        
        # Resolve services from container
        self.audio_service = self.container.resolve(IAudioService)
        self.speech_service = self.container.resolve(ISpeechService)
        self.tts_service = self.container.resolve(ITTSService)
        self.neural_engine = self.container.resolve(INeuralEngine)
        self.app_controller = self.container.resolve(IAppController)
        self.system_controller = self.container.resolve(ISystemController)
        self.weather_controller = self.container.resolve(IWeatherController)
        self.spotify_controller = self.container.resolve(ISpotifyController)
        self.terminal_controller = self.container.resolve(ITerminalController)
        
        # VAD service (optional)
        if config.audio.vad_enabled:
            self.vad_service = self.container.resolve(IVoiceActivityDetector)
        else:
            self.vad_service = None
        
        # Phone tracking (optional)
        self.phone_tracking_controller = None
        self.phone_tracking_http_server = None
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
            configure_phone_tracking(self.container, phone_tracking_config)
            self.phone_tracking_controller = self.container.resolve(IPhoneTrackingController)
            
            # Register alert callback
            self.phone_tracking_controller.register_alert_callback(self._phone_tracking_alert_callback)
            
            # Start HTTP server
            from assistance.controllers.phone_tracking_http_server import PhoneTrackingHTTPServer
            self.phone_tracking_http_server = PhoneTrackingHTTPServer(
                self.phone_tracking_controller,
                port=config.phone_tracking.http_server_port,
                host=config.phone_tracking.http_server_host
            )
            
            if self.phone_tracking_http_server.start():
                logger.success(f"Phone tracking HTTP server started on {config.phone_tracking.http_server_host}:{config.phone_tracking.http_server_port}")
            
            # Auto-start tracking if configured
            if config.phone_tracking.auto_start_tracking:
                mode = TrackingMode.PASSIVE
                if config.phone_tracking.default_tracking_mode == 'active':
                    mode = TrackingMode.ACTIVE
                elif config.phone_tracking.default_tracking_mode == 'continuous':
                    mode = TrackingMode.CONTINUOUS
                
                self.phone_tracking_controller.start_tracking(mode)
                logger.success(f"Phone tracking auto-started in {config.phone_tracking.default_tracking_mode} mode")
        
        # Messaging services (optional)
        self.messaging_controller = None
        self.whatsapp_service = None
        self.instagram_service = None
        self.message_monitor = None
        self._unread_alert_thread = None
        self._unread_alert_stop_event = None
        
        if hasattr(config, 'messaging') and config.messaging.enabled:
            messaging_config = {
                'whatsapp_enabled': config.messaging.whatsapp_enabled,
                'whatsapp_chrome_profile': config.messaging.whatsapp_chrome_profile,
                'whatsapp_headless': config.messaging.whatsapp_headless,
                'instagram_enabled': config.messaging.instagram_enabled,
                'instagram_username': config.messaging.instagram_username,
                'instagram_password': config.messaging.instagram_password,
                'instagram_session_file': config.messaging.instagram_session_file,
                'message_monitor_enabled': config.messaging.message_monitor_enabled,
                'message_polling_interval': config.messaging.message_polling_interval,
                'message_alerts_enabled': config.messaging.message_alerts_enabled,
                'db_path': config.messaging.db_path
            }
            configure_messaging(self.container, messaging_config)
            
            # Try to resolve messaging services
            try:
                self.whatsapp_service = self.container.resolve(IMessagingService, name='whatsapp')
            except:
                pass
            
            try:
                self.instagram_service = self.container.resolve(IMessagingService, name='instagram')
            except:
                pass
            
            try:
                self.message_monitor = self.container.resolve(IMessageMonitor)
            except:
                pass
            
            # Create messaging controller
            self.messaging_controller = MessagingController(
                whatsapp_service=self.whatsapp_service,
                instagram_service=self.instagram_service,
                message_monitor=self.message_monitor,
                tts_service=self.tts_service
            )
            
            # Start message monitor if enabled
            if self.message_monitor:
                # Register callback for new message alerts
                self.message_monitor.register_new_message_callback(self._new_message_alert_callback)
                self.message_monitor.start_monitoring()
                logger.success("Message monitoring started")
            
            logger.success("Messaging services initialized")
        
        # Setup event subscribers
        self._setup_event_subscribers()
        
        # State tracking
        self.stop_requested = False
        
        # Start unread message alert checker if messaging is enabled
        if self.messaging_controller and hasattr(config, 'messaging') and config.messaging.enabled:
            self._start_unread_alert_checker(config.messaging.unread_alert_threshold_days)
        
        # Register cleanup handlers
        atexit.register(self._cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.success("JeanMax modules initialized with modern architecture!")

    def _setup_event_subscribers(self):
        """Setup event subscribers for event-driven communication"""
        # Subscribe to speech recognized events
        self.event_bus.subscribe(EventType.SPEECH_RECOGNIZED, self._on_speech_recognized)
        
        # Subscribe to intent detected events
        self.event_bus.subscribe(EventType.INTENT_DETECTED, self._on_intent_detected)
        
        # Subscribe to TTS events
        self.event_bus.subscribe(EventType.TTS_STARTED, self._on_tts_started)
        self.event_bus.subscribe(EventType.TTS_STOPPED, self._on_tts_stopped)
    
    def _on_speech_recognized(self, event):
        """Handle speech recognized event"""
        text = event.data.get('text', '')
        logger.speech(f"Heard: \"{text}\"")
    
    def _on_intent_detected(self, event):
        """Handle intent detected event"""
        intent = event.data.get('intent')
        entity = event.data.get('entity')
        logger.command(f"Intent: {intent}, Entity: {entity}")
    
    def _on_tts_started(self, event):
        """Handle TTS started event"""
        self.state.is_speaking = True
    
    def _on_tts_stopped(self, event):
        """Handle TTS stopped event"""
        self.state.is_speaking = False
    
    def _is_interruption(self, text: str) -> bool:
        """Check if transcribed text contains interruption commands"""
        if not text:
            return False
        text_lower = text.lower().strip()
        interruption_keywords = [
            "wait jean", "stop jean", "jean stop", "jean wait", 
            "wait please", "wait max", "stop max", "wait a minute", "hold on"
        ]
        return any(kw in text_lower for kw in interruption_keywords)

    def handle_interruption(self):
        """Stop current speech and ask the user why they stopped Jean Max"""
        logger.warning("Interruption detected! Stopping speech...")
        self.tts_service.stop()
        response_text = "What happening, i can hear tell me why are you stopping me ?"
        logger.speech(f"[Jean Max]: {response_text}")
        self.tts_service.speak(response_text, blocking=True)
    
    def _phone_tracking_alert_callback(self, location_data: dict):
        """
        Callback for phone tracking alerts
        Called when significant location change is detected
        """
        logger.warning(f"Phone location alert: {location_data}")
        
        # Format alert message
        address = location_data.get('address', 'Unknown location')
        alert_msg = f"Sir, your phone has moved to {address}"
        
        # Speak alert if not interrupted
        if not self.state.is_speaking:
            self.tts_service.speak(alert_msg)
    
    def _new_message_alert_callback(self, messages: List):
        """
        Callback for new message alerts
        Called when new messages are detected by the message monitor
        """
        if not messages:
            return
        
        logger.info(f"New message alert: {len(messages)} messages detected")
        
        # Group messages by platform
        whatsapp_count = sum(1 for m in messages if hasattr(m, 'platform') and m.platform.value == 'whatsapp')
        instagram_count = sum(1 for m in messages if hasattr(m, 'platform') and m.platform.value == 'instagram')
        
        alert_msg = f"Sir, you have {len(messages)} new messages"
        
        if whatsapp_count > 0:
            alert_msg += f". {whatsapp_count} on WhatsApp"
        if instagram_count > 0:
            alert_msg += f". {instagram_count} on Instagram"
        
        # Speak alert if not interrupted
        if not self.state.is_speaking:
            self.tts_service.speak(alert_msg)
    
    def _start_unread_alert_checker(self, threshold_days: int):
        """Start background thread for unread message alerts"""
        self._unread_alert_stop_event = threading.Event()
        
        def _unread_alert_loop():
            while not self._unread_alert_stop_event.is_set():
                try:
                    # Check for unread messages not viewed for threshold days
                    if self.messaging_controller:
                        success, response = self.messaging_controller.check_messages_not_viewed(threshold_days)
                        if success and response:
                            logger.info(f"Unread message check: {response}")
                    
                    # Check every hour
                    self._unread_alert_stop_event.wait(3600)
                except Exception as e:
                    logger.error(f"Error in unread alert checker: {e}")
                    self._unread_alert_stop_event.wait(300)  # Wait 5 minutes on error
        
        self._unread_alert_thread = threading.Thread(
            target=_unread_alert_loop,
            daemon=True,
            name="UnreadAlertChecker"
        )
        self._unread_alert_thread.start()
        logger.success(f"Unread message alert checker started (threshold: {threshold_days} days)")

    def listen_and_process(self) -> bool:
        """Listen for voice command using VAD continuous listening"""
        try:
            if self.vad_service:
                return self._listen_with_vad()
            else:
                audio = self.audio_service.record(4.0)
                return self._process_audio(audio)
        except Exception as e:
            logger.error(f"Listening error: {e}")
            return False

    def _listen_with_vad(self) -> bool:
        """Listen continuously using VAD to detect speech start and stop"""
        import sounddevice as sd

        blocksize = 1024
        audio_buffer = []
        silence_frames = 0
        max_silence_frames = 12
        speech_detected = False
        max_duration = 15

        logger.listening("Listening...")
        self.state.is_listening = True

        def audio_callback(indata, frames, time_info, status):
            nonlocal audio_buffer, silence_frames, speech_detected
            if status:
                pass
            
            frame = indata.flatten()
            audio_buffer.extend(frame)

            if len(frame) >= self.vad_service.frame_size:
                for i in range(0, len(frame) - self.vad_service.frame_size + 1, self.vad_service.frame_size):
                    vad_frame = frame[i:i + self.vad_service.frame_size]
                    if self.vad_service.is_speech(vad_frame):
                        if not speech_detected:
                            speech_detected = True
                            logger.listening("Hearing voice...")
                        silence_frames = 0
                    else:
                        if speech_detected:
                            silence_frames += 1

        try:
            with sd.InputStream(
                samplerate=self.config.audio.sample_rate,
                channels=1,
                dtype=np.float32,
                device=self.audio_service.audio_handler.device,
                callback=audio_callback,
                blocksize=blocksize
            ):
                start_time = time.time()
                while True:
                    if time.time() - start_time > max_duration:
                        break
                    
                    if speech_detected and silence_frames >= max_silence_frames:
                        logger.listening("Speech finished")
                        break
                    
                    sd.sleep(30)

            self.state.is_listening = False

            if audio_buffer and speech_detected:
                audio = np.array(audio_buffer, dtype=np.float32)
                return self._process_audio(audio)
            else:
                return False

        except Exception as e:
            self.state.is_listening = False
            logger.error(f"VAD listening error: {e}")
            audio = self.audio_service.record(4.0)
            return self._process_audio(audio)

    def _process_audio(self, audio: np.ndarray) -> bool:
        """Transcribe audio and execute parsed command with conversational responses"""
        logger.transcribing("Transcribing speech...")
        text = self.speech_service.transcribe(audio, self.config.audio.sample_rate)

        if not text or len(text.strip()) < 2:
            return False

        # Publish speech recognized event
        event = self.event_bus.create_event(EventType.SPEECH_RECOGNIZED, {'text': text})
        import asyncio
        asyncio.run(self.event_bus.publish_sync(event))

        # Check interruption command
        if self._is_interruption(text):
            self.handle_interruption()
            return True

        # Process input via Neural Engine
        command, conversational_response = self.neural_engine.predict(text)

        # If conversational response is available, speak it
        if conversational_response:
            logger.speech(f"[Jean Max]: {conversational_response}")
            self.tts_service.speak(conversational_response)
        
        # If command is available, execute it
        if command and command.intent != Intent.UNKNOWN:
            return self._execute_command(command)
        
        return True

    def _execute_command(self, command) -> bool:
        """Execute parsed command using controller services"""
        intent = command.intent
        entity = command.entity

        try:
            # Publish intent detected event
            event = self.event_bus.create_event(EventType.INTENT_DETECTED, {
                'intent': intent,
                'entity': entity
            })
            import asyncio
            asyncio.run(self.event_bus.publish_sync(event))

            if intent == Intent.INTERRUPT:
                self.handle_interruption()
                return True

            elif intent == Intent.OPEN_APP:
                if entity:
                    logger.command(f"Opening application: {entity}")
                    success = self.app_controller.open_app(entity)
                    if success:
                        self.tts_service.speak(f"Yes sir, opening {entity}")
                    else:
                        self.tts_service.speak(f"Sorry sir, I could not find {entity} installed on your laptop")
                    return success
                else:
                    self.tts_service.speak("Sir, please specify which application to open")
                    return False

            elif intent == Intent.CLOSE_APP:
                if entity:
                    logger.command(f"Closing application: {entity}")
                    success = self.app_controller.close_app(entity)
                    if success:
                        self.tts_service.speak(f"Yes sir, closing {entity}")
                    else:
                        self.tts_service.speak(f"Sir, {entity} does not appear to be running")
                    return success
                else:
                    self.tts_service.speak("Sir, please specify which application to close")
                    return False

            elif intent == Intent.CLOSE_ALL_APPS:
                success = self.app_controller.close_all_apps()
                if success:
                    self.tts_service.speak("Yes sir, closing all applications")
                return success

            elif intent == Intent.WEATHER:
                location = entity if entity else None
                logger.system(f"Fetching weather for: {location if location else 'current location'}")
                weather_info = self.weather_controller.get_weather(location)
                if weather_info:
                    weather_response = self.weather_controller.format_weather_response(weather_info)
                    self.tts_service.speak(weather_response)
                    return True
                else:
                    self.tts_service.speak("Sorry sir, I could not fetch weather information right now")
                    return False

            elif intent == Intent.BATTERY:
                msg = self.system_controller.get_battery_info()
                self.tts_service.speak(msg)
                return True

            elif intent == Intent.SYSTEM_STATUS:
                msg = self.system_controller.get_system_status()
                self.tts_service.speak(msg)
                return True

            elif intent == Intent.TIME_DATE:
                msg = self.system_controller.get_time_date()
                self.tts_service.speak(msg)
                return True

            elif intent == Intent.VOLUME_UP:
                msg = self.system_controller.set_volume("up")
                self.tts_service.speak(msg)
                return True

            elif intent == Intent.VOLUME_DOWN:
                msg = self.system_controller.set_volume("down")
                self.tts_service.speak(msg)
                return True

            elif intent == Intent.VOLUME_MUTE:
                msg = self.system_controller.set_volume("mute")
                self.tts_service.speak(msg)
                return True

            elif intent == Intent.SEARCH_WEB:
                msg = self.system_controller.search_web(entity)
                self.tts_service.speak(msg)
                return True

            elif intent == Intent.SPOTIFY_PLAY:
                if entity:
                    logger.command(f"Playing song on Spotify: {entity}", module="Daemon")
                    success, msg = self.spotify_controller.play_song(entity)
                    self.tts_service.speak(msg)
                    return success
                else:
                    self.tts_service.speak("Sir, please specify which song to play")
                    return False

            elif intent == Intent.SPOTIFY_NEXT:
                success, msg = self.spotify_controller.change_track("next")
                self.tts_service.speak(msg)
                return success

            elif intent == Intent.SPOTIFY_PREVIOUS:
                success, msg = self.spotify_controller.change_track("previous")
                self.tts_service.speak(msg)
                return success

            elif intent == Intent.SPOTIFY_PAUSE:
                success, msg = self.spotify_controller.change_track("pause")
                self.tts_service.speak(msg)
                return success

            elif intent == Intent.SPOTIFY_RESUME:
                success, msg = self.spotify_controller.change_track("resume")
                self.tts_service.speak(msg)
                return success

            elif intent == Intent.GREETING:
                greeting = f"Hello sir! I am Jean Max, your voice assistant. How can I help you today?"
                self.tts_service.speak(greeting)
                return True

            elif intent == Intent.TERMINAL_EXEC:
                logger.command("Processing Terminal Command...")
                task_text = entity if entity else command.original_text if hasattr(command, 'original_text') else "update system"
                success, response_msg = self.terminal_controller.execute_task_by_phrase(task_text)
                self.tts_service.speak(response_msg)
                return success

            elif intent == Intent.POWER_OFF:
                self.tts_service.speak("Yes sir, shutting down system")
                return self.system_controller.power_off(self.config.shutdown_delay)

            elif intent == Intent.RESTART:
                self.tts_service.speak("Yes sir, restarting system")
                return self.system_controller.restart(self.config.shutdown_delay)

            elif intent == Intent.PHONE_LOCATION:
                if self.phone_tracking_controller:
                    logger.system("Fetching phone location...")
                    location = self.phone_tracking_controller.get_current_location()
                    response = self.phone_tracking_controller.format_location_response(location)
                    self.tts_service.speak(response)
                    return True
                else:
                    self.tts_service.speak("Sorry sir, phone tracking is not enabled")
                    return False

            elif intent == Intent.START_TRACKING:
                if self.phone_tracking_controller:
                    logger.system("Starting phone tracking...")
                    mode = TrackingMode.ACTIVE
                    if entity and "continuous" in entity.lower():
                        mode = TrackingMode.CONTINUOUS
                    elif entity and "passive" in entity.lower():
                        mode = TrackingMode.PASSIVE
                    
                    success = self.phone_tracking_controller.start_tracking(mode)
                    if success:
                        mode_desc = "active monitoring" if mode == TrackingMode.ACTIVE else "continuous tracking" if mode == TrackingMode.CONTINUOUS else "passive mode"
                        self.tts_service.speak(f"Yes sir, phone tracking started in {mode_desc}")
                    else:
                        self.tts_service.speak("Sorry sir, failed to start phone tracking")
                    return success
                else:
                    self.tts_service.speak("Sorry sir, phone tracking is not enabled")
                    return False

            elif intent == Intent.STOP_TRACKING:
                if self.phone_tracking_controller:
                    logger.system("Stopping phone tracking...")
                    success = self.phone_tracking_controller.stop_tracking()
                    if success:
                        self.tts_service.speak("Yes sir, phone tracking stopped")
                    else:
                        self.tts_service.speak("Sorry sir, failed to stop phone tracking")
                    return success
                else:
                    self.tts_service.speak("Sorry sir, phone tracking is not enabled")
                    return False

            elif intent == Intent.TRACKING_STATUS:
                if self.phone_tracking_controller:
                    logger.system("Getting phone tracking status...")
                    status = self.phone_tracking_controller.get_tracking_status()
                    self.tts_service.speak(status)
                    return True
                else:
                    self.tts_service.speak("Sorry sir, phone tracking is not enabled")
                    return False

            # Messaging commands
            elif intent == Intent.WHATSAPP_READ:
                if self.messaging_controller:
                    logger.command("Reading WhatsApp messages...")
                    success, response = self.messaging_controller.read_whatsapp_messages()
                    self.messaging_controller.update_last_check_time()
                    return success
                else:
                    self.tts_service.speak("Sorry sir, messaging service is not enabled")
                    return False

            elif intent == Intent.WHATSAPP_SEND:
                if self.messaging_controller:
                    logger.command("Sending WhatsApp message...")
                    # Extract recipient and message from entity
                    if entity:
                        parts = entity.split(' ', 1)
                        recipient = parts[0]
                        text = parts[1] if len(parts) > 1 else ""
                        success, response = self.messaging_controller.send_whatsapp_message(recipient, text)
                        if not success:
                            self.tts_service.speak(response)
                        return success
                    else:
                        self.tts_service.speak("Sir, please specify the recipient and message")
                        return False
                else:
                    self.tts_service.speak("Sorry sir, messaging service is not enabled")
                    return False

            elif intent == Intent.WHATSAPP_UNREAD_COUNT:
                if self.messaging_controller:
                    logger.command("Getting WhatsApp unread count...")
                    success, response = self.messaging_controller.get_whatsapp_unread_count()
                    return success
                else:
                    self.tts_service.speak("Sorry sir, messaging service is not enabled")
                    return False

            elif intent == Intent.INSTAGRAM_READ:
                if self.messaging_controller:
                    logger.command("Reading Instagram messages...")
                    success, response = self.messaging_controller.read_instagram_messages()
                    self.messaging_controller.update_last_check_time()
                    return success
                else:
                    self.tts_service.speak("Sorry sir, messaging service is not enabled")
                    return False

            elif intent == Intent.INSTAGRAM_SEND:
                if self.messaging_controller:
                    logger.command("Sending Instagram message...")
                    if entity:
                        parts = entity.split(' ', 1)
                        recipient = parts[0]
                        text = parts[1] if len(parts) > 1 else ""
                        success, response = self.messaging_controller.send_instagram_message(recipient, text)
                        if not response:
                            self.tts_service.speak(response)
                        return success
                    else:
                        self.tts_service.speak("Sir, please specify the recipient and message")
                        return False
                else:
                    self.tts_service.speak("Sorry sir, messaging service is not enabled")
                    return False

            elif intent == Intent.INSTAGRAM_UNREAD_COUNT:
                if self.messaging_controller:
                    logger.command("Getting Instagram unread count...")
                    success, response = self.messaging_controller.get_instagram_unread_count()
                    return success
                else:
                    self.tts_service.speak("Sorry sir, messaging service is not enabled")
                    return False

            elif intent == Intent.MESSAGES_CHECK:
                if self.messaging_controller:
                    logger.command("Checking all messages...")
                    success, response = self.messaging_controller.read_all_messages()
                    self.messaging_controller.update_last_check_time()
                    return success
                else:
                    self.tts_service.speak("Sorry sir, messaging service is not enabled")
                    return False

            elif intent == Intent.MESSAGES_UNREAD_COUNT:
                if self.messaging_controller:
                    logger.command("Getting total unread count...")
                    success, response = self.messaging_controller.get_total_unread_count()
                    return success
                else:
                    self.tts_service.speak("Sorry sir, messaging service is not enabled")
                    return False

            elif intent == Intent.REPLY_MESSAGE:
                if self.messaging_controller:
                    logger.command("Replying to message...")
                    if entity:
                        success, response = self.messaging_controller.reply_to_last_message(entity)
                        if not response:
                            self.tts_service.speak(response)
                        return success
                    else:
                        self.tts_service.speak("Sir, please specify your reply message")
                        return False
                else:
                    self.tts_service.speak("Sorry sir, messaging service is not enabled")
                    return False

            elif intent == Intent.MARK_MESSAGES_READ:
                if self.messaging_controller:
                    logger.command("Marking messages as read...")
                    success, response = self.messaging_controller.mark_all_as_read()
                    return success
                else:
                    self.tts_service.speak("Sorry sir, messaging service is not enabled")
                    return False

            elif intent == Intent.UNKNOWN:
                logger.warning("Command not recognized")
                self._print_help()
                return False

        except Exception as e:
            logger.error(f"Execution error: {e}")
            return False

        return False

    def _print_help(self):
        """Print available commands"""
        logger.section("Available Jean Max Commands")
        logger.print_raw("  - open [app]             (e.g., 'open chrome', 'open vs code', 'open spotify')")
        logger.print_raw("  - play [song name]       (e.g., 'play Bohemian Rhapsody', 'play song Starboy')")
        logger.print_raw("  - next track / previous track / pause music / resume music")
        logger.print_raw("  - close [app]            (e.g., 'close firefox', 'close code', 'close spotify')")
        logger.print_raw("  - close all apps")
        logger.print_raw("  - weather [location]     (e.g., 'weather', 'weather delhi')")
        logger.print_raw("  - wait jean / stop jean  (Interrupts Jean Max when speaking)")
        logger.print_raw("  - battery status")
        logger.print_raw("  - system status")
        logger.print_raw("  - what time is it / date")
        logger.print_raw("  - volume up / volume down / mute")
        logger.print_raw("  - search google for [query] / search youtube for [query]")
        logger.print_raw("  - update system / upgrade linux")
        logger.print_raw("  - run command [cmd]      (e.g., 'run command htop', 'run command git status')")
        logger.print_raw("  - install [package]      (e.g., 'install vlc', 'install htop')")
        logger.print_raw("  - power off / restart")
        logger.print_raw("  📱 Phone Tracking:")
        logger.print_raw("    - where is my phone / phone location")
        logger.print_raw("    - start tracking / stop tracking")
        logger.print_raw("    - tracking status")
        logger.print_raw("  💬 Messaging:")
        logger.print_raw("    - read my whatsapp messages / read my instagram messages")
        logger.print_raw("    - check my messages / read my messages")
        logger.print_raw("    - send whatsapp message to [contact] [message]")
        logger.print_raw("    - send instagram message to [contact] [message]")
        logger.print_raw("    - reply to [message]")
        logger.print_raw("    - how many messages / unread messages count")
        logger.print_raw("    - mark all as read\n")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.warning(f"Received signal {signum}, shutting down...")
        self._cleanup()
        sys.exit(0)
    
    def _cleanup(self):
        """Cleanup resources on shutdown"""
        logger.system("Cleaning up resources...")
        
        try:
            # Stop TTS
            if self.tts_service:
                self.tts_service.stop()
            
            # Stop phone tracking
            if self.phone_tracking_controller:
                self.phone_tracking_controller.stop_tracking()
            
            # Stop HTTP server
            if self.phone_tracking_http_server:
                self.phone_tracking_http_server.stop()
            
            # Stop message monitor
            if self.message_monitor:
                self.message_monitor.stop_monitoring()
            
            # Stop unread alert checker
            if self._unread_alert_stop_event:
                self._unread_alert_stop_event.set()
            if self._unread_alert_thread:
                self._unread_alert_thread.join(timeout=5)
            
            # Cleanup messaging services
            if self.whatsapp_service:
                self.whatsapp_service.cleanup()
            if self.instagram_service:
                self.instagram_service.cleanup()
            
            # Close audio devices
            try:
                import sounddevice as sd
                sd.terminate()
            except (ImportError, AttributeError, Exception) as e:
                logger.error(f"Error closing audio devices: {e}")
                pass
            
            logger.success("Cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def run(self):
        """Main event loop"""
        logger.separator("=", 60)
        logger.header("Jean Max Voice Assistant Active! (Refactored)", 58)
        logger.separator("=", 60)
        
        greeting = self.tts_service.get_greeting() + ". Jean Max is online."
        logger.print_raw(f"\n{greeting}\n")
        self.tts_service.speak(greeting)
        
        self._print_help()
        
        try:
            while not self.stop_requested:
                if not self.tts_service.is_speaking():
                    self.listen_and_process()
                else:
                    time.sleep(0.05)
                
                time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Goodbye!")
            self.tts_service.speak("Goodbye sir")
            sys.exit(0)
