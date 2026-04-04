# RenderDoc MCP 重构总结

## 重构内容

参照 `renderdoc-mcp2` 的架构，对原有代码进行了全面重构。

## 主要改动

### 1. 项目结构重组

**旧结构:**
```
RenderDocMCP/
├── mcp_server/
│   ├── server.py
│   ├── bridge/
│   └── config.py
└── renderdoc_extension/
```

**新结构:**
```
RenderDocMCP/
├── src/renderdoc_mcp/
│   ├── __init__.py
│   ├── __main__.py
│   ├── server.py              # FastMCP 入口
│   ├── backend.py             # 后端抽象
│   ├── bridge/                # Socket 通信层
│   ├── application/           # 应用层
│   │   ├── app.py
│   │   ├── context.py
│   │   ├── registry.py
│   │   ├── handlers/          # Handlers 分层
│   │   └     ├── captures.py
│   │   ├── └   ├── actions.py
│   │   └   └── resources.py
│   └── errors.py
│   └── protocol.py
└── renderdoc_extension/       # RenderDoc 扩展
```

### 2. 通信协议升级

**旧方式:** 文件 IPC (`%TEMP%/renderdoc_mcp/`)
- 100ms 轮询间隔
- 读写文件同步

**新方式:** Socket IPC (localhost:19876)
- 实时通信
- 更低延迟

### 3. AI-First 工具设计

新增分页支持:
- `cursor` / `limit` 参数
- `has_more` / `next_cursor` 响应字段
- 默认 compact 响应

工具命名规范化:
- `renderdoc_open_capture`
- `renderdoc_get_capture_overview`
- `renderdoc_list_draw_calls`
- 等等...

### 4. 分层架构

**Application Layer:**
- `RenderDocApplication` - 主应用协调器
- `ApplicationContext` - 上下文管理
- `CaptureSessionPool` - 会话池管理

**Handlers Layer:**
- `CaptureHandlers` - 捕获操作
- `ActionHandlers` - Action/Draw 操作
- `ResourceHandlers` - 资源操作

**Bridge Layer:**
- `SocketBridgeClient` - Socket 客户端
- `BridgeManager` - 生命周期管理

### 5. 依赖更新

**旧依赖:**
```toml
dependencies = ["fastmcp>=2.0.0,<3.0.0"]
```

**新依赖:**
```toml
dependencies = ["mcp>=1.26.0,<2.0.0", "pydantic>=2.0.0"]
```

### 6. 后端抽象

支持双后端:
- `qrenderdoc` (默认) - GUI 版 RenderDoc
- `native_python` - 独立 renderdoc.pyd 模块

## 安装步骤

### 1. 安装 RenderDoc 扩展
```bash
cd D:\CodeProjects\RenderDocMCP
uv run renderdoc-install-extension
```

### 2. 在 RenderDoc 中启用扩展
1. 启动 RenderDoc
2. Tools > Manage Extensions
3. 启用 "RenderDoc MCP Bridge"

### 3. 安装 MCP 服务器
```bash
uv tool install
uv tool update-shell
```

## 使用示例

### 打开捕获
```python
result = renderdoc_open_capture(capture_path="E:\\path\\to\\capture.rdc")
# 返回：{"capture_id": "capture_xxx", ...}
```

### 获取捕获概览
```python
renderdoc_get_capture_overview(capture_id="capture_xxx")
```

### 分页获取 Draw Calls
```python
renderdoc_list_draw_calls(
    capture_id="capture_xxx",
    limit=50,
    cursor=0,
    only_actions=True,
    flags_filter=["Drawcall"]
)
# 返回：{"items": [...], "total": 1000, "cursor": 0, "has_more": true}
```

## 文件对比

| 文件类型 | 旧版本 | 新版本 |
|---------|--------|--------|
| Python 文件数 | ~20 | ~24+ |
| server.py | ~340 行 | ~60 行 |
| 架构复杂度 | 简单 | 分层清晰 |

## 兼容性

- RenderDoc 最低版本：1.20+
- Python 最低版本：3.10+
- 操作系统：Windows

## 待办事项

1. 可选：添加更多分析工具 (如 renderdoc-mcp2 的 analysis 模块)
2. 可选：添加 Shader 调试功能
3. 可选：添加 Benchmark 工具
