import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock, AsyncMock
from nanobot.cli.commands import app


runner = CliRunner()


@pytest.fixture
def mock_knowledge_store():
    """Mock knowledge store for CLI tests."""
    from nanobot.cli.commands import set_mocked_store
    store = AsyncMock()
    set_mocked_store(store)
    yield store
    set_mocked_store(None)


@pytest.fixture
def mock_note():
    """Mock note object."""
    note = MagicMock()
    note.id = "test-note-id"
    note.title = "Test Note"
    note.content = "Test content"
    note.created_at = "2026-04-04T12:00:00"
    note.updated_at = "2026-04-04T12:00:00"
    note.tags = [MagicMock(name="tag1"), MagicMock(name="tag2")]
    return note


def test_kb_create_command(mock_knowledge_store, mock_note):
    """Test kb create command."""
    mock_knowledge_store.create_note.return_value = mock_note
    
    result = runner.invoke(
        app, 
        ["kb", "create", "Test Note", "--content", "Test content", "--tags", "tag1", "--tags", "tag2"]
    )
    
    assert result.exit_code == 0
    assert "Note created successfully" in result.stdout
    assert "test-note-id" in result.stdout
    assert "Test Note" in result.stdout
    
    # Verify create_note was called with correct parameters
    mock_knowledge_store.create_note.assert_called_once()
    args = mock_knowledge_store.create_note.call_args[0][0]
    assert args.title == "Test Note"
    assert args.content == "Test content"
    assert args.tags == ["tag1", "tag2"]


def test_kb_create_command_opens_editor(mock_knowledge_store, mock_note):
    """Test kb create command opens editor when no content is provided."""
    mock_knowledge_store.create_note.return_value = mock_note
    
    with patch('nanobot.cli.commands.open_editor') as mock_editor:
        mock_editor.return_value = "Editor content"
        
        result = runner.invoke(
            app, 
            ["kb", "create", "Test Note"],
            input="\n"  # Simulate user pressing enter to open editor
        )
        
        assert result.exit_code == 0
        mock_editor.assert_called_once()
        assert mock_knowledge_store.create_note.call_args[0][0].content == "Editor content"


def test_kb_list_command(mock_knowledge_store, mock_note):
    """Test kb list command."""
    mock_knowledge_store.list_notes.return_value = [mock_note]
    
    result = runner.invoke(app, ["kb", "list"])
    
    assert result.exit_code == 0
    assert "Test Note" in result.stdout
    assert "tag1, tag2" in result.stdout
    
    # With tag filter
    result = runner.invoke(app, ["kb", "list", "--tags", "tag1", "--tags", "tag2"])
    assert result.exit_code == 0
    mock_knowledge_store.list_notes.assert_called_with(tag_filter=["tag1", "tag2"], limit=50, offset=0)
    
    # With pagination
    result = runner.invoke(app, ["kb", "list", "--limit", "10", "--offset", "20"])
    assert result.exit_code == 0
    mock_knowledge_store.list_notes.assert_called_with(tag_filter=None, limit=10, offset=20)
    
    # With sort
    result = runner.invoke(app, ["kb", "list", "--sort", "created", "--reverse"])
    assert result.exit_code == 0
    mock_knowledge_store.list_notes.assert_called_with(tag_filter=None, limit=50, offset=0, order_by="created", order_direction="desc")


def test_kb_show_command(mock_knowledge_store, mock_note):
    """Test kb show command."""
    mock_knowledge_store.get_note_by_id.return_value = mock_note
    mock_knowledge_store.get_note_by_title.return_value = mock_note
    
    # By ID
    result = runner.invoke(app, ["kb", "show", "test-note-id"])
    assert result.exit_code == 0
    assert "Test Note" in result.stdout
    assert "Test content" in result.stdout
    mock_knowledge_store.get_note_by_id.assert_called_with("test-note-id", include_relations=True)
    
    # By title
    result = runner.invoke(app, ["kb", "show", "Test Note"])
    assert result.exit_code == 0
    mock_knowledge_store.get_note_by_title.assert_called_with("Test Note", case_sensitive=False)
    
    # Specific version
    with patch('nanobot.knowledge.version.VersionManager') as mock_vm:
        mock_version = MagicMock()
        mock_version.content = "Version 1 content"
        mock_vm.return_value.get_version.return_value = mock_version
        
        result = runner.invoke(app, ["kb", "show", "test-note-id", "--version", "1"])
        assert result.exit_code == 0
        assert "Version 1 content" in result.stdout


def test_kb_show_note_not_found(mock_knowledge_store):
    """Test kb show command with non-existent note."""
    mock_knowledge_store.get_note_by_id.return_value = None
    mock_knowledge_store.get_note_by_title.return_value = None
    
    result = runner.invoke(app, ["kb", "show", "non-existent-id"])
    assert result.exit_code != 0
    assert "Note not found" in result.stdout


def test_kb_edit_command(mock_knowledge_store, mock_note):
    """Test kb edit command."""
    mock_knowledge_store.get_note_by_id.return_value = mock_note
    mock_knowledge_store.update_note.return_value = mock_note
    
    # Update content directly
    result = runner.invoke(
        app, 
        ["kb", "edit", "test-note-id", "--content", "New content", "--add-tags", "new-tag", "--message", "Updated content"]
    )
    
    assert result.exit_code == 0
    assert "Note updated successfully" in result.stdout
    mock_knowledge_store.update_note.assert_called_once()
    args = mock_knowledge_store.update_note.call_args[0]
    assert args[0] == "test-note-id"
    assert args[1].content == "New content"
    assert args[1].add_tags == ["new-tag"]
    assert args[2] == "Updated content"
    
    # Open editor when no content provided
    with patch('nanobot.cli.commands.open_editor') as mock_editor:
        mock_editor.return_value = "Editor updated content"
        
        result = runner.invoke(app, ["kb", "edit", "test-note-id"])
        assert result.exit_code == 0
        mock_editor.assert_called_once_with(mock_note.content)
        assert mock_knowledge_store.update_note.call_args[0][1].content == "Editor updated content"


def test_kb_delete_command(mock_knowledge_store, mock_note):
    """Test kb delete command."""
    mock_knowledge_store.get_note_by_id.return_value = mock_note
    
    # Soft delete with confirmation
    result = runner.invoke(app, ["kb", "delete", "test-note-id"], input="y\n")
    assert result.exit_code == 0
    assert "Note deleted successfully" in result.stdout
    mock_knowledge_store.delete_note.assert_called_with("test-note-id", soft_delete=True)
    
    # Permanent delete without confirmation
    result = runner.invoke(app, ["kb", "delete", "test-note-id", "--permanent", "--yes"])
    assert result.exit_code == 0
    mock_knowledge_store.delete_note.assert_called_with("test-note-id", soft_delete=False)
    
    # Cancel deletion
    result = runner.invoke(app, ["kb", "delete", "test-note-id"], input="n\n")
    assert result.exit_code == 0
    assert "Deletion cancelled" in result.stdout


def test_kb_search_command(mock_knowledge_store, mock_note):
    """Test kb search command."""
    from nanobot.knowledge.models import SearchResult
    mock_result = SearchResult(
        note=mock_note,
        score=0.95,
        match_highlights=["Test content matches query"],
        match_type="fulltext"
    )
    mock_knowledge_store.search.fulltext_search.return_value = [mock_result]
    
    result = runner.invoke(app, ["kb", "search", "test query", "--tags", "tag1", "--include-content"])
    
    assert result.exit_code == 0
    assert "Test Note" in result.stdout
    assert "Score: 0.95" in result.stdout
    assert "Test content matches query" in result.stdout
    
    mock_knowledge_store.search.fulltext_search.assert_called_with(
        "test query",
        tag_filter=["tag1"],
        limit=20,
        min_score=0.7
    )


def test_kb_tags_command(mock_knowledge_store):
    """Test kb tags command."""
    mock_tag1 = MagicMock(name="tag1", note_count=5, color="#ff0000")
    mock_tag2 = MagicMock(name="tag2", note_count=3, color="#00ff00")
    mock_knowledge_store.list_tags.return_value = [mock_tag1, mock_tag2]
    
    result = runner.invoke(app, ["kb", "tags", "--sort", "count", "--reverse"])
    
    assert result.exit_code == 0
    assert "tag1" in result.stdout
    assert "tag2" in result.stdout
    assert "5" in result.stdout
    assert "3" in result.stdout
    
    mock_knowledge_store.list_tags.assert_called_with(prefix=None, include_count=True)
    
    # With search filter
    result = runner.invoke(app, ["kb", "tags", "--search", "tag1"])
    assert result.exit_code == 0
    mock_knowledge_store.list_tags.assert_called_with(prefix="tag1", include_count=True)


def test_kb_tag_rename_command(mock_knowledge_store):
    """Test kb tag-rename command."""
    mock_tag = MagicMock(name="old-tag")
    mock_knowledge_store.get_tag_by_name.return_value = mock_tag
    
    result = runner.invoke(app, ["kb", "tag-rename", "old-tag", "new-tag"], input="y\n")
    
    assert result.exit_code == 0
    assert "Tag renamed successfully" in result.stdout
    mock_knowledge_store.rename_tag.assert_called_with("old-tag", "new-tag")


def test_kb_tag_delete_command(mock_knowledge_store):
    """Test kb tag-delete command."""
    mock_tag = MagicMock(name="tag-to-delete", note_count=5)
    mock_knowledge_store.get_tag_by_name.return_value = mock_tag
    
    result = runner.invoke(app, ["kb", "tag-delete", "tag-to-delete"], input="y\n")
    
    assert result.exit_code == 0
    assert "Tag deleted successfully" in result.stdout
    mock_knowledge_store.delete_tag.assert_called_with("tag-to-delete")


def test_kb_versions_command(mock_knowledge_store):
    """Test kb versions command."""
    mock_version1 = MagicMock(
        version_number=2,
        created_at="2026-04-04T13:00:00",
        change_description="Second update",
        author="test-user"
    )
    mock_version2 = MagicMock(
        version_number=1,
        created_at="2026-04-04T12:00:00",
        change_description="First version",
        author="test-user"
    )
    with patch('nanobot.knowledge.version.VersionManager') as mock_vm:
        mock_vm.return_value.list_versions.return_value = [mock_version1, mock_version2]
        
        result = runner.invoke(app, ["kb", "versions", "test-note-id", "--limit", "10"])
        
        assert result.exit_code == 0
        assert "Version 2" in result.stdout
        assert "Version 1" in result.stdout
        assert "Second update" in result.stdout
        assert "First version" in result.stdout


def test_kb_restore_command(mock_knowledge_store, mock_note):
    """Test kb restore command."""
    mock_knowledge_store.get_note_by_id.return_value = mock_note
    
    with patch('nanobot.knowledge.version.VersionManager') as mock_vm:
        mock_restored_note = MagicMock()
        mock_restored_note.id = "test-note-id"
        mock_restored_note.title = "Restored Note"
        mock_vm.return_value.restore_version.return_value = mock_restored_note
        
        result = runner.invoke(app, ["kb", "restore", "test-note-id", "--version", "1"], input="y\n")
        
        assert result.exit_code == 0
        assert "Note restored successfully" in result.stdout
        mock_vm.return_value.restore_version.assert_called_with(
            "test-note-id",
            version_number=1,
            create_snapshot=True
        )


def test_kb_links_command(mock_knowledge_store):
    """Test kb links command."""
    mock_link1 = MagicMock(
        target_note_id="note-2-id",
        target_note_title="Note 2",
        link_text="[[Note 2]]",
        created_at="2026-04-04T12:00:00"
    )
    mock_link2 = MagicMock(
        source_note_id="note-3-id",
        source_note_title="Note 3",
        link_text="[[Test Note]]",
        created_at="2026-04-04T13:00:00"
    )
    mock_knowledge_store.get_links_for_note.return_value = (
        [mock_link1],  # Outgoing
        [mock_link2]   # Incoming
    )
    
    result = runner.invoke(app, ["kb", "links", "test-note-id", "--list"])
    
    assert result.exit_code == 0
    assert "Outgoing links" in result.stdout
    assert "Note 2" in result.stdout
    assert "Incoming links" in result.stdout
    assert "Note 3" in result.stdout
    
    # Add link
    result = runner.invoke(app, ["kb", "links", "test-note-id", "--add", "note-2-id"])
    assert result.exit_code == 0
    assert "Link added successfully" in result.stdout
    
    # Remove link
    result = runner.invoke(app, ["kb", "links", "test-note-id", "--remove", "note-2-id"])
    assert result.exit_code == 0
    assert "Link removed successfully" in result.stdout


def test_kb_graph_command(mock_knowledge_store):
    """Test kb graph command."""
    with patch('nanobot.knowledge.graph.KnowledgeGraph') as mock_graph:
        mock_export = {
            "nodes": [{"id": "note1", "label": "Note 1"}, {"id": "note2", "label": "Note 2"}],
            "edges": [{"from": "note1", "to": "note2"}]
        }
        mock_graph.return_value.export_graph.return_value = mock_export
        
        # Text format
        result = runner.invoke(app, ["kb", "graph", "test-note-id", "--depth", "2"])
        assert result.exit_code == 0
        assert "Note 1" in result.stdout
        assert "Note 2" in result.stdout
        
        # JSON format output to file
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["kb", "graph", "--format", "json", "--output", "graph.json"])
            assert result.exit_code == 0
            assert os.path.exists("graph.json")
            
        # DOT format
        mock_graph.return_value.export_graph.return_value = "digraph G { ... }"
        result = runner.invoke(app, ["kb", "graph", "--format", "dot"])
        assert result.exit_code == 0
        assert "digraph G" in result.stdout


def test_kb_import_command(mock_knowledge_store):
    """Test kb import command."""
    with patch('nanobot.knowledge.importers.MarkdownImporter') as mock_importer:
        mock_importer.return_value.import_notes.return_value = 5  # 5 notes imported
        
        with runner.isolated_filesystem():
            # Create test markdown file
            with open("test.md", "w") as f:
                f.write("# Test Note\n\nContent")
            
            result = runner.invoke(
                app, 
                ["kb", "import", "test.md", "--format", "markdown", "--tags", "imported"]
            )
            
            assert result.exit_code == 0
            assert "Successfully imported 5 notes" in result.stdout
            mock_importer.return_value.import_notes.assert_called_with(Path("test.md"), tags=["imported"])


def test_kb_export_command(mock_knowledge_store):
    """Test kb export command."""
    with patch('nanobot.knowledge.exporters.JsonExporter') as mock_exporter:
        mock_exporter.return_value.export.return_value = 10  # 10 notes exported
        
        with runner.isolated_filesystem():
            result = runner.invoke(
                app, 
                ["kb", "export", "export.json", "--format", "json", "--tags", "tag1", "--include-versions"]
            )
            
            assert result.exit_code == 0
            assert "Successfully exported 10 notes" in result.stdout
            assert os.path.exists("export.json")
            mock_exporter.return_value.export.assert_called_with(
                Path("export.json"),
                tag_filter=["tag1"],
                include_versions=True,
                include_deleted=False
            )


def test_kb_status_command(mock_knowledge_store):
    """Test kb status command."""
    mock_knowledge_store.get_stats.return_value = {
        "notes_count": 42,
        "tags_count": 15,
        "links_count": 78,
        "files_size": "1.2 MB",
        "db_size": "500 KB"
    }
    
    result = runner.invoke(app, ["kb", "status"])
    
    assert result.exit_code == 0
    assert "Knowledge Base Status" in result.stdout
    assert "Notes: 42" in result.stdout
    assert "Tags: 15" in result.stdout
    assert "Links: 78" in result.stdout
    assert "Total Size: 1.2 MB" in result.stdout


def test_kb_migrate_command(mock_knowledge_store):
    """Test kb migrate command."""
    with patch('nanobot.knowledge.migrations.MigrationManager') as mock_mm:
        mock_mm.return_value.run_migrations.return_value = 3  # 3 migrations applied
        
        result = runner.invoke(app, ["kb", "migrate"])
        assert result.exit_code == 0
        assert "Successfully applied 3 migrations" in result.stdout
        
        # Rollback
        result = runner.invoke(app, ["kb", "migrate", "--rollback", "1"])
        assert result.exit_code == 0
        assert "Rolled back to version 1" in result.stdout


def test_kb_command_feature_disabled():
    """Test that kb commands are not available when feature is disabled."""
    with patch('nanobot.config.load_config') as mock_load_config:
        mock_config = MagicMock()
        mock_config.knowledge_base.enabled = False
        mock_load_config.return_value = mock_config
        
        result = runner.invoke(app, ["kb", "list"])
        assert result.exit_code != 0
        assert "Knowledge base feature is disabled" in result.stdout