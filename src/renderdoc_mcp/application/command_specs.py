"""Tool and Resource specifications."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Tool specification."""
    name: str
    description: str
    command: str
    handler: Callable[[Any], Callable[..., dict[str, Any]]]


@dataclass(frozen=True, slots=True)
class ResourceSpec:
    """Resource specification."""
    uri: str
    name: str
    description: str
    handler: Callable[[Any], Callable[..., dict[str, Any]]]
