"""
RenderDoc MCP Bridge Extension
Provides socket server for external MCP server communication.

Note: This extension now uses pure Python threading for polling and does not
require PySide2. It will use Qt Timer if PySide2 is available.

Supports both 'renderdoc' (official) and 'bdcam' (custom build) module names.
"""

import os
import sys

# ==================== Module Name Compatibility ====================
# Support both 'renderdoc' (official) and 'bdcam' (custom build) names
# Try to import the replay module with either name
_renderdoc_module = None
_module_name = None

for name in ['bdcam', 'renderdoc']:
    try:
        _renderdoc_module = __import__(name)
        _module_name = name
        print(f"[MCP Bridge] Using '{name}' as renderdoc module")
        break
    except ImportError:
        continue

if _renderdoc_module is None:
    print("[MCP Bridge] WARNING: Neither 'bdcam' nor 'renderdoc' module found")
    print("[MCP Bridge] Extension may not function correctly")

# Add to sys.modules for subsequent imports
if _module_name and _renderdoc_module:
    sys.modules['renderdoc'] = _renderdoc_module
    if _module_name == 'bdcam':
        # Also make 'import renderdoc' work by aliasing
        pass

# Add RenderDoc's Python module directory to sys.path for PySide2 import
# This is needed for RenderDoc 1.17 which bundles PySide2 in a non-standard location
_script_dir = os.path.dirname(os.path.abspath(__file__))
_possible_paths = [
    # Standard RenderDoc installation paths
    r"C:\Program Files\RenderDoc 1.17",
    r"C:\Program Files\RenderDoc",
    # Custom build output path
    r"D:\CodeProjects\renderdoc_J_inlineHook\x64\Release",
    # Custom RenderDoc installation path (JTAOO bdcam)
    r"C:\Program Files\A1_JTAOO\x64\Release",
    # Relative to script (if installed in AppData)
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(_script_dir)))),
]

for path in _possible_paths:
    if os.path.isdir(path):
        if path not in sys.path:
            sys.path.insert(0, path)
        # Also try pymodules subdirectory
        pymodules_path = os.path.join(path, "pymodules")
        if os.path.isdir(pymodules_path) and pymodules_path not in sys.path:
            sys.path.insert(0, pymodules_path)

# Try to add PySide2 to path if it exists
_pyside_paths = [
    r"D:\CodeProjects\renderdoc_J_inlineHook\qrenderdoc\3rdparty\pyside\x64\PySide2",
]
for path in _pyside_paths:
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)
        print(f"[MCP Bridge] Added PySide2 path: {path}")

from . import socket_server
from . import request_handler
from . import renderdoc_facade

# Global state
_context = None
_server = None
_version = ""

# Try to import qrenderdoc for UI integration (only available in RenderDoc)
try:
    import qrenderdoc as qrd

    _has_qrenderdoc = True
except ImportError:
    _has_qrenderdoc = False


def register(version, ctx):
    """
    Called when extension is loaded.

    Args:
        version: RenderDoc version string (e.g., "1.20")
        ctx: CaptureContext handle
    """
    global _context, _server, _version
    _version = version
    _context = ctx

    # Create facade and handler
    facade = renderdoc_facade.RenderDocFacade(ctx)
    handler = request_handler.RequestHandler(facade)

    # Start socket server
    _server = socket_server.MCPBridgeServer(
        host="127.0.0.1", port=19876, handler=handler
    )
    _server.start()

    # Register menu item if UI is available
    if _has_qrenderdoc:
        try:
            ctx.Extensions().RegisterWindowMenu(
                qrd.WindowMenu.Tools, ["MCP Bridge", "Status"], _show_status
            )
        except Exception as e:
            print("[MCP Bridge] Could not register menu: %s" % str(e))

    print("[MCP Bridge] Extension loaded (RenderDoc %s)" % version)
    print("[MCP Bridge] Server listening on 127.0.0.1:19876")


def unregister():
    """Called when extension is unloaded"""
    global _server
    if _server:
        _server.stop()
        _server = None
    print("[MCP Bridge] Extension unloaded")


def _show_status(ctx, data):
    """Show status dialog"""
    if _server and _server.is_running():
        ctx.Extensions().MessageDialog(
            "MCP Bridge is running on port 19876", "MCP Bridge Status"
        )
    else:
        ctx.Extensions().ErrorDialog("MCP Bridge is not running", "MCP Bridge Status")
