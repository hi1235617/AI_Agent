import pytest
from pathlib import Path


@pytest.fixture
def temp_kb_dir(tmp_path: Path) -> Path:
    """Create a temporary knowledge base directory for isolated testing."""
    kb_dir = tmp_path / "knowledge"
    kb_dir.mkdir()
    return kb_dir


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Create a temporary SQLite database path."""
    return tmp_path / "test_kb.db"


@pytest.fixture
async def knowledge_store(temp_kb_dir, temp_db_path):
    """Create a KnowledgeStore instance for testing."""
    from nanobot.knowledge.store import KnowledgeStore
    store = KnowledgeStore(db_path=str(temp_db_path), storage_path=str(temp_kb_dir))
    await store.initialize()
    yield store
    # Cleanup
    await store.close()