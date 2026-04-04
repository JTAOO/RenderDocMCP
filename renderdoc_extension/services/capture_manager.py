"""
Capture management service for RenderDoc.
"""

from ..renderdoc_compat import rd


class CaptureManager:
    """Capture management service"""

    def __init__(self, ctx, invoke_fn):
        self.ctx = ctx
        self._invoke = invoke_fn

    def get_capture_status(self):
        """Check if a capture is loaded and get API info"""
        if not self.ctx.IsCaptureLoaded():
            return {"loaded": False}

        result = {"loaded": True, "api": None, "filename": None}

        try:
            result["filename"] = self.ctx.GetCaptureFilename()
        except Exception:
            pass

        # Get API type via replay
        def callback(controller):
            try:
                props = controller.GetAPIProperties()
                result["api"] = str(props.pipelineType)
            except Exception:
                pass

        self._invoke(callback)
        return result

    def list_captures(self, directory):
        """
        List all .rdc files in the specified directory.

        Args:
            directory: Directory path to search

        Returns:
            dict with 'captures' list containing file info
        """
        import os
        import datetime

        # Validate directory exists
        if not os.path.isdir(directory):
            raise ValueError("Directory not found: %s" % directory)

        captures = []

        try:
            for filename in os.listdir(directory):
                if filename.lower().endswith(".rdc"):
                    filepath = os.path.join(directory, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        # Format timestamp as ISO 8601
                        mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                        captures.append({
                            "filename": filename,
                            "path": filepath,
                            "size_bytes": stat.st_size,
                            "modified_time": mtime.isoformat(),
                        })
        except Exception as e:
            raise ValueError("Failed to list directory: %s" % str(e))

        # Sort by modified time (newest first)
        captures.sort(key=lambda x: x["modified_time"], reverse=True)

        return {
            "directory": directory,
            "count": len(captures),
            "captures": captures,
        }

    def open_capture(self, capture_path):
        """
        Open a capture file in RenderDoc.

        Args:
            capture_path: Full path to the .rdc file

        Returns:
            dict with success status and capture info
        """
        import os
        import time

        print("[MCP Bridge] Opening capture: %s" % capture_path)

        # Validate file exists
        if not os.path.isfile(capture_path):
            raise ValueError("Capture file not found: %s" % capture_path)

        # Validate extension
        if not capture_path.lower().endswith(".rdc"):
            raise ValueError("Invalid file type. Expected .rdc file: %s" % capture_path)

        # Create ReplayOptions with defaults
        opts = rd.ReplayOptions()

        # Open the capture
        # LoadCapture is asynchronous - it spawns a thread to load the capture
        try:
            print("[MCP Bridge] Calling LoadCapture...")
            self.ctx.LoadCapture(
                capture_path,   # captureFile
                opts,           # ReplayOptions
                capture_path,   # origFilename (same as capture path)
                False,          # temporary (False = permanent load)
                True,           # local (True = local file)
            )
            print("[MCP Bridge] LoadCapture called successfully")
        except Exception as e:
            print("[MCP Bridge] LoadCapture exception: %s" % str(e))
            raise ValueError("Failed to start loading capture: %s" % str(e))

        # Wait for capture to finish loading (LoadCapture is async)
        # Poll IsCaptureLoaded() with timeout
        timeout = 120.0  # 120 second timeout for large captures
        start_time = time.time()
        wait_count = 0

        print("[MCP Bridge] Waiting for capture to load...")
        while not self.ctx.IsCaptureLoaded():
            elapsed = time.time() - start_time
            wait_count += 1

            # Log progress every 5 seconds
            if wait_count % 50 == 0:
                print("[MCP Bridge] Still loading... %.1f seconds elapsed" % elapsed)

            if elapsed > timeout:
                print("[MCP Bridge] Load timeout after %.1f seconds" % timeout)
                raise ValueError("Failed to load capture: timeout after %.0f seconds" % timeout)

            time.sleep(0.1)  # 100ms poll interval

        print("[MCP Bridge] Capture loaded successfully in %.1f seconds" % (time.time() - start_time))

        # Small delay to ensure replay is fully initialized
        time.sleep(0.05)

        # Get capture info
        result = {
            "success": True,
            "capture_path": capture_path,
            "filename": os.path.basename(capture_path),
        }

        # Get API type if possible (may require replay thread)
        try:
            api_result = {"api": None}

            def callback(controller):
                try:
                    props = controller.GetAPIProperties()
                    api_result["api"] = str(props.pipelineType)
                except Exception as e:
                    print("[MCP Bridge] GetAPIProperties error: %s" % str(e))

            self._invoke(callback)
            if api_result["api"]:
                result["api"] = api_result["api"]
        except Exception as e:
            print("[MCP Bridge] API check error: %s" % str(e))

        return result
