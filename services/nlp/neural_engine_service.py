"""
Neural Engine Service Implementation
Implements INeuralEngine interface using existing JeanMaxNeuralEngine
"""

from typing import Optional, Tuple
from core.interfaces.nlp_service import INeuralEngine
from assistance.nlp.neural_engine import JeanMaxNeuralEngine
from assistance.nlp.parser import ParsedCommand


class NeuralEngineService(INeuralEngine):
    """Neural engine service implementation"""
    
    def __init__(self):
        self.engine = JeanMaxNeuralEngine()
    
    def predict(self, text: str) -> Tuple[Optional[ParsedCommand], Optional[str]]:
        """Predict intent and generate conversational response"""
        return self.engine.predict(text)
    
    def load_model(self):
        """Load neural model"""
        # Model is loaded in __init__
        pass
