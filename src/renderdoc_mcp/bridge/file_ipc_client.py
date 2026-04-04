"""File-based IPC bridge client for RenderDoc communication."""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from typing import Any

from renderdoc_mcp.errors import BridgeDisconnectedError, BridgeHandshakeTimeoutError


# IPC directory (must match renderdoc_extension/socket_server.py)
IPC_DIR = os.path.join(tempfile.gettempdir(), "renderdoc_mcp")
REQUEST_FILE = os.path.join(IPC_DIR, "request.json")
RESPONSE_FILE = os.path.join(IPC_DIR, "response.json")
LOCK_FILE = os.path.join(IPC_DIR, "lock")


class FileIpcBridgeClient:
    """File-based IPC bridge client."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout
        self._connected = False

    def connect(self) -> None:
        """Check if bridge is available."""
        if not os.path.exists(IPC_DIR):
            raise BridgeHandshakeTimeoutError(
                f"Cannot connect to RenderDoc MCP Bridge. "
                f"IPC directory not found: {IPC_DIR}. "
                "Make sure RenderDoc is running with the MCP Bridge extension loaded."
            )
        self._connected = True

    def close(self) -> None:
        """Close connection (no-op for file IPC)."""
        self._connected = False

    def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Call a method on the bridge server."""
        # Lazy connect - check connection on first call
        if not self._connected:
            self.connect()

        request = {
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params or {},
        }

        try:
            # Clean up any stale response file
            if os.path.exists(RESPONSE_FILE):
                os.remove(RESPONSE_FILE)

            # Create lock file to signal we're writing
            with open(LOCK_FILE, "w") as f:
                f.write("lock")

            # Write request
            with open(REQUEST_FILE, "w", encoding="utf-8") as f:
                json.dump(request, f, ensure_ascii=False)

            # Remove lock file to signal write complete
            os.remove(LOCK_FILE)

            # Wait for response
            start_time = time.time()
            while True:
                if os.path.exists(RESPONSE_FILE):
                    # Small delay to ensure file is fully written
                    time.sleep(0.01)

                    # Read response
                    with open(RESPONSE_FILE, "r", encoding="utf-8") as f:
                        response = json.load(f)

                    # Clean up response file
                    os.remove(RESPONSE_FILE)

                    if "error" in response:
                        error = response["error"]
                        raise Exception(f"[{error.get('code', -1)}] {error.get('message', 'Unknown error')}")

                    return response.get("result")

                # Check timeout
                if time.time() - start_time > self.timeout:
                    raise BridgeHandshakeTimeoutError(
                        f"Request timed out after {self.timeout}s. "
                        "Make sure RenderDoc is running with the MCP Bridge extension loaded."
                    )

                # Poll interval
                time.sleep(0.05)

        except (BridgeDisconnectedError, BridgeHandshakeTimeoutError):
            raise
        except Exception as e:
            raise BridgeDisconnectedError(f"Communication error: {e}")
