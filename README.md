# RenderDoc MCP Server

RenderDoc MCP server with AI-first design for graphics debugging assistance.

## Architecture

```
Claude/AI Client (stdio)
        │
        ▼
MCP Server Process (Python + mcp>=1.26.0)
        │ Socket IPC (localhost:19876)
        ▼
RenderDoc Process (Extension)
```

## Setup

### 1. Install RenderDoc Extension

```bash
cd D:\CodeProjects\RenderDocMCP
uv run renderdoc-install-extension
```

The extension will be installed to `%APPDATA%\qrenderdoc\extensions\renderdoc_mcp_bridge`.

### 2. Enable Extension in RenderDoc

1. Start RenderDoc
2. Go to **Tools > Manage Extensions**
3. Enable **"RenderDoc MCP Bridge"**

### 3. Install MCP Server

```bash
uv tool install
uv tool update-shell
```

### 4. Configure MCP Client

#### Claude Code

Update `.mcp.json`:

```json
{
  "mcpServers": {
    "renderdoc": {
      "command": "uv",
      "args": ["run", "renderdoc-mcp"],
      "cwd": "D:\\CodeProjects\\RenderDocMCP"
    }
  }
}
```

## Quick Start

### Open a Capture

```python
renderdoc_open_capture(capture_path="E:\\path\\to\\capture.rdc")
# Returns: {"capture_id": "capture_xxx", "capture_path": "...", "success": true, ...}
```

### Get Capture Overview

```python
renderdoc_get_capture_overview(capture_id="capture_xxx")
```

### List Draw Calls with Pagination

```python
renderdoc_list_draw_calls(
    capture_id="capture_xxx",
    limit=50,
    cursor=0,
    only_actions=True,
    flags_filter=["Drawcall"]
)
# Returns: {"items": [...], "total": 1000, "cursor": 0, "has_more": true, "next_cursor": 50}
```

### Get Draw Call Details

```python
renderdoc_get_draw_call_details(
    capture_id="capture_xxx",
    event_id=1234
)
```

### Get Shader Info

```python
renderdoc_get_shader_info(
    capture_id="capture_xxx",
    event_id=1234,
    stage="pixel"
)
```

### Get Pipeline State

```python
renderdoc_get_pipeline_state(
    capture_id="capture_xxx",
    event_id=1234
)
```

### Find Draw Calls by Shader/Texture

```python
renderdoc_find_draws_by_shader(
    capture_id="capture_xxx",
    shader_name="ToonShader",
    stage="pixel"
)

renderdoc_find_draws_by_texture(
    capture_id="capture_xxx",
    texture_name="CharacterSkin"
)

renderdoc_find_draws_by_resource(
    capture_id="capture_xxx",
    resource_id="ResourceId::12345"
)
```

### Get Buffer/Texture Data

```python
renderdoc_get_buffer_contents(
    capture_id="capture_xxx",
    resource_id="ResourceId::456",
    offset=0,
    length=256
)

renderdoc_get_texture_data(
    capture_id="capture_xxx",
    resource_id="ResourceId::789",
    mip=0,
    slice=0
)
```

## AI-First Design Principles

1. **ID-based Navigation**: All tools use `capture_id` and `event_id` for navigation
2. **Pagination**: List tools support `cursor` and `limit` parameters
3. **Compact Responses**: Default responses are small; use detail tools for more info
4. **No Duplicate Arrays**: Data is returned once, referenced by ID thereafter

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RENDERDOC_BACKEND` | `qrenderdoc` | Backend to use (`qrenderdoc` or `native_python`) |
| `RENDERDOC_QRENDERDOC_PATH` | Auto-detect | Override qrenderdoc.exe path |
| `RENDERDOC_BRIDGE_TIMEOUT_SECONDS` | 30 | Handshake timeout |

## Requirements

- Python 3.10+
- RenderDoc 1.20+
- Windows (for socket IPC)

## License

MIT
