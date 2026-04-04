import pytest
from datetime import datetime
from pydantic import ValidationError
from nanobot.knowledge.models import (
    BaseKnowledgeModel,
    Note,
    NoteCreate,
    NoteUpdate,
    Tag,
    Link,
    Version,
    SearchResult
)


def test_base_model_config():
    """Test base model configuration."""
    # Base model should allow from_attributes and populate_by_name
    assert BaseKnowledgeModel.model_config["from_attributes"] == True
    assert BaseKnowledgeModel.model_config["populate_by_name"] == True
    assert BaseKnowledgeModel.model_config["extra"] == "forbid"


def test_note_create_model_validation():
    """Test NoteCreate model validation rules."""
    # Valid note creation
    note_create = NoteCreate(
        title="Valid Title",
        content="Valid content",
        tags=["tag1", "tag2"],
        metadata={"key": "value"}
    )
    assert note_create.title == "Valid Title"
    assert note_create.content == "Valid content"
    assert note_create.tags == ["tag1", "tag2"]
    assert note_create.metadata == {"key": "value"}
    
    # Title is required
    with pytest.raises(ValidationError):
        NoteCreate(content="Missing title")
    
    # Title cannot be empty
    with pytest.raises(ValidationError):
        NoteCreate(title="", content="Empty title")
    
    # Title minimum length is 1
    with pytest.raises(ValidationError):
        NoteCreate(title="a" * 0, content="Content")
    
    # Content is optional, defaults to empty string
    note_create = NoteCreate(title="Title")
    assert note_create.content == ""
    
    # Tags are optional, defaults to None
    note_create = NoteCreate(title="Title", content="Content")
    assert note_create.tags is None
    
    # Metadata is optional, defaults to None
    note_create = NoteCreate(title="Title", content="Content")
    assert note_create.metadata is None


def test_note_update_model_validation():
    """Test NoteUpdate model validation rules."""
    # All fields are optional in update
    note_update = NoteUpdate()
    assert note_update.title is None
    assert note_update.content is None
    assert note_update.tags is None
    assert note_update.metadata is None
    
    # Partial update is allowed
    note_update = NoteUpdate(title="New Title")
    assert note_update.title == "New Title"
    assert note_update.content is None
    
    # Title min length validation if provided
    with pytest.raises(ValidationError):
        NoteUpdate(title="")
    
    # add_tags and remove_tags fields
    note_update = NoteUpdate(
        add_tags=["new-tag"],
        remove_tags=["old-tag"],
        change_message="Updated tags",
        author="test-user"
    )
    assert note_update.add_tags == ["new-tag"]
    assert note_update.remove_tags == ["old-tag"]
    assert note_update.change_message == "Updated tags"
    assert note_update.author == "test-user"


def test_note_model_validation():
    """Test Note model validation rules."""
    now = datetime.now()
    
    # Valid note
    note = Note(
        id="note-123",
        title="Test Note",
        content="Test content",
        created_at=now,
        updated_at=now,
        tags=[],
        links=[],
        backlinks=[]
    )
    
    assert note.id == "note-123"
    assert note.title == "Test Note"
    assert note.content == "Test content"
    assert note.created_at == now
    assert note.updated_at == now
    assert note.tags == []
    assert note.links == []
    assert note.backlinks == []
    
    # Missing required fields
    with pytest.raises(ValidationError):
        Note(
            # Missing id
            title="Test Note",
            content="Test content",
            created_at=now,
            updated_at=now
        )
    
    with pytest.raises(ValidationError):
        Note(
            id="note-123",
            # Missing title
            content="Test content",
            created_at=now,
            updated_at=now
        )
    
    # Default values for optional fields
    note = Note(
        id="note-123",
        title="Test Note",
        content="Test content",
        created_at=now,
        updated_at=now
    )
    assert note.metadata == {}  # metadata defaults to empty dict
    assert note.tags == []  # tags defaults to empty list
    assert note.links == []  # links defaults to empty list
    assert note.backlinks == []  # backlinks defaults to empty list


def test_tag_model_validation():
    """Test Tag model validation rules."""
    now = datetime.now()
    
    # Valid tag
    tag = Tag(
        id="tag-123",
        name="test/tag",
        description="Test tag",
        color="#ff0000",
        created_at=now,
        note_count=5
    )
    
    assert tag.id == "tag-123"
    assert tag.name == "test/tag"
    assert tag.description == "Test tag"
    assert tag.color == "#ff0000"
    assert tag.created_at == now
    assert tag.note_count == 5
    
    # Missing required fields
    with pytest.raises(ValidationError):
        Tag(
            # Missing id
            name="test/tag",
            created_at=now
        )
    
    with pytest.raises(ValidationError):
        Tag(
            id="tag-123",
            # Missing name
            created_at=now
        )
    
    with pytest.raises(ValidationError):
        Tag(
            id="tag-123",
            name="test/tag",
            # Missing created_at
        )
    
    # Optional fields default to None
    tag = Tag(
        id="tag-123",
        name="test/tag",
        created_at=now
    )
    assert tag.description is None
    assert tag.color is None
    assert tag.note_count is None
    
    # Color format validation
    # TODO: Add color format validation if implemented
    # with pytest.raises(ValidationError):
    #     Tag(id="tag-123", name="test", created_at=now, color="invalid-color")


def test_link_model_validation():
    """Test Link model validation rules."""
    now = datetime.now()
    
    # Valid link
    link = Link(
        id="link-123",
        source_note_id="note-1",
        target_note_id="note-2",
        link_text="[[Note 2]]",
        created_at=now
    )
    
    assert link.id == "link-123"
    assert link.source_note_id == "note-1"
    assert link.target_note_id == "note-2"
    assert link.link_text == "[[Note 2]]"
    assert link.created_at == now
    
    # Missing required fields
    with pytest.raises(ValidationError):
        Link(
            # Missing id
            source_note_id="note-1",
            target_note_id="note-2",
            link_text="link",
            created_at=now
        )
    
    with pytest.raises(ValidationError):
        Link(
            id="link-123",
            # Missing source_note_id
            target_note_id="note-2",
            link_text="link",
            created_at=now
        )


def test_version_model_validation():
    """Test Version model validation rules."""
    now = datetime.now()
    
    # Valid version
    version = Version(
        id="version-123",
        note_id="note-123",
        version_number=1,
        title="Version 1",
        content="Version content",
        created_at=now
    )
    
    assert version.id == "version-123"
    assert version.note_id == "note-123"
    assert version.version_number == 1
    assert version.title == "Version 1"
    assert version.content == "Version content"
    assert version.created_at == now
    
    # Missing required fields
    with pytest.raises(ValidationError):
        Version(
            # Missing id
            note_id="note-123",
            version_number=1,
            title="Version 1",
            content="Content",
            created_at=now
        )
    
    with pytest.raises(ValidationError):
        Version(
            id="version-123",
            note_id="note-123",
            # Missing version_number
            title="Version 1",
            content="Content",
            created_at=now
        )
    
    # Optional fields
    version = Version(
        id="version-123",
        note_id="note-123",
        version_number=1,
        title="Version 1",
        content="Content",
        created_at=now,
        change_description="Changed content",
        author="test-user"
    )
    assert version.change_description == "Changed content"
    assert version.author == "test-user"


def test_search_result_model_validation():
    """Test SearchResult model validation rules."""
    now = datetime.now()
    note = Note(
        id="note-123",
        title="Test Note",
        content="Test content",
        created_at=now,
        updated_at=now
    )
    
    # Valid search result
    search_result = SearchResult(
        note=note,
        score=0.85,
        match_highlights=["content matches"],
        match_type="fulltext"
    )
    
    assert search_result.note == note
    assert search_result.score == 0.85
    assert search_result.match_highlights == ["content matches"]
    assert search_result.match_type == "fulltext"
    
    # Missing required fields
    with pytest.raises(ValidationError):
        SearchResult(
            # Missing note
            score=0.85,
            match_type="fulltext"
        )
    
    with pytest.raises(ValidationError):
        SearchResult(
            note=note,
            # Missing score
            match_type="fulltext"
        )
    
    with pytest.raises(ValidationError):
        SearchResult(
            note=note,
            score=0.85,
            # Missing match_type
        )
    
    # Score must be between 0 and 1
    with pytest.raises(ValidationError):
        SearchResult(
            note=note,
            score=1.5,  # Too high
            match_type="fulltext"
        )
    
    with pytest.raises(ValidationError):
        SearchResult(
            note=note,
            score=-0.1,  # Too low
            match_type="fulltext"
        )
    
    # Default values
    search_result = SearchResult(
        note=note,
        score=0.85,
        match_type="fulltext"
    )
    assert search_result.match_highlights == []  # Defaults to empty list


def test_model_serialization_deserialization():
    """Test that models can be serialized to and deserialized from JSON/dict."""
    now = datetime.now()
    
    # Test Note serialization
    note = Note(
        id="note-123",
        title="Test Note",
        content="Test content",
        created_at=now,
        updated_at=now
    )
    
    # To dict
    note_dict = note.model_dump()
    assert note_dict["id"] == "note-123"
    assert note_dict["title"] == "Test Note"
    assert note_dict["content"] == "Test content"
    assert "created_at" in note_dict
    assert "updated_at" in note_dict
    
    # From dict
    note_from_dict = Note.model_validate(note_dict)
    assert note_from_dict.id == note.id
    assert note_from_dict.title == note.title
    assert note_from_dict.content == note.content
    assert note_from_dict.created_at == note.created_at
    assert note_from_dict.updated_at == note.updated_at
    
    # To JSON
    note_json = note.model_dump_json()
    assert "note-123" in note_json
    assert "Test Note" in note_json
    
    # From JSON
    note_from_json = Note.model_validate_json(note_json)
    assert note_from_json.id == note.id
    assert note_from_json.title == note.title


def test_model_extra_fields_forbidden():
    """Test that extra fields are forbidden in models."""
    now = datetime.now()
    
    # Extra fields should raise validation error
    with pytest.raises(ValidationError):
        Note(
            id="note-123",
            title="Test Note",
            content="Test content",
            created_at=now,
            updated_at=now,
            extra_field="not allowed"  # Extra field
        )
    
    with pytest.raises(ValidationError):
        NoteCreate(
            title="Test",
            content="Content",
            extra_field="not allowed"
        )


def test_note_create_partial_model():
    """Test partial model updates with exclude_unset."""
    note_update = NoteUpdate(title="New Title")
    
    # Only set fields should be included in dump
    dump = note_update.model_dump(exclude_unset=True)
    assert dump == {"title": "New Title"}
    assert "content" not in dump
    assert "tags" not in dump
    
    # Full dump includes None fields
    full_dump = note_update.model_dump()
    assert full_dump["title"] == "New Title"
    assert full_dump["content"] is None
    assert full_dump["tags"] is None


def test_tag_hierarchical_name_validation():
    """Test that hierarchical tag names are allowed."""
    now = datetime.now()
    
    # Hierarchical tags should be allowed
    tag = Tag(
        id="tag-1",
        name="projects/nanobot/knowledge-base",
        created_at=now
    )
    assert tag.name == "projects/nanobot/knowledge-base"
    
    # Tags with spaces should be allowed
    tag = Tag(
        id="tag-2",
        name="test tag with spaces",
        created_at=now
    )
    assert tag.name == "test tag with spaces"
    
    # Empty tag name not allowed
    with pytest.raises(ValidationError):
        Tag(id="tag-3", name="", created_at=now)


def test_version_number_validation():
    """Test that version numbers are positive integers."""
    now = datetime.now()
    
    # Version number must be positive
    with pytest.raises(ValidationError):
        Version(
            id="version-1",
            note_id="note-1",
            version_number=0,  # Invalid
            title="Version 0",
            content="Content",
            created_at=now
        )
    
    with pytest.raises(ValidationError):
        Version(
            id="version-1",
            note_id="note-1",
            version_number=-1,  # Invalid
            title="Version -1",
            content="Content",
            created_at=now
        )
    
    # Positive integers are allowed
    version = Version(
        id="version-1",
        note_id="note-1",
        version_number=1,
        title="Version 1",
        content="Content",
        created_at=now
    )
    assert version.version_number == 1
    
    version = Version(
        id="version-100",
        note_id="note-1",
        version_number=100,
        title="Version 100",
        content="Content",
        created_at=now
    )
    assert version.version_number == 100


def test_model_field_aliases():
    """Test that model fields support aliases (camelCase)."""
    now = datetime.now()
    
    # Test with camelCase input
    note_data = {
        "id": "note-123",
        "title": "Test Note",
        "content": "Test content",
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat()
    }
    
    # Should be able to parse camelCase fields
    note = Note.model_validate(note_data, from_attributes=True)
    assert note.created_at == now
    assert note.updated_at == now
    
    # Serialize to camelCase
    camel_case_dump = note.model_dump(by_alias=True)
    assert "createdAt" in camel_case_dump
    assert "updatedAt" in camel_case_dump
    assert "created_at" not in camel_case_dump
    assert "updated_at" not in camel_case_dump