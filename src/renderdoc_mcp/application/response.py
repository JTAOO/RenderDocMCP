"""Response utilities for AI-first design."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PageResult:
    """Paginated result."""
    items: list[dict[str, Any]]
    total: int
    cursor: int
    has_more: bool
    next_cursor: int | None = None


def create_page_result(
    items: list[dict[str, Any]],
    total: int,
    cursor: int,
    limit: int,
) -> PageResult:
    """Create a paginated result."""
    has_more = cursor + len(items) < total
    next_cursor = cursor + limit if has_more else None

    return PageResult(
        items=items,
        total=total,
        cursor=cursor,
        has_more=has_more,
        next_cursor=next_cursor,
    )


def attach_capture(result: dict[str, Any], session: Any) -> dict[str, Any]:
    """Attach capture metadata to result."""
    return {
        **result,
        "capture_id": session.capture_id,
        "capture_path": session.capture_path,
    }


def bridge_meta(session: any) -> dict[str, Any]:
    """Get bridge metadata."""
    return {
        "capture_id": session.capture_id,
        "capture_path": session.capture_path,
    }
