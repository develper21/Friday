"""
Intent Parser Service Implementation
Implements IIntentParser interface using existing parser
"""

from core.interfaces.nlp_service import IIntentParser
from assistance.nlp.parser import Intent, ParsedCommand


class IntentParserService(IIntentParser):
    """Intent parser service implementation"""
    
    def __init__(self):
        from assistance.nlp.parser import IntentParser
        self.parser = IntentParser()
    
    def parse(self, text: str) -> ParsedCommand:
        """Parse text into command"""
        return self.parser.parse(text)
    
    def extract_entities(self, text: str, intent: Intent) -> dict:
        """Extract entities from text based on intent"""
        return self.parser.extract_entities(text, intent)
