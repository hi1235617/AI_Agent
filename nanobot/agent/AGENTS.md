# AGENT MODULE KNOWLEDGE BASE

**Generated:** Sat Apr 04 2026
**Commit:** 4edbd9e
**Branch:** dev

## OVERVIEW
Core agent runtime implementation for nanobot including loop logic, tool handling, context management, and memory systems.

## STRUCTURE
```
./nanobot/agent/
├── tools/             # Agent tool implementations
├── context.py         # Context management and prompt building
├── loop.py            # Main agent execution loop
├── memory.py          # Memory management and persistence
├── tools.py           # Tool registry and execution logic
└── __init__.py
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add new agent tool | `./tools/` | Implement tool interface in new file |
| Modify agent loop behavior | `loop.py` | Core execution flow logic |
| Update prompt context building | `context.py` | Prompt template and context management |
| Extend memory functionality | `memory.py` | Session and long-term memory handling |

## CONVENTIONS
- Tools follow the base tool interface with `name`, `description`, `parameters`, and `run()` method
- All tool execution is async/await
- Context is immutable once built for a turn
- Memory operations use Pydantic models for data validation

## ANTI-PATTERNS
- Never modify context after it's been passed to the LLM
- Avoid blocking operations in the main agent loop
- Don't hardcode prompt templates - use template system
- Don't store sensitive data in memory unencrypted
