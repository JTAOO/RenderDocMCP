"""Bridge layer for RenderDoc communication."""

from renderdoc_mcp.bridge.file_ipc_client import FileIpcBridgeClient

__all__ = ["FileIpcBridgeClient", "get_bridge"]

_bridge_instance: FileIpcBridgeClient | None = None


def get_bridge(lazy: bool = True) -> FileIpcBridgeClient:
    """Get global bridge instance.

    Args:
        lazy: If True, don't check connection until first call.
              This allows MCP server to start even if RenderDoc is not running.
    """
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = FileIpcBridgeClient()
        if not lazy:
            _bridge_instance.connect()
    return _bridge_instance
