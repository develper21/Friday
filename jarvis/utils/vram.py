"""
VRAM detection compatibility module.
Provides stub implementations for desktop app compatibility.
"""

from typing import Optional

def detect_total_vram_mb() -> Optional[int]:
    """Detect total VRAM in MB. Returns None if unavailable."""
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return int(result.stdout.strip())
    except Exception:
        pass
    return None

def get_recommended_model_id(vram_mb: Optional[int]) -> str:
    """Get recommended model ID based on available VRAM."""
    if vram_mb is None:
        return "llama3.2"
    if vram_mb >= 24000:
        return "llama3.2:70b"
    elif vram_mb >= 16000:
        return "llama3.2:34b"
    elif vram_mb >= 8000:
        return "llama3.2"
    else:
        return "llama3.2:3b"

def required_vram_mb(model_id: str) -> int:
    """Get required VRAM for a model."""
    if "70b" in model_id:
        return 24000
    elif "34b" in model_id:
        return 16000
    elif "3b" in model_id:
        return 4000
    return 8000

def format_vram_warning(vram_mb: int, model_id: str) -> str:
    """Format VRAM warning message."""
    required = required_vram_mb(model_id)
    if vram_mb < required:
        return f"Warning: Only {vram_mb}MB VRAM available, {model_id} requires ~{required}MB"
    return ""
