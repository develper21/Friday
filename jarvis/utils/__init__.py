"""
Utils compatibility module.
"""

_REDACTION_RULES = []

def detect_total_vram_mb():
    """Detect VRAM (compatibility stub)"""
    return None

def format_vram_warning(vram_mb):
    """Format VRAM warning (compatibility stub)"""
    return ""

__all__ = ['_REDACTION_RULES', 'detect_total_vram_mb', 'format_vram_warning']
