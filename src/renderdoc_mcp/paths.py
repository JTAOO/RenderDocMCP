"""Path utilities for RenderDoc MCP."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_qrenderdoc_path() -> Path:
    """Resolve qrenderdoc.exe path."""
    # Check environment override
    env_path = os.environ.get("RENDERDOC_QRENDERDOC_PATH")
    if env_path:
        return Path(env_path)

    # Default installation paths
    program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
    candidates = [
        Path(program_files) / "RenderDoc" / "qrenderdoc.exe",
        Path(program_files) / "RenderDoc 1.43" / "qrenderdoc.exe",
        Path(program_files) / "RenderDoc 1.42" / "qrenderdoc.exe",
        Path(program_files) / "RenderDoc 1.41" / "qrenderdoc.exe",
        Path(program_files) / "RenderDoc 1.40" / "qrenderdoc.exe",
        Path(program_files) / "RenderDoc 1.17" / "qrenderdoc.exe",
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    # Try PATH
    return Path("qrenderdoc.exe")
