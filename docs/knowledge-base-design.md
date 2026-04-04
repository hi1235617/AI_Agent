# Knowledge Base Design Document

## 1. Version Information

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Date | 2026-04-04 |
| Author | AI Agent |
| Status | Draft |

### Change Log

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-04-04 | Initial design document creation |

---

## 2. Project Overview

### 2.1 Background

The nanobot personal assistant framework currently provides core agent functionality, multi-channel messaging support, and flexible LLM provider integration. However, users lack a built-in mechanism to manage and retrieve persistent knowledge within the nanobot ecosystem. This design document proposes a comprehensive knowledge base feature that enables nanobot users to store, organize, and retrieve information through both independent CLI usage and deep integration with AI agents.

### 2.2 Goals

The knowledge base feature aims to provide:

1. **Note Management**: Create, read, update, and delete text notes with rich metadata support
2. **Document Management**: Handle file uploads, multi-format support, full-text search, and version history tracking
3. **Knowledge Graph Capabilities**: Enable bidirectional linking between notes, tag-based organization, graph visualization, and semantic search functionality
4. **Flexible Integration**: Support both standalone CLI workflows and seamless integration with nanobot's agent runtime

### 2.3 Scope

This project includes:

- Complete knowledge base storage backend with local filesystem persistence
- CLI commands for independent knowledge base operations
- Agent tool integration for natural language knowledge base interactions
- Core knowledge graph engine with bidirectional link resolution
- Full-text search capabilities across notes and documents
- Multi-format document support (text, markdown, JSON, YAML)
- Version history tracking for notes and documents
- Tag system with hierarchical organization
- Graph visualization for knowledge relationships

This project explicitly excludes:

- Cloud synchronization or remote storage backends
- Real-time collaborative editing features
- Integration with external note-taking applications
- Advanced natural language processing for auto-tagging or summarization

---

## 3. Requirements Analysis

### 3.1 Functional Requirements

#### 3.1.1 Note Storage and Retrieval

**NFR-NOTE-001**: The system shall allow users to create notes with a unique identifier, title, content, and optional metadata (tags, creation timestamp, last modified timestamp).

**NFR-NOTE-002**: The system shall support reading notes by ID or title, with fuzzy matching for title search.

**NFR-NOTE-003**: The system shall support updating note content and metadata while preserving modification history.

**NFR-NOTE-004**: The system shall support deleting notes by ID, with optional confirmation prompt.

**NFR-NOTE-005**: The system shall list all notes with optional filtering by tags or date ranges.

**NFR-NOTE-006**: The system shall support bulk operations on notes (export, import, batch delete).

#### 3.1.2 Document and File Management

**NFR-DOC-001**: The system shall support file uploads and storage within the knowledge base directory structure.

**NFR-DOC-002**: The system shall support basic file operations: read, rename, move, delete.

**NFR-DOC-003**: The system shall support multiple file formats including plain text (.txt), Markdown (.md), JSON (.json), and YAML (.yaml/.yml).

**NFR-DOC-004**: The system shall provide full-text search across all stored documents and notes.

**NFR-DOC-005**: The system shall maintain version history for notes and track last modified timestamps for files.

**NFR-DOC-006**: The system shall support exporting documents to different formats with appropriate conversion.

**NFR-DOC-007**: The system shall support file attachments linked to specific notes.

#### 3.1.3 Knowledge Graph

**NFR-KG-001**: The system shall support bidirectional link syntax using double square brackets `[[Note Title]]` or `[[note-id]]` within note content.

**NFR-KG-002**: The system shall automatically resolve and validate bidirectional links, updating the graph when notes are created, updated, or deleted.

**NFR-KG-003**: The system shall provide a tag system for organizing notes, supporting both flat and hierarchical tags (e.g., `projects/nanobot/core`).

**NFR-KG-004**: The system shall generate and display a graph visualization showing relationships between linked notes.

**NFR-KG-005**: The system shall provide semantic search capabilities using vector embeddings or similarity matching to find related notes based on content.

**NFR-KG-006**: The system shall support querying the knowledge graph to find connected components, shortest paths, and neighborhood queries.

**NFR-KG-007**: The system shall maintain bidirectional reference tracking: if Note A links to Note B, Note B's back-references must include Note A.

#### 3.1.4 Integration

**NFR-INT-001**: The system shall provide independent CLI commands for all knowledge base operations without requiring agent runtime.

**NFR-INT-002**: The system shall expose agent tools that enable natural language knowledge base interactions within agent conversations.

**NFR-INT-003**: The system shall support natural language queries for searching, creating, and updating knowledge base content.

**NFR-INT-004**: The system shall provide an extensible plugin interface for custom knowledge base backends or processors.

**NFR-INT-005**: The system shall integrate with nanobot's existing configuration management system.

**NFR-INT-006**: The system shall support both synchronous and asynchronous operations for agent integration.

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance

**NFR-PERF-001**: Full-text search across 10,000 notes must return results within 1 second on typical hardware.

**NFR-PERF-002**: Note creation and update operations must complete within 100 milliseconds.

**NFR-PERF-003**: Graph visualization generation for typical knowledge graphs (up to 1,000 nodes) must complete within 2 seconds.

**NFR-PERF-004**: The system must maintain efficient indexing structures to support fast lookups as the knowledge base grows.

**NFR-PERF-005**: Memory usage for indexing structures must not grow linearly with the number of notes; use efficient data structures where possible.

#### 3.2.2 Compatibility

**NFR-COMP-001**: The system must work on Windows, macOS, and Linux without platform-specific modifications.

**NFR-COMP-002**: The system must use cross-compatible file paths and filesystem operations.

**NFR-COMP-003**: The system must handle Windows path limitations (MAX_PATH) gracefully.

**NFR-COMP-004**: The system must support Python 3.11+ as required by the nanobot framework.

**NFR-COMP-005**: The system must not require external native dependencies or system-level packages.

#### 3.2.3 Maintainability

**NFR-MAIN-001**: The codebase must follow nanobot's existing code conventions including Ruff linting rules.

**NFR-MAIN-002**: The system must use Pydantic for data validation and configuration, consistent with nanobot's architecture.

**NFR-MAIN-003**: The codebase must include comprehensive test coverage using pytest with asyncio support.

**NFR-MAIN-004**: The system must follow the existing project structure with components placed in appropriate nanobot subdirectories.

**NFR-MAIN-005**: The codebase must include inline documentation and type hints for all public APIs.

**NFR-MAIN-006**: The system must maintain clear separation of concerns between storage, indexing, search, and agent integration layers.

#### 3.2.4 Security

**NFR-SEC-001**: All data must be stored locally on the user's filesystem with no cloud transmission or remote sync.

**NFR-SEC-002**: The system must validate file paths to prevent directory traversal attacks when handling user-provided paths.

**NFR-SEC-003**: The system must sanitize user input to prevent injection attacks in search queries and natural language processing.

**NFR-SEC-004**: File uploads must be restricted to safe file types and validated before processing.

**NFR-SEC-005**: The system must not expose sensitive system information through error messages or logs.

**NFR-SEC-006**: Knowledge base data must be stored in the user's home directory or a configurable location, not in system directories.

---

## 4. Overall Architecture Design

### 4.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Nanobot Runtime                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Agent Tools │  │ CLI Commands│  │   Integration Layer     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Knowledge Base Core Module                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┬─────────────┐│
│  │  store.py   │  │  graph.py   │  │ search.py   │ version.py  ││
│  └─────────────┘  └─────────────┘  └─────────────┴─────────────┘│
│  ┌─────────────┐  ┌─────────────┐                                │
│  │ models.py   │  │exceptions.py│                                │
│  └─────────────┘  └─────────────┘                                │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Persistence Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┬─────────────┐│
│  │  SQLite DB  │  │  Filesystem │  │  FTS5 Index │ Version Log ││
│  └─────────────┘  └─────────────┘  └─────────────┴─────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Module Division

The knowledge base feature is implemented as a standalone submodule within `nanobot/knowledge/` with the following structure:

| Module | Responsibility |
|--------|----------------|
| `store.py` | Primary data access layer, implements CRUD operations for notes, tags, and links |
| `graph.py` | Knowledge graph engine, handles relationship traversal, graph queries, and pathfinding |
| `search.py` | Search service layer, unifies full-text search, tag filtering, and semantic search interfaces |
| `version.py` | Version management system, tracks change history and implements restore functionality |
| `models.py` | Pydantic data models for all knowledge base entities, validation, and serialization |
| `exceptions.py` | Custom exception types for knowledge base operations, consistent with nanobot's error handling patterns |

All modules follow nanobot's existing architectural principles: clear separation of concerns, async/await support for I/O-bound operations, and type hints for all public APIs.

### 4.3 Technology Selection

The knowledge base leverages nanobot's existing infrastructure and industry-standard lightweight technologies to ensure portability and minimal dependencies:

| Technology | Purpose | Rationale |
|------------|---------|-----------|
| **Python 3.11+** | Core implementation language | Aligns with nanobot's minimum supported Python version, leverages modern async/await capabilities |
| **SQLite with FTS5** | Primary database and full-text search engine | Built into Python standard library, no external dependencies, supports efficient relational queries and full-text search natively |
| **Pydantic v2** | Data validation and model serialization | Consistent with nanobot's existing usage of Pydantic for configuration and data models, provides fast validation and serialization |
| **Typer** | CLI command implementation | Used by nanobot's existing CLI infrastructure, enables seamless integration of knowledge base commands into the existing CLI interface |
| **Nanobot Core Infrastructure** | Configuration, logging, error handling | Reuses nanobot's existing components for configuration management, structured logging, and consistent error handling to maintain architectural consistency |

No external services or native dependencies are required, ensuring the feature runs on all supported platforms without additional installation steps.

---

## 5. Data Storage Design

### 5.1 Storage Structure

All knowledge base data is stored within a user-configurable root directory (default: `~/.nanobot/knowledge/` or workspace-specific `workspace/knowledge/` for project-local knowledge bases) with the following subdirectory structure:

```
knowledge/
├── db/                # SQLite database files
│   └── knowledge.db   # Main knowledge base database
├── notes/             # Raw note files stored as markdown (optional, for direct user access)
├── files/             # Uploaded file attachments, organized by file hash
└── versions/          # Version history snapshots for notes
    └── <note-id>/     # Version history per note, stored as diffs or full snapshots
```

The storage structure is platform-agnostic, using relative paths and appropriate filesystem permissions to ensure compatibility across Windows, macOS, and Linux.

### 5.2 Database Design

The SQLite database schema consists of 5 core tables, including an FTS5 virtual table for full-text search:

```sql
-- Notes table: stores core note metadata and content
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,                -- Unique nanoid for the note
    title TEXT NOT NULL,                -- Note title
    content TEXT NOT NULL,              -- Note content (markdown format)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSON DEFAULT '{}',         -- Optional user-defined metadata
    deleted BOOLEAN DEFAULT 0           -- Soft delete flag
);

-- Tags table: stores hierarchical tags
CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,                -- Unique tag ID
    name TEXT NOT NULL UNIQUE,          -- Full tag path (e.g., "projects/nanobot/core")
    description TEXT,                   -- Optional tag description
    color TEXT,                         -- Optional tag display color
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Note-tags junction table: many-to-many relationship between notes and tags
CREATE TABLE IF NOT EXISTS note_tags (
    note_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (note_id, tag_id),
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Links table: stores bidirectional links between notes
CREATE TABLE IF NOT EXISTS links (
    id TEXT PRIMARY KEY,
    source_note_id TEXT NOT NULL,       -- ID of note containing the link
    target_note_id TEXT NOT NULL,       -- ID of note being linked to
    link_text TEXT NOT NULL,            -- Original link text from source note
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_note_id) REFERENCES notes(id) ON DELETE CASCADE,
    UNIQUE(source_note_id, target_note_id)
);

-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS note_fts USING fts5(
    title,
    content,
    content='notes',
    content_rowid='rowid',
    tokenize='porter unicode61'
);

-- Triggers to keep FTS index updated
CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
    INSERT INTO note_fts(rowid, title, content) VALUES (new.rowid, new.title, new.content);
END;

CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
    UPDATE note_fts SET title = new.title, content = new.content WHERE rowid = old.rowid;
END;

CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
    DELETE FROM note_fts WHERE rowid = old.rowid;
END;
```

Indexes are added on frequently queried fields:
- `notes(title, created_at)` for fast title-based lookups and sorting
- `tags(name)` for fast tag searches
- `links(source_note_id, target_note_id)` for fast graph traversal queries

### 5.3 Data Models

All knowledge base entities are defined using Pydantic v2 models, consistent with nanobot's existing data model patterns:

```python
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class BaseKnowledgeModel(BaseModel):
    """Base model for all knowledge base entities with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="forbid"
    )

class Note(BaseKnowledgeModel):
    """Full note entity model"""
    id: str = Field(description="Unique nanoid identifier for the note")
    title: str = Field(description="Note title")
    content: str = Field(description="Note content in markdown format")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last modification timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional user metadata")
    tags: List["Tag"] = Field(default_factory=list, description="Associated tags")
    links: List["Link"] = Field(default_factory=list, description="Outgoing links")
    backlinks: List["Link"] = Field(default_factory=list, description="Incoming backlinks")

class NoteCreate(BaseKnowledgeModel):
    """Model for note creation requests"""
    title: str = Field(min_length=1, description="Note title")
    content: str = Field(default="", description="Note content in markdown format")
    tags: Optional[List[str]] = Field(default=None, description="List of tag names to associate")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional user metadata")

class NoteUpdate(BaseKnowledgeModel):
    """Model for note update requests"""
    title: Optional[str] = Field(default=None, min_length=1, description="Updated note title")
    content: Optional[str] = Field(default=None, description="Updated note content")
    tags: Optional[List[str]] = Field(default=None, description="Updated list of tag names")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Updated metadata (merged with existing)")

class Tag(BaseKnowledgeModel):
    """Tag entity model"""
    id: str = Field(description="Unique tag identifier")
    name: str = Field(description="Full tag path (e.g., 'projects/nanobot/core')")
    description: Optional[str] = Field(default=None, description="Optional tag description")
    color: Optional[str] = Field(default=None, description="Hex color code for display")
    created_at: datetime = Field(description="Tag creation timestamp")
    note_count: Optional[int] = Field(default=None, description="Number of notes associated with this tag")

class Link(BaseKnowledgeModel):
    """Link entity model representing a connection between two notes"""
    id: str = Field(description="Unique link identifier")
    source_note_id: str = Field(description="ID of the note containing the link")
    target_note_id: str = Field(description="ID of the note being linked to")
    link_text: str = Field(description="Original link text from the source note")
    created_at: datetime = Field(description="Link creation timestamp")

class Version(BaseKnowledgeModel):
    """Version snapshot model for note history"""
    id: str = Field(description="Unique version identifier")
    note_id: str = Field(description="ID of the note this version belongs to")
    version_number: int = Field(description="Sequential version number")
    title: str = Field(description="Note title at this version")
    content: str = Field(description="Note content at this version")
    change_description: Optional[str] = Field(default=None, description="Optional description of changes")
    created_at: datetime = Field(description="Version creation timestamp")
    author: Optional[str] = Field(default=None, description="Optional author identifier")

class SearchResult(BaseKnowledgeModel):
    """Search result model containing matched note and relevance information"""
    note: Note = Field(description="Matched note entity")
    score: float = Field(description="Search relevance score (0-1)")
    match_highlights: List[str] = Field(default_factory=list, description="Snippets of content matching the search query")
    match_type: str = Field(description="Type of match: 'fulltext', 'tag', 'semantic'")
```

All models include proper validation rules, type hints, and documentation consistent with nanobot's coding conventions.

---

## 6. Core Module Detailed Design

### 6.1 store.py - KnowledgeStore Class

The `KnowledgeStore` class is the primary data access layer, implementing all CRUD operations for notes, tags, and links with proper transaction handling and data consistency guarantees.

#### Core Interface:
```python
class KnowledgeStore:
    """
    Primary data access layer for knowledge base operations.
    Implements async CRUD operations with transaction support.
    """
    
    def __init__(self, db_path: str):
        """Initialize knowledge store with path to SQLite database"""
        self.db_path = db_path
        self._connection_pool = None
    
    async def initialize(self) -> None:
        """Initialize database schema and connection pool"""
        # Creates tables if they don't exist, sets up connection pooling
    
    async def create_note(self, note_create: NoteCreate) -> Note:
        """
        Create a new note with optional tags.
        Automatically parses and creates links from note content.
        """
    
    async def get_note_by_id(self, note_id: str, include_relations: bool = True) -> Optional[Note]:
        """
        Retrieve a note by ID.
        If include_relations is True, loads associated tags, links, and backlinks.
        """
    
    async def get_note_by_title(self, title: str, case_sensitive: bool = False) -> Optional[Note]:
        """Retrieve a note by exact or case-insensitive title match"""
    
    async def update_note(self, note_id: str, note_update: NoteUpdate) -> Note:
        """
        Update note content and metadata.
        Automatically updates links when content changes.
        Creates a version snapshot before applying changes.
        """
    
    async def delete_note(self, note_id: str, soft_delete: bool = True) -> None:
        """
        Delete a note. Uses soft delete by default, preserving version history.
        Hard delete removes all associated data including links and tags.
        """
    
    async def list_notes(
        self,
        tag_filter: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "updated_at",
        order_direction: str = "desc"
    ) -> List[Note]:
        """List notes with optional filtering and pagination"""
    
    # Tag operations
    async def create_tag(self, name: str, description: Optional[str] = None, color: Optional[str] = None) -> Tag:
        """Create a new tag with optional metadata"""
    
    async def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """Retrieve a tag by its full path name"""
    
    async def list_tags(self, prefix: Optional[str] = None, include_count: bool = True) -> List[Tag]:
        """List all tags, optionally filtered by path prefix"""
    
    # Link operations
    async def get_links_for_note(self, note_id: str, direction: Literal["outgoing", "incoming", "both"] = "both") -> List[Link]:
        """Retrieve outgoing links or incoming backlinks for a note"""
```

#### Key Features:
- Async database operations using `aiosqlite` for non-blocking I/O
- Automatic link parsing and resolution when notes are created/updated
- Transaction support for atomic operations across multiple tables
- Soft delete support preserving version history
- Automatic validation using Pydantic models for all input/output

### 6.2 graph.py - KnowledgeGraph Class

The `KnowledgeGraph` class implements graph-based operations on the knowledge base, enabling relationship traversal and graph queries.

#### Core Interface:
```python
class KnowledgeGraph:
    """
    Knowledge graph engine for relationship queries and traversal.
    Builds in-memory graph representation from database data for efficient queries.
    """
    
    def __init__(self, store: KnowledgeStore):
        """Initialize graph with reference to knowledge store"""
        self.store = store
        self._graph_cache = None
        self._cache_updated_at = None
    
    async def build_graph(self, force_rebuild: bool = False) -> nx.DiGraph:
        """
        Build directed graph representation of all notes and links.
        Caches results for performance, rebuilds only when data changes.
        Returns NetworkX DiGraph object for advanced graph operations.
        """
    
    async def get_neighbors(
        self,
        note_id: str,
        depth: int = 1,
        direction: Literal["outgoing", "incoming", "both"] = "both"
    ) -> Dict[str, Any]:
        """
        Get neighbor nodes for a given note up to specified depth.
        Returns nested structure with nodes, edges, and depth information.
        """
    
    async def get_shortest_path(self, source_note_id: str, target_note_id: str) -> Optional[List[str]]:
        """
        Find shortest path between two notes using breadth-first search.
        Returns list of note IDs in path order, or None if no path exists.
        """
    
    async def get_connected_components(self, min_size: int = 2) -> List[List[str]]:
        """
        Find all connected components in the knowledge graph.
        Returns list of note ID lists, each representing a connected component.
        """
    
    async def export_graph(self, format: Literal["json", "gexf", "dot"] = "json") -> Any:
        """Export graph data in standard formats for visualization tools"""
```

#### Key Features:
- Uses NetworkX for efficient graph operations and algorithm implementations
- Smart caching with automatic invalidation when knowledge base data changes
- Support for multiple export formats for integration with visualization tools
- Efficient traversal algorithms optimized for typical knowledge graph sizes

### 6.3 search.py - SearchService Class

The `SearchService` class provides a unified interface for all search operations, abstracting underlying search implementations.

#### Core Interface:
```python
class SearchService:
    """
    Unified search service combining full-text, tag, and semantic search capabilities.
    Implements result ranking and deduplication across search types.
    """
    
    def __init__(self, store: KnowledgeStore, graph: KnowledgeGraph):
        """Initialize search service with dependencies"""
        self.store = store
        self.graph = graph
    
    async def fulltext_search(
        self,
        query: str,
        tag_filter: Optional[List[str]] = None,
        limit: int = 20,
        min_score: float = 0.1
    ) -> List[SearchResult]:
        """
        Perform full-text search across note titles and content using SQLite FTS5.
        Supports boolean operators, phrase matching, and relevance ranking.
        """
    
    async def tag_search(
        self,
        tags: List[str],
        match_all: bool = True,
        limit: int = 100,
        include_subtags: bool = True
    ) -> List[SearchResult]:
        """
        Search for notes tagged with specified tags.
        If match_all is True, notes must have all specified tags.
        If include_subtags is True, matches hierarchical child tags.
        """
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 20,
        min_similarity: float = 0.7
    ) -> List[SearchResult]:
        """
        Perform semantic similarity search using vector embeddings.
        Uses nanobot's existing LLM provider integration for embedding generation.
        """
    
    async def hybrid_search(
        self,
        query: str,
        tag_filter: Optional[List[str]] = None,
        limit: int = 20,
        fulltext_weight: float = 0.6,
        semantic_weight: float = 0.4
    ) -> List[SearchResult]:
        """
        Combined hybrid search using both full-text and semantic matching.
        Results are ranked using weighted combination of scores from both methods.
        """
    
    async def autocomplete(
        self,
        prefix: str,
        field: Literal["title", "tag", "content"] = "title",
        limit: int = 10
    ) -> List[str]:
        """Provide autocomplete suggestions for search inputs"""
```

#### Key Features:
- Unified result format across all search types with consistent scoring
- Support for advanced full-text search features (boolean queries, phrase matching)
- Semantic search integration using existing nanobot LLM provider infrastructure
- Hybrid search combining keyword and semantic matching for improved relevance
- Fast autocomplete for user input fields

### 6.4 version.py - VersionManager Class

The `VersionManager` class handles version history tracking for notes, enabling change auditing and restore functionality.

#### Core Interface:
```python
class VersionManager:
    """
    Manages version history for notes, implementing snapshot storage and restore.
    Uses efficient diff storage for version history to minimize disk usage.
    """
    
    def __init__(self, store: KnowledgeStore, versions_dir: str):
        """Initialize version manager with storage directory and knowledge store"""
        self.store = store
        self.versions_dir = versions_dir
    
    async def save_version(
        self,
        note_id: str,
        change_description: Optional[str] = None,
        author: Optional[str] = None
    ) -> Version:
        """
        Create a new version snapshot for a note.
        Automatically called before note updates. Uses diff storage for incremental changes.
        """
    
    async def list_versions(
        self,
        note_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Version]:
        """List all versions for a note, ordered by version number descending"""
    
    async def get_version(self, note_id: str, version_number: int) -> Optional[Version]:
        """Retrieve a specific version of a note"""
    
    async def restore_version(
        self,
        note_id: str,
        version_number: int,
        create_snapshot: bool = True
    ) -> Note:
        """
        Restore a note to a previous version.
        Creates a snapshot of the current state before restore by default.
        Returns the restored note entity.
        """
    
    async def delete_version_history(self, note_id: str, keep_latest: Optional[int] = None) -> None:
        """
        Delete version history for a note.
        If keep_latest is specified, retains the N most recent versions.
        """
    
    async def get_version_diff(self, note_id: str, version1: int, version2: int) -> Dict[str, Any]:
        """
        Generate diff between two versions of a note.
        Returns structured diff with added/removed/changed sections.
        """
```

#### Key Features:
- Efficient diff-based storage for version history (only stores changes between versions)
- Automatic version creation before note modifications
- Structured diff generation for comparing versions
- Configurable retention policies for version history
- Full audit trail of all changes with optional author tracking

All modules implement async/await patterns for non-blocking operation, consistent with nanobot's existing codebase, and include comprehensive error handling using custom exceptions defined in `exceptions.py`.
