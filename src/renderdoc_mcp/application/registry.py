"""Tool and Resource registry builder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from renderdoc_mcp.application.app import RenderDocApplication
from renderdoc_mcp.application.command_specs import ToolSpec, ResourceSpec


@dataclass(frozen=True, slots=True)
class ToolRegistration:
    """Tool registration."""
    name: str
    description: str
    handler: Callable[..., dict[str, Any]]


@dataclass(frozen=True, slots=True)
class ResourceRegistration:
    """Resource registration."""
    uri: str
    name: str
    description: str
    handler: Callable[..., dict[str, Any]]


TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        "renderdoc_open_capture",
        "Open a RenderDoc capture and return a capture_id plus compact overview metadata.",
        "load_capture",
        lambda application: application.captures.renderdoc_open_capture,
    ),
    ToolSpec(
        "renderdoc_close_capture",
        "Close an open RenderDoc capture session by capture_id.",
        "close_capture",
        lambda application: application.captures.renderdoc_close_capture,
    ),
    ToolSpec(
        "renderdoc_get_capture_overview",
        "Return compact capture, frame, statistics, and capability overview data for an open capture.",
        "get_capture_overview",
        lambda application: application.captures.renderdoc_get_capture_overview,
    ),
    ToolSpec(
        "renderdoc_get_frame_summary",
        "Return a summary of all actions in the capture with statistics.",
        "get_frame_summary",
        lambda application: application.actions.renderdoc_get_frame_summary,
    ),
    ToolSpec(
        "renderdoc_list_draw_calls",
        "List draw calls with pagination and filtering support.",
        "get_draw_calls",
        lambda application: application.actions.renderdoc_list_draw_calls,
    ),
    ToolSpec(
        "renderdoc_get_draw_call_details",
        "Get detailed information about a specific draw call by event_id.",
        "get_draw_call_details",
        lambda application: application.actions.renderdoc_get_draw_call_details,
    ),
    ToolSpec(
        "renderdoc_get_shader_info",
        "Get shader information for a specific stage at an event.",
        "get_shader_info",
        lambda application: application.actions.renderdoc_get_shader_info,
    ),
    ToolSpec(
        "renderdoc_get_pipeline_state",
        "Get full pipeline state at an event.",
        "get_pipeline_state",
        lambda application: application.actions.renderdoc_get_pipeline_state,
    ),
    ToolSpec(
        "renderdoc_get_cbuffer_contents",
        "Get constant buffer contents for a specific stage at an event.",
        "get_cbuffer_contents",
        lambda application: application.actions.renderdoc_get_cbuffer_contents,
    ),
    ToolSpec(
        "renderdoc_get_buffer_contents",
        "Get buffer data with offset and length support.",
        "get_buffer_contents",
        lambda application: application.resources.renderdoc_get_buffer_contents,
    ),
    ToolSpec(
        "renderdoc_get_texture_info",
        "Get texture metadata.",
        "get_texture_info",
        lambda application: application.resources.renderdoc_get_texture_info,
    ),
    ToolSpec(
        "renderdoc_get_texture_data",
        "Get texture pixel data with mip/slice support.",
        "get_texture_data",
        lambda application: application.resources.renderdoc_get_texture_data,
    ),
    ToolSpec(
        "renderdoc_find_draws_by_shader",
        "Find draw calls by shader name (partial match).",
        "find_draws_by_shader",
        lambda application: application.actions.renderdoc_find_draws_by_shader,
    ),
    ToolSpec(
        "renderdoc_find_draws_by_texture",
        "Find draw calls by texture name (partial match).",
        "find_draws_by_texture",
        lambda application: application.actions.renderdoc_find_draws_by_texture,
    ),
    ToolSpec(
        "renderdoc_find_draws_by_resource",
        "Find draw calls by resource ID (exact match).",
        "find_draws_by_resource",
        lambda application: application.actions.renderdoc_find_draws_by_resource,
    ),
    ToolSpec(
        "renderdoc_list_captures",
        "List capture files in a directory.",
        "list_captures",
        lambda application: application.captures.renderdoc_list_captures,
    ),
)

RESOURCE_SPECS: tuple[ResourceSpec, ...] = ()


def build_tool_registry(application: RenderDocApplication) -> list[ToolRegistration]:
    """Build tool registry from specs."""
    return [
        ToolRegistration(
            name=spec.name,
            description=spec.description,
            handler=spec.handler(application),
        )
        for spec in TOOL_SPECS
    ]


def build_resource_registry(application: RenderDocApplication) -> list[ResourceRegistration]:
    """Build resource registry from specs."""
    return [
        ResourceRegistration(
            uri=spec.uri,
            name=spec.name,
            description=spec.description,
            handler=spec.handler(application),
        )
        for spec in RESOURCE_SPECS
    ]
