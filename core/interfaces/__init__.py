"""
Core Interfaces for JeanMax Voice Assistant
Defines abstract interfaces for all services to enable dependency injection and loose coupling
"""

from .audio_service import IAudioService, IVoiceActivityDetector
from .speech_service import ISpeechService, ITTSService
from .nlp_service import INeuralEngine, IIntentParser
from .controller_service import IAppController, ISystemController, IWeatherController, ISpotifyController, ITerminalController, IPhoneTrackingController

__all__ = [
    'IAudioService',
    'IVoiceActivityDetector',
    'ISpeechService',
    'ITTSService',
    'INeuralEngine',
    'IIntentParser',
    'IAppController',
    'ISystemController',
    'IWeatherController',
    'ISpotifyController',
    'ITerminalController',
    'IPhoneTrackingController',
]
