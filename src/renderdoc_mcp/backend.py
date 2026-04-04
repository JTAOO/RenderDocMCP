"""Backend abstraction layer."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BACKEND = "qrenderdoc"
NATIVE_PYTHON_BACKEND = "native_python"
SUPPORTED_BACKENDS = [DEFAULT_BACKEND, NATIVE_PYTHON_BACKEND]


@dataclass(slots=True)
class NativePythonConfig:
    """Native Python backend configuration."""
    python_executable: str
    module_dir: Path
    dll_dir: Path

    @property
    def renderdoc_module_path(self) -> Path:
        return self.module_dir / "renderdoc.pyd"


def current_backend_name() -> str:
    """Get current backend name."""
    raw = str(os.environ.get("RENDERDOC_BACKEND", DEFAULT_BACKEND) or DEFAULT_BACKEND).strip().lower()
    backend = raw or DEFAULT_BACKEND
    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Invalid backend '{backend}'. Supported: {SUPPORTED_BACKENDS}")
    return backend


def resolve_native_python_config() -> NativePythonConfig | None:
    """Resolve native Python configuration if configured."""
    module_dir_raw = str(os.environ.get("RENDERDOC_NATIVE_MODULE_DIR", "") or "").strip()
    if not module_dir_raw:
        return None

    module_dir = Path(module_dir_raw)
    if not module_dir.is_dir():
        return None

    renderdoc_module_path = module_dir / "renderdoc.pyd"
    if not renderdoc_module_path.is_file():
        return None

    python_executable = str(os.environ.get("RENDERDOC_NATIVE_PYTHON_EXE", "") or "").strip() or sys.executable

    dll_dir_raw = str(os.environ.get("RENDERDOC_NATIVE_DLL_DIR", "") or "").strip()
    dll_dir = Path(dll_dir_raw) if dll_dir_raw else module_dir

    return NativePythonConfig(
        python_executable=python_executable,
        module_dir=module_dir,
        dll_dir=dll_dir,
    )
