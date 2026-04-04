# Nanobot Knowledge Base Design Document
## Sections 7-9

---

## 7. CLI Command Design

All knowledge base functionality is exposed via the `nanobot kb` subcommand group, following nanobot's existing Typer CLI patterns.

### Subcommand Group Setup
The `kb` subcommand group is added to the main nanobot CLI app in `nanobot/cli/commands.py`:

```python
kb_app = typer.Typer(help="Manage knowledge base")
app.add_typer(kb_app, name="kb")
```

### Command Reference

#### 7.1 `kb create`
**Functionality**: Create a new knowledge base entry
**Usage**:
```bash
nanobot kb create [OPTIONS] TITLE
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `TITLE` | str | Title/name of the knowledge entry (required positional) |
| `--content`, `-c` | str | Content of the entry (if not provided, opens editor) |
| `--tags`, `-t` | list[str] | Tags to apply to the entry (can specify multiple times) |
| `--parent`, `-p` | str | Parent entry ID to create as child |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Examples**:
```bash
# Create entry with content and tags
nanobot kb create "Python Async Best Practices" --content "Always use async/await with I/O operations..." --tags python --tags async

# Create entry and open editor for content
nanobot kb create "Project Architecture" --tags documentation
```

---

#### 7.2 `kb list`
**Functionality**: List all knowledge base entries with optional filtering
**Usage**:
```bash
nanobot kb list [OPTIONS]
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `--tags`, `-t` | list[str] | Filter entries by tags (matches any tag) |
| `--search`, `-s` | str | Filter entries by title/content search term |
| `--limit`, `-l` | int | Max number of entries to return (default: 50) |
| `--offset`, `-o` | int | Offset for pagination (default: 0) |
| `--sort`, `-S` | str | Sort order: `created`, `updated`, `title` (default: `updated`) |
| `--reverse`, `-r` | bool | Reverse sort order |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Examples**:
```bash
# List all entries sorted by creation date
nanobot kb list --sort created --reverse

# List entries tagged with "python"
nanobot kb list --tags python --tags code
```

---

#### 7.3 `kb show`
**Functionality**: Display detailed content of a specific knowledge entry
**Usage**:
```bash
nanobot kb show [OPTIONS] ENTRY_ID
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `ENTRY_ID` | str | ID or partial title of the entry to show (required positional) |
| `--version`, `-v` | int | Show specific version number (default: latest) |
| `--no-markdown` | bool | Disable Markdown rendering |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Examples**:
```bash
# Show latest version of an entry
nanobot kb show "python-async-best-practices"

# Show version 2 of an entry
nanobot kb show 123 --version 2
```

---

#### 7.4 `kb edit`
**Functionality**: Edit an existing knowledge base entry
**Usage**:
```bash
nanobot kb edit [OPTIONS] ENTRY_ID
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `ENTRY_ID` | str | ID or partial title of the entry to edit (required positional) |
| `--content`, `-c` | str | New content (if not provided, opens editor) |
| `--title`, `-t` | str | Update entry title |
| `--add-tags` | list[str] | Add tags to entry |
| `--remove-tags` | list[str] | Remove tags from entry |
| `--message`, `-m` | str | Version change message |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Examples**:
```bash
# Edit entry content in editor
nanobot kb edit "python-async-best-practices"

# Add a tag and update content directly
nanobot kb edit 123 --add-tags best-practices --content "Updated content..."
```

---

#### 7.5 `kb delete`
**Functionality**: Delete a knowledge base entry (soft delete by default)
**Usage**:
```bash
nanobot kb delete [OPTIONS] ENTRY_ID
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `ENTRY_ID` | str | ID or partial title of the entry to delete (required positional) |
| `--permanent`, `-p` | bool | Permanently delete entry (cannot be restored) |
| `--yes`, `-y` | bool | Skip confirmation prompt |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Examples**:
```bash
# Soft delete entry with confirmation
nanobot kb delete "old-article"

# Permanently delete without confirmation
nanobot kb delete 123 --permanent --yes
```

---

#### 7.6 `kb search`
**Functionality**: Full-text search across all knowledge base entries
**Usage**:
```bash
nanobot kb search [OPTIONS] QUERY
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `QUERY` | str | Search query (required positional) |
| `--tags`, `-t` | list[str] | Filter results by tags |
| `--limit`, `-l` | int | Max results (default: 20) |
| `--threshold`, `-T` | float | Similarity threshold (0.0-1.0, default: 0.7) |
| `--include-content` | bool | Include matching content snippets |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Examples**:
```bash
# Search for entries about async programming
nanobot kb search "async await best practices" --include-content

# Search within python-tagged entries
nanobot kb search "error handling" --tags python
```

---

#### 7.7 `kb graph`
**Functionality**: Visualize knowledge base entry relationships as a graph
**Usage**:
```bash
nanobot kb graph [OPTIONS] [ENTRY_ID]
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `ENTRY_ID` | str | Optional entry ID to center graph on |
| `--format`, `-f` | str | Output format: `text`, `json`, `dot` (default: `text`) |
| `--depth`, `-d` | int | Graph traversal depth (default: 3) |
| `--output`, `-o` | str | Output file path for graph export |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Examples**:
```bash
# Show text-based relationship graph
nanobot kb graph "python-async-best-practices"

# Export graph as DOT file for Graphviz
nanobot kb graph --format dot --output kb_graph.dot
```

---

#### 7.8 `kb links`
**Functionality**: Manage entry relationships (links)
**Usage**:
```bash
nanobot kb links [OPTIONS] ENTRY_ID
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `ENTRY_ID` | str | Entry ID to manage links for (required positional) |
| `--add`, `-a` | str | Add link to another entry ID |
| `--remove`, `-r` | str | Remove link to another entry ID |
| `--list`, `-l` | bool | List all links for the entry |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Examples**:
```bash
# List all links for an entry
nanobot kb links 123 --list

# Link two related entries
nanobot kb links "python-async-best-practices" --add "fastapi-tips"
```

---

#### 7.9 `kb tags`
**Functionality**: List all tags and their usage counts
**Usage**:
```bash
nanobot kb tags [OPTIONS]
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `--search`, `-s` | str | Filter tags by search term |
| `--min-count`, `-m` | int | Only show tags with at least this many entries (default: 1) |
| `--sort`, `-S` | str | Sort order: `name`, `count` (default: `count`) |
| `--reverse`, `-r` | bool | Reverse sort order |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Examples**:
```bash
# List all tags sorted by usage
nanobot kb tags --sort count --reverse

# Find tags containing "python"
nanobot kb tags --search python
```

---

#### 7.10 `kb tag-rename`
**Functionality**: Rename a tag across all entries
**Usage**:
```bash
nanobot kb tag-rename [OPTIONS] OLD_TAG NEW_TAG
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `OLD_TAG` | str | Existing tag name to rename (required positional) |
| `NEW_TAG` | str | New tag name (required positional) |
| `--yes`, `-y` | bool | Skip confirmation prompt |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Example**:
```bash
# Rename tag from "py" to "python"
nanobot kb tag-rename py python
```

---

#### 7.11 `kb tag-delete`
**Functionality**: Delete a tag and remove it from all entries
**Usage**:
```bash
nanobot kb tag-delete [OPTIONS] TAG_NAME
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `TAG_NAME` | str | Tag name to delete (required positional) |
| `--yes`, `-y` | bool | Skip confirmation prompt |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Example**:
```bash
# Delete obsolete "deprecated" tag
nanobot kb tag-delete deprecated
```

---

#### 7.12 `kb versions`
**Functionality**: List version history of an entry
**Usage**:
```bash
nanobot kb versions [OPTIONS] ENTRY_ID
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `ENTRY_ID` | str | Entry ID to show versions for (required positional) |
| `--limit`, `-l` | int | Max versions to show (default: 20) |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Example**:
```bash
# Show version history of an entry
nanobot kb versions "python-async-best-practices"
```

---

#### 7.13 `kb restore`
**Functionality**: Restore a deleted entry or revert to an older version
**Usage**:
```bash
nanobot kb restore [OPTIONS] ENTRY_ID
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `ENTRY_ID` | str | Entry ID to restore (required positional) |
| `--version`, `-v` | int | Version number to restore (default: last active version) |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Examples**:
```bash
# Restore a soft-deleted entry
nanobot kb restore "old-article"

# Revert to version 3 of an entry
nanobot kb restore 123 --version 3
```

---

#### 7.14 `kb import`
**Functionality**: Import entries from external files/URLs
**Usage**:
```bash
nanobot kb import [OPTIONS] SOURCE
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `SOURCE` | str | File path or URL to import from (required positional) |
| `--format`, `-f` | str | Source format: `markdown`, `json`, `html`, `pdf` (auto-detected by default) |
| `--tags`, `-t` | list[str] | Tags to apply to all imported entries |
| `--prefix`, `-p` | str | Prefix to add to imported entry titles |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Examples**:
```bash
# Import a Markdown file
nanobot kb import ./docs/architecture.md --tags documentation

# Import entries from a JSON export
nanobot kb import ./kb_backup.json
```

---

#### 7.15 `kb export`
**Functionality**: Export knowledge base entries to file
**Usage**:
```bash
nanobot kb export [OPTIONS] OUTPUT_PATH
```
**Parameters**:
| Name | Type | Description |
|------|------|-------------|
| `OUTPUT_PATH` | str | Output file path (required positional) |
| `--format`, `-f` | str | Export format: `json`, `markdown`, `html`, `pdf` (default: `json`) |
| `--tags`, `-t` | list[str] | Filter exported entries by tags |
| `--include-versions` | bool | Include all entry versions (default: only latest) |
| `--include-deleted` | bool | Include soft-deleted entries |
| `--workspace`, `-w` | str | Workspace directory override |
| `--config`, `-c` | str | Config file path override |

**Examples**:
```bash
# Export full knowledge base as JSON backup
nanobot kb export ./kb_backup.json --include-versions

# Export all python-related entries as Markdown files
nanobot kb export ./python_docs/ --format markdown --tags python
```

---

## 8. Agent Tool Design

Four knowledge base tools are provided for the agent to interact with the knowledge base, all extending the base `Tool` class from `nanobot.agent.tools.base`.

### Tool Registration
Tools are registered in `nanobot/agent/tools/__init__.py` and automatically loaded by the agent loop.

---

#### 8.1 `knowledge_search` Tool
**Name**: `knowledge_search`
**Description**: Search the knowledge base for information relevant to the current query. Use this tool to retrieve existing knowledge before asking the user or searching the web.
**Parameters Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query to find relevant knowledge base entries"
    },
    "tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Optional list of tags to filter results by"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20,
      "default": 5,
      "description": "Maximum number of results to return"
    },
    "threshold": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1.0,
      "default": 0.7,
      "description": "Similarity threshold for matching entries"
    }
  },
  "required": ["query"]
}
```
**Return Value**:
List of matching entries with title, ID, tags, and content snippet:
```json
[
  {
    "id": "entry-id-123",
    "title": "Python Async Best Practices",
    "tags": ["python", "async"],
    "snippet": "Always use async/await with I/O operations to avoid blocking the event loop...",
    "similarity": 0.92
  }
]
```
**Functionality**: Performs semantic search across the knowledge base to find entries relevant to the query. Returns the most relevant results sorted by similarity.

---

#### 8.2 `knowledge_create` Tool
**Name**: `knowledge_create`
**Description**: Create a new entry in the knowledge base to store information for future reference. Use this tool to save useful information, lessons learned, or important facts that should be remembered.
**Parameters Schema**:
```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "Short descriptive title for the knowledge entry"
    },
    "content": {
      "type": "string",
      "description": "Full content of the entry in Markdown format"
    },
    "tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Optional list of tags to categorize the entry"
    },
    "parent_id": {
      "type": "string",
      "description": "Optional ID of a parent entry to link this entry to"
    }
  },
  "required": ["title", "content"]
}
```
**Return Value**:
Created entry metadata:
```json
{
  "id": "new-entry-id-456",
  "title": "Python Async Best Practices",
  "created_at": "2026-04-04T12:00:00Z",
  "version": 1
}
```
**Functionality**: Creates a new knowledge base entry with the provided content and metadata. Automatically versioned and indexed for search.

---

#### 8.3 `knowledge_update` Tool
**Name**: `knowledge_update`
**Description**: Update an existing knowledge base entry with new information. Use this tool to correct outdated information, add new details, or improve existing entries.
**Parameters Schema**:
```json
{
  "type": "object",
  "properties": {
    "entry_id": {
      "type": "string",
      "description": "ID of the entry to update"
    },
    "content": {
      "type": "string",
      "description": "New full content of the entry (leave empty for partial updates)"
    },
    "title": {
      "type": "string",
      "description": "Optional new title for the entry"
    },
    "add_tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Optional list of tags to add to the entry"
    },
    "remove_tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Optional list of tags to remove from the entry"
    },
    "change_message": {
      "type": "string",
      "description": "Optional description of what was changed and why"
    }
  },
  "required": ["entry_id"]
}
```
**Return Value**:
Updated entry metadata:
```json
{
  "id": "entry-id-123",
  "title": "Python Async Best Practices (Updated)",
  "updated_at": "2026-04-04T13:00:00Z",
  "version": 2
}
```
**Functionality**: Updates an existing entry, creates a new version with the changes, and re-indexes the entry for search. Preserves full version history.

---

#### 8.4 `knowledge_get` Tool
**Name**: `knowledge_get`
**Description**: Retrieve the full content of a specific knowledge base entry by ID. Use this tool when you need the complete content of an entry that was referenced in search results.
**Parameters Schema**:
```json
{
  "type": "object",
  "properties": {
    "entry_id": {
      "type": "string",
      "description": "ID of the entry to retrieve"
    },
    "version": {
      "type": "integer",
      "description": "Optional version number to retrieve (defaults to latest)"
    }
  },
  "required": ["entry_id"]
}
```
**Return Value**:
Full entry content:
```json
{
  "id": "entry-id-123",
  "title": "Python Async Best Practices",
  "content": "# Python Async Best Practices\n\nAlways use async/await with I/O operations...",
  "tags": ["python", "async"],
  "created_at": "2026-04-04T12:00:00Z",
  "updated_at": "2026-04-04T13:00:00Z",
  "version": 2,
  "links": ["related-entry-id-789"]
}
```
**Functionality**: Retrieves the complete content and metadata of a specific knowledge base entry.

---

## 9. Integration Scheme

All integrations follow nanobot's existing patterns and architecture.

---

### 9.1 Configuration Integration
Add `KnowledgeBaseConfig` to the nanobot config schema in `nanobot/config/schema.py`:

```python
class KnowledgeBaseConfig(Base):
    """Knowledge base configuration."""

    enabled: bool = True
    path: str = "~/.nanobot/knowledge"  # Storage directory for knowledge base
    embedding_model: str = "ollama/nomic-embed-text"  # Model for semantic embeddings
    embedding_dim: int = 768  # Embedding vector dimension
    similarity_metric: Literal["cosine", "l2"] = "cosine"
    version_history_limit: int = 50  # Max versions per entry
    auto_save: bool = True  # Auto-save agent discoveries to knowledge base
    auto_save_threshold: float = 0.8  # Similarity threshold for auto-save
```

Add to the root `Config` class:
```python
class Config(BaseSettings):
    # ... existing fields ...
    knowledge_base: KnowledgeBaseConfig = Field(default_factory=KnowledgeBaseConfig)
```

---

### 9.2 CLI Integration
1. Add the `kb` subcommand group to `nanobot/cli/commands.py` following existing subcommand patterns (like `channels` or `plugins`)
2. All commands use the existing `_load_runtime_config()` helper to load configuration
3. Commands use Rich library for output formatting (tables, progress, colors) consistent with existing CLI
4. Error handling follows existing patterns with `typer.Exit()` for failures

---

### 9.3 Agent Integration

#### Tool Registration
Add knowledge base tools to the agent tool registry in `nanobot/agent/tools/__init__.py`:
```python
from .knowledge import (
    KnowledgeSearchTool,
    KnowledgeCreateTool,
    KnowledgeUpdateTool,
    KnowledgeGetTool,
)

__all__ = [
    # ... existing tools ...
    "KnowledgeSearchTool",
    "KnowledgeCreateTool",
    "KnowledgeUpdateTool",
    "KnowledgeGetTool",
]
```

#### Agent Loop Integration
The knowledge base is initialized in the `AgentLoop.__init__()` method in `nanobot/agent/loop.py`:
```python
from nanobot.knowledge.base import KnowledgeBase

class AgentLoop:
    def __init__(self, ...):
        # ... existing initialization ...
        self.knowledge_base = KnowledgeBase(
            config=config.knowledge_base,
            workspace=config.workspace_path,
        )
```

Knowledge tools are instantiated with the knowledge base instance:
```python
self.tools = {
    # ... existing tools ...
    "knowledge_search": KnowledgeSearchTool(self.knowledge_base),
    "knowledge_create": KnowledgeCreateTool(self.knowledge_base),
    "knowledge_update": KnowledgeUpdateTool(self.knowledge_base),
    "knowledge_get": KnowledgeGetTool(self.knowledge_base),
}
```

#### Context Injection
Relevant knowledge base entries are automatically injected into the agent context at the start of each turn:
1. Before processing a user message, the agent performs a background search of the knowledge base using the user's query
2. Top matching results are added to the system prompt context to provide relevant knowledge
3. This improves response quality by giving the agent access to existing knowledge without explicit tool calls

#### Memory Integration
The knowledge base integrates with the agent's memory system:
1. Important information from conversations can be auto-saved to the knowledge base based on relevance and user preferences
2. Knowledge base entries are included in long-term memory retrieval
3. Entries can be linked to session memory for context-aware retrieval
