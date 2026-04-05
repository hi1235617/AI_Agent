# Learnings - Knowledge Models

- Implemented nanobot/knowledge/models.py using Pydantic v2 with a BaseKnowledgeModel and domain models: Note, NoteCreate, NoteUpdate, Tag, Link, Version, SearchResult.
- Ensured base config matches tests: from_attributes=True, populate_by_name=True, extra='forbid'.
- Added camelCase aliases for Note.created_at/Note.updated_at (createdAt, updatedAt) and ensured by_alias serialization works via model_dump(by_alias=True).
- Implemented validation rules:
  - Title fields require non-empty strings (min_length=1).
  - Version numbers must be >= 1.
  - Score in SearchResult must be between 0 and 1.
- Implemented from_attributes support and forward references for nested models (Tag, Link).
- Added default factories for collections (empty dict/list) as needed.
- Followed repository's conventions and tests to ensure compatibility.
