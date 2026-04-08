## 1. Fix get_knowledge_store function

- [x] 1.1 Modify `get_knowledge_store` to store and return a mocked value when provided
- [x] 1.2 Ensure `get_knowledge_store` bypasses `_init_knowledge_base` when a mocked store is provided

## 2. Fix Test Mocking

- [x] 2.1 Update test fixture to use `set_mocked_store` function instead of patching
- [x] 2.2 Update test fixture to use `AsyncMock` for async method mocking

## 3. Fix graph node tag extraction

- [x] 3.1 No changes needed - original graph.py is correct

## 4. Verify fixes

- [x] 4.1 Run pytest to verify fixes
