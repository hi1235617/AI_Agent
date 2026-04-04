# TESTS MODULE KNOWLEDGE BASE

**Generated:** Sat Apr 04 2026
**Commit:** 4edbd9e
**Branch:** dev

## OVERVIEW
Test suite for nanobot, using pytest as the testing framework. Covers all core functionality including agent logic, channels, providers, CLI, and tools.

## STRUCTURE
```
./tests/
├── agent/             # Tests for agent module
├── channels/          # Tests for messaging channels
├── providers/         # Tests for LLM providers
├── cli/               # Tests for CLI commands
├── tools/             # Tests for agent tools
├── config/            # Tests for configuration handling
└── conftest.py        # Pytest fixtures and configuration
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add tests for agent functionality | `agent/` directory | Follow test_*.py naming convention |
| Add channel-specific tests | `channels/` directory | Test each channel implementation separately |
| Add provider tests | `providers/` directory | Mock external LLM APIs in tests |
| Add CLI tests | `cli/` directory | Use Typer's CliRunner for testing CLI commands |
| Add shared test fixtures | `conftest.py` | Reusable fixtures across test modules |

## CONVENTIONS
- Test files follow `test_*.py` naming convention
- Use pytest fixtures for test isolation and setup
- Async tests use pytest-asyncio with asyncio_mode = "auto"
- Mock external dependencies (LLM APIs, messaging platforms) in unit tests
- Use tmp_path fixture for temporary file system operations
- CLI tests use Typer's CliRunner for end-to-end command testing

## ANTI-PATTERNS
- Don't make real network calls in unit tests - always mock external services
- Avoid slow-running tests without explicit marking as integration tests
- Never hardcode secrets or API keys in test files
- Don't rely on local system state for test execution
- Avoid duplicate test logic - use fixtures and helper functions
