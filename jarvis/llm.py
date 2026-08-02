"""
LLM compatibility module.
"""

class LLMBackend:
    """LLM backend compatibility stub"""
    def list_models(self, timeout_sec=5):
        return []

def get_llm_backend(cfg):
    """Get LLM backend (compatibility stub)"""
    return LLMBackend()

__all__ = ['get_llm_backend', 'LLMBackend']
