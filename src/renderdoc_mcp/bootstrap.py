"""Bootstrap runtime utilities."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def prepare_runtime() -> None:
    """Prepare runtime environment."""
    # Ensure TEMP directory exists
    temp_dir = Path(os.environ.get("TEMP", os.environ.get("TMP", ".")))
    ipc_dir = temp_dir / "renderdoc_mcp"
    ipc_dir.mkdir(parents=True, exist_ok=True)
