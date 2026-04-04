# PROVIDERS MODULE KNOWLEDGE BASE

**Generated:** Sat Apr 04 2026
**Commit:** 4edbd9e
**Branch:** dev

## OVERVIEW
LLM provider integrations for nanobot. Uses LiteLLM as the base abstraction layer for multi-provider support.

## STRUCTURE
```
./nanobot/providers/
├── base.py            # BaseProvider abstract class
├── litellm_provider.py # LiteLLM-based provider implementation
├── openai_responses/  # OpenAI response handling utilities
└── __init__.py
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add new LLM provider | Extend `BaseProvider` or extend LiteLLM provider | LiteLLM supports most providers natively |
| Modify LLM request/response handling | `litellm_provider.py` | Core provider logic |
| Add provider-specific response parsing | `openai_responses/` directory | Provider-specific utility functions |
| Update cost calculation logic | Provider implementation files | Track token usage and costs |

## CONVENTIONS
- All providers extend the abstract `BaseProvider` class
- Required methods: `__init__`, `chat_completion`, `stream_chat_completion`
- Uses LiteLLM for standardizing request/response formats across providers
- All provider operations are async/await
- Token usage tracking is mandatory for all provider calls

## ANTI-PATTERNS
- Don't hardcode provider API endpoints or keys
- Avoid provider-specific logic in core agent code
- Never disable retry/backoff logic for provider calls
- Don't ignore rate limit headers from providers
