# TOOLS MODULE KNOWLEDGE BASE

**Generated:** Sat Apr 04 2026
**Commit:** 4edbd9e
**Branch:** dev

## OVERVIEW
Agent tool implementations for nanobot. Tools extend the agent's capabilities with external functionality like web search, file operations, code execution, etc.

## STRUCTURE
```
./nanobot/agent/tools/
├── base.py            # BaseTool abstract class
├── websearch.py       # Web search tool implementation
├── file_tools.py      # File operation tools (read/write/edit)
├── code_tools.py      # Code execution and analysis tools
├── shell_tools.py     # Shell command execution tools
├── cron_tools.py      # Scheduled task tools
└── __init__.py
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add new agent tool | Create new file extending `BaseTool` from base.py | Follow existing tool patterns |
| Modify existing tool behavior | Corresponding tool file | e.g., `websearch.py` for search functionality |
| Update tool execution logic | `../tools.py` (parent directory) | Tool registry and execution orchestration |
| Add tool parameter validation | Tool implementation files | Use Pydantic models for parameter validation |

## CONVENTIONS
- All tools extend the abstract `BaseTool` class
- Required properties: `name`, `description`, `parameters`
- Required method: `run()` (async)
- All tool parameters use Pydantic models for validation
- Tool outputs must be serializable to JSON
- Error handling: raise ToolError for tool-specific failures

## ANTI-PATTERNS
- Never allow unfiltered shell command execution without proper sandboxing
- Don't expose sensitive system information in tool outputs
- Avoid long-running operations in tools without async support
- Don't modify system state without explicit user confirmation
- Never return raw binary data in tool responses
