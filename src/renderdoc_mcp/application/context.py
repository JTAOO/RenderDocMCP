"""Application context for RenderDoc MCP."""

from __future__ import annotations

from typing import Any

from renderdoc_mcp.application.services.capture_sessions import CaptureSessionPool


class InputNormalizer:
    """Normalize input values."""

    @staticmethod
    def normalize_int(value: Any, field_name: str = "value") -> int:
        """Normalize to int."""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"{field_name} must be an integer")
        raise ValueError(f"{field_name} must be an integer")

    @staticmethod
    def normalize_optional_int(value: Any, field_name: str = "value") -> int | None:
        """Normalize to optional int."""
        if value is None:
            return None
        return InputNormalizer.normalize_int(value, field_name)

    @staticmethod
    def normalize_string(value: Any, field_name: str = "value") -> str:
        """Normalize to string."""
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def normalize_optional_string(value: Any, field_name: str = "value") -> str | None:
        """Normalize to optional string."""
        if value is None:
            return None
        return str(value)


class ApplicationContext:
    """Application context for managing sessions and normalization."""

    def __init__(self, pool: CaptureSessionPool) -> None:
        self.pool = pool
        self.normalizer = InputNormalizer()

    def get_session(self, capture_id: str):
        """Get session by capture_id."""
        return self.pool.get_session(capture_id)

    def normalize_optional_int(self, value: Any, field_name: str = "value") -> int | None:
        """Normalize optional int."""
        return self.normalizer.normalize_optional_int(value, field_name)

    def normalize_optional_string(self, value: Any, field_name: str = "value") -> str | None:
        """Normalize optional string."""
        return self.normalizer.normalize_optional_string(value, field_name)

    def capture_tool(self, capture_id: str, method: str, params: dict | None = None):
        """Execute a capture tool method."""
        session = self.get_session(capture_id)
        result = session.bridge.call(method, params or {})
        return session, result
