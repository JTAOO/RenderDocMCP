# RenderDoc 1.17 支持说明

本文档说明如何使用修改后的 RenderDocMCP 与自定义 RenderDoc 1.17 版本配合使用。

## 修改内容

### 1. extension.json
- 将 `minimum_renderdoc` 从 `1.20` 改为 `1.17`

### 2. paths.py
- 添加了 `RenderDoc 1.17` 到 qrenderdoc 路径候选列表

### 3. socket_server.py
- 增强了 PySide2 导入的兼容性，支持 PySide 回退
- **新增纯 Python threading 轮询模式**，在 PySide2 不可用时自动切换

### 4. __init__.py
- 添加了 PySide2 路径配置（如果可用）
- **新增模块名兼容层**，支持 `bdcam` 和 `renderdoc` 两个模块名

### 5. renderdoc_compat.py（新文件）
- 模块兼容层，自动检测并导入 `bdcam` 或 `renderdoc`
- 将导入的模块注册到 `sys.modules['renderdoc']`

### 6. 所有服务文件和工具文件
- `services/*.py` - 修改为 `from ..renderdoc_compat import rd`
- `utils/*.py` - 修改为 `from ..renderdoc_compat import rd`

## 安装步骤

### 步骤 1: 确认你的 RenderDoc 1.17 路径
```
D:\CodeProjects\renderdoc_J_inlineHook\x64\Release\
```

该目录应包含：
- `bdcam64.dll` - Vulkan 捕获层
- `bdcam.pyd` / `bdcam_qrenderdoc.pyd` - Python 扩展模块
- `python36.dll` - Python 3.6 运行时
- `pymodules/` - Python 模块目录

### 步骤 2: 安装 RenderDocMCP 扩展

使用你的虚拟环境运行安装命令：

```bash
cd D:\CodeProjects\RenderDocMCP
D:\CodeProjects\RenderDocMCP\.venv\Scripts\python.exe -m renderdoc_mcp.install_cli
```

或者直接运行：

```bash
cd D:\CodeProjects\RenderDocMCP
uv run renderdoc-install-extension
```

### 步骤 3: 配置环境变量（可选）

如果你的 RenderDoc 1.17 不在默认路径，可以设置环境变量：

```bash
# 在启动 RenderDoc 之前设置
set ENABLE_VULKAN_BDCAM64_CAPTURE=1
```

### 步骤 4: 启动 RenderDoc 1.17 并启用扩展

1. 启动你的自定义 RenderDoc 1.17 (`bdcam.exe` 或 `renderdocui.exe`)
2. 进入 **Tools > Manage Extensions**
3. 找到 **"RenderDoc MCP Bridge"** 并启用它
4. 确认状态显示服务器在 `127.0.0.1:19876` 运行

### 步骤 4.5: 测试扩展加载（可选）

在启动扩展之前，可以先测试是否能正确加载：

1. 启动 RenderDoc 1.17
2. 打开 **Tools > Python Console**
3. 运行测试脚本：
   ```python
   exec(open(r"D:\CodeProjects\RenderDocMCP\renderdoc_extension\test_extension_load.py").read())
   ```
4. 查看输出，确认所有测试通过

### 步骤 5: 验证连接

```bash
# 运行 MCP 服务器测试
cd D:\CodeProjects\RenderDocMCP
uv run renderdoc-mcp
```

## Python 依赖兼容性

### RenderDocMCP 外部 Python 环境
- Python 版本：3.10+ (当前使用 3.14.3)
- 依赖包：
  - `mcp>=1.26.0,<2.0.0`
  - `pydantic>=2.0.0`

### RenderDoc 1.17 内置 Python 环境
- Python 版本：3.6
- PySide2: 内置于 `qrenderdoc/3rdparty/pyside/x64/PySide2/`
- 扩展模块：
  - `bdcam.pyd` - 核心 Replay 模块
  - `bdcam_qrenderdoc.pyd` - UI 扩展模块

### 通信方式
两个 Python 环境通过 **文件 IPC** 通信：
- 请求文件：`%TEMP%\renderdoc_mcp\request.json`
- 响应文件：`%TEMP%\renderdoc_mcp\response.json`
- 锁文件：`%TEMP%\renderdoc_mcp\lock`

由于使用文件 IPC，两个 Python 环境的版本差异不会影响功能。

## 故障排除

### 问题 1: 扩展无法加载
**症状**: RenderDoc 启动后在扩展列表中看不到 "RenderDoc MCP Bridge"

**解决方案**:
1. 检查扩展是否安装到正确位置：
   ```
   %APPDATA%\qrenderdoc\extensions\renderdoc_mcp_bridge\
   ```
2. 确认 `__init__.py`、`socket_server.py`、`request_handler.py`、`renderdoc_facade.py` 存在
3. 检查 RenderDoc 日志

### 问题 2: PySide2 导入失败
**症状**: `[MCP Bridge] PySide not available, using pure Python threading`

**解决方案**:
这是**正常行为**。从 v2.0.1 开始，扩展会自动检测 PySide2 可用性：
- 如果 PySide2 可用：使用 QTimer 轮询（更精确，与 UI 线程集成）
- 如果 PySide2 不可用：使用 threading.Thread 轮询（独立后台线程）

看到这个消息表示扩展正在使用**纯 Python threading 模式**，功能完全正常。

如果你想使用 PySide2 模式：
1. 确认你的 RenderDoc 1.17 构建包含完整的 PySide2
2. 检查 PySide2 模块是否被复制到输出目录：
   ```
   D:\CodeProjects\renderdoc_J_inlineHook\x64\Release\PySide2\
   ```
3. 重新构建 RenderDoc，确保 PySide2 模块被正确构建

### 问题 3: MCP 服务器连接超时
**症状**: `BridgeHandshakeTimeoutError: Request timed out`

**解决方案**:
1. 确认 RenderDoc 已启动且扩展已启用
2. 检查 IPC 目录是否存在：
   ```
   %TEMP%\renderdoc_mcp\
   ```
3. 确认没有其他进程占用 IPC 文件
4. 增加超时时间：
   ```bash
   set RENDERDOC_BRIDGE_TIMEOUT_SECONDS=60
   ```

### 问题 4: bdcam_qrenderdoc.pyd 无法导入
**症状**: 扩展加载时崩溃或报错

**解决方案**:
1. 确认 `bdcam_qrenderdoc.pyd` 在你的 Python 路径中
2. 检查依赖的 DLL 文件是否存在：
   - `python36.dll`
   - `Qt5Core.dll`
   - `Qt5Gui.dll`
   - `d3dcompiler_47.dll`
3. 使用 `test_extensions.py` 测试：
   ```bash
   cd D:\CodeProjects\renderdoc_J_inlineHook\x64\Release
   python test_extensions.py
   ```

## 架构对比

```
┌─────────────────────────────────────────────────────────────┐
│                    修改后的架构 (1.17 支持)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Claude/AI Client (stdio)                                   │
│          │                                                  │
│          ▼                                                  │
│  MCP Server Process (Python 3.14 + mcp)                     │
│          │ 文件 IPC (轮询)                                   │
│          ▼                                                  │
│  RenderDoc 1.17 扩展                                         │
│      ├─ socket_server.py (纯 Python threading 轮询)          │
│      │   - 自动检测 PySide2，如果可用则使用 QTimer          │
│      │   - 无 PySide2 时使用 threading.Thread               │
│      │                                                      │
│      ├─ renderdoc_facade.py (使用 bdcam API)                 │
│      │   - 通过 CaptureContext 调用 RenderDoc 内部 API        │
│      │                                                      │
│      └─ services/ (业务逻辑层)                               │
│          - 无 PySide 依赖                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 关键修改说明

### PySide2 兼容性修复

原来的 `socket_server.py` 依赖 `QTimer` 进行文件轮询。由于你的 RenderDoc 1.17 构建中没有包含完整的 PySide2 模块，我们添加了**纯 Python threading 轮询模式**：

```python
# 自动检测模式
if PySide2 可用:
    使用 QTimer 轮询（更精确，与 UI 线程集成）
else:
    使用 threading.Thread 轮询（独立后台线程）
```

这确保了扩展在**有无 PySide2 的环境中都能工作**。

### Python 路径配置

在 `__init__.py` 中添加了路径配置，尝试在以下位置查找 PySide2：
- `D:\CodeProjects\renderdoc_J_inlineHook\qrenderdoc\3rdparty\pyside\x64\PySide2\`

如果 PySide2 被正确构建并放置在该路径，扩展将自动使用 QTimer 模式。

## 文件变更清单

1. `renderdoc_extension/extension.json` - 修改 minimum_renderdoc 为 1.17
2. `src/renderdoc_mcp/paths.py` - 添加 1.17 路径候选
3. `renderdoc_extension/socket_server.py` - 增强 PySide 导入兼容性

## 后续建议

1. **测试完整功能**: 打开一个 capture 文件，测试所有 MCP 工具
2. **日志记录**: 在 `socket_server.py` 中添加详细日志以便调试
3. **版本检测**: 在扩展启动时输出 RenderDoc 实际版本号
4. **Python 路径**: 如果需要，可以在 `__init__.py` 中添加 `sys.path` 配置

## 参考资源

- RenderDoc 1.17 Python API 文档：`D:\CodeProjects\renderdoc_J_inlineHook\docs\python_api\`
- 示例代码：`D:\CodeProjects\renderdoc_J_inlineHook\docs\python_api\examples\`
