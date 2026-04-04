"""RenderDoc Application - main application coordinator."""

from __future__ import annotations

from dataclasses import dataclass

from renderdoc_mcp.application.context import ApplicationContext
from renderdoc_mcp.application.services.capture_sessions import CaptureSessionPool
from renderdoc_mcp.backend import current_backend_name, DEFAULT_BACKEND


@dataclass(slots=True)
class RenderDocApplication:
    """Main application coordinator."""

    pool: CaptureSessionPool
    context: ApplicationContext

    def __init__(self) -> None:
        self.pool = CaptureSessionPool()
        self.context = ApplicationContext(self.pool)

    @property
    def captures(self):
        """Get capture handlers."""
        from renderdoc_mcp.application.handlers.captures import CaptureHandlers
        return CaptureHandlers(self.context)

    @property
    def actions(self):
        """Get action handlers."""
        from renderdoc_mcp.application.handlers.actions import ActionHandlers
        return ActionHandlers(self.context)

    @property
    def resources(self):
        """Get resource handlers."""
        from renderdoc_mcp.application.handlers.resources import ResourceHandlers
        return ResourceHandlers(self.context)
