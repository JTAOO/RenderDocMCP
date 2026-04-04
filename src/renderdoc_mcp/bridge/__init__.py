"""Bridge layer for RenderDoc communication."""

from renderdoc_mcp.bridge.file_ipc_client import FileIpcBridgeClient

__all__ = ["FileIpcBridgeClient", "get_bridge"]

_bridge_instance: FileIpcBridgeClient | None = None


def get_bridge() -> FileIpcBridgeClient:
    """Get global bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = FileIpcBridgeClient()
    return _bridge_instance
