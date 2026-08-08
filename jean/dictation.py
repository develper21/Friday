"""
Dictation compatibility module.
"""

class DictationHistory:
    """Dictation history compatibility stub"""
    def __init__(self):
        self.entries = []
    
    def add_entry(self, text):
        self.entries.append(text)

__all__ = ['DictationHistory']
