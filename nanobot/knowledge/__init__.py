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
from .exceptions import (
    KnowledgeBaseError,
    NoteNotFoundError,
    TagNotFoundError,
    LinkNotFoundError,
    VersionNotFoundError,
    StorageError,
    SearchError,
    GraphError,
)

__version__ = "1.0.0"
__author__ = "Nanobot Team"

__all__ = [
    "KnowledgeBase",
    "KnowledgeStore",
    "KnowledgeGraph", 
    "SearchService",
    "VersionManager",
    "KnowledgeBaseError",
    "NoteNotFoundError",
    "TagNotFoundError",
    "LinkNotFoundError", 
    "VersionNotFoundError",
    "StorageError",
    "SearchError",
    "GraphError",
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


def is_enabled() -> bool:
    """Check if knowledge base feature is enabled in configuration."""
    from nanobot.config import load_config
    config = load_config()
    return getattr(config, "knowledge_base", {}).get("enabled", False)
