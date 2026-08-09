"""
Service Configuration
Configures dependency injection container with all services
"""

from core.di.container import DIContainer
from core.interfaces.audio_service import IAudioService, IVoiceActivityDetector
from core.interfaces.speech_service import ISpeechService, ITTSService
from core.interfaces.nlp_service import INeuralEngine, IIntentParser
from core.interfaces.controller_service import (
    IAppController, ISystemController, IWeatherController,
    ISpotifyController, ITerminalController, IPhoneTrackingController
)
from services.audio import AudioService, VADService
from services.speech import SpeechService, TTSService
from services.nlp import NeuralEngineService, IntentParserService
from services.controllers import (
    AppControllerService, SystemControllerService, WeatherControllerService,
    SpotifyControllerService, TerminalControllerService, PhoneTrackingControllerService
)
from assistance.config.settings import ConfigLoader, Config


def configure_container(config: Config = None) -> DIContainer:
    """
    Configure dependency injection container with all services
    
    Args:
        config: Configuration object (optional, will load if not provided)
    
    Returns:
        Configured DIContainer
    """
    if config is None:
        config_loader = ConfigLoader()
        config = config_loader.load()
    
    container = DIContainer()
    
    # Register audio services
    container.register(IAudioService, AudioService, singleton=True)
    container.register(IVoiceActivityDetector, VADService, singleton=True)
    
    # Register speech services
    container.register(ISpeechService, SpeechService, singleton=True)
    container.register(ITTSService, TTSService, singleton=True)
    
    # Register NLP services
    container.register(INeuralEngine, NeuralEngineService, singleton=True)
    container.register(IIntentParser, IntentParserService, singleton=True)
    
    # Register controller services
    container.register(IAppController, AppControllerService, singleton=True)
    container.register(ISystemController, SystemControllerService, singleton=True)
    container.register(IWeatherController, WeatherControllerService, singleton=True)
    container.register(ISpotifyController, SpotifyControllerService, singleton=True)
    container.register(ITerminalController, TerminalControllerService, singleton=True)
    
    # Register config as instance
    container.register_instance(Config, config)
    
    return container


def configure_phone_tracking(container: DIContainer, config: dict):
    """
    Configure phone tracking service with specific config
    
    Args:
        container: DIContainer instance
        config: Phone tracking configuration dict
    """
    # Register phone tracking controller with config
    phone_tracking_service = PhoneTrackingControllerService(config)
    container.register_instance(IPhoneTrackingController, phone_tracking_service)
