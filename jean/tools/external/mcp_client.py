"""
MCP client compatibility module.
"""

import shutil
from typing import Optional

def _resolve_command(command: str) -> str:
    """Resolve command to full path"""
    path = shutil.which(command)
    if path is None:
        raise FileNotFoundError(f"Command not found: {command}")
    return path
