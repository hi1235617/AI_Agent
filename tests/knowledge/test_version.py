import pytest
from nanobot.knowledge.version import VersionManager
from nanobot.knowledge.models import NoteCreate, NoteUpdate


@pytest.fixture
def temp_versions_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for version storage."""
    versions_dir = tmp_path / "versions"
    versions_dir.mkdir()
    return versions_dir


@pytest.fixture
async def version_manager(knowledge_store, temp_versions_dir):
    """Create a VersionManager instance for testing."""
    return VersionManager(store=knowledge_store, versions_dir=str(temp_versions_dir))


@pytest.mark.asyncio
async def test_save_version_on_note_update(knowledge_store, version_manager):
    """Test that a new version is saved automatically when a note is updated."""
    # Create initial note
    note = await knowledge_store.create_note(NoteCreate(
        title="Test Note",
        content="Initial content"
    ))
    
    # Update note - should create version 1
    update1 = NoteUpdate(content="Updated content v1")
    updated1 = await knowledge_store.update_note(note.id, update1)
    
    # Check that version exists
    versions = await version_manager.list_versions(note.id)
    assert len(versions) == 1
    assert versions[0].version_number == 1
    assert versions[0].title == "Test Note"
    assert versions[0].content == "Initial content"  # Version saves state before update
    
    # Update again - should create version 2
    update2 = NoteUpdate(content="Updated content v2")
    updated2 = await knowledge_store.update_note(note.id, update2)
    
    versions = await version_manager.list_versions(note.id)
    assert len(versions) == 2
    assert versions[0].version_number == 2  # Newest first
    assert versions[1].version_number == 1
    assert versions[0].content == "Updated content v1"
    assert versions[1].content == "Initial content"


@pytest.mark.asyncio
async def test_restore_version(knowledge_store, version_manager):
    """Test restoring a note to a previous version."""
    # Create note and multiple versions
    note = await knowledge_store.create_note(NoteCreate(
        title="Original Title",
        content="Version 0 content"
    ))
    
    # Version 1
    await knowledge_store.update_note(note.id, NoteUpdate(content="Version 1 content"))
    # Version 2
    await knowledge_store.update_note(note.id, NoteUpdate(title="Updated Title", content="Version 2 content"))
    
    # Current state
    current = await knowledge_store.get_note_by_id(note.id)
    assert current.title == "Updated Title"
    assert current.content == "Version 2 content"
    
    # Restore to version 1
    restored = await version_manager.restore_version(note.id, version_number=1, create_snapshot=True)
    
    # Check that note is restored
    assert restored.title == "Original Title"  # Title from version 1 time
    assert restored.content == "Version 1 content"
    
    # A new version should be created for the restore operation
    versions = await version_manager.list_versions(note.id)
    assert len(versions) == 3  # Original 2 + 1 restore snapshot
    assert versions[0].version_number == 3
    assert "Restore to version 1" in versions[0].change_description


@pytest.mark.asyncio
async def test_restore_version_without_snapshot(knowledge_store, version_manager):
    """Test restoring a version without creating a new snapshot."""
    note = await knowledge_store.create_note(NoteCreate(
        title="Test",
        content="v0"
    ))
    await knowledge_store.update_note(note.id, NoteUpdate(content="v1"))
    await knowledge_store.update_note(note.id, NoteUpdate(content="v2"))
    
    versions_before = await version_manager.list_versions(note.id)
    assert len(versions_before) == 2
    
    # Restore without snapshot
    restored = await version_manager.restore_version(note.id, version_number=1, create_snapshot=False)
    
    assert restored.content == "v1"
    
    # No new version created
    versions_after = await version_manager.list_versions(note.id)
    assert len(versions_after) == 2


@pytest.mark.asyncio
async def test_list_versions_pagination(knowledge_store, version_manager):
    """Test pagination for version listing."""
    note = await knowledge_store.create_note(NoteCreate(title="Test", content="v0"))
    
    # Create 15 versions
    for i in range(15):
        await knowledge_store.update_note(note.id, NoteUpdate(content=f"v{i+1}"))
    
    # List first page
    page1 = await version_manager.list_versions(note.id, limit=10)
    assert len(page1) == 10
    assert page1[0].version_number == 15  # Newest first
    assert page1[-1].version_number == 6
    
    # List second page
    page2 = await version_manager.list_versions(note.id, limit=10, offset=10)
    assert len(page2) == 5
    assert page2[0].version_number == 5
    assert page2[-1].version_number == 1


@pytest.mark.asyncio
async def test_get_version(knowledge_store, version_manager):
    """Test retrieving a specific version by number."""
    note = await knowledge_store.create_note(NoteCreate(title="Test", content="v0"))
    await knowledge_store.update_note(note.id, NoteUpdate(content="v1"))
    await knowledge_store.update_note(note.id, NoteUpdate(content="v2"))
    
    # Get specific version
    version1 = await version_manager.get_version(note.id, version_number=1)
    assert version1 is not None
    assert version1.content == "v0"
    
    version2 = await version_manager.get_version(note.id, version_number=2)
    assert version2 is not None
    assert version2.content == "v1"
    
    # Non-existent version
    version99 = await version_manager.get_version(note.id, version_number=99)
    assert version99 is None


@pytest.mark.asyncio
async def test_version_diff(knowledge_store, version_manager):
    """Test generating diff between two versions."""
    note = await knowledge_store.create_note(NoteCreate(
        title="Test Note",
        content="Line 1\nLine 2\nLine 3"
    ))
    
    # Update with changes
    await knowledge_store.update_note(note.id, NoteUpdate(
        content="Line 1\nModified Line 2\nLine 3\nNew Line 4"
    ))
    
    # Get diff between version 1 and 2
    diff = await version_manager.get_version_diff(note.id, version1=1, version2=2)
    
    # Diff should show the changes
    assert "Modified Line 2" in diff["added"]
    assert "Line 2" in diff["removed"]
    assert "New Line 4" in diff["added"]
    assert "Line 1" in diff["unchanged"]
    assert "Line 3" in diff["unchanged"]


@pytest.mark.asyncio
async def test_delete_version_history(knowledge_store, version_manager):
    """Test deleting version history for a note."""
    note = await knowledge_store.create_note(NoteCreate(title="Test", content="v0"))
    
    # Create 10 versions
    for i in range(10):
        await knowledge_store.update_note(note.id, NoteUpdate(content=f"v{i+1}"))
    
    versions_before = await version_manager.list_versions(note.id)
    assert len(versions_before) == 10
    
    # Delete all except latest 3
    await version_manager.delete_version_history(note.id, keep_latest=3)
    
    versions_after = await version_manager.list_versions(note.id)
    assert len(versions_after) == 3
    assert versions_after[0].version_number == 10  # Latest
    assert versions_after[1].version_number == 9
    assert versions_after[2].version_number == 8
    
    # Delete all versions
    await version_manager.delete_version_history(note.id, keep_latest=0)
    
    versions_after = await version_manager.list_versions(note.id)
    assert len(versions_after) == 0


@pytest.mark.asyncio
async def test_version_metadata(knowledge_store, version_manager):
    """Test that version metadata is correctly saved."""
    note = await knowledge_store.create_note(NoteCreate(title="Test", content="v0"))
    
    # Update with change message and author
    update = NoteUpdate(content="v1")
    await knowledge_store.update_note(
        note.id, 
        update,
        change_message="Fixed typo in content",
        author="test-user"
    )
    
    versions = await version_manager.list_versions(note.id)
    assert len(versions) == 1
    
    version = versions[0]
    assert version.change_description == "Fixed typo in content"
    assert version.author == "test-user"
    assert version.created_at is not None
    assert version.note_id == note.id


@pytest.mark.asyncio
async def test_version_storage_efficiency(knowledge_store, version_manager):
    """Test that versions are stored efficiently using diffs."""
    note = await knowledge_store.create_note(NoteCreate(
        title="Large Note",
        content="X" * 10000  # 10KB content
    ))
    
    # Create multiple versions with small changes
    for i in range(10):
        await knowledge_store.update_note(
            note.id, 
            NoteUpdate(content=f"{content[:-1]}{i}")  # Only change last character
        )
    
    versions = await version_manager.list_versions(note.id)
    assert len(versions) == 10
    
    # Total storage should be much less than 10 * 10KB because of diff storage
    # Check that versions are not storing full copies for small changes
    total_size = 0
    for version_file in Path(version_manager.versions_dir / note.id).glob("*"):
        total_size += version_file.stat().st_size
    
    # Should be less than 20KB (instead of 100KB for full copies)
    assert total_size < 20 * 1024


@pytest.mark.asyncio
async def test_restore_version_preserves_links(knowledge_store, version_manager):
    """Test that restoring a version preserves links correctly."""
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content=""))
    
    # Create note with link to note2
    note1 = await knowledge_store.create_note(NoteCreate(
        title="Note 1",
        content="Links to [[Note 2]]"
    ))
    
    # Verify link exists
    links = await knowledge_store.get_links_for_note(note1.id)
    assert len(links) == 1
    
    # Update note to remove link
    await knowledge_store.update_note(note1.id, NoteUpdate(
        content="No links here anymore"
    ))
    
    # Link should be gone
    links = await knowledge_store.get_links_for_note(note1.id)
    assert len(links) == 0
    
    # Restore to version 1
    await version_manager.restore_version(note1.id, version_number=1)
    
    # Link should be restored
    links = await knowledge_store.get_links_for_note(note1.id)
    assert len(links) == 1
    assert links[0].target_note_id == note2.id


@pytest.mark.asyncio
async def test_version_history_preserved_on_note_delete(knowledge_store, version_manager):
    """Test that version history is preserved when note is soft deleted."""
    note = await knowledge_store.create_note(NoteCreate(title="To Delete", content="v0"))
    await knowledge_store.update_note(note.id, NoteUpdate(content="v1"))
    
    versions_before = await version_manager.list_versions(note.id)
    assert len(versions_before) == 1
    
    # Soft delete note
    await knowledge_store.delete_note(note.id, soft_delete=True)
    
    # Version history should still exist
    versions_after = await version_manager.list_versions(note.id)
    assert len(versions_after) == 1
    
    # Restore note
    restored = await knowledge_store.restore_note(note.id)
    
    # Versions still there
    versions_after_restore = await version_manager.list_versions(restored.id)
    assert len(versions_after_restore) == 1


@pytest.mark.asyncio
async def test_max_version_limit(knowledge_store, version_manager):
    """Test that old versions are pruned when exceeding max version limit."""
    # Set max versions per note to 5
    version_manager.max_versions_per_note = 5
    
    note = await knowledge_store.create_note(NoteCreate(title="Test", content="v0"))
    
    # Create 10 versions
    for i in range(10):
        await knowledge_store.update_note(note.id, NoteUpdate(content=f"v{i+1}"))
    
    # Only last 5 versions should be kept
    versions = await version_manager.list_versions(note.id)
    assert len(versions) == 5
    assert versions[0].version_number == 10  # Newest
    assert versions[-1].version_number == 6  # Oldest kept


@pytest.mark.asyncio
async def test_version_restore_creates_proper_backlink(knowledge_store, version_manager):
    """Test that when restoring a version that links to another note, backlinks are properly created."""
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content=""))
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content="[[Note 2]]"))
    
    # Update to remove link
    await knowledge_store.update_note(note1.id, NoteUpdate(content="No link"))
    
    # Note2 has no backlinks now
    backlinks = await knowledge_store.get_links_for_note(note2.id, direction="incoming")
    assert len(backlinks) == 0
    
    # Restore version with link
    await version_manager.restore_version(note1.id, version_number=1)
    
    # Backlink should be recreated
    backlinks = await knowledge_store.get_links_for_note(note2.id, direction="incoming")
    assert len(backlinks) == 1
    assert backlinks[0].source_note_id == note1.id