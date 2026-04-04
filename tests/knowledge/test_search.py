import pytest
from nanobot.knowledge.search import SearchService
from nanobot.knowledge.models import NoteCreate


@pytest.fixture
async def search_service(knowledge_store, knowledge_graph):
    """Create a SearchService instance for testing."""
    return SearchService(store=knowledge_store, graph=knowledge_graph)


@pytest.mark.asyncio
async def test_fulltext_search_basic(knowledge_store, search_service):
    """Test basic full-text search functionality."""
    # Create test notes
    await knowledge_store.create_note(NoteCreate(
        title="Python Async Guide",
        content="This guide covers async programming in Python. Async/await is used for I/O operations."
    ))
    await knowledge_store.create_note(NoteCreate(
        title="JavaScript Async Guide",
        content="This guide covers async programming in JavaScript. Promises and async/await are common patterns."
    ))
    await knowledge_store.create_note(NoteCreate(
        title="Python Basics",
        content="This guide covers basic Python syntax, data types, and control flow."
    ))
    
    # Search for "async" - should match both async guides
    results = await search_service.fulltext_search("async", limit=10)
    assert len(results) == 2
    result_titles = [r.note.title for r in results]
    assert "Python Async Guide" in result_titles
    assert "JavaScript Async Guide" in result_titles
    
    # Search for "Python async" - should match only Python async guide
    results = await search_service.fulltext_search("Python async", limit=10)
    assert len(results) == 1
    assert results[0].note.title == "Python Async Guide"
    assert results[0].match_type == "fulltext"
    
    # Search for non-existent term
    results = await search_service.fulltext_search("nonexistent", limit=10)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_fulltext_search_with_tag_filter(knowledge_store, search_service):
    """Test full-text search with tag filtering."""
    await knowledge_store.create_note(NoteCreate(
        title="Python Async",
        content="Async content",
        tags=["python", "async"]
    ))
    await knowledge_store.create_note(NoteCreate(
        title="JS Async",
        content="Async content",
        tags=["javascript", "async"]
    ))
    await knowledge_store.create_note(NoteCreate(
        title="Python Basics",
        content="Python content",
        tags=["python", "basics"]
    ))
    
    # Search for "async" with python tag filter
    results = await search_service.fulltext_search("async", tag_filter=["python"])
    assert len(results) == 1
    assert results[0].note.title == "Python Async"
    
    # Search for "async" with async tag filter (matches both)
    results = await search_service.fulltext_search("async", tag_filter=["async"])
    assert len(results) == 2
    
    # Search for "content" with multiple tags
    results = await search_service.fulltext_search("content", tag_filter=["python", "async"])
    assert len(results) == 1  # Only Python Async has both tags


@pytest.mark.asyncio
async def test_fulltext_search_ranking(knowledge_store, search_service):
    """Test that search results are ranked by relevance."""
    # Note with exact match in title and content
    await knowledge_store.create_note(NoteCreate(
        title="Python Async Programming",
        content="Async programming in Python uses async/await syntax. Async functions are defined with async def."
    ))
    # Note with match only in content
    await knowledge_store.create_note(NoteCreate(
        title="Programming Guide",
        content="This guide covers various programming topics including Python async programming."
    ))
    
    # Search for "Python async"
    results = await search_service.fulltext_search("Python async")
    
    # First result should be the one with match in title and content (higher relevance)
    assert len(results) == 2
    assert results[0].score > results[1].score
    assert results[0].note.title == "Python Async Programming"
    assert results[1].note.title == "Programming Guide"


@pytest.mark.asyncio
async def test_fulltext_search_match_highlights(knowledge_store, search_service):
    """Test that search results include matching content snippets."""
    await knowledge_store.create_note(NoteCreate(
        title="Test Note",
        content="This is a test note with some important content about Python programming. "
                "The note also mentions async/await patterns and database operations."
    ))
    
    # Search for "Python async"
    results = await search_service.fulltext_search("Python async", include_content=True)
    
    assert len(results) == 1
    assert len(results[0].match_highlights) > 0
    # Highlights should contain the matching terms
    assert any("Python" in h for h in results[0].match_highlights)
    assert any("async" in h for h in results[0].match_highlights)


@pytest.mark.asyncio
async def test_tag_search(knowledge_store, search_service):
    """Test searching notes by tags."""
    await knowledge_store.create_note(NoteCreate(title="Python Note 1", content="", tags=["python", "code"]))
    await knowledge_store.create_note(NoteCreate(title="Python Note 2", content="", tags=["python", "tutorial"]))
    await knowledge_store.create_note(NoteCreate(title="JS Note", content="", tags=["javascript", "code"]))
    await knowledge_store.create_note(NoteCreate(title="Other Note", content="", tags=["other"]))
    
    # Search by single tag
    results = await search_service.tag_search(tags=["python"])
    assert len(results) == 2
    assert all("python" in [t.name for t in r.note.tags] for r in results)
    
    # Search by multiple tags (match all)
    results = await search_service.tag_search(tags=["python", "code"], match_all=True)
    assert len(results) == 1
    assert results[0].note.title == "Python Note 1"
    
    # Search by multiple tags (match any)
    results = await search_service.tag_search(tags=["python", "javascript"], match_all=False)
    assert len(results) == 3  # Both Python notes + JS note
    
    # Search with subtags
    # First create hierarchical tags
    await knowledge_store.create_note(NoteCreate(title="Web Dev Python", content="", tags=["dev/web/python"]))
    await knowledge_store.create_note(NoteCreate(title="Web Dev JS", content="", tags=["dev/web/javascript"]))
    await knowledge_store.create_note(NoteCreate(title="Backend Dev", content="", tags=["dev/backend"]))
    
    # Search with prefix match
    results = await search_service.tag_search(tags=["dev/web"], include_subtags=True)
    assert len(results) == 2  # Both web dev notes
    
    # Search without subtags
    results = await search_service.tag_search(tags=["dev/web"], include_subtags=False)
    assert len(results) == 0  # No exact match for "dev/web" tag


@pytest.mark.asyncio
async def test_hybrid_search(knowledge_store, search_service):
    """Test hybrid search combining full-text and tag filters."""
    await knowledge_store.create_note(NoteCreate(
        title="Python Async Guide",
        content="Async programming in Python",
        tags=["python", "async"]
    ))
    await knowledge_store.create_note(NoteCreate(
        title="JS Async Guide",
        content="Async programming in JavaScript",
        tags=["javascript", "async"]
    ))
    await knowledge_store.create_note(NoteCreate(
        title="Python Basics",
        content="Basic Python programming",
        tags=["python", "basics"]
    ))
    
    # Hybrid search: text "async" with tag "python"
    results = await search_service.hybrid_search(
        query="async",
        tag_filter=["python"]
    )
    
    assert len(results) == 1
    assert results[0].note.title == "Python Async Guide"
    
    # Hybrid search with different weights
    results = await search_service.hybrid_search(
        query="programming",
        fulltext_weight=0.8,
        semantic_weight=0.2
    )
    
    # Should return all notes with programming content
    assert len(results) >= 2


@pytest.mark.asyncio
async def test_autocomplete(knowledge_store, search_service):
    """Test autocomplete functionality for search inputs."""
    await knowledge_store.create_note(NoteCreate(title="Python Async Programming", content=""))
    await knowledge_store.create_note(NoteCreate(title="Python Basics", content=""))
    await knowledge_store.create_note(NoteCreate(title="JavaScript Guide", content=""))
    await knowledge_store.create_note(NoteCreate(title="PostgreSQL Tutorial", content=""))
    
    # Autocomplete for title prefix "Py"
    suggestions = await search_service.autocomplete(prefix="Py", field="title")
    assert len(suggestions) == 2
    assert "Python Async Programming" in suggestions
    assert "Python Basics" in suggestions
    
    # Autocomplete for title prefix "P"
    suggestions = await search_service.autocomplete(prefix="P", field="title")
    assert len(suggestions) == 3  # Python*, PostgreSQL*
    
    # Autocomplete for tags
    # First create tags
    await knowledge_store.create_note(NoteCreate(title="Test", content="", tags=["python", "pytest", "javascript"]))
    
    tag_suggestions = await search_service.autocomplete(prefix="py", field="tag")
    assert len(tag_suggestions) == 2
    assert "python" in tag_suggestions
    assert "pytest" in tag_suggestions


@pytest.mark.asyncio
async def test_search_pagination(knowledge_store, search_service):
    """Test pagination for search results."""
    # Create 20 test notes with similar content
    for i in range(20):
        await knowledge_store.create_note(NoteCreate(
            title=f"Test Note {i}",
            content=f"This is test note {i} about Python programming"
        ))
    
    # First page
    page1 = await search_service.fulltext_search("Python", limit=10)
    assert len(page1) == 10
    
    # Second page
    page2 = await search_service.fulltext_search("Python", limit=10, offset=10)
    assert len(page2) == 10
    
    # Combined should have all 20 notes
    all_ids = {r.note.id for r in page1 + page2}
    assert len(all_ids) == 20


@pytest.mark.asyncio
async def test_search_min_score_threshold(knowledge_store, search_service):
    """Test that search results below min_score are filtered out."""
    await knowledge_store.create_note(NoteCreate(
        title="Python Programming",
        content="This is a guide about Python programming"
    ))
    await knowledge_store.create_note(NoteCreate(
        title="Unrelated Note",
        content="This note is about gardening and has no Python content"
    ))
    
    # Search with high threshold - should only match relevant note
    results = await search_service.fulltext_search("Python", min_score=0.8)
    assert len(results) == 1
    assert results[0].note.title == "Python Programming"
    
    # Search with lower threshold - may match more
    results = await search_service.fulltext_search("Python", min_score=0.1)
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_search_ignores_deleted_notes(knowledge_store, search_service):
    """Test that soft-deleted notes are not included in search results."""
    note = await knowledge_store.create_note(NoteCreate(
        title="To Delete",
        content="This note will be deleted"
    ))
    
    # Should be searchable before deletion
    results = await search_service.fulltext_search("deleted")
    assert len(results) == 1
    
    # Soft delete
    await knowledge_store.delete_note(note.id, soft_delete=True)
    
    # Should not be searchable after deletion
    results = await search_service.fulltext_search("deleted")
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_updates_after_note_modification(knowledge_store, search_service):
    """Test that search index is updated when notes are modified."""
    note = await knowledge_store.create_note(NoteCreate(
        title="Original Title",
        content="Original content about Python"
    ))
    
    # Initial search
    results = await search_service.fulltext_search("Python")
    assert len(results) == 1
    
    # Update note content
    await knowledge_store.update_note(note.id, NoteUpdate(
        title="Updated Title",
        content="Now about JavaScript instead of Python"
    ))
    
    # Search for Python should no longer find it
    results = await search_service.fulltext_search("Python")
    assert len(results) == 0
    
    # Search for JavaScript should find it
    results = await search_service.fulltext_search("JavaScript")
    assert len(results) == 1
    assert results[0].note.title == "Updated Title"


@pytest.mark.asyncio
async def test_semantic_search_interface(knowledge_store, search_service):
    """Test semantic search interface (implementation may use embeddings)."""
    await knowledge_store.create_note(NoteCreate(
        title="Python Async",
        content="How to use async/await in Python for I/O operations"
    ))
    await knowledge_store.create_note(NoteCreate(
        title="Python FastAPI",
        content="Building APIs with FastAPI and async endpoints"
    ))
    await knowledge_store.create_note(NoteCreate(
        title="Cooking Recipe",
        content="How to bake chocolate chip cookies"
    ))
    
    # Semantic search for "async web development"
    # Should find Python Async and FastAPI notes as semantically related
    results = await search_service.semantic_search("async web development", limit=10)
    
    # At least the two programming notes should be returned
    assert len(results) >= 2
    result_titles = [r.note.title for r in results]
    assert "Python Async" in result_titles
    assert "Python FastAPI" in result_titles
    
    # Cooking recipe should not be in results (low similarity)
    assert "Cooking Recipe" not in result_titles


@pytest.mark.asyncio
async def test_tag_search_note_count(knowledge_store, search_service):
    """Test that tag search returns correct note counts."""
    await knowledge_store.create_note(NoteCreate(title="Note 1", tags=["tag1"]))
    await knowledge_store.create_note(NoteCreate(title="Note 2", tags=["tag1"]))
    await knowledge_store.create_note(NoteCreate(title="Note 3", tags=["tag2"]))
    
    results = await search_service.tag_search(tags=["tag1"])
    assert len(results) == 2
    
    results = await search_service.tag_search(tags=["tag2"])
    assert len(results) == 1