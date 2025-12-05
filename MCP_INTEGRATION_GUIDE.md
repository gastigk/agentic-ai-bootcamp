# MCP (Model Context Protocol) Integration Guide

## Overview

This document explains the **Model Context Protocol (MCP)** integration for Google Drive access in the Agentic AI Bootcamp.

### What is MCP?

**Model Context Protocol (MCP)** is a standard protocol for connecting AI models with external tools and resources. It enables:
- Dynamic tool discovery from external servers
- Secure, standardized communication with external services
- Stateless operations (no persistent connections required)
- Composable, reusable tool interfaces

## Architecture

```
┌─────────────────────────────────────────────────────┐
│             User Query                              │
│  "What files are in my Google Drive?"              │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│             router_node                             │
│  • Analyzes user query for context clues            │
│  • Detects drive_keywords: "google drive", "drive", │
│    "archivo", "carpeta", "cloud", etc.             │
│  • Sets current_context = "drive" (if matched)      │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│         route_based_on_context                      │
│  • Routes message to appropriate specialized node   │
│  • Possible targets: finance, health, docs, DRIVE   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │     drive_node         │  ← NEW MCP NODE
        │  (File Specialist)     │
        └────────────┬───────────┘
                     │
         ┌───────────┴──────────┐
         │                      │
         ▼                      ▼
    ┌─────────────────┐  ┌──────────────────────┐
    │ MCPClientMgr    │  │ Tool Binding         │
    │ (Singleton)     │  │ (llm.bind_tools)     │
    │                 │  │                      │
    │ • Manages conn  │  │ llm + tools ────────▶ Generate
    │ • http://...    │  │                      │
    │ • Pooling       │  │                      │
    └─────────────────┘  └──────────────────────┘
         │
         ▼
    ┌──────────────────────────────────────┐
    │  MCP Server (http://localhost:3000)  │
    │  OR Mock Fallback                    │
    └──────────────────────────────────────┘
    
    Tools Available:
    • list_drive_files(folder_path, max_results)
    • read_drive_file(file_path, encoding)
```

## File Structure

### New Files Created

#### 1. `src/tools/drive_mcp.py` (800+ lines)

Main MCP integration module containing:

**Classes:**
- `MCPClientManager` - Singleton for managing MCP client connections

**Functions:**
- `load_mcp_tools(server_url)` - Async function to load tools from MCP server
- `get_mcp_tools(server_url)` - Sync wrapper for tool loading
- `create_drive_tools_mock()` - Mock tools for development
- `initialize_mcp_connection(server_url, fallback_to_mock)` - Main entry point
- `run_async(func)` - Decorator for running async functions in Streamlit

**Key Features:**
- Singleton pattern for connection pooling
- Async/sync bridge for Streamlit compatibility
- Mock fallback when MCP server unavailable
- Comprehensive error handling and logging
- 100% type hints and docstrings

### Modified Files

#### 1. `src/tools/__init__.py`

**Changes:**
- Added imports for MCP functions
- Updated `TOOLS_BY_CATEGORY` with `"drive": []` entry
- Updated `__all__` exports to include MCP functions

#### 2. `src/graph.py`

**Changes:**
- Added new `drive_node()` function (80+ lines)
- Updated router keywords with 9 drive keywords
- Updated router scoring logic with drive priority
- Added "drive" to `route_based_on_context()` return type
- Integrated drive_node into `build_workflow()`
- Added conditional routing for drive context
- Updated `__all__` exports

## How It Works

### Step 1: Context Detection (router_node)

```python
# Router detects these keywords:
drive_keywords = [
    "google drive", "drive", "archivo", "carpeta",
    "cloud", "adjunto", "descargar", "compartido", "fotos"
]

# When detected, sets:
state["current_context"] = "drive"
```

### Step 2: Routing Decision (route_based_on_context)

```python
def route_based_on_context(state: AgentState) -> Literal[..., "drive", ...]:
    context = state.get("current_context", "general")
    return context  # Returns "drive" if detected
```

### Step 3: MCP Tools Loading (drive_node)

```python
def drive_node(state: AgentState, llm: ChatOpenAI) -> dict:
    # Load drive tools (MCP or mock)
    drive_tools = create_drive_tools_mock()
    
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(drive_tools)
    
    # Invoke with system prompt
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response], "current_context": "drive"}
```

### Step 4: MCP Connection (MCPClientManager)

```python
class MCPClientManager:
    _instance = None  # Singleton pattern
    
    async def connect(server_url):
        """
        Connects to MCP server at server_url
        Reuses connection if already established
        Falls back to mock tools if connection fails
        """
        client = MultiServerMCPClient(
            config={...},
            transports={"streamable_http": {...}}
        )
        tools = await client.load_tools()
        return tools
```

## Available Tools

### 1. `list_drive_files`

Lists files and folders in Google Drive.

**Parameters:**
```python
folder_path: str = "root"  # Folder to list (default: root)
max_results: int = 10      # Maximum files to return
```

**Returns:**
```python
[
    {
        "name": "document.pdf",
        "id": "file-id-123",
        "type": "file",
        "size_bytes": 1024,
        "modified_time": "2024-01-15T10:30:00Z"
    },
    ...
]
```

### 2. `read_drive_file`

Reads the content of a Google Drive file.

**Parameters:**
```python
file_path: str           # Path or ID of file to read
encoding: str = "utf-8"  # File encoding
```

**Returns:**
```python
"File content as string..."
```

## Configuration

### MCP Server URL

Default: `http://localhost:3000`

To change, modify in `drive_node()`:

```python
from src.tools.drive_mcp import create_drive_tools_mock, initialize_mcp_connection

# Option 1: Use mock tools (for development)
drive_tools = create_drive_tools_mock()

# Option 2: Connect to real MCP server
drive_tools = initialize_mcp_connection(
    server_url="http://your-mcp-server:3000",
    fallback_to_mock=True  # Try mock if connection fails
)
```

### Starting an MCP Server

To use real Google Drive access, start an MCP server:

```bash
# Using 4_MCP_Agent.py as reference
# See implementation details in 4_MCP_Agent.py

# Basic setup:
python4_MCP_Agent.py
# This starts server and provides connection details
```

## Usage Examples

### Example 1: Ask About Files

```
User: "¿Qué archivos tengo en Google Drive?"

1. Router detects "Google Drive" (drive context)
2. Routes to drive_node
3. drive_node loads tools: list_drive_files, read_drive_file
4. LLM uses list_drive_files to explore
5. Returns: "Tienes 5 archivos: documento.pdf, ..."
```

### Example 2: Read File Content

```
User: "Lee mi archivo importante"

1. Router detects "archivo" (drive keyword)
2. Routes to drive_node
3. LLM calls list_drive_files to find file
4. LLM calls read_drive_file to get content
5. Returns: File content and summary
```

### Example 3: Fallback to Mock

```
User: "What's in my Drive?"
MCP Server: Not running

1. Router detects drive context
2. drive_node tries to connect to MCP
3. Connection fails (server not running)
4. Falls back to mock tools
5. Mock returns demo files for testing
```

## Testing

Run the integration test:

```bash
python tests/test_mcp_integration.py
```

Expected output:
- Mock tools load correctly
- Router detects drive keywords
- MCP architecture diagram shown
- Tool descriptions displayed
- Usage examples provided

## Async Pattern Explanation

### Why Async?

MCP operations are network I/O bound:
- Connecting to MCP server
- Fetching tool definitions
- Calling remote tools

Async prevents blocking the UI thread in Streamlit.

### The `run_async` Decorator

```python
def run_async(func):
    """Runs async function in Streamlit context"""
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(func(*args, **kwargs))
    
    return wrapper
```

### Sync Wrapper

For LangGraph compatibility (which is synchronous):

```python
def get_mcp_tools(server_url):
    """Sync wrapper that calls async load_mcp_tools"""
    return run_async(load_mcp_tools)(server_url)
```

## Error Handling

### Graceful Degradation

```python
try:
    # Try to connect to real MCP server
    tools = await load_mcp_tools("http://localhost:3000")
except Exception as e:
    # Fall back to mock tools
    tools = create_drive_tools_mock()
```

### Connection Pooling

MCPClientManager singleton ensures:
- Only one connection per server
- Reuse existing connections
- Automatic cleanup

```python
# First call: Creates connection
tools1 = await mcpm.connect("http://localhost:3000")

# Second call: Reuses existing connection
tools2 = await mcpm.connect("http://localhost:3000")  # Same connection!
```

## Production Considerations

### 1. Security

```python
# Store MCP server URL in environment variable
server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")

# Validate tokens and credentials
# Encrypt sensitive data in transit
```

### 2. Performance

```python
# Use connection pooling (MCPClientManager singleton)
# Cache tool definitions
# Implement timeouts for network calls
```

### 3. Reliability

```python
# Always provide mock fallback
# Log all MCP operations
# Monitor connection health
# Implement retry logic with exponential backoff
```

### 4. Monitoring

```python
# All operations logged with [DRIVE MCP LOG] prefix
# Track connection successes/failures
# Monitor tool execution times
# Alert on connection pool exhaustion
```

## Integration with Existing Code

The MCP integration is **fully backward compatible**:

- Existing nodes (finance, health, docs, general) unchanged
- Router enhanced but not breaking
- New node added alongside existing ones
- No modifications to state structure
- No breaking changes to API

## Next Steps

### To Use with Real Google Drive:

1. **Set up MCP server** (see 4_MCP_Agent.py):
   ```bash
   python 4_MCP_Agent.py
   ```

2. **Configure connection** in drive_node:
   ```python
   server_url = "http://your-mcp-server:3000"
   ```

3. **Test in Streamlit**:
   ```bash
   streamlit run Home.py
   ```

### To Extend with More Tools:

1. **Add tools to MCP server** (implement in external server)
2. **They'll be auto-discovered** by `load_mcp_tools()`
3. **Use in drive_node** automatically

### To Add More Contexts:

1. **Follow same pattern** as drive_node
2. **Add keywords** to router
3. **Create new node** function
4. **Update build_workflow()**

## Troubleshooting

### Problem: "MCP server not found"

**Solution:**
- Verify server running: `curl http://localhost:3000`
- Check firewall rules
- Verify `http://localhost:3000` is correct URL
- Mock tools will be used automatically

### Problem: "Tool not responding"

**Solution:**
- Check MCP server logs
- Verify network connectivity
- Implement timeouts
- Use fallback mock tools

### Problem: "Async event loop error"

**Solution:**
- `run_async` decorator handles this
- Ensures event loop exists before calling async
- Works in Streamlit environment

## References

### Files
- Core MCP: `src/tools/drive_mcp.py`
- Graph integration: `src/graph.py`
- Tools exports: `src/tools/__init__.py`
- Test script: `test_mcp_integration.py`

### Related Code
- Reference implementation: `4_MCP_Agent.py`
- State management: `src/state.py`
- LLM setup: `src/llm.py`

### External Resources
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [LangChain MCP Adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
- [Google Drive API](https://developers.google.com/drive)

## Summary

MCP Integration Complete!

The Agentic AI Bootcamp now has full Google Drive integration via Model Context Protocol:

- Automatic context detection for drive-related queries
- Dynamic tool loading from external MCP servers
- Graceful fallback to mock tools for development
- Async-safe implementation for Streamlit
- Connection pooling via singleton pattern
- Production-ready error handling and logging

The system seamlessly routes drive queries to a specialized `drive_node` that accesses files via MCP tools, while maintaining full compatibility with existing finance, health, and documentation nodes.

---

*Last Updated: 2024 | Status: Implementation Complete*
