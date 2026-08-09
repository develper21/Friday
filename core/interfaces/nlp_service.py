"""
NLP Service Interfaces
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from assistance.nlp.parser import Intent, ParsedCommand


class INeuralEngine(ABC):
    """Interface for neural engine for intent classification and conversational AI"""
    
    @abstractmethod
    def predict(self, text: str) -> Tuple[Optional[ParsedCommand], Optional[str]]:
        """Predict intent and generate conversational response"""
        pass
    
    @abstractmethod
    def load_model(self):
        """Load neural model"""
        pass


class IIntentParser(ABC):
    """Interface for intent parsing"""
    
    @abstractmethod
    def parse(self, text: str) -> ParsedCommand:
        """Parse text into command"""
        pass
    
    @abstractmethod
    def extract_entities(self, text: str, intent: Intent) -> dict:
        """Extract entities from text based on intent"""
        pass
