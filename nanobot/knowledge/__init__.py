"""
Nanobot Knowledge Base Module
============================

A comprehensive knowledge base system for nanobot personal assistant.
Features:
- Note storage and retrieval
- Bidirectional linking between notes
- Tag system for organization
- Full-text search using SQLite FTS5
- Knowledge graph visualization
- Version history tracking
- CLI commands for independent usage
- Agent tools for AI integration
"""

from pathlib import Path
from typing import Optional

from nanobot.config import Config
from .store import KnowledgeStore
from .graph import KnowledgeGraph
from .search import SearchService
from .version import VersionManager
from . import importers
from . import exporters
from . import migrations
from .exceptions import (
    KnowledgeBaseError,
    NoteNotFoundError,
    TagNotFoundError,
    LinkNotFoundError,
    VersionNotFoundError,
    StorageError,
    SearchError,
    GraphError,
    ImportError,
    ExportError,
    MigrationError,
)

__version__ = "1.0.0"
__author__ = "Nanobot Team"

__all__ = [
    "KnowledgeBase",
    "KnowledgeStore",
    "KnowledgeGraph", 
    "SearchService",
    "VersionManager",
    "get_knowledge_base",
    "is_enabled",
    "importers",
    "exporters",
    "migrations",
    "KnowledgeBaseError",
    "NoteNotFoundError",
    "TagNotFoundError",
    "LinkNotFoundError", 
    "VersionNotFoundError",
    "StorageError",
    "SearchError",
    "GraphError",
    "ImportError",
    "ExportError",
    "MigrationError",
]


class KnowledgeBase:
    """Main knowledge base entry point."""
    
    def __init__(self, config: Config, workspace_path: Optional[str] = None):
        """
        Initialize knowledge base.
        
        Args:
            config: Nanobot configuration object
            workspace_path: Optional workspace path override
        """
        self.config = config
        self.workspace_path = workspace_path or config.workspace_path
        self.base_path = Path(self.workspace_path) / "knowledge"
        
        # Initialize components
        self.store = KnowledgeStore(
            db_path=str(self.base_path / "db" / "knowledge.db"),
            storage_path=str(self.base_path)
        )
        self.graph = KnowledgeGraph(store=self.store)
        self.search = SearchService(store=self.store, graph=self.graph)
        self.version_manager = VersionManager(
            store=self.store,
            versions_dir=str(self.base_path / "versions")
        )
    
    async def initialize(self) -> None:
        """Initialize all knowledge base components."""
        # Create directories
        self.base_path.mkdir(parents=True, exist_ok=True)
        (self.base_path / "db").mkdir(exist_ok=True)
        (self.base_path / "notes").mkdir(exist_ok=True)
        (self.base_path / "files").mkdir(exist_ok=True)
        (self.base_path / "versions").mkdir(exist_ok=True)
        
        # Initialize store
        await self.store.initialize()
    
    async def close(self) -> None:
        """Close all connections and clean up resources."""
        await self.store.close()


_KB_INSTANCE: Optional["KnowledgeBase"] = None


def is_enabled() -> bool:
    """Check if knowledge base feature is enabled in configuration."""
    from nanobot.config import load_config
    config = load_config()
    kb_config = getattr(config, "knowledge_base", None)
    if kb_config is None:
        return False
    # Support both dict and object config
    if hasattr(kb_config, "enabled"):
        return bool(kb_config.enabled)
    elif isinstance(kb_config, dict):
        return bool(kb_config.get("enabled", False))
    return False


def get_knowledge_base() -> Optional["KnowledgeBase"]:
    """Get the global knowledge base instance.
    
    Returns:
        KnowledgeBase instance if enabled and initialized, None otherwise
    """
    global _KB_INSTANCE
    if _KB_INSTANCE is not None:
        return _KB_INSTANCE
        
    if not is_enabled():
        return None
        
    try:
        from nanobot.config import load_config
        config = load_config()
        _KB_INSTANCE = KnowledgeBase(config)
        return _KB_INSTANCE
    except Exception:
        return None
