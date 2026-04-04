"""Resource handlers."""

from __future__ import annotations

from typing import Any, Literal

from renderdoc_mcp.application.context import ApplicationContext


class ResourceHandlers:
    """Handler for resource operations."""

    def __init__(self, context: ApplicationContext) -> None:
        self.context = context

    def renderdoc_get_buffer_contents(
        self,
        capture_id: str,
        resource_id: str,
        offset: int = 0,
        length: int = 0,
    ) -> dict[str, Any]:
        """Get buffer contents."""
        _, result = self.context.capture_tool(capture_id, "get_buffer_contents", {
            "resource_id": resource_id,
            "offset": offset,
            "length": length,
        })
        return result

    def renderdoc_get_texture_info(self, capture_id: str, resource_id: str) -> dict[str, Any]:
        """Get texture info."""
        _, result = self.context.capture_tool(capture_id, "get_texture_info", {"resource_id": resource_id})
        return result

    def renderdoc_get_texture_data(
        self,
        capture_id: str,
        resource_id: str,
        mip: int = 0,
        slice: int = 0,
        sample: int = 0,
        depth_slice: int | None = None,
    ) -> dict[str, Any]:
        """Get texture data."""
        params = {"resource_id": resource_id, "mip": mip, "slice": slice, "sample": sample}
        if depth_slice is not None:
            params["depth_slice"] = depth_slice
        _, result = self.context.capture_tool(capture_id, "get_texture_data", params)
        return result
