## Why

The knowledge base module tests are failing (21 tests) due to several issues: CLI commands not properly mocking, async functions not being awaited, Pydantic validation errors, and graph metadata not including tags. This fix is needed to ensure the knowledge base module functions correctly and reliably.

## What Changes

- Fix `get_knowledge_store` function to properly return mocked values for testing
- Update CLI output messages to match test expectations
- Fix SearchResult test mock to provide proper Pydantic validation
- Fix graph tag extraction to handle Tag objects correctly
- Ensure async functions are properly awaited in CLI commands

## Capabilities

### New Capabilities

### Modified Capabilities

## Impact

Affected code:
- `nanobot/cli/commands.py`: CLI command implementation and `get_knowledge_store` function
- `nanobot/knowledge/graph.py`: Graph tag extraction logic
- `tests/knowledge/test_cli.py`: Test expectations (if needed)
- `tests/knowledge/test_graph.py`: Test expectations (if needed)
