"""
Custom Exceptions for JeanMax
Provides specific error types for better error handling
"""


class AudioInputError(Exception):
    """Raised when audio input fails"""
    pass


class SpeechRecognitionError(Exception):
    """Raised when speech recognition fails"""
    pass


class TTSError(Exception):
    """Raised when text-to-speech fails"""
    pass


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass


class ModelLoadError(Exception):
    """Raised when model loading fails"""
    pass
