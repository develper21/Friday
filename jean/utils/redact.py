"""
Redaction utilities compatibility module.
Provides stub implementations for desktop app compatibility.
"""

_REDACTION_RULES = {
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'ip': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
}

def redact_text(text: str) -> str:
    """Redact sensitive information from text."""
    import re
    redacted = text
    for pattern in _REDACTION_RULES.values():
        redacted = re.sub(pattern, '[REDACTED]', redacted)
    return redacted
