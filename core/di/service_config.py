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
from core.interfaces.messaging_service import IMessagingService, IMessageMonitor
from services.audio import AudioService, VADService
from services.speech import SpeechService, TTSService
from services.nlp import NeuralEngineService, IntentParserService
from services.controllers import (
    AppControllerService, SystemControllerService, WeatherControllerService,
    SpotifyControllerService, TerminalControllerService, PhoneTrackingControllerService
)
from services.messaging import WhatsAppService, InstagramService, MessageMonitor
from infrastructure.storage.message_repository import MessageRepository
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


def configure_messaging(container: DIContainer, config: dict):
    """
    Configure messaging services with specific config
    
    Args:
        container: DIContainer instance
        config: Messaging configuration dict
    """
    # Register message repository
    message_repository = MessageRepository(
        db_path=config.get('db_path', 'data/messages.db')
    )
    container.register_instance(MessageRepository, message_repository)
    
    # Register WhatsApp service if enabled
    if config.get('whatsapp_enabled', False):
        whatsapp_service = WhatsAppService(
            chrome_profile=config.get('whatsapp_chrome_profile', 'Default'),
            repository=message_repository,
            headless=config.get('whatsapp_headless', False)
        )
        container.register_instance(IMessagingService, whatsapp_service, name='whatsapp')
        logger.system("WhatsApp service registered")
    
    # Register Instagram service if enabled
    if config.get('instagram_enabled', False):
        instagram_service = InstagramService(
            username=config.get('instagram_username'),
            password=config.get('instagram_password'),
            session_file=config.get('instagram_session_file', 'data/instagram_session.json'),
            repository=message_repository
        )
        container.register_instance(IMessagingService, instagram_service, name='instagram')
        logger.system("Instagram service registered")
    
    # Register message monitor if enabled
    if config.get('message_monitor_enabled', False):
        # Collect all registered messaging services
        messaging_services = []
        
        try:
            whatsapp_service = container.resolve(IMessagingService, name='whatsapp')
            messaging_services.append(whatsapp_service)
        except:
            pass
        
        try:
            instagram_service = container.resolve(IMessagingService, name='instagram')
            messaging_services.append(instagram_service)
        except:
            pass
        
        if messaging_services:
            message_monitor = MessageMonitor(
                messaging_services=messaging_services,
                repository=message_repository,
                polling_interval=config.get('message_polling_interval', 30),
                enable_alerts=config.get('message_alerts_enabled', True)
            )
            container.register_instance(IMessageMonitor, message_monitor)
            logger.system("Message monitor registered")
