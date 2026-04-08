## Context

The knowledge base module has 21 failing tests due to several issues:
1. `get_knowledge_store` function always returns None, so test mocks don't work properly
2. CLI output messages don't match what tests expect
3. SearchResult test uses MagicMock objects which fail Pydantic validation
4. Graph node tags are empty - tags not extracted correctly from Note objects

## Goals / Non-Goals

**Goals:**
- Fix all 21 failing knowledge base tests
- Ensure CLI test mocking works correctly via `get_knowledge_store`
- Fix output messages to match test expectations
- Make SearchResult tests pass by properly mocking Pydantic models
- Fix graph node tag extraction to include tags in exports

**Non-Goals:**
- Rewrite the entire knowledge base module
- Change existing functionality beyond what's needed for tests

## Decisions

1. **Fix `get_knowledge_store` function**: Modify to allow setting a mocked store and returning it immediately, bypassing `_init_knowledge_base`
2. **Update CLI output messages**: Match what tests expect or update tests to match, whichever makes more sense
3. **Fix SearchResult test mock**: Use real Pydantic model instances instead of raw MagicMock objects
4. **Fix graph tag extraction**: Ensure tags are properly extracted from Note objects when building graph nodes

## Risks / Trade-offs

- Risk: Updating CLI messages might break existing user scripts → Mitigation: Keep existing functionality, just add/modify messages to match tests
- Risk: Over-mocking might hide real implementation issues → Mitigation: Keep tests focused on actual behavior

## Open Questions

None at this time - all changes can be made without further user input.
