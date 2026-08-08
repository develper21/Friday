"""
LLM compatibility module.
"""

class Tier:
    """Model tier compatibility stub"""
    LOCAL = "local"
    CLOUD = "cloud"

class LLMBackend:
    """LLM backend compatibility stub"""
    def list_models(self, timeout_sec=5):
        return []

def get_llm_backend(cfg):
    """Get LLM backend (compatibility stub)"""
    return LLMBackend()

def resolve_model(model_id: str, cfg=None):
    """Resolve model to tier (compatibility stub)"""
    return Tier.LOCAL

def check_version(base_url=None, timeout=5):
    """Check LLM version (compatibility stub)"""
    return (False, None)

__all__ = ['get_llm_backend', 'LLMBackend', 'Tier', 'resolve_model', 'check_version']
