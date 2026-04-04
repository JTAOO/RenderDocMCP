"""
Test script to verify RenderDoc MCP Bridge extension can be loaded.
Run this script using RenderDoc's built-in Python environment.

Usage:
    1. Start RenderDoc 1.17
    2. Open Python console (Tools > Python Console)
    3. Run this script
"""

import os
import sys

print("=" * 60)
print("RenderDoc MCP Bridge - Extension Load Test")
print("=" * 60)

# Print Python info
print("\n[1] Python Environment:")
print("    Python version:", sys.version)
print("    Python executable:", sys.executable)

# Print sys.path
print("\n[2] Current sys.path:")
for i, path in enumerate(sys.path[:10]):
    print("    [%d] %s" % (i, path))
if len(sys.path) > 10:
    print("    ... and %d more paths" % (len(sys.path) - 10))

# Test PySide2 import
print("\n[3] Testing PySide2 import:")
try:
    from PySide2.QtCore import QObject, QTimer
    print("    SUCCESS: PySide2 imported")
    print("    PySide2 location:", QObject.__module__)
except ImportError as e:
    print("    FAILED: PySide2 not available")
    print("    Error:", e)
    print("    -> Will use pure Python threading mode")

# Test threading module
print("\n[4] Testing threading module:")
try:
    import threading
    print("    SUCCESS: threading module available")
    print("    Location:", threading.__file__)
except ImportError as e:
    print("    FAILED: threading module not available")
    print("    Error:", e)

# Test bdcam import (if available)
print("\n[5] Testing bdcam import:")
try:
    import bdcam
    print("    SUCCESS: bdcam imported")
except ImportError as e:
    print("    INFO: bdcam not available (only available in qrenderdoc context)")
    print("    Error:", e)

# Test bdcam_qrenderdoc import (if available)
print("\n[6] Testing bdcam_qrenderdoc import:")
try:
    import bdcam_qrenderdoc
    print("    SUCCESS: bdcam_qrenderdoc imported")
except ImportError as e:
    print("    INFO: bdcam_qrenderdoc not available (only available in qrenderdoc context)")
    print("    Error:", e)

# Test extension load
print("\n[7] Testing extension module load:")
extension_dir = os.path.dirname(os.path.abspath(__file__))
print("    Extension directory:", extension_dir)

try:
    # Add extension directory to path
    if extension_dir not in sys.path:
        sys.path.insert(0, extension_dir)

    # Try to import the extension
    import __init__ as ext
    print("    SUCCESS: Extension module loaded")
    print("    _has_qrenderdoc:", ext._has_qrenderdoc)
except Exception as e:
    print("    FAILED: Could not load extension")
    print("    Error:", e)
    import traceback
    traceback.print_exc()

# Test socket server
print("\n[8] Testing socket server initialization:")
try:
    from socket_server import MCPBridgeServer
    print("    SUCCESS: MCPBridgeServer class imported")

    # Create a mock handler
    class MockHandler:
        def handle(self, request):
            return {"result": "mock"}

    # Try to create server instance
    server = MCPBridgeServer(host="127.0.0.1", port=19876, handler=MockHandler())
    print("    SUCCESS: MCPBridgeServer instance created")

    # Try to start server
    server.start()
    print("    SUCCESS: MCPBridgeServer started")

    # Stop server
    server.stop()
    print("    SUCCESS: MCPBridgeServer stopped")

except Exception as e:
    print("    FAILED: Socket server test failed")
    print("    Error:", e)
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
