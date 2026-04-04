import pytest
from nanobot.knowledge.models import NoteCreate, NoteUpdate


@pytest.mark.asyncio
async def test_store_initialization(knowledge_store):
    """Test that knowledge store initializes correctly with database schema."""
    # Check that tables exist
    async with knowledge_store._get_connection() as conn:
        tables = await conn.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [t['name'] for t in tables]
        
        assert 'notes' in table_names
        assert 'tags' in table_names
        assert 'note_tags' in table_names
        assert 'links' in table_names
        assert 'note_fts' in table_names


@pytest.mark.asyncio
async def test_create_note(knowledge_store):
    """Test creating a new note with basic properties."""
    note_create = NoteCreate(
        title="Test Note",
        content="This is a test note content",
        tags=["test", "example"]
    )
    
    note = await knowledge_store.create_note(note_create)
    
    assert note.title == "Test Note"
    assert note.content == "This is a test note content"
    assert len(note.tags) == 2
    assert "test" in [t.name for t in note.tags]
    assert "example" in [t.name for t in note.tags]
    assert note.id is not None
    assert note.created_at is not None
    assert note.updated_at is not None
    
    # Verify note exists in database
    retrieved = await knowledge_store.get_note_by_id(note.id)
    assert retrieved is not None
    assert retrieved.title == note.title
    assert retrieved.content == note.content


@pytest.mark.asyncio
async def test_create_note_duplicate_title(knowledge_store):
    """Test that notes can have duplicate titles but different IDs."""
    note1 = await knowledge_store.create_note(NoteCreate(title="Duplicate Title", content="Content 1"))
    note2 = await knowledge_store.create_note(NoteCreate(title="Duplicate Title", content="Content 2"))
    
    assert note1.id != note2.id
    assert note1.title == note2.title
    assert note1.content != note2.content


@pytest.mark.asyncio
async def test_get_note_by_title(knowledge_store):
    """Test retrieving note by title with case-insensitive matching."""
    await knowledge_store.create_note(NoteCreate(title="Test Note", content="Content"))
    
    # Exact match
    note = await knowledge_store.get_note_by_title("Test Note", case_sensitive=True)
    assert note is not None
    assert note.title == "Test Note"
    
    # Case-insensitive match
    note = await knowledge_store.get_note_by_title("test note", case_sensitive=False)
    assert note is not None
    assert note.title == "Test Note"
    
    # Non-existent note
    note = await knowledge_store.get_note_by_title("Non-existent", case_sensitive=False)
    assert note is None


@pytest.mark.asyncio
async def test_update_note(knowledge_store):
    """Test updating note content and metadata."""
    note = await knowledge_store.create_note(NoteCreate(
        title="Original Title",
        content="Original content",
        tags=["old-tag"]
    ))
    
    # Update content and title
    update = NoteUpdate(
        title="Updated Title",
        content="Updated content",
        tags=["new-tag"]
    )
    
    updated = await knowledge_store.update_note(note.id, update)
    
    assert updated.title == "Updated Title"
    assert updated.content == "Updated content"
    assert len(updated.tags) == 1
    assert "new-tag" in [t.name for t in updated.tags]
    assert updated.updated_at > note.updated_at
    
    # Partial update - only add tag
    update2 = NoteUpdate(
        add_tags=["additional-tag"]
    )
    
    updated2 = await knowledge_store.update_note(note.id, update2)
    assert updated2.title == "Updated Title"  # Unchanged
    assert len(updated2.tags) == 2
    assert "new-tag" in [t.name for t in updated2.tags]
    assert "additional-tag" in [t.name for t in updated2.tags]


@pytest.mark.asyncio
async def test_update_note_parses_links(knowledge_store):
    """Test that updating note content parses and creates bidirectional links."""
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content="Content 1"))
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content="Content 2"))
    
    # Update note1 to link to note2 using [[title]] syntax
    update = NoteUpdate(
        content=f"This links to [[{note2.title}]]"
    )
    
    await knowledge_store.update_note(note1.id, update)
    
    # Check that link was created
    links = await knowledge_store.get_links_for_note(note1.id, direction="outgoing")
    assert len(links) == 1
    assert links[0].target_note_id == note2.id
    
    # Check that backlink exists for note2
    backlinks = await knowledge_store.get_links_for_note(note2.id, direction="incoming")
    assert len(backlinks) == 1
    assert backlinks[0].source_note_id == note1.id


@pytest.mark.asyncio
async def test_delete_note_soft(knowledge_store):
    """Test soft deleting a note (preserves version history)."""
    note = await knowledge_store.create_note(NoteCreate(title="To Delete", content="Content"))
    
    # Soft delete
    await knowledge_store.delete_note(note.id, soft_delete=True)
    
    # Note should still exist but marked as deleted
    retrieved = await knowledge_store.get_note_by_id(note.id, include_deleted=True)
    assert retrieved is not None
    assert retrieved.deleted == True
    
    # Should not be returned in normal queries
    notes = await knowledge_store.list_notes()
    assert not any(n.id == note.id for n in notes)


@pytest.mark.asyncio
async def test_delete_note_hard(knowledge_store):
    """Test permanently deleting a note."""
    note = await knowledge_store.create_note(NoteCreate(title="To Delete Permanently", content="Content"))
    
    # Hard delete
    await knowledge_store.delete_note(note.id, soft_delete=False)
    
    # Note should be completely removed
    retrieved = await knowledge_store.get_note_by_id(note.id, include_deleted=True)
    assert retrieved is None


@pytest.mark.asyncio
async def test_list_notes_filter_by_tag(knowledge_store):
    """Test listing notes filtered by tags."""
    await knowledge_store.create_note(NoteCreate(title="Python Note", content="Python content", tags=["python", "code"]))
    await knowledge_store.create_note(NoteCreate(title="JS Note", content="JS content", tags=["javascript", "code"]))
    await knowledge_store.create_note(NoteCreate(title="Other Note", content="Other content", tags=["other"]))
    
    # Filter by single tag
    python_notes = await knowledge_store.list_notes(tag_filter=["python"])
    assert len(python_notes) == 1
    assert python_notes[0].title == "Python Note"
    
    # Filter by multiple tags (OR match)
    code_notes = await knowledge_store.list_notes(tag_filter=["python", "javascript"])
    assert len(code_notes) == 2
    
    # Filter by tag that doesn't exist
    no_notes = await knowledge_store.list_notes(tag_filter=["non-existent"])
    assert len(no_notes) == 0


@pytest.mark.asyncio
async def test_list_notes_pagination(knowledge_store):
    """Test pagination for note listing."""
    # Create 15 test notes
    for i in range(15):
        await knowledge_store.create_note(NoteCreate(title=f"Note {i}", content=f"Content {i}"))
    
    # First page
    page1 = await knowledge_store.list_notes(limit=10, offset=0)
    assert len(page1) == 10
    
    # Second page
    page2 = await knowledge_store.list_notes(limit=10, offset=10)
    assert len(page2) == 5


@pytest.mark.asyncio
async def test_tag_operations(knowledge_store):
    """Test tag creation, retrieval, and listing."""
    # Create tag
    tag = await knowledge_store.create_tag(name="test-tag", description="Test tag", color="#ff0000")
    
    assert tag.name == "test-tag"
    assert tag.description == "Test tag"
    assert tag.color == "#ff0000"
    
    # Get tag by name
    retrieved = await knowledge_store.get_tag_by_name("test-tag")
    assert retrieved is not None
    assert retrieved.id == tag.id
    
    # List tags
    tags = await knowledge_store.list_tags()
    assert len(tags) == 1
    assert tags[0].name == "test-tag"
    
    # List tags with prefix
    tags = await knowledge_store.list_tags(prefix="test")
    assert len(tags) == 1
    
    tags = await knowledge_store.list_tags(prefix="other")
    assert len(tags) == 0


@pytest.mark.asyncio
async def test_link_operations(knowledge_store):
    """Test creating and retrieving links between notes."""
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content="Content 1"))
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content="Content 2"))
    note3 = await knowledge_store.create_note(NoteCreate(title="Note 3", content="Content 3"))
    
    # Create link from note1 to note2
    await knowledge_store._create_link(note1.id, note2.id, "link text")
    
    # Get outgoing links from note1
    outgoing = await knowledge_store.get_links_for_note(note1.id, direction="outgoing")
    assert len(outgoing) == 1
    assert outgoing[0].target_note_id == note2.id
    assert outgoing[0].link_text == "link text"
    
    # Get incoming links to note2
    incoming = await knowledge_store.get_links_for_note(note2.id, direction="incoming")
    assert len(incoming) == 1
    assert incoming[0].source_note_id == note1.id
    
    # Get all links for note1 (both directions)
    all_links = await knowledge_store.get_links_for_note(note1.id, direction="both")
    assert len(all_links) == 1  # Only outgoing
    
    # Create link from note2 to note3
    await knowledge_store._create_link(note2.id, note3.id, "another link")
    
    # Now note2 has both incoming and outgoing links
    note2_links = await knowledge_store.get_links_for_note(note2.id, direction="both")
    assert len(note2_links) == 2


@pytest.mark.asyncio
async def test_create_note_auto_creates_tags(knowledge_store):
    """Test that creating a note with tags automatically creates tag entries if they don't exist."""
    # Tag doesn't exist yet
    tag = await knowledge_store.get_tag_by_name("new-tag")
    assert tag is None
    
    # Create note with new tag
    await knowledge_store.create_note(NoteCreate(
        title="Test Note",
        content="Content",
        tags=["new-tag", "existing-tag"]
    ))
    
    # Both tags should now exist
    tag1 = await knowledge_store.get_tag_by_name("new-tag")
    tag2 = await knowledge_store.get_tag_by_name("existing-tag")
    
    assert tag1 is not None
    assert tag2 is not None
    assert tag1.name == "new-tag"
    assert tag2.name == "existing-tag"


@pytest.mark.asyncio
async def test_note_content_parses_double_bracket_links(knowledge_store):
    """Test that [[link]] syntax in note content is automatically parsed into links."""
    target_note = await knowledge_store.create_note(NoteCreate(
        title="Target Note",
        content="Target content"
    ))
    
    # Create note with link to target using [[title]] syntax
    source_note = await knowledge_store.create_note(NoteCreate(
        title="Source Note",
        content=f"This links to [[{target_note.title}]] and [[Non-existent Note]]"
    ))
    
    # Check that link to existing note was created
    links = await knowledge_store.get_links_for_note(source_note.id, direction="outgoing")
    assert len(links) == 1
    assert links[0].target_note_id == target_note.id
    
    # Non-existent note should not create a link
    # (We don't create links to non-existent notes to avoid orphaned links)


@pytest.mark.asyncio
async def test_update_note_updates_links(knowledge_store):
    """Test that updating note content updates links accordingly."""
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content="Content 1"))
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content="Content 2"))
    note3 = await knowledge_store.create_note(NoteCreate(title="Note 3", content="Content 3"))
    
    # Initial note links to note2
    source = await knowledge_store.create_note(NoteCreate(
        title="Source",
        content=f"Links to [[{note2.title}]]"
    ))
    
    assert len(await knowledge_store.get_links_for_note(source.id)) == 1
    
    # Update to link to note3 instead
    await knowledge_store.update_note(source.id, NoteUpdate(
        content=f"Now links to [[{note3.title}]]"
    ))
    
    # Should now link to note3, not note2
    links = await knowledge_store.get_links_for_note(source.id)
    assert len(links) == 1
    assert links[0].target_note_id == note3.id
    
    # Backlink should be removed from note2
    note2_backlinks = await knowledge_store.get_links_for_note(note2.id, direction="incoming")
    assert len(note2_backlinks) == 0
    
    # Backlink should be added to note3
    note3_backlinks = await knowledge_store.get_links_for_note(note3.id, direction="incoming")
    assert len(note3_backlinks) == 1


@pytest.mark.asyncio
async def test_delete_note_removes_links(knowledge_store):
    """Test that deleting a note removes all links to and from it."""
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content="[[Note 2]]"))
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content="[[Note 1]]"))
    
    # Both notes have links
    assert len(await knowledge_store.get_links_for_note(note1.id)) == 1
    assert len(await knowledge_store.get_links_for_note(note2.id)) == 1
    
    # Delete note1
    await knowledge_store.delete_note(note1.id, soft_delete=False)
    
    # Note2 should no longer have incoming link
    note2_links = await knowledge_store.get_links_for_note(note2.id)
    assert len(note2_links) == 0


@pytest.mark.asyncio
async def test_note_creation_with_metadata(knowledge_store):
    """Test creating a note with custom metadata."""
    note = await knowledge_store.create_note(NoteCreate(
        title="Note with metadata",
        content="Content",
        metadata={"author": "test-user", "category": "documentation"}
    ))
    
    assert note.metadata == {"author": "test-user", "category": "documentation"}
    
    # Update metadata
    updated = await knowledge_store.update_note(note.id, NoteUpdate(
        metadata={"author": "new-user", "status": "draft"}
    ))
    
    # Metadata should be merged
    assert updated.metadata == {
        "author": "new-user",
        "category": "documentation",
        "status": "draft"
    }