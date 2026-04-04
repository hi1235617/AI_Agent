# Personal Knowledge Base Feature Design Document for nanobot

## 1. Document Version Information
| Item | Value |
|------|-------|
| Version | 1.0.0 |
| Date | 2026-04-04 |
| Author | nanobot Development Team |
| Status | Draft |

### Change Log
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2026-04-04 | Initial complete design document | nanobot Dev Team |

---

## 2. Project Overview
### 2.1 Background
nanobot is a lightweight personal AI assistant framework built with Python and TypeScript, supporting multiple messaging channels and LLM providers via LiteLLM. Currently, users need a dedicated knowledge management solution integrated with nanobot to store, retrieve, and organize personal information, notes, and documents, with the ability to leverage these resources through the AI agent system.

### 2.2 Goals
- Build a fully functional personal knowledge base module for nanobot with core capabilities including note management, file management, and knowledge graph
- Support both standalone usage via CLI and deep integration with nanobot's agent system, allowing the AI to automatically learn and use knowledge base content
- Follow nanobot's existing architecture and code conventions to ensure maintainability and extensibility

### 2.3 Scope
#### In Scope
- Core knowledge base modules (storage, graph, search, version control)
- SQLite database for metadata, links, and tag storage
- Local file system storage for Markdown notes and attachments
- `kb` CLI command group for standalone knowledge base operations
- 4 agent tools for AI integration with the knowledge base
- Full-text search and basic semantic search capabilities
- Version history management for notes

#### Out of Scope (Future Releases)
- Web-based UI for knowledge base management
- Cloud synchronization and multi-device support
- Third-party service integrations (Notion, Obsidian, etc.)
- Advanced AI-powered knowledge organization and recommendation features

---

## 3. Requirements Analysis
### 3.1 Functional Requirements
#### 3.1.1 Note Management
- Create, read, update, delete Markdown notes
- Support Obsidian-style `[[note-name]]` bidirectional link syntax
- Automatic link parsing and relationship tracking
- Tag assignment and management for note categorization

#### 3.1.2 File Management
- Basic file system operations: create, edit, delete, rename files and folders
- Support for common file formats: Markdown, PDF, Word documents, images, and plain text files
- Full-text search across all file content
- Version history tracking with ability to restore previous versions of files
- Attachment storage and management for note resources

#### 3.1.3 Knowledge Graph
- Bidirectional link tracking between notes
- Tag network construction and navigation
- Knowledge graph data export for visualization
- Semantic search capabilities based on content understanding (not just keyword matching)
- Backlink display for all notes

#### 3.1.4 CLI Interface
- Dedicated `kb` command group for all knowledge base operations
- Subcommands for note management, search, graph operations, tag management, version management, and import/export
- Intuitive command syntax with helpful documentation and examples

#### 3.1.5 Agent Integration
- 4 dedicated agent tools: knowledge_search, knowledge_create, knowledge_update, knowledge_get
- Automatic registration of tools to nanobot's agent tool registry
- Agent can access and manipulate knowledge base content during conversations
- AI can use knowledge base content to provide more accurate, context-aware responses

### 3.2 Non-Functional Requirements
- **Performance**: Search operations return results in < 1 second for up to 10,000 notes
- **Compatibility**: Supports Python 3.11+, works on Windows, macOS, and Linux platforms
- **Data Safety**: Automatic version history prevents accidental data loss, all file operations follow atomic write patterns
- **Maintainability**: Follows nanobot's existing code conventions (Ruff linting, Pydantic for data validation, modular design)
- **Extensibility**: Modular architecture allows easy addition of new features like cloud sync or web UI in future releases
- **Usability**: CLI commands follow intuitive, consistent patterns matching existing nanobot CLI conventions
---

## 4. Overall Architecture Design
### 4.1 Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                         nanobot CLI                              │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │  kb  Command Group│  │  Existing Agent Commands            │ │
│  └──────────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    nanobot.knowledge Module                        │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │   store.py  │  │ graph.py │  │ search.py│  │ version.py │ │
│  │   (Storage) │  │ (Graph)  │  │ (Search) │  │ (Version)  │ │
│  └─────────────┘  └──────────┘  └──────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         ┌─────────┐   ┌──────────┐   ┌──────────────┐
         │ SQLite  │   │ File System│   │ nanobot.agent │
         │ Database│   │ (Notes)   │   │   Tool System│
         └─────────┘   └──────────┘   └──────────────┘
```

### 4.2 Module Division
| Module | Location | Responsibility |
|--------|----------|----------------|
| Knowledge Base Core | `nanobot/knowledge/` | Core knowledge base functionality |
| - Models | `nanobot/knowledge/models.py` | Pydantic data models for all knowledge base entities |
| - Store | `nanobot/knowledge/store.py` | Data storage layer, CRUD operations for all entities |
| - Graph | `nanobot/knowledge/graph.py` | Knowledge graph implementation, link management, graph data generation |
| - Search | `nanobot/knowledge/search.py` | Full-text and semantic search implementation |
| - Version | `nanobot/knowledge/version.py` | Version history management and recovery |
| - Exceptions | `nanobot/knowledge/exceptions.py` | Custom exceptions for knowledge base operations |
| Agent Tools | `nanobot/agent/tools/knowledge.py` | Knowledge base tools for agent integration |
| Configuration | `nanobot/config/schema.py` | Extended configuration schema for knowledge base |
| CLI Commands | `nanobot/cli/kb.py` | `kb` command group implementation |

### 4.3 Technology Selection
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Database | SQLite + FTS5 | Lightweight, file-based, no external dependencies, built-in full-text search support |
| Data Validation | Pydantic v2 | Aligns with existing nanobot code conventions, provides strong type checking |
| CLI Framework | Typer | Matches existing nanobot CLI implementation, provides automatic help generation |
| Semantic Search | Sentence Transformers | Lightweight, local execution, no external API dependencies for basic semantic search |
| Version Control | Diff Match Patch | Efficient delta storage for version history, reduces storage overhead |

---

## 5. Data Storage Design
### 5.1 Storage Structure
All knowledge base data is stored in the user's nanobot workspace directory:
```
~/.nanobot/workspace/
└── knowledge/              # Knowledge base root directory
    ├── db/                 # SQLite database storage
    │   └── knowledge.db    # Metadata, links, tags, search index
    ├── notes/              # Markdown note files (plain text, user editable)
    ├── files/              # Attachment files (PDF, images, documents, etc.)
    └── versions/           # Version history files (delta patches)
```

### 5.2 Database Design
All tables use SQLite with foreign key constraints enabled.

#### 5.2.1 Notes Table
Stores metadata for all notes:
```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5.2.2 Tags Table
Stores tag definitions:
```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#3b82f6'
);
```

#### 5.2.3 Note-Tag Association Table
Many-to-many relationship between notes and tags:
```sql
CREATE TABLE note_tags (
    note_id INTEGER,
    tag_id INTEGER,
    PRIMARY KEY (note_id, tag_id),
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
```

#### 5.2.4 Links Table
Stores bidirectional links between notes:
```sql
CREATE TABLE links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_note_id INTEGER NOT NULL,
    to_note_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (to_note_id) REFERENCES notes(id) ON DELETE CASCADE,
    UNIQUE(from_note_id, to_note_id)
);
```

#### 5.2.5 Full-Text Search Table
Uses SQLite FTS5 for fast full-text search:
```sql
CREATE VIRTUAL TABLE note_fts USING fts5(
    title,
    content,
    content=notes,
    content_rowid=id
);
```

### 5.3 Data Models
All data models are implemented using Pydantic v2 for type safety and validation:
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class Note(BaseModel):
    id: Optional[int] = None
    title: str
    file_path: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    backlinks: List["Note"] = Field(default_factory=list)
    forward_links: List["Note"] = Field(default_factory=list)

class Tag(BaseModel):
    id: Optional[int] = None
    name: str
    color: str = "#3b82f6"
    note_count: int = 0

class Link(BaseModel):
    id: Optional[int] = None
    from_note_id: int
    to_note_id: int
    created_at: datetime = Field(default_factory=datetime.now)

class Version(BaseModel):
    id: str
    note_id: int
    version_number: int
    timestamp: datetime
    change_summary: Optional[str] = None
    patch_content: str

class SearchResult(BaseModel):
    note: Note
    score: float
    match_highlights: List[str] = Field(default_factory=list)
```

---

## 6. Core Module Detailed Design
### 6.1 Store Module (`store.py`)
**Responsibility**: Data access layer, abstracts database and file system operations, provides unified CRUD interface for all knowledge base entities.

**Key Interfaces**:
```python
class KnowledgeStore:
    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize store with configuration"""
    
    # Note operations
    def create_note(self, title: str, content: str, tags: Optional[List[str]] = None) -> Note:
        """Create a new note, write content to file system, save metadata to DB"""
    
    def get_note(self, note_id: int) -> Optional[Note]:
        """Get note by ID, including tags and links"""
    
    def get_note_by_path(self, file_path: str) -> Optional[Note]:
        """Get note by file path"""
    
    def update_note(self, note_id: int, title: Optional[str] = None, content: Optional[str] = None, tags: Optional[List[str]] = None) -> Note:
        """Update note content/metadata, automatically parse links from content"""
    
    def delete_note(self, note_id: int) -> None:
        """Delete note, remove from file system and DB, cascade delete links and tag associations"""
    
    def list_notes(self, tag_filter: Optional[List[str]] = None, limit: int = 100, offset: int = 0) -> List[Note]:
        """List notes with optional tag filtering"""
    
    # Tag operations
    def create_tag(self, name: str, color: Optional[str] = None) -> Tag:
        """Create a new tag"""
    
    def get_tag(self, tag_id: int) -> Optional[Tag]:
        """Get tag by ID"""
    
    def list_tags(self) -> List[Tag]:
        """List all tags with note counts"""
    
    # Link operations
    def get_links_for_note(self, note_id: int) -> Tuple[List[Note], List[Note]]:
        """Get forward and backlinks for a note"""
```

**Implementation Notes**:
- Automatically parses `[[link]]` syntax from note content on create/update
- Maintains referential integrity with foreign key constraints
- Uses transactions for all write operations to ensure data consistency

### 6.2 Graph Module (`graph.py`)
**Responsibility**: Knowledge graph operations, link management, graph data generation, path finding between notes.

**Key Interfaces**:
```python
class KnowledgeGraph:
    def __init__(self, store: KnowledgeStore):
        """Initialize graph with store instance"""
    
    def get_graph_data(self) -> Dict:
        """Get full graph data in format compatible with visualization tools (nodes and edges)"""
    
    def get_neighborhood_graph(self, note_id: int, depth: int = 2) -> Dict:
        """Get subgraph around a specific note up to specified depth"""
    
    def find_path(self, from_note_id: int, to_note_id: int, max_depth: int = 5) -> Optional[List[int]]:
        """Find shortest path between two notes in the graph"""
    
    def get_tag_network(self) -> Dict:
        """Get tag network data showing relationships between tags based on co-occurrence"""
```

**Implementation Notes**:
- Uses BFS for path finding operations
- Generates output compatible with common visualization libraries (D3.js, Mermaid)
- Caches graph data for improved performance, invalidates on note/link changes

### 6.3 Search Module (`search.py`)
**Responsibility**: Search functionality including full-text search, tag search, and semantic search.

**Key Interfaces**:
```python
class SearchService:
    def __init__(self, store: KnowledgeStore, config: KnowledgeBaseConfig):
        """Initialize search service"""
    
    def full_text_search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """Full-text search across all note titles and content using FTS5"""
    
    def tag_search(self, tags: List[str], limit: int = 20) -> List[Note]:
        """Search for notes matching all specified tags"""
    
    def semantic_search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """Semantic search using sentence embeddings to find conceptually similar content"""
    
    def hybrid_search(self, query: str, limit: int = 20, semantic_weight: float = 0.5) -> List[SearchResult]:
        """Hybrid search combining full-text and semantic results"""
```

**Implementation Notes**:
- FTS5 used for full-text search with BM25 ranking
- Sentence Transformers used for semantic embeddings (local execution, no external API)
- Hybrid search combines both result sets with configurable weighting

### 6.4 Version Module (`version.py`)
**Responsibility**: Version history management, tracking changes to notes, allowing restoration of previous versions.

**Key Interfaces**:
```python
class VersionManager:
    def __init__(self, store: KnowledgeStore, config: KnowledgeBaseConfig):
        """Initialize version manager"""
    
    def save_version(self, note_id: int, old_content: str, new_content: str, change_summary: Optional[str] = None) -> Version:
        """Save a new version for a note, stores delta patch to reduce storage usage"""
    
    def get_versions(self, note_id: int, limit: int = 50) -> List[Version]:
        """Get all versions for a note, sorted newest first"""
    
    def restore_version(self, note_id: int, version_id: str) -> Note:
        """Restore a note to a previous version, creates a new version with restored content"""
    
    def cleanup_old_versions(self, note_id: int, keep_last: int = 100) -> None:
        """Clean up old versions, keep only the most recent N versions"""
```

**Implementation Notes**:
- Uses diff-match-patch library to generate and apply delta patches
- Version history is stored as separate patch files in the versions directory
- Restore operation creates a new version to preserve complete change history
---

## 7. CLI Command Design
All knowledge base operations are available under the `nanobot kb` command group, following Typer conventions consistent with existing nanobot CLI commands.

### 7.1 Note Management Commands
#### 7.1.1 `kb create`
Create a new note.
**Usage**:
```bash
nanobot kb create <title> [--content <content>] [--tags <tag1,tag2>] [--file <path/to/file.md>]
```
**Parameters**:
- `title`: Note title (required)
- `--content`: Note content (optional, if not provided opens default editor)
- `--tags`: Comma-separated list of tags (optional)
- `--file`: Path to existing Markdown file to import as note (optional)
**Example**:
```bash
nanobot kb create "Project Ideas" --tags "projects,ideas" --content "1. Build personal knowledge base\n2. Implement AI assistant"
```

#### 7.1.2 `kb list`
List all notes.
**Usage**:
```bash
nanobot kb list [--tags <tag1,tag2>] [--limit <number>] [--offset <number>] [--sort <field>]
```
**Parameters**:
- `--tags`: Filter notes by tags (optional)
- `--limit`: Maximum number of results (default: 50)
- `--offset`: Pagination offset (default: 0)
- `--sort`: Sort field: `updated_at`, `created_at`, `title` (default: `updated_at`)
**Example**:
```bash
nanobot kb list --tags "work,urgent" --limit 20
```

#### 7.1.3 `kb show`
Display note content and metadata.
**Usage**:
```bash
nanobot kb show <note-id-or-title> [--show-backlinks] [--show-links]
```
**Parameters**:
- `note-id-or-title`: Note ID or exact title (required)
- `--show-backlinks`: Show backlinks to this note (optional)
- `--show-links`: Show forward links from this note (optional)
**Example**:
```bash
nanobot kb show "Project Ideas" --show-backlinks
```

#### 7.1.4 `kb edit`
Edit an existing note.
**Usage**:
```bash
nanobot kb edit <note-id-or-title> [--content <new-content>] [--tags <new-tags>]
```
**Parameters**:
- `note-id-or-title`: Note ID or exact title (required)
- `--content`: New content (optional, if not provided opens default editor)
- `--tags`: New comma-separated tag list (optional, replaces existing tags)
**Example**:
```bash
nanobot kb edit 5 --tags "projects,ideas,active"
```

#### 7.1.5 `kb delete`
Delete a note.
**Usage**:
```bash
nanobot kb delete <note-id-or-title> [--force]
```
**Parameters**:
- `note-id-or-title`: Note ID or exact title (required)
- `--force`: Skip confirmation prompt (optional)
**Example**:
```bash
nanobot kb delete "Old Project" --force
```

### 7.2 Search Commands
#### 7.2.1 `kb search`
Search notes using full-text, semantic, or hybrid search.
**Usage**:
```bash
nanobot kb search <query> [--mode <fulltext|semantic|hybrid>] [--limit <number>] [--show-highlights]
```
**Parameters**:
- `query`: Search query (required)
- `--mode`: Search mode: `fulltext`, `semantic`, `hybrid` (default: `hybrid`)
- `--limit`: Maximum number of results (default: 20)
- `--show-highlights`: Show match highlights in results (optional)
**Example**:
```bash
nanobot kb search "knowledge base implementation" --mode semantic --show-highlights
```

### 7.3 Knowledge Graph Commands
#### 7.3.1 `kb graph`
Export knowledge graph data.
**Usage**:
```bash
nanobot kb graph [--format <json|mermaid|dot>] [--output <path>] [--note-id <note-id>] [--depth <number>]
```
**Parameters**:
- `--format`: Output format: `json`, `mermaid`, `dot` (default: `json`)
- `--output`: Output file path (optional, prints to stdout if not provided)
- `--note-id`: Generate subgraph around specific note (optional, full graph if not provided)
- `--depth`: Subgraph depth (default: 2)
**Example**:
```bash
nanobot kb graph --format mermaid --output graph.md --note-id 5 --depth 3
```

#### 7.3.2 `kb links`
Show links for a note.
**Usage**:
```bash
nanobot kb links <note-id-or-title> [--direction <in|out|both>]
```
**Parameters**:
- `note-id-or-title`: Note ID or exact title (required)
- `--direction`: Link direction: `in` (backlinks), `out` (forward links), `both` (default: `both`)
**Example**:
```bash
nanobot kb links "Project Ideas" --direction in
```

### 7.4 Tag Management Commands
#### 7.4.1 `kb tags`
List all tags with note counts.
**Usage**:
```bash
nanobot kb tags [--sort <name|count>]
```
**Parameters**:
- `--sort`: Sort field: `name`, `count` (default: `count`)
**Example**:
```bash
nanobot kb tags --sort name
```

#### 7.4.2 `kb tag-rename`
Rename a tag across all notes.
**Usage**:
```bash
nanobot kb tag-rename <old-tag-name> <new-tag-name>
```
**Parameters**:
- `old-tag-name`: Existing tag name (required)
- `new-tag-name`: New tag name (required)
**Example**:
```bash
nanobot kb tag-rename "work" "professional"
```

#### 7.4.3 `kb tag-delete`
Delete a tag and remove it from all notes.
**Usage**:
```bash
nanobot kb tag-delete <tag-name> [--force]
```
**Parameters**:
- `tag-name`: Tag name to delete (required)
- `--force`: Skip confirmation prompt (optional)
**Example**:
```bash
nanobot kb tag-delete "deprecated-tag" --force
```

### 7.5 Version Management Commands
#### 7.5.1 `kb versions`
List version history for a note.
**Usage**:
```bash
nanobot kb versions <note-id-or-title> [--limit <number>]
```
**Parameters**:
- `note-id-or-title`: Note ID or exact title (required)
- `--limit`: Maximum number of versions to show (default: 20)
**Example**:
```bash
nanobot kb versions "Project Ideas"
```

#### 7.5.2 `kb restore`
Restore a note to a previous version.
**Usage**:
```bash
nanobot kb restore <note-id-or-title> <version-id>
```
**Parameters**:
- `note-id-or-title`: Note ID or exact title (required)
- `version-id`: Version ID to restore (required)
**Example**:
```bash
nanobot kb restore "Project Ideas" ver_123456789
```

### 7.6 Import/Export Commands
#### 7.6.1 `kb import`
Import notes from external sources.
**Usage**:
```bash
nanobot kb import <path> [--format <markdown|obsidian>] [--tags <tags-to-add>]
```
**Parameters**:
- `path`: Path to file or directory to import (required)
- `--format`: Import format: `markdown` (plain Markdown files), `obsidian` (Obsidian vault) (default: `markdown`)
- `--tags`: Comma-separated tags to add to all imported notes (optional)
**Example**:
```bash
nanobot kb import ~/obsidian-vault --format obsidian --tags "imported"
```

#### 7.6.2 `kb export`
Export notes to external format.
**Usage**:
```bash
nanobot kb export <output-path> [--format <markdown|json>] [--tags <filter-tags>]
```
**Parameters**:
- `output-path`: Path to export to (required)
- `--format`: Export format: `markdown` (individual files), `json` (single JSON file) (default: `markdown`)
- `--tags`: Filter notes to export by tags (optional, exports all if not provided)
**Example**:
```bash
nanobot kb export ~/backup --tags "work" --format json
```

---

## 8. Agent Tool Design
Four dedicated tools are provided for nanobot agent integration, automatically registered to the agent tool registry. All tools follow nanobot's existing tool interface conventions.

### 8.1 `knowledge_search`
**Function**: Search the knowledge base for relevant content using hybrid search.
**Parameters**:
```json
{
  "query": {
    "type": "string",
    "description": "Search query string",
    "required": true
  },
  "mode": {
    "type": "string",
    "description": "Search mode: fulltext, semantic, hybrid",
    "default": "hybrid",
    "required": false
  },
  "limit": {
    "type": "number",
    "description": "Maximum number of results to return",
    "default": 10,
    "required": false
  }
}
```
**Return Value**: Array of search results with note content, metadata, and match highlights.
```json
[
  {
    "note": {
      "id": 5,
      "title": "Project Ideas",
      "content": "1. Build personal knowledge base\n2. Implement AI assistant",
      "tags": ["projects", "ideas"],
      "created_at": "2026-04-04T12:00:00",
      "updated_at": "2026-04-04T14:30:00"
    },
    "score": 0.92,
    "match_highlights": ["Build <mark>personal knowledge base</mark>"]
  }
]
```

### 8.2 `knowledge_create`
**Function**: Create a new note in the knowledge base.
**Parameters**:
```json
{
  "title": {
    "type": "string",
    "description": "Note title",
    "required": true
  },
  "content": {
    "type": "string",
    "description": "Note content in Markdown format",
    "required": true
  },
  "tags": {
    "type": "array",
    "items": {"type": "string"},
    "description": "List of tags for the note",
    "required": false
  }
}
```
**Return Value**: Created note object with metadata.
```json
{
  "id": 12,
  "title": "New Feature Plan",
  "file_path": "new-feature-plan.md",
  "created_at": "2026-04-04T15:00:00",
  "updated_at": "2026-04-04T15:00:00",
  "tags": ["features", "planning"]
}
```

### 8.3 `knowledge_update`
**Function**: Update an existing note in the knowledge base.
**Parameters**:
```json
{
  "note_id": {
    "type": "number",
    "description": "ID of note to update",
    "required": true
  },
  "title": {
    "type": "string",
    "description": "New title (optional)",
    "required": false
  },
  "content": {
    "type": "string",
    "description": "New content (optional)",
    "required": false
  },
  "tags": {
    "type": "array",
    "items": {"type": "string"},
    "description": "New tag list (replaces existing tags, optional)",
    "required": false
  }
}
```
**Return Value**: Updated note object.
```json
{
  "id": 12,
  "title": "Updated Feature Plan",
  "updated_at": "2026-04-04T15:30:00",
  "tags": ["features", "planning", "active"]
}
```

### 8.4 `knowledge_get`
**Function**: Get full details of a specific note, including links and backlinks.
**Parameters**:
```json
{
  "note_id": {
    "type": "number",
    "description": "ID of note to retrieve",
    "required": true
  },
  "include_links": {
    "type": "boolean",
    "description": "Include forward and backlinks in response",
    "default": true,
    "required": false
  }
}
```
**Return Value**: Full note details with links.
```json
{
  "id": 5,
  "title": "Project Ideas",
  "content": "1. Build personal knowledge base\n2. Implement AI assistant\n3. [[New Feature Plan]]",
  "tags": ["projects", "ideas"],
  "forward_links": [{"id": 12, "title": "New Feature Plan"}],
  "backlinks": [],
  "created_at": "2026-04-04T12:00:00",
  "updated_at": "2026-04-04T14:30:00"
}
```

---

## 9. Integration Scheme
The knowledge base feature integrates seamlessly with nanobot's existing systems through the following integration points:

### 9.1 Configuration Integration
- Extend `nanobot/config/schema.py` with new `KnowledgeBaseConfig` Pydantic model containing all knowledge base configuration options:
  ```python
  class KnowledgeBaseConfig(BaseModel):
      enabled: bool = True
      workspace_path: Optional[str] = None
      semantic_search_enabled: bool = True
      semantic_model: str = "all-MiniLM-L6-v2"
      version_history_limit: int = 100
      auto_backup_enabled: bool = True
  ```
- Add default configuration values to nanobot's default config file
- Support configuration via environment variables and config file, following existing nanobot config patterns

### 9.2 CLI Integration
- Add new `kb` command group in `nanobot/cli/kb.py`
- Import and register the command group in the main nanobot CLI entrypoint
- All commands follow existing nanobot CLI conventions for error handling, output formatting, and help text
- Use shared nanobot CLI utilities for output formatting, user prompts, and editor integration

### 9.3 Agent Tool Integration
- Implement agent tools in `nanobot/agent/tools/knowledge.py` following the existing BaseTool interface
- Register tools in the global agent tool registry during nanobot startup
- Tools automatically respect nanobot's existing permission model and tool execution policies
- Tool output formats are optimized for LLM consumption with clear, structured data

### 9.4 Startup Initialization
- Add knowledge base initialization step to nanobot's startup sequence
- Automatically create required directory structure and database tables on first run
- Run database migrations automatically on version upgrades
- Initialize semantic search model on startup if enabled
---

## 10. Testing Strategy
This feature follows Test-Driven Development (TDD) practices with a three-layer testing strategy: unit tests, integration tests, and functional tests. All tests are integrated into nanobot's existing pytest test suite.

### 10.1 Unit Tests
**Scope**: Test individual components in isolation, mocking external dependencies.
**Coverage Target**: 90%+ code coverage for all knowledge base modules.
**Test Cases**:
- `store.py`: CRUD operations for notes, tags, links; link parsing; transaction handling; error cases
- `graph.py`: Graph data generation; path finding; tag network construction
- `search.py`: Full-text search accuracy; semantic search relevance; hybrid search weighting
- `version.py`: Version saving; patch generation and application; restore operations
- Data models: Validation rules; serialization/deserialization
- Custom exceptions: Correct error types and messages for different failure scenarios

**Tools**: pytest, pytest-mock, coverage.py
**Example Unit Test**:
```python
def test_create_note_parses_links(mock_store, sample_note_content_with_links):
    """Test that note creation automatically parses [[link]] syntax"""
    note = mock_store.create_note("Test Note", sample_note_content_with_links)
    assert len(note.forward_links) == 2
    assert note.forward_links[0].title == "Linked Note 1"
```

### 10.2 Integration Tests
**Scope**: Test interactions between components and external systems (database, file system).
**Coverage Target**: 100% of integration points and cross-module workflows.
**Test Cases**:
- End-to-end note lifecycle: create → update → link → search → delete
- Database transactions and consistency: verify no partial updates on failure
- File system operations: atomic writes, correct file permissions, path handling across platforms
- Semantic search integration: model loading, embedding generation, result relevance
- CLI command integration: command parsing, parameter validation, correct output formatting
- Agent tool integration: tool registration, parameter validation, correct return formats

**Tools**: pytest, temporary directories, in-memory SQLite database for fast testing
**Example Integration Test**:
```python
def test_note_search_integration(temp_store, sample_notes):
    """Test end-to-end search workflow with real database"""
    temp_store.create_note("Python Tips", "Use virtual environments for dependency management", tags=["python", "dev"])
    temp_store.create_note("Project Setup", "Python project setup with virtualenv", tags=["python", "projects"])
    
    results = temp_store.search.full_text_search("python virtual environment")
    assert len(results) == 2
    assert results[0].note.title == "Python Tips"
```

### 10.3 Functional Tests
**Scope**: Test complete user-facing workflows, simulating real user usage patterns.
**Test Cases**:
- Complete CLI workflow: create note → add tags → link notes → search → view graph → restore version
- Agent tool workflow: agent searches knowledge base → creates note → updates note → retrieves note
- Import/export workflow: import Obsidian vault → verify all notes and links are preserved → export as Markdown
- Edge case handling: large notes (10k+ words), large number of notes (10k+), special characters in titles/content
- Cross-platform compatibility: test file path handling on Windows, macOS, Linux
- Data safety: accidental deletion recovery via version history, database corruption recovery

**Tools**: pytest, typer-test-runner for CLI testing, test data sets including sample Obsidian vaults
**Example Functional Test**:
```python
def test_cli_workflow(runner, temp_workspace):
    """Test complete CLI user workflow"""
    # Create note
    result = runner.invoke(["kb", "create", "Test Note", "--content", "Hello [[World]]", "--tags", "test"])
    assert result.exit_code == 0
    
    # Search for note
    result = runner.invoke(["kb", "search", "Hello"])
    assert "Test Note" in result.output
    
    # Show links
    result = runner.invoke(["kb", "links", "Test Note"])
    assert "World" in result.output
```

### 10.4 CI/CD Integration
- All tests run automatically on every commit via GitHub Actions
- Coverage reports are generated and uploaded to Codecov
- Integration tests run on Windows, macOS, and Linux runners to ensure cross-platform compatibility
- Semantic search tests run with and without GPU acceleration to cover all deployment scenarios

---

## 11. Deployment & Upgrade Scheme
### 11.1 Installation
The knowledge base feature is included as a core module of nanobot, no separate installation is required. Optional dependencies for semantic search can be installed via:
```bash
pip install nanobot[knowledge-semantic]
```
If semantic search is not needed, the feature works with only core nanobot dependencies.

**First Run Initialization**:
- On first execution of any `kb` command, nanobot automatically:
  1. Creates the knowledge base directory structure in the user's workspace
  2. Initializes the SQLite database and creates all required tables
  3. Runs any necessary database migrations
  4. Downloads the semantic search model (if enabled)

### 11.2 Database Migration
- Database migrations are managed using Alembic, integrated with nanobot's existing migration system
- Migrations run automatically on nanobot startup when a new version is detected
- Migration rollback support is provided for all schema changes
- Backup of the knowledge.db file is automatically created before running migrations

### 11.3 Backward Compatibility
- Full backward compatibility with existing nanobot installations
- The feature is disabled by default in existing installations, users can enable it via configuration
- All existing nanobot functionality remains unchanged when the knowledge base is enabled
- Note files are stored as plain Markdown in the file system, fully compatible with other Markdown editors including Obsidian
- No breaking changes to existing APIs, CLI commands, or configuration options

### 11.4 Upgrade Procedure
1. Upgrade nanobot to the latest version: `pip install --upgrade nanobot`
2. Run `nanobot kb list` to trigger automatic initialization and migration
3. (Optional) Import existing notes from Obsidian or other Markdown sources using `nanobot kb import`
4. Verify all existing data is preserved and functionality works as expected

### 11.5 Rollback Procedure
If issues are encountered after upgrade:
1. Restore the previous version of nanobot: `pip install nanobot==<previous-version>`
2. Restore the knowledge.db backup file created during migration
3. All note files remain unchanged and compatible with previous versions

---

## 12. Risk Assessment & Countermeasures
| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| Semantic search model download fails or is too large for user's system | Medium | Medium | - Make semantic search optional, disabled by default for users with limited bandwidth/storage<br>- Provide fallback to full-text search only if semantic model fails to load<br>- Allow users to specify custom model paths for offline usage |
| Database corruption leads to data loss | Low | High | - Use SQLite write-ahead logging (WAL) for improved data integrity<br>- Automatic daily backups of the knowledge.db file<br>- All write operations use transactions to prevent partial updates<br>- Note content is stored as plain text files on disk, providing a backup even if database is corrupted |
| Performance degradation with large note collections (10k+ notes) | Medium | Medium | - Implement database indexing on frequently queried fields<br>- Use FTS5 for fast full-text search optimized for large datasets<br>- Add pagination to all list operations<br>- Implement caching for graph data and frequent search queries |
| Cross-platform file path handling issues | Medium | Medium | - Use Python's pathlib for all file system operations, ensuring platform-agnostic path handling<br>- Run integration tests on Windows, macOS, and Linux CI runners<br>- Normalize all file paths to use consistent separators |
| Version history storage consumes excessive disk space | Low | Medium | - Use delta patches instead of full file copies for version history, reducing storage overhead by 90%+<br>- Allow users to configure version history limits and automatic cleanup policies<br>- Provide CLI command to manually clean up old versions |
| Agent tool misuse leads to accidental data modification/deletion | Low | High | - Add safety checks to all agent tools, requiring explicit confirmation for destructive operations<br>- Log all agent tool operations to an audit log<br>- Agent deletion operations are soft-delete by default, with recovery option<br>- Allow users to disable write operations for agent tools via configuration |
| Link parsing errors break knowledge graph integrity | Medium | Medium | - Use robust Markdown parsing library with error handling for invalid link syntax<br>- Add validation step for all links before saving to database<br>- Provide CLI command to verify and repair link integrity<br>- Ignore invalid links instead of failing entire note save operation |
