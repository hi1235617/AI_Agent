import pytest
from unittest.mock import MagicMock, patch
from nanobot.agent.tools.knowledge import (
    KnowledgeSearchTool,
    KnowledgeCreateTool,
    KnowledgeUpdateTool,
    KnowledgeGetTool
)


@pytest.fixture
def mock_knowledge_store():
    """Mock knowledge store for tool tests."""
    store = MagicMock()
    return store


@pytest.fixture
def mock_note():
    """Mock note object."""
    note = MagicMock()
    note.id = "test-note-id"
    note.title = "Test Note"
    note.content = "# Test Note\n\nThis is test content for the knowledge base."
    note.created_at = "2026-04-04T12:00:00"
    note.updated_at = "2026-04-04T12:00:00"
    note.tags = [MagicMock(name="python"), MagicMock(name="test")]
    note.links = []
    note.backlinks = []
    note.metadata = {}
    return note


@pytest.fixture
def mock_search_result(mock_note):
    """Mock search result object."""
    result = MagicMock()
    result.note = mock_note
    result.score = 0.95
    result.match_highlights = ["test content for the knowledge base"]
    result.match_type = "fulltext"
    return result


# ==================== KnowledgeSearchTool Tests ====================

@pytest.mark.asyncio
async def test_knowledge_search_tool_name_and_description(mock_knowledge_store):
    """Test tool name and description."""
    tool = KnowledgeSearchTool(store=mock_knowledge_store)
    
    assert tool.name == "knowledge_search"
    assert "搜索" in tool.description or "search" in tool.description.lower()


@pytest.mark.asyncio
async def test_knowledge_search_tool_parameters(mock_knowledge_store):
    """Test tool parameters schema."""
    tool = KnowledgeSearchTool(store=mock_knowledge_store)
    params = tool.parameters
    
    assert params["type"] == "object"
    assert "query" in params["properties"]
    assert "limit" in params["properties"]
    assert "search_type" in params["properties"]
    assert "query" in params["required"]


@pytest.mark.asyncio
async def test_knowledge_search_tool_fulltext_search(mock_knowledge_store, mock_search_result):
    """Test full-text search functionality."""
    mock_knowledge_store.search.fulltext_search.return_value = [mock_search_result]
    
    tool = KnowledgeSearchTool(store=mock_knowledge_store)
    result = await tool.execute(
        query="test content",
        limit=5,
        search_type="fulltext"
    )
    
    # Verify search was called correctly
    mock_knowledge_store.search.fulltext_search.assert_called_once_with(
        query="test content",
        limit=5,
        min_score=0.1
    )
    
    # Verify result format
    assert len(result) == 1
    assert result[0]["id"] == "test-note-id"
    assert result[0]["title"] == "Test Note"
    assert result[0]["score"] == 0.95
    assert "test content for the knowledge base" in result[0]["snippet"]


@pytest.mark.asyncio
async def test_knowledge_search_tool_tag_search(mock_knowledge_store, mock_search_result):
    """Test tag search functionality."""
    mock_knowledge_store.search.tag_search.return_value = [mock_search_result]
    
    tool = KnowledgeSearchTool(store=mock_knowledge_store)
    result = await tool.execute(
        query="python",
        search_type="tag",
        limit=10
    )
    
    mock_knowledge_store.search.tag_search.assert_called_once_with(
        tags=["python"],
        limit=10
    )
    
    assert len(result) == 1
    assert result[0]["title"] == "Test Note"


@pytest.mark.asyncio
async def test_knowledge_search_tool_semantic_search(mock_knowledge_store, mock_search_result):
    """Test semantic search functionality."""
    mock_knowledge_store.search.semantic_search.return_value = [mock_search_result]
    
    tool = KnowledgeSearchTool(store=mock_knowledge_store)
    result = await tool.execute(
        query="knowledge management",
        search_type="semantic",
        limit=5
    )
    
    mock_knowledge_store.search.semantic_search.assert_called_once_with(
        query="knowledge management",
        limit=5,
        min_similarity=0.7
    )
    
    assert len(result) == 1


@pytest.mark.asyncio
async def test_knowledge_search_tool_no_results(mock_knowledge_store):
    """Test search with no results."""
    mock_knowledge_store.search.fulltext_search.return_value = []
    
    tool = KnowledgeSearchTool(store=mock_knowledge_store)
    result = await tool.execute(query="nonexistent", limit=5)
    
    assert len(result) == 0
    assert "未找到相关笔记" in result or "No results found" in str(result)


@pytest.mark.asyncio
async def test_knowledge_search_tool_default_parameters(mock_knowledge_store, mock_search_result):
    """Test search with default parameters."""
    mock_knowledge_store.search.fulltext_search.return_value = [mock_search_result]
    
    tool = KnowledgeSearchTool(store=mock_knowledge_store)
    result = await tool.execute(query="test")
    
    # Should use default limit=10
    mock_knowledge_store.search.fulltext_search.assert_called_once_with(
        query="test",
        limit=10,
        min_score=0.1
    )


@pytest.mark.asyncio
async def test_knowledge_search_tool_validation(mock_knowledge_store):
    """Test parameter validation."""
    tool = KnowledgeSearchTool(store=mock_knowledge_store)
    
    # Query is required
    errors = tool.validate_params({})
    assert len(errors) > 0
    assert any("query" in err.lower() for err in errors)
    
    # Limit must be positive
    errors = tool.validate_params({"query": "test", "limit": -1})
    assert len(errors) > 0
    
    # Limit must be within range
    errors = tool.validate_params({"query": "test", "limit": 100})
    assert len(errors) > 0


# ==================== KnowledgeCreateTool Tests ====================

@pytest.mark.asyncio
async def test_knowledge_create_tool_name_and_description(mock_knowledge_store):
    """Test tool name and description."""
    tool = KnowledgeCreateTool(store=mock_knowledge_store)
    
    assert tool.name == "knowledge_create"
    assert "创建" in tool.description or "create" in tool.description.lower()


@pytest.mark.asyncio
async def test_knowledge_create_tool_parameters(mock_knowledge_store):
    """Test tool parameters schema."""
    tool = KnowledgeCreateTool(store=mock_knowledge_store)
    params = tool.parameters
    
    assert params["type"] == "object"
    assert "title" in params["properties"]
    assert "content" in params["properties"]
    assert "tags" in params["properties"]
    assert "title" in params["required"]
    assert "content" in params["required"]


@pytest.mark.asyncio
async def test_knowledge_create_tool_basic(mock_knowledge_store, mock_note):
    """Test basic note creation."""
    mock_knowledge_store.create_note.return_value = mock_note
    
    tool = KnowledgeCreateTool(store=mock_knowledge_store)
    result = await tool.execute(
        title="New Note",
        content="# New Note\n\nThis is new content.",
        tags=["new", "test"]
    )
    
    # Verify create_note was called correctly
    mock_knowledge_store.create_note.assert_called_once()
    args = mock_knowledge_store.create_note.call_args[0][0]
    assert args.title == "New Note"
    assert args.content == "# New Note\n\nThis is new content."
    assert args.tags == ["new", "test"]
    
    # Verify result format
    assert "id" in result
    assert result["id"] == "test-note-id"
    assert result["title"] == "New Note"
    assert "创建成功" in result["message"] or "created successfully" in result["message"].lower()


@pytest.mark.asyncio
async def test_knowledge_create_tool_minimal(mock_knowledge_store, mock_note):
    """Test note creation with minimal parameters."""
    mock_knowledge_store.create_note.return_value = mock_note
    
    tool = KnowledgeCreateTool(store=mock_knowledge_store)
    result = await tool.execute(
        title="Minimal Note",
        content=""
    )
    
    mock_knowledge_store.create_note.assert_called_once()
    args = mock_knowledge_store.create_note.call_args[0][0]
    assert args.title == "Minimal Note"
    assert args.content == ""
    assert args.tags is None


@pytest.mark.asyncio
async def test_knowledge_create_tool_validation(mock_knowledge_store):
    """Test parameter validation."""
    tool = KnowledgeCreateTool(store=mock_knowledge_store)
    
    # Title and content are required
    errors = tool.validate_params({})
    assert len(errors) > 0
    assert any("title" in err.lower() for err in errors)
    assert any("content" in err.lower() for err in errors)
    
    # Title cannot be empty
    errors = tool.validate_params({"title": "", "content": "test"})
    assert len(errors) > 0


# ==================== KnowledgeUpdateTool Tests ====================

@pytest.mark.asyncio
async def test_knowledge_update_tool_name_and_description(mock_knowledge_store):
    """Test tool name and description."""
    tool = KnowledgeUpdateTool(store=mock_knowledge_store)
    
    assert tool.name == "knowledge_update"
    assert "更新" in tool.description or "update" in tool.description.lower()


@pytest.mark.asyncio
async def test_knowledge_update_tool_parameters(mock_knowledge_store):
    """Test tool parameters schema."""
    tool = KnowledgeUpdateTool(store=mock_knowledge_store)
    params = tool.parameters
    
    assert params["type"] == "object"
    assert "note_id" in params["properties"]
    assert "title" in params["properties"]
    assert "content" in params["properties"]
    assert "add_tags" in params["properties"]
    assert "remove_tags" in params["properties"]
    assert "note_id" in params["required"]


@pytest.mark.asyncio
async def test_knowledge_update_tool_full_update(mock_knowledge_store, mock_note):
    """Test full note update."""
    mock_knowledge_store.get_note_by_id.return_value = mock_note
    mock_knowledge_store.update_note.return_value = mock_note
    
    tool = KnowledgeUpdateTool(store=mock_knowledge_store)
    result = await tool.execute(
        note_id="test-note-id",
        title="Updated Title",
        content="# Updated Content\n\nNew content here.",
        add_tags=["updated"],
        change_message="Updated title and content"
    )
    
    # Verify update_note was called correctly
    mock_knowledge_store.update_note.assert_called_once()
    args = mock_knowledge_store.update_note.call_args[0]
    assert args[0] == "test-note-id"
    assert args[1].title == "Updated Title"
    assert args[1].content == "# Updated Content\n\nNew content here."
    assert args[1].add_tags == ["updated"]
    assert args[2] == "Updated title and content"
    
    # Verify result format
    assert "id" in result
    assert result["id"] == "test-note-id"
    assert "更新成功" in result["message"] or "updated successfully" in result["message"].lower()


@pytest.mark.asyncio
async def test_knowledge_update_tool_partial_update(mock_knowledge_store, mock_note):
    """Test partial note update (only add tags)."""
    mock_knowledge_store.get_note_by_id.return_value = mock_note
    mock_knowledge_store.update_note.return_value = mock_note
    
    tool = KnowledgeUpdateTool(store=mock_knowledge_store)
    result = await tool.execute(
        note_id="test-note-id",
        add_tags=["new-tag"]
    )
    
    mock_knowledge_store.update_note.assert_called_once()
    args = mock_knowledge_store.update_note.call_args[0]
    assert args[0] == "test-note-id"
    assert args[1].title is None
    assert args[1].content is None
    assert args[1].add_tags == ["new-tag"]
    assert args[1].remove_tags is None


@pytest.mark.asyncio
async def test_knowledge_update_tool_remove_tags(mock_knowledge_store, mock_note):
    """Test removing tags from a note."""
    mock_knowledge_store.get_note_by_id.return_value = mock_note
    mock_knowledge_store.update_note.return_value = mock_note
    
    tool = KnowledgeUpdateTool(store=mock_knowledge_store)
    result = await tool.execute(
        note_id="test-note-id",
        remove_tags=["python"]
    )
    
    mock_knowledge_store.update_note.assert_called_once()
    args = mock_knowledge_store.update_note.call_args[0]
    assert args[1].remove_tags == ["python"]


@pytest.mark.asyncio
async def test_knowledge_update_tool_note_not_found(mock_knowledge_store):
    """Test updating a non-existent note."""
    mock_knowledge_store.get_note_by_id.return_value = None
    
    tool = KnowledgeUpdateTool(store=mock_knowledge_store)
    
    with pytest.raises(Exception) as exc_info:
        await tool.execute(note_id="non-existent-id", content="New content")
    
    assert "not found" in str(exc_info.value).lower() or "不存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_knowledge_update_tool_validation(mock_knowledge_store):
    """Test parameter validation."""
    tool = KnowledgeUpdateTool(store=mock_knowledge_store)
    
    # note_id is required
    errors = tool.validate_params({})
    assert len(errors) > 0
    assert any("note_id" in err.lower() for err in errors)


# ==================== KnowledgeGetTool Tests ====================

@pytest.mark.asyncio
async def test_knowledge_get_tool_name_and_description(mock_knowledge_store):
    """Test tool name and description."""
    tool = KnowledgeGetTool(store=mock_knowledge_store)
    
    assert tool.name == "knowledge_get"
    assert "获取" in tool.description or "get" in tool.description.lower() or "retrieve" in tool.description.lower()


@pytest.mark.asyncio
async def test_knowledge_get_tool_parameters(mock_knowledge_store):
    """Test tool parameters schema."""
    tool = KnowledgeGetTool(store=mock_knowledge_store)
    params = tool.parameters
    
    assert params["type"] == "object"
    assert "note_id" in params["properties"]
    assert "note_id" in params["required"]


@pytest.mark.asyncio
async def test_knowledge_get_tool_basic(mock_knowledge_store, mock_note):
    """Test getting a note by ID."""
    mock_knowledge_store.get_note_by_id.return_value = mock_note
    
    tool = KnowledgeGetTool(store=mock_knowledge_store)
    result = await tool.execute(note_id="test-note-id")
    
    mock_knowledge_store.get_note_by_id.assert_called_once_with(
        "test-note-id",
        include_relations=True
    )
    
    # Verify result format
    assert result["id"] == "test-note-id"
    assert result["title"] == "Test Note"
    assert result["content"] == "# Test Note\n\nThis is test content for the knowledge base."
    assert "tags" in result
    assert "python" in [t.name for t in result["tags"]]
    assert "test" in [t.name for t in result["tags"]]


@pytest.mark.asyncio
async def test_knowledge_get_tool_with_version(mock_knowledge_store, mock_note):
    """Test getting a specific version of a note."""
    mock_version = MagicMock()
    mock_version.content = "# Version 1 Content\n\nOld content."
    mock_version.title = "Test Note v1"
    mock_version.created_at = "2026-04-04T11:00:00"
    
    with patch('nanobot.knowledge.version.VersionManager') as mock_vm:
        mock_vm.return_value.get_version.return_value = mock_version
        
        tool = KnowledgeGetTool(store=mock_knowledge_store)
        result = await tool.execute(note_id="test-note-id", version=1)
        
        mock_vm.return_value.get_version.assert_called_once_with("test-note-id", version_number=1)
        
        assert result["content"] == "# Version 1 Content\n\nOld content."
        assert result["title"] == "Test Note v1"


@pytest.mark.asyncio
async def test_knowledge_get_tool_note_not_found(mock_knowledge_store):
    """Test getting a non-existent note."""
    mock_knowledge_store.get_note_by_id.return_value = None
    
    tool = KnowledgeGetTool(store=mock_knowledge_store)
    
    with pytest.raises(Exception) as exc_info:
        await tool.execute(note_id="non-existent-id")
    
    assert "not found" in str(exc_info.value).lower() or "不存在" in str(exc_info.value)


@pytest.mark.asyncio
async def test_knowledge_get_tool_validation(mock_knowledge_store):
    """Test parameter validation."""
    tool = KnowledgeGetTool(store=mock_knowledge_store)
    
    # note_id is required
    errors = tool.validate_params({})
    assert len(errors) > 0
    assert any("note_id" in err.lower() for err in errors)


# ==================== Tool Integration Tests ====================

@pytest.mark.asyncio
async def test_tool_read_only_properties(mock_knowledge_store):
    """Test read_only property for each tool."""
    search_tool = KnowledgeSearchTool(store=mock_knowledge_store)
    create_tool = KnowledgeCreateTool(store=mock_knowledge_store)
    update_tool = KnowledgeUpdateTool(store=mock_knowledge_store)
    get_tool = KnowledgeGetTool(store=mock_knowledge_store)
    
    # Search and get are read-only
    assert search_tool.read_only == True
    assert get_tool.read_only == True
    
    # Create and update are not read-only
    assert create_tool.read_only == False
    assert update_tool.read_only == False


@pytest.mark.asyncio
async def test_tool_concurrency_safe_properties(mock_knowledge_store):
    """Test concurrency_safe property for each tool."""
    search_tool = KnowledgeSearchTool(store=mock_knowledge_store)
    create_tool = KnowledgeCreateTool(store=mock_knowledge_store)
    update_tool = KnowledgeUpdateTool(store=mock_knowledge_store)
    get_tool = KnowledgeGetTool(store=mock_knowledge_store)
    
    # Read-only tools are concurrency safe
    assert search_tool.concurrency_safe == True
    assert get_tool.concurrency_safe == True
    
    # Write tools are not concurrency safe
    assert create_tool.concurrency_safe == False
    assert update_tool.concurrency_safe == False


@pytest.mark.asyncio
async def test_tool_to_schema(mock_knowledge_store):
    """Test tool schema conversion."""
    search_tool = KnowledgeSearchTool(store=mock_knowledge_store)
    schema = search_tool.to_schema()
    
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "knowledge_search"
    assert "description" in schema["function"]
    assert "parameters" in schema["function"]
    assert schema["function"]["parameters"] == search_tool.parameters


@pytest.mark.asyncio
async def test_tool_execute_error_handling(mock_knowledge_store):
    """Test error handling during tool execution."""
    mock_knowledge_store.search.fulltext_search.side_effect = Exception("Database connection failed")
    
    tool = KnowledgeSearchTool(store=mock_knowledge_store)
    
    with pytest.raises(Exception) as exc_info:
        await tool.execute(query="test")
    
    assert "Database connection failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tool_markdown_content_handling(mock_knowledge_store, mock_note):
    """Test that tools handle Markdown content correctly."""
    mock_note.content = "# Heading\n\n## Subheading\n\n- List item 1\n- List item 2\n\n**Bold text**"
    mock_knowledge_store.get_note_by_id.return_value = mock_note
    
    tool = KnowledgeGetTool(store=mock_knowledge_store)
    result = await tool.execute(note_id="test-note-id")
    
    # Content should be preserved exactly
    assert result["content"] == "# Heading\n\n## Subheading\n\n- List item 1\n- List item 2\n\n**Bold text**"


@pytest.mark.asyncio
async def test_tool_link_parsing_in_create(mock_knowledge_store, mock_note):
    """Test that creating a note with [[links]] parses them correctly."""
    mock_knowledge_store.create_note.return_value = mock_note
    
    tool = KnowledgeCreateTool(store=mock_knowledge_store)
    await tool.execute(
        title="Note with Links",
        content="This links to [[Another Note]] and [[Third Note]]"
    )
    
    # Verify the content was passed correctly to the store
    args = mock_knowledge_store.create_note.call_args[0][0]
    assert args.content == "This links to [[Another Note]] and [[Third Note]]"
    # Link parsing should happen in the store layer


@pytest.mark.asyncio
async def test_tool_large_content_handling(mock_knowledge_store, mock_note):
    """Test handling of large note content."""
    large_content = "X" * 100000  # 100KB content
    mock_note.content = large_content
    mock_knowledge_store.get_note_by_id.return_value = mock_note
    
    tool = KnowledgeGetTool(store=mock_knowledge_store)
    result = await tool.execute(note_id="test-note-id")
    
    # Should handle large content without issues
    assert len(result["content"]) == 100000


@pytest.mark.asyncio
async def test_tool_special_characters_in_content(mock_knowledge_store, mock_note):
    """Test handling of special characters in content."""
    special_content = "Special chars: <>&\"'\\/\n\t\r\nUnicode: 中文 日本語 한국어"
    mock_note.content = special_content
    mock_knowledge_store.get_note_by_id.return_value = mock_note
    
    tool = KnowledgeGetTool(store=mock_knowledge_store)
    result = await tool.execute(note_id="test-note-id")
    
    # Special characters should be preserved
    assert result["content"] == special_content
    assert "中文" in result["content"]
    assert "日本語" in result["content"]
    assert "한국어" in result["content"]


@pytest.mark.asyncio
async def test_tool_empty_search_results_format(mock_knowledge_store):
    """Test formatting of empty search results."""
    mock_knowledge_store.search.fulltext_search.return_value = []
    
    tool = KnowledgeSearchTool(store=mock_knowledge_store)
    result = await tool.execute(query="nonexistent")
    
    # Should return a clear message for empty results
    assert isinstance(result, list) or isinstance(result, dict)
    if isinstance(result, list):
        assert len(result) == 0
    else:
        assert "未找到" in result.get("message", "") or "No results" in result.get("message", "")


@pytest.mark.asyncio
async def test_tool_multiple_tag_operations(mock_knowledge_store, mock_note):
    """Test adding and removing multiple tags at once."""
    mock_knowledge_store.get_note_by_id.return_value = mock_note
    mock_knowledge_store.update_note.return_value = mock_note
    
    tool = KnowledgeUpdateTool(store=mock_knowledge_store)
    await tool.execute(
        note_id="test-note-id",
        add_tags=["tag1", "tag2", "tag3"],
        remove_tags=["old1", "old2"]
    )
    
    args = mock_knowledge_store.update_note.call_args[0]
    assert args[1].add_tags == ["tag1", "tag2", "tag3"]
    assert args[1].remove_tags == ["old1", "old2"]