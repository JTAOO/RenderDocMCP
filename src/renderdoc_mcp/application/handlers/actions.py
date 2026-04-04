"""Action handlers with AI-first pagination support."""

from __future__ import annotations

from typing import Any, Literal

from renderdoc_mcp.application.context import ApplicationContext


# Constants for pagination
MAX_PAGE_LIMIT = 200
DEFAULT_PAGE_LIMIT = 50


class ActionHandlers:
    """Handler for action/draw call operations with AI-first design."""

    def __init__(self, context: ApplicationContext) -> None:
        self.context = context

    def renderdoc_get_frame_summary(self, capture_id: str) -> dict[str, Any]:
        """Get frame summary."""
        _, result = self.context.capture_tool(capture_id, "get_frame_summary")
        return {
            "capture_id": capture_id,
            **result,
        }

    def renderdoc_list_draw_calls(
        self,
        capture_id: str,
        cursor: int | str | None = None,
        limit: int | str | None = None,
        include_children: bool = False,
        marker_filter: str | None = None,
        exclude_markers: list[str] | None = None,
        event_id_min: int | None = None,
        event_id_max: int | None = None,
        only_actions: bool = True,
        flags_filter: list[str] | None = None,
    ) -> dict[str, Any]:
        """List draw calls with pagination support.

        Args:
            capture_id: The capture session ID
            cursor: Starting cursor (offset) for pagination
            limit: Maximum items to return (default: 50, max: 200)
            include_children: Include child actions (default: False for flat list)
            marker_filter: Filter by marker name (partial match)
            exclude_markers: Exclude markers containing these strings
            event_id_min: Minimum event ID filter
            event_id_max: Maximum event ID filter
            only_actions: Only return action items (exclude markers)
            flags_filter: Filter by action flags (e.g., ["Drawcall", "Dispatch"])

        Returns:
            Paginated list of draw calls with cursor-based navigation
        """
        # Normalize pagination params
        normalized_cursor = self.context.normalize_optional_int(cursor, "cursor") or 0
        normalized_limit = self.context.normalize_optional_int(limit, "limit") or DEFAULT_PAGE_LIMIT

        # Clamp limit
        if normalized_limit > MAX_PAGE_LIMIT:
            normalized_limit = MAX_PAGE_LIMIT
        if normalized_limit < 1:
            normalized_limit = 1

        # Build params - note: cursor/limit handled at this layer
        params = {
            "include_children": include_children,
            "only_actions": only_actions,
        }
        if marker_filter is not None:
            params["marker_filter"] = marker_filter
        if exclude_markers is not None:
            params["exclude_markers"] = exclude_markers
        if event_id_min is not None:
            params["event_id_min"] = event_id_min
        if event_id_max is not None:
            params["event_id_max"] = event_id_max
        if flags_filter is not None:
            params["flags_filter"] = flags_filter

        _, result = self.context.capture_tool(capture_id, "get_draw_calls", params)

        # Apply pagination at this layer
        actions = result.get("actions", [])
        total = len(actions)

        # Apply cursor and limit
        paginated_actions = actions[normalized_cursor:normalized_cursor + normalized_limit]

        has_more = normalized_cursor + len(paginated_actions) < total
        next_cursor = normalized_cursor + normalized_limit if has_more else None

        return {
            "capture_id": capture_id,
            "items": paginated_actions,
            "total": total,
            "cursor": normalized_cursor,
            "limit": normalized_limit,
            "has_more": has_more,
            "next_cursor": next_cursor,
        }

    def renderdoc_get_draw_call_details(self, capture_id: str, event_id: int) -> dict[str, Any]:
        """Get draw call details."""
        _, result = self.context.capture_tool(capture_id, "get_draw_call_details", {"event_id": event_id})
        return {
            "capture_id": capture_id,
            "event_id": event_id,
            **result,
        }

    def renderdoc_get_shader_info(
        self,
        capture_id: str,
        event_id: int,
        stage: Literal["vertex", "hull", "domain", "geometry", "pixel", "compute"],
    ) -> dict[str, Any]:
        """Get shader info."""
        _, result = self.context.capture_tool(capture_id, "get_shader_info", {
            "event_id": event_id,
            "stage": stage,
        })
        return {
            "capture_id": capture_id,
            "event_id": event_id,
            "stage": stage,
            **result,
        }

    def renderdoc_get_pipeline_state(self, capture_id: str, event_id: int) -> dict[str, Any]:
        """Get pipeline state."""
        _, result = self.context.capture_tool(capture_id, "get_pipeline_state", {"event_id": event_id})
        return {
            "capture_id": capture_id,
            "event_id": event_id,
            **result,
        }

    def renderdoc_get_cbuffer_contents(
        self,
        capture_id: str,
        event_id: int,
        stage: Literal["vertex", "hull", "domain", "geometry", "pixel", "compute"],
    ) -> dict[str, Any]:
        """Get constant buffer contents."""
        _, result = self.context.capture_tool(capture_id, "get_cbuffer_contents", {
            "event_id": event_id,
            "stage": stage,
        })
        return {
            "capture_id": capture_id,
            "event_id": event_id,
            "stage": stage,
            **result,
        }

    def renderdoc_find_draws_by_shader(
        self,
        capture_id: str,
        shader_name: str,
        stage: Literal["vertex", "hull", "domain", "geometry", "pixel", "compute"] | None = None,
    ) -> dict[str, Any]:
        """Find draws by shader."""
        params = {"shader_name": shader_name}
        if stage is not None:
            params["stage"] = stage
        _, result = self.context.capture_tool(capture_id, "find_draws_by_shader", params)
        return {
            "capture_id": capture_id,
            **result,
        }

    def renderdoc_find_draws_by_texture(self, capture_id: str, texture_name: str) -> dict[str, Any]:
        """Find draws by texture."""
        _, result = self.context.capture_tool(capture_id, "find_draws_by_texture", {"texture_name": texture_name})
        return {
            "capture_id": capture_id,
            **result,
        }

    def renderdoc_find_draws_by_resource(self, capture_id: str, resource_id: str) -> dict[str, Any]:
        """Find draws by resource ID."""
        _, result = self.context.capture_tool(capture_id, "find_draws_by_resource", {"resource_id": resource_id})
        return {
            "capture_id": capture_id,
            **result,
        }
