"""
RenderDoc module compatibility layer.
Supports both 'renderdoc' (official) and 'bdcam' (custom build) module names.

Usage:
    from renderdoc_compat import rd

    # Now use rd just like the original renderdoc module
    rd.OpenCaptureFile()
"""

import sys

# Try to find the renderdoc module with either name
_renderdoc = None

# First check if already aliased in sys.modules (by __init__.py)
if 'renderdoc' in sys.modules:
    _renderdoc = sys.modules['renderdoc']
else:
    # Try both names
    for name in ['bdcam', 'renderdoc']:
        try:
            _renderdoc = __import__(name)
            break
        except ImportError:
            continue

if _renderdoc is None:
    raise ImportError(
        "Neither 'bdcam' nor 'renderdoc' module found. "
        "Make sure you are running within a compatible RenderDoc environment."
    )

# Export as 'rd' for convenience
rd = _renderdoc

# Also export common symbols for direct import
ReplayStatus = getattr(_renderdoc, 'ReplayStatus', None)
ReplayController = getattr(_renderdoc, 'ReplayController', None)
CaptureFile = getattr(_renderdoc, 'CaptureFile', None)
OpenCaptureFile = getattr(_renderdoc, 'OpenCaptureFile', None)
InitialiseReplay = getattr(_renderdoc, 'InitialiseReplay', None)
ShutdownReplay = getattr(_renderdoc, 'ShutdownReplay', None)
GlobalEnvironment = getattr(_renderdoc, 'GlobalEnvironment', None)
