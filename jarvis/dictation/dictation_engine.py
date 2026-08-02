"""
Dictation engine compatibility module.
"""

def format_hotkey_display(hotkey: str) -> str:
    """Format hotkey for display"""
    return hotkey.replace('+', ' + ').upper()
