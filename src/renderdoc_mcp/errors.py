"""RenderDoc MCP error types."""

from __future__ import annotations


class RenderDocMCPError(Exception):
    """Base error for RenderDoc MCP."""
    pass


class BridgeHandshakeTimeoutError(RenderDocMCPError):
    """Bridge handshake timeout."""
    pass


class BridgeDisconnectedError(RenderDocMCPError):
    """Bridge disconnected."""
    pass


class CapturePathError(RenderDocMCPError):
    """Invalid capture path."""
    pass


class InvalidEventIDError(RenderDocMCPError):
    """Invalid event ID."""
    pass


class ReplayFailureError(RenderDocMCPError):
    """Replay failure."""
    pass


class InvalidBackendError(RenderDocMCPError):
    """Invalid backend."""
    def __init__(self, backend: str, supported: list[str]):
        self.backend = backend
        self.supported = supported
        super().__init__(f"Invalid backend '{backend}'. Supported: {supported}")


class NativePythonNotConfiguredError(RenderDocMCPError):
    """Native Python backend not configured."""
    pass


class NativePythonModuleNotFoundError(RenderDocMCPError):
    """Native Python module not found."""
    def __init__(self, path: str, kind: str = "module"):
        self.path = path
        self.kind = kind
        super().__init__(f"{kind} not found: {path}")
