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


@pytest.fixture
async def knowledge_graph(knowledge_store):
    """Create a KnowledgeGraph instance for testing."""
    from nanobot.knowledge.graph import KnowledgeGraph
    graph = KnowledgeGraph(store=knowledge_store)
    await graph.build_graph()
    yield graph


@pytest.fixture
def temp_versions_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for version storage."""
    versions_dir = tmp_path / "versions"
    versions_dir.mkdir()
    return versions_dir


@pytest.fixture
async def version_manager(knowledge_store, temp_versions_dir):
    """Create a VersionManager instance for testing and wire it to the store."""
    from nanobot.knowledge.version import VersionManager
    vm = VersionManager(store=knowledge_store, versions_dir=str(temp_versions_dir))
    knowledge_store.version_manager = vm
    yield vm