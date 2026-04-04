"""RenderDoc MCP Extension Installer CLI."""

import os
import shutil
import sys
from pathlib import Path


def get_extension_dir() -> Path:
    """Get RenderDoc extension directory."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "qrenderdoc" / "extensions"
    else:
        home = Path.home()
        return home / ".local" / "share" / "qrenderdoc" / "extensions"
    raise RuntimeError("Cannot determine RenderDoc extension directory")


def install() -> None:
    """Install the extension."""
    # Source directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    extension_src = project_root / "renderdoc_extension"

    if not extension_src.exists():
        print(f"Error: Extension source not found at {extension_src}")
        sys.exit(1)

    # Destination directory
    ext_dir = get_extension_dir()
    ext_dir.mkdir(parents=True, exist_ok=True)

    dest = ext_dir / "renderdoc_mcp_bridge"

    # Remove existing installation
    if dest.exists():
        print(f"Removing existing installation at {dest}")
        shutil.rmtree(dest)

    # Copy extension (excluding __pycache__)
    shutil.copytree(
        extension_src,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    print(f"Extension installed to {dest}")
    print("  (__pycache__ directories excluded)")
    print("")
    print("Please restart RenderDoc and enable the extension in:")
    print("  Tools > Manage Extensions > RenderDoc MCP Bridge")


def uninstall() -> None:
    """Uninstall the extension."""
    ext_dir = get_extension_dir()
    dest = ext_dir / "renderdoc_mcp_bridge"

    if dest.exists():
        shutil.rmtree(dest)
        print(f"Extension uninstalled from {dest}")
    else:
        print(f"Extension not found at {dest}")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall()
    else:
        install()


if __name__ == "__main__":
    main()
