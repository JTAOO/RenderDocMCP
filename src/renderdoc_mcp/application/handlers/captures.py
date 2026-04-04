"""Capture handlers."""

from __future__ import annotations

import os
from typing import Any

from renderdoc_mcp.application.context import ApplicationContext


class CaptureHandlers:
    """Handler for capture operations."""

    def __init__(self, context: ApplicationContext) -> None:
        self.context = context

    def renderdoc_open_capture(self, capture_path: str) -> dict[str, Any]:
        """Open a capture file."""
        from renderdoc_mcp.bridge import get_bridge

        # Validate file exists
        if not os.path.isfile(capture_path):
            raise ValueError(f"Capture file not found: {capture_path}")

        if not capture_path.lower().endswith(".rdc"):
            raise ValueError(f"Invalid file type. Expected .rdc file: {capture_path}")

        # Get bridge and open capture
        bridge = get_bridge()
        result = bridge.call("open_capture", {"capture_path": capture_path})

        # Create session
        session = self.context.pool.create_session(capture_path, bridge)

        return {
            "capture_id": session.capture_id,
            "capture_path": session.capture_path,
            **result,
        }

    def renderdoc_close_capture(self, capture_id: str) -> dict[str, Any]:
        """Close a capture session."""
        session = self.context.get_session(capture_id)
        self.context.pool.remove_session(capture_id)

        return {
            "capture_id": session.capture_id,
            "closed": True,
        }

    def renderdoc_get_capture_overview(self, capture_id: str) -> dict[str, Any]:
        """Get capture overview."""
        session, result = self.context.capture_tool(capture_id, "get_capture_status")
        return {
            "capture_id": session.capture_id,
            **result,
        }

    def renderdoc_list_captures(self, directory: str) -> dict[str, Any]:
        """List captures in directory."""
        import datetime

        if not os.path.isdir(directory):
            raise ValueError(f"Directory not found: {directory}")

        captures = []
        try:
            for filename in os.listdir(directory):
                if filename.lower().endswith(".rdc"):
                    filepath = os.path.join(directory, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                        captures.append({
                            "filename": filename,
                            "path": filepath,
                            "size_bytes": stat.st_size,
                            "modified_time": mtime.isoformat(),
                        })
        except Exception as e:
            raise ValueError(f"Failed to list directory: {str(e)}")

        captures.sort(key=lambda x: x["modified_time"], reverse=True)

        return {
            "directory": directory,
            "count": len(captures),
            "captures": captures,
        }
