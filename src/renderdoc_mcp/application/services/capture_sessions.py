"""Capture session pool management."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CaptureSession:
    """Capture session with bridge and metadata."""

    capture_id: str
    capture_path: str
    bridge: Any
    created_at: float = field(default_factory=lambda: 0)


class CaptureSessionPool:
    """Manage capture sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, CaptureSession] = {}

    def create_session(self, capture_path: str, bridge: Any) -> CaptureSession:
        """Create a new capture session."""
        import time
        capture_id = f"capture_{uuid.uuid4().hex[:8]}"
        session = CaptureSession(
            capture_id=capture_id,
            capture_path=capture_path,
            bridge=bridge,
            created_at=time.time(),
        )
        self._sessions[capture_id] = session
        return session

    def get_session(self, capture_id: str) -> CaptureSession:
        """Get session by capture_id."""
        if capture_id not in self._sessions:
            raise ValueError(f"Capture session not found: {capture_id}")
        return self._sessions[capture_id]

    def remove_session(self, capture_id: str) -> None:
        """Remove session."""
        if capture_id in self._sessions:
            del self._sessions[capture_id]

    def list_sessions(self) -> list[CaptureSession]:
        """List all sessions."""
        return list(self._sessions.values())
