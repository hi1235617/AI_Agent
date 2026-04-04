## 10. Testing Strategy

### 10.1 Testing Philosophy

The knowledge base module follows strict Test-Driven Development (TDD) practices. All features are developed through the red-green-refactor cycle: write failing tests first, implement minimal code to pass, then refactor for quality. This approach ensures comprehensive test coverage, reduces bugs, and facilitates future maintenance.

### 10.2 Unit Testing

**Coverage Requirements**: All knowledge module functions must have corresponding unit tests with a minimum of 80% code coverage. Critical paths (database operations, file I/O, link parsing) must have 95%+ coverage.

**Test File Structure**:
```
tests/
└── knowledge/
    ├── test_storage.py          # Database and file storage tests
    ├── test_graph.py            # Knowledge graph and link tracking tests
    ├── test_search.py           # Search functionality tests
    ├── test_version.py          # Version history management tests
    ├── test_models.py           # Pydantic model validation tests
    ├── test_tools.py            # Agent tool integration tests
    └── test_cli.py              # CLI command tests
```

**Testing Framework**: pytest with pytest-asyncio for async operations, pytest-cov for coverage reporting. All async tests use the `@pytest.mark.asyncio` decorator.

**Fixture Examples**:
```python
# tests/knowledge/conftest.py
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
    from nanobot.knowledge.storage import KnowledgeStore
    store = await KnowledgeStore.initialize(temp_db_path, temp_kb_dir)
    yield store
    # Cleanup: close database connection, delete files
    await store.close()
```

**Unit Test Example** (TDD approach):
```python
# tests/knowledge/test_storage.py

# Step 1: Write failing test
@pytest.mark.asyncio
async def test_create_note_saves_to_database(temp_db_path, temp_kb_dir):
    """Test that creating a note saves metadata to database."""
    from nanobot.knowledge.storage import KnowledgeStore
    from nanobot.knowledge.models import Note

    store = await KnowledgeStore.initialize(temp_db_path, temp_kb_dir)
    note = await store.create_note("test-note", "# Test Content", ["tag1"])

    # Verify database contains the note
    result = await store.get_note_by_id(note.id)
    assert result is not None
    assert result.title == "test-note"
    assert result.content == "# Test Content"
    assert "tag1" in result.tags

    await store.close()

# Step 2: Run test (should fail initially)
# Step 3: Implement minimal code to pass
# Step 4: Run test again (should pass)
# Step 5: Refactor if needed
```

**Mocking Strategy**:
- External file system operations: use `tmp_path` fixture for real file operations in tests
- Database: use in-memory SQLite or temporary databases
- Agent LLM calls: mock LiteLLM providers to avoid real API calls
- CLI runner: use Typer's `CliRunner` for end-to-end CLI testing

### 10.3 Integration Testing

**Goal**: Test CLI commands and agent tool integration with nanobot's core systems.

**CLI Integration Tests**:
```python
# tests/knowledge/test_cli.py
from typer.testing import CliRunner
from nanobot.cli.commands import app

runner = CliRunner()

@pytest.mark.asyncio
async def test_kb_note_create_command(temp_kb_dir, temp_db_path):
    """Test CLI command for creating a note."""
    with patch("nanobot.knowledge.cli.get_kb_paths") as mock_paths:
        mock_paths.return_value = (temp_db_path, temp_kb_dir)

        result = runner.invoke(app, ["kb", "note", "create", "my-note", "--content", "Hello"])
        assert result.exit_code == 0
        assert "Note created successfully" in result.stdout
```

**Agent Tool Integration Tests**:
```python
# tests/knowledge/test_tools.py

@pytest.mark.asyncio
async def test_knowledge_search_tool_integration(temp_kb_dir, temp_db_path):
    """Test that knowledge_search tool works within agent context."""
    from nanobot.agent.tools.knowledge import KnowledgeSearchTool
    from nanobot.knowledge.storage import KnowledgeStore

    # Setup: Create test data
    store = await KnowledgeStore.initialize(temp_db_path, temp_kb_dir)
    await store.create_note("test-note", "Searchable content", ["test"])

    # Test: Execute tool
    tool = KnowledgeSearchTool(store)
    result = await tool.run(query="searchable")

    # Verify: Tool returns expected results
    assert len(result) > 0
    assert "test-note" in result[0]["title"]

    await store.close()
```

### 10.4 Functional Testing

**Goal**: End-to-end testing for complete user scenarios from CLI interaction to data persistence.

**Scenario 1: Complete Note Lifecycle**:
1. Create note via CLI
2. Add tags via CLI
3. Search note via agent tool
4. Update note content
5. Restore previous version
6. Delete note

**Scenario 2: Link Traversal**:
1. Create two notes with bidirectional links
2. Query backlinks
3. Export knowledge graph
4. Verify graph structure

**Scenario 3: Full-Text Search**:
1. Create multiple notes with overlapping content
2. Perform search with filters
3. Verify pagination and relevance ranking

**Functional Test Example**:
```python
# tests/knowledge/test_functional.py

@pytest.mark.asyncio
async def test_complete_note_lifecycle(temp_kb_dir, temp_db_path):
    """Test complete workflow from creation to deletion."""
    from nanobot.knowledge.storage import KnowledgeStore

    store = await KnowledgeStore.initialize(temp_db_path, temp_kb_dir)

    # Create note
    note = await store.create_note("lifecycle-note", "Initial content", ["test"])

    # Update note
    await store.update_note(note.id, content="Updated content")

    # Get version history
    history = await store.get_version_history(note.id)
    assert len(history) == 2

    # Restore previous version
    await store.restore_version(note.id, history[0].version_id)

    # Delete note
    await store.delete_note(note.id)

    # Verify deletion
    result = await store.get_note_by_id(note.id)
    assert result is None

    await store.close()
```

### 10.5 Test Conventions Summary

**File Naming**: All test files must follow `test_*.py` pattern under `tests/knowledge/` directory.

**Async Testing**: All async functions must use `@pytest.mark.asyncio` decorator. Test functions must be defined as `async def`.

**Isolation**: Each test must be independent. Use fixtures for setup and teardown. No shared state between tests.

**Assertion Style**: Use explicit assertions with clear messages. Prefer `assert result is not None` over `assert result`.

**Coverage Goals**:
- Overall coverage: 80%+
- Critical paths (storage, search): 95%+
- CLI commands: 90%+
- Agent tools: 90%+

**Running Tests**:
```bash
# Run all knowledge tests
pytest tests/knowledge/ -v

# Run with coverage
pytest tests/knowledge/ --cov=nanobot.knowledge --cov-report=html

# Run specific test file
pytest tests/knowledge/test_storage.py -v

# Run specific test
pytest tests/knowledge/test_storage.py::test_create_note_saves_to_database -v
```

---

## 11. Deployment and Upgrade Scheme

### 11.1 Installation Steps

The knowledge base feature is designed for easy, non-breaking installation on existing nanobot deployments.

**Step 1: Enable Feature via Configuration**

Add knowledge base configuration to `~/.nanobot/config.json`:
```json
{
  "knowledge": {
    "enabled": true,
    "storagePath": "~/.nanobot/knowledge",
    "databasePath": "~/.nanobot/knowledge/kb.db",
    "maxFileSizeMB": 50,
    "maxVersions": 10
  }
}
```

If the configuration file doesn't exist, nanobot will create it with default knowledge settings on first run.

**Step 2: Automatic Initialization**

On first run with knowledge enabled, the system performs automatic initialization:

```python
# nanobot/knowledge/storage.py
class KnowledgeStore:
    @classmethod
    async def initialize(cls, db_path: Path, storage_path: Path) -> "KnowledgeStore":
        """Initialize knowledge base storage, creating directories and database if needed."""
        # Create storage directory if it doesn't exist
        storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        store = cls(db_path, storage_path)
        await store._initialize_database()

        # Create default notes directory
        (storage_path / "notes").mkdir(exist_ok=True)

        return store
```

**Step 3: Verify Installation**

Run the knowledge base health check:
```bash
nanobot kb status
```

Expected output:
```
Knowledge Base Status
====================
Status: ✓ Active
Storage: ~/.nanobot/knowledge
Database: ~/.nanobot/knowledge/kb.db
Notes: 0
Files: 0
```

**Step 4: Optional: Register Agent Tools**

The knowledge base agent tools are automatically registered when the feature is enabled. To verify tool registration:
```bash
nanobot tools list | grep knowledge
```

### 11.2 Database Migration Strategy

Database schema changes are handled through a versioned migration system that ensures smooth upgrades without data loss.

**Migration System Architecture**:

```python
# nanobot/knowledge/migrations.py
from pathlib import Path
from typing import Callable

class Migration:
    """Database migration definition."""
    def __init__(self, version: int, name: str, up: Callable, down: Callable):
        self.version = version
        self.name = name
        self.up = up  # Migration function
        self.down = down  # Rollback function

class MigrationManager:
    """Manages database schema migrations."""

    MIGRATIONS = [
        Migration(
            version=1,
            name="initial_schema",
            up=lambda conn: _create_initial_schema(conn),
            down=lambda conn: _drop_all_tables(conn)
        ),
        Migration(
            version=2,
            name="add_attachment_metadata",
            up=lambda conn: _add_attachment_columns(conn),
            down=lambda conn: _remove_attachment_columns(conn)
        ),
    ]

    async def run_migrations(self, connection) -> None:
        """Run pending migrations."""
        current_version = await self._get_current_version(connection)

        for migration in self.MIGRATIONS:
            if migration.version > current_version:
                await self._run_migration(connection, migration)

    async def rollback(self, connection, target_version: int) -> None:
        """Rollback to a specific version."""
        current_version = await self._get_current_version(connection)

        for migration in reversed(self.MIGRATIONS):
            if migration.version > target_version and migration.version <= current_version:
                await self._rollback_migration(connection, migration)
```

**Migration Example** (Adding attachment support):

```python
async def _add_attachment_columns(conn) -> None:
    """Add attachment metadata columns to files table."""
    await conn.execute("""
        ALTER TABLE files ADD COLUMN mime_type TEXT;
        ALTER TABLE files ADD COLUMN size INTEGER;
        ALTER TABLE files ADD COLUMN checksum TEXT;
    """)

async def _remove_attachment_columns(conn) -> None:
    """Remove attachment metadata columns from files table."""
    await conn.execute("""
        ALTER TABLE files DROP COLUMN mime_type;
        ALTER TABLE files DROP COLUMN size;
        ALTER TABLE files DROP COLUMN checksum;
    """)
```

**Running Migrations**:

Migrations run automatically on database initialization. Manual migration is available:
```bash
nanobot kb migrate

# Rollback to specific version
nanobot kb migrate --rollback 1
```

**Migration Safety**:
- All migrations run within a database transaction
- Automatic backup before migration (`kb.db.backup`)
- Rollback on failure
- Migration history tracked in `schema_migrations` table

### 11.3 Backward Compatibility

The knowledge base module is designed to maintain full backward compatibility with existing nanobot installations.

**Configuration Backward Compatibility**:

Old configuration files without knowledge settings are automatically upgraded:
```python
# nanobot/config/loader.py
class Config(Base):
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig)

    def __init__(self, **data):
        # If old config, add default knowledge settings
        if "knowledge" not in data:
            data["knowledge"] = {"enabled": False}
        super().__init__(**data)
```

**CLI Backward Compatibility**:

The `kb` command group is only registered if the feature is enabled:
```python
# nanobot/cli/commands.py
def register_kb_commands(app: Typer) -> None:
    """Register knowledge base commands if feature is enabled."""
    config = load_config()

    if config.knowledge.enabled:
        app.add_typer(kb_commands.app, name="kb")
```

**Feature Flag Pattern**:

All knowledge base functionality is guarded by a feature flag:
```python
# nanobot/knowledge/__init__.py
def is_enabled() -> bool:
    """Check if knowledge base feature is enabled."""
    config = load_config()
    return config.knowledge.enabled

# Usage throughout the codebase
if is_enabled():
    from nanobot.knowledge.storage import KnowledgeStore
    # Knowledge base functionality
else:
    # Fallback or skip knowledge operations
```

**Graceful Degradation**:

If the knowledge base fails to initialize (e.g., corrupted database), nanobot continues to operate without it:
```python
# nanobot/cli/commands.py
try:
    kb_store = await KnowledgeStore.initialize(db_path, storage_path)
except DatabaseError as e:
    logger.warning(f"Knowledge base initialization failed: {e}")
    logger.info("Running nanobot without knowledge base functionality")
    kb_store = None
```

### 11.4 Data Migration from Third-Party Tools

While third-party integrations are out of scope for this release, the migration system provides hooks for future tool-specific importers.

**Extensible Importer Pattern**:

```python
# nanobot/knowledge/importers/base.py
class BaseImporter(ABC):
    """Base class for third-party knowledge importers."""

    @abstractmethod
    async def import_notes(self, source_path: Path) -> list[Note]:
        """Import notes from a third-party tool."""
        pass

# Future implementation examples:
# - ObsidianImporter: Import from Obsidian vaults
# - NotionImporter: Import from Notion exports
# - MarkdownImporter: Import from plain Markdown files
```

**Generic Markdown Import**:

A built-in Markdown importer helps users transition from simple note collections:
```bash
nanobot kb import /path/to/notes --format markdown
```

### 11.5 Upgrade Path Summary

**From v1.0.0 to v1.1.0** (hypothetical future release):
1. Backup existing database: `cp ~/.nanobot/knowledge/kb.db ~/.nanobot/knowledge/kb.db.backup`
2. Install new version: `pip install --upgrade nanobot-ai`
3. Run migration (automatic on next run, or manual): `nanobot kb migrate`
4. Verify status: `nanobot kb status`

**Rollback Procedure**:
1. Restore database backup: `cp ~/.nanobot/knowledge/kb.db.backup ~/.nanobot/knowledge/kb.db`
2. Rollback migrations: `nanobot kb migrate --rollback 1`
3. Downgrade package: `pip install nanobot-ai==1.0.0`

---

## 12. Risk Assessment and Countermeasures

### 12.1 Risk Matrix

| Risk ID | Risk Description | Likelihood | Impact | Priority |
|---------|------------------|-------------|---------|----------|
| R1 | Data corruption from file system or database failures | Medium | High | Critical |
| R2 | Performance degradation with large knowledge bases | High | Medium | High |
| R3 | Integration conflicts with existing nanobot features | Low | High | High |
| R4 | Data migration issues during upgrades | Low | Critical | High |
| R5 | Security vulnerabilities in file uploads | Medium | High | High |
| R6 | Resource exhaustion from concurrent operations | Medium | Medium | Medium |

### 12.2 Risk 1: Data Corruption

**Description**: User data could be corrupted due to file system errors, disk failures, or database corruption, resulting in loss of notes, links, or version history.

**Countermeasures**:

1. **Automatic Backups**: Create periodic backups of the database and note files.

```python
# nanobot/knowledge/backup.py
class BackupManager:
    """Manages automatic backups of knowledge base data."""

    async def create_backup(self) -> Path:
        """Create a timestamped backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.storage_path / "backups" / f"kb_backup_{timestamp}"

        # Copy database
        shutil.copy(self.db_path, backup_path / "kb.db")

        # Copy note files
        shutil.copytree(self.storage_path / "notes", backup_path / "notes")

        return backup_path

    async def restore_backup(self, backup_path: Path) -> None:
        """Restore from a backup."""
        # Validate backup integrity
        await self._validate_backup(backup_path)

        # Create pre-restore backup
        await self.create_backup()

        # Restore database
        shutil.copy(backup_path / "kb.db", self.db_path)

        # Restore note files
        shutil.rmtree(self.storage_path / "notes")
        shutil.copytree(backup_path / "notes", self.storage_path / "notes")
```

2. **Version History**: Maintain version history for all notes, allowing rollback to previous states.

```python
# nanobot/knowledge/storage.py
async def create_version_snapshot(self, note_id: str, content: str) -> str:
    """Create a version snapshot of a note."""
    version_id = str(uuid4())
    timestamp = datetime.now()

    await self.db.execute(
        "INSERT INTO note_versions (id, note_id, content, timestamp) VALUES (?, ?, ?, ?)",
        (version_id, note_id, content, timestamp)
    )

    return version_id

async def restore_version(self, note_id: str, version_id: str) -> None:
    """Restore a note to a previous version."""
    version = await self.db.fetch_one(
        "SELECT content FROM note_versions WHERE id = ? AND note_id = ?",
        (version_id, note_id)
    )

    if version:
        await self.db.execute(
            "UPDATE notes SET content = ?, updated_at = ? WHERE id = ?",
            (version["content"], datetime.now(), note_id)
        )
```

3. **Atomic Writes**: Use atomic write patterns to prevent corruption during file writes.

```python
# nanobot/knowledge/storage.py
async def _atomic_write(self, path: Path, content: str) -> None:
    """Write content to file atomically."""
    temp_path = path.with_suffix(".tmp")

    try:
        # Write to temporary file
        temp_path.write_text(content, encoding="utf-8")

        # Atomic rename (works on Unix and Windows)
        temp_path.replace(path)
    except Exception as e:
        # Cleanup on failure
        if temp_path.exists():
            temp_path.unlink()
        raise
```

4. **Database Transactions**: All database operations run within transactions with automatic rollback on failure.

```python
# nanobot/knowledge/storage.py
async def update_note(self, note_id: str, **updates) -> Note:
    """Update a note within a transaction."""
    async with self.db.transaction():
        # Create version snapshot
        old_note = await self.get_note_by_id(note_id)
        await self.create_version_snapshot(note_id, old_note.content)

        # Update note
        await self.db.execute(
            "UPDATE notes SET ... WHERE id = ?",
            (note_id, ...)
        )

        # If any exception occurs, transaction rolls back automatically
```

**Monitoring**: Log backup operations, database integrity checks, and file system errors for early detection.

### 12.3 Risk 2: Performance Degradation

**Description**: As the knowledge base grows with thousands of notes and files, search and query operations may become slow, degrading user experience.

**Countermeasures**:

1. **Proper Indexing**: Create database indexes on frequently queried columns.

```sql
-- nanobot/knowledge/schema.sql
CREATE INDEX idx_notes_title ON notes(title);
CREATE INDEX idx_notes_tags ON notes(tags);
CREATE INDEX idx_notes_updated ON notes(updated_at);
CREATE INDEX idx_links_source ON links(source_note_id);
CREATE INDEX idx_links_target ON links(target_note_id);
CREATE INDEX idx_file_versions ON files(note_id, version_id);
```

2. **Full-Text Search Indexing**: Use SQLite FTS5 for fast content search.

```python
# nanobot/knowledge/schema.py
async def _setup_fts(self) -> None:
    """Set up full-text search virtual table."""
    await self.db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts
        USING fts5(title, content, tags, content_rowid=notes.id)
    """)

async def search_notes(self, query: str, limit: int = 50) -> list[Note]:
    """Search notes using FTS5."""
    results = await self.db.fetch_all("""
        SELECT notes.* FROM notes
        JOIN notes_fts ON notes.id = notes_fts.rowid
        WHERE notes_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, limit))

    return [Note.from_dict(r) for r in results]
```

3. **Pagination**: Implement pagination for all list operations to avoid loading large datasets.

```python
# nanobot/knowledge/storage.py
async def list_notes(
    self,
    page: int = 1,
    page_size: int = 50,
    tag_filter: str | None = None
) -> tuple[list[Note], int]:
    """List notes with pagination."""
    offset = (page - 1) * page_size

    query = "SELECT * FROM notes"
    params = []

    if tag_filter:
        query += " WHERE tags LIKE ?"
        params.append(f"%{tag_filter}%")

    query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
    params.extend([page_size, offset])

    notes = await self.db.fetch_all(query, params)
    total = await self.db.fetch_one("SELECT COUNT(*) as count FROM notes")[0]["count"]

    return [Note.from_dict(n) for n in notes], total
```

4. **Caching**: Implement in-memory caching for frequently accessed data.

```python
# nanobot/knowledge/cache.py
from functools import lru_cache
from datetime import datetime, timedelta

class NoteCache:
    """LRU cache for notes."""

    def __init__(self, ttl_seconds: int = 300):
        self.cache: dict[str, tuple[Note, datetime]] = {}
        self.ttl = timedelta(seconds=ttl_seconds)

    def get(self, note_id: str) -> Note | None:
        """Get note from cache if not expired."""
        if note_id in self.cache:
            note, timestamp = self.cache[note_id]
            if datetime.now() - timestamp < self.ttl:
                return note
            else:
                del self.cache[note_id]
        return None

    def set(self, note_id: str, note: Note) -> None:
        """Cache a note."""
        self.cache[note_id] = (note, datetime.now())
```

5. **Lazy Loading**: Load large file contents only when needed.

```python
# nanobot/knowledge/storage.py
async def get_note_metadata(self, note_id: str) -> NoteMetadata:
    """Get note metadata without content."""
    result = await self.db.fetch_one(
        "SELECT id, title, tags, created_at, updated_at FROM notes WHERE id = ?",
        (note_id,)
    )
    return NoteMetadata.from_dict(result)

async def get_note_content(self, note_id: str) -> str:
    """Get only the note content."""
    result = await self.db.fetch_one(
        "SELECT content FROM notes WHERE id = ?",
        (note_id,)
    )
    return result["content"] if result else ""
```

### 12.4 Risk 3: Integration Conflicts

**Description**: The knowledge base module may conflict with existing nanobot features such as file tools, memory systems, or CLI commands.

**Countermeasures**:

1. **Modular Design**: Keep knowledge base functionality isolated within the `nanobot/knowledge/` module with minimal cross-module dependencies.

```python
# nanobot/knowledge/__init__.py
"""Knowledge base module - isolated from core nanobot functionality."""

from nanobot.knowledge.storage import KnowledgeStore
from nanobot.knowledge.graph import KnowledgeGraph

# Explicit imports only - no implicit side effects
__all__ = ["KnowledgeStore", "KnowledgeGraph"]
```

2. **Feature Flag**: Guard all knowledge base functionality with a feature flag.

```python
# nanobot/knowledge/registry.py
class KnowledgeRegistry:
    """Registry for knowledge base tools and commands."""

    def __init__(self, enabled: bool):
        self.enabled = enabled

    def register_tools(self, tool_registry: ToolRegistry) -> None:
        """Register knowledge tools only if enabled."""
        if not self.enabled:
            return

        from nanobot.knowledge.tools import KnowledgeSearchTool
        from nanobot.knowledge.tools import KnowledgeCreateTool

        tool_registry.register(KnowledgeSearchTool())
        tool_registry.register(KnowledgeCreateTool())
```

3. **Namespace Isolation**: Use distinct CLI command namespaces and tool names.

```python
# nanobot/knowledge/cli.py
# Use 'kb' namespace to avoid conflicts with other commands
kb_commands = typer.Typer(help="Knowledge base commands")

@kb_commands.command("note")
def note_commands():
    """Note management commands."""
    pass

# Tools use 'knowledge_' prefix
class KnowledgeSearchTool(Tool):
    @property
    def name(self) -> str:
        return "knowledge_search"  # Distinct from other search tools
```

4. **Conflict Detection**: Detect and warn about potential conflicts during initialization.

```python
# nanobot/knowledge/storage.py
async def initialize(cls, db_path: Path, storage_path: Path) -> "KnowledgeStore":
    """Initialize with conflict detection."""
    # Check for existing databases
    if db_path.exists():
        # Check schema version
        existing_version = await cls._get_schema_version(db_path)
        if existing_version != cls.CURRENT_SCHEMA_VERSION:
            logger.warning(f"Schema version mismatch: expected {cls.CURRENT_SCHEMA_VERSION}, got {existing_version}")
            logger.info("Run 'nanobot kb migrate' to upgrade")

    # Check storage path conflicts
    if storage_path.exists():
        if not (storage_path / "kb.db").exists():
            logger.warning(f"Storage path exists but no database found: {storage_path}")

    return cls(db_path, storage_path)
```

### 12.5 Risk 4: Data Migration Issues

**Description**: Schema changes or version upgrades could cause data migration failures, leading to data loss or corruption.

**Countermeasures**:

1. **Migration Scripts**: Provide tested migration scripts for all schema changes.

```python
# nanobot/knowledge/migrations.py
class MigrationManager:
    """Manages database schema migrations with safety checks."""

    async def run_migrations(self, connection) -> None:
        """Run pending migrations with safety checks."""
        # Create backup before migration
        await self._create_backup()

        try:
            # Run migrations within transaction
            async with connection.transaction():
                await self._apply_migrations(connection)
        except Exception as e:
            # Rollback on failure
            await self._restore_backup()
            raise MigrationError(f"Migration failed: {e}")
```

2. **Backup Before Upgrade**: Automatically create full backup before any migration.

```python
# nanobot/knowledge/backup.py
async def pre_upgrade_backup(self) -> Path:
    """Create backup before upgrade."""
    backup_path = self.storage_path / "backups" / f"pre_upgrade_{datetime.now().timestamp()}"
    backup_path.mkdir(parents=True, exist_ok=True)

    # Copy database and all files
    shutil.copy(self.db_path, backup_path / "kb.db")
    shutil.copytree(self.storage_path / "notes", backup_path / "notes")

    logger.info(f"Pre-upgrade backup created at: {backup_path}")
    return backup_path
```

3. **Rollback Capability**: Provide automatic or manual rollback on migration failure.

```python
# nanobot/knowledge/cli.py
@kb_commands.command("migrate")
async def migrate(rollback: int = None):
    """Run database migrations or rollback."""
    if rollback is not None:
        logger.warning(f"Rolling back to version {rollback}")
        await migration_manager.rollback(connection, rollback)
    else:
        await migration_manager.run_migrations(connection)
```

4. **Validation**: Validate data integrity after migration.

```python
# nanobot/knowledge/validation.py
class Validator:
    """Validates knowledge base data integrity."""

    async def validate_database(self, connection) -> bool:
        """Validate database integrity."""
        # Check table structure
        tables = await connection.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
        required_tables = ["notes", "links", "tags", "files", "note_versions"]

        for table in required_tables:
            if not any(t["name"] == table for t in tables):
                logger.error(f"Missing required table: {table}")
                return False

        # Check foreign key integrity
        integrity_check = await connection.fetch_one("PRAGMA integrity_check")
        if integrity_check["integrity_check"] != "ok":
            logger.error(f"Database integrity check failed: {integrity_check}")
            return False

        return True

    async def validate_files(self, storage_path: Path) -> bool:
        """Validate file system integrity."""
        notes_dir = storage_path / "notes"

        if not notes_dir.exists():
            logger.error("Notes directory missing")
            return False

        # Check for orphaned files
        file_count = len(list(notes_dir.glob("**/*.md")))
        db_files = await self.db.fetch_one("SELECT COUNT(*) as count FROM files")

        if file_count != db_files["count"]:
            logger.warning(f"File count mismatch: filesystem={file_count}, database={db_files['count']}")
            # This is a warning, not an error

        return True
```

### 12.6 Risk 5: Security Vulnerabilities

**Description**: File uploads and content processing could introduce security vulnerabilities such as path traversal, code injection, or resource exhaustion attacks.

**Countermeasures**:

1. **File Upload Validation**: Validate file types, sizes, and content before processing.

```python
# nanobot/knowledge/security.py
from pathlib import Path
import magic  # python-magic library

class FileValidator:
    """Validates file uploads for security."""

    ALLOWED_MIME_TYPES = {
        "text/plain": [".txt", ".md"],
        "text/markdown": [".md"],
        "application/pdf": [".pdf"],
        "image/png": [".png"],
        "image/jpeg": [".jpg", ".jpeg"],
    }

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

    async def validate_file(self, file_path: Path) -> bool:
        """Validate file is safe to process."""
        # Check file size
        size = file_path.stat().st_size
        if size > self.MAX_FILE_SIZE:
            raise SecurityError(f"File too large: {size} bytes")

        # Check file extension
        if file_path.suffix not in self._get_allowed_extensions():
            raise SecurityError(f"File type not allowed: {file_path.suffix}")

        # Check actual MIME type
        mime = magic.from_file(str(file_path), mime=True)
        if mime not in self.ALLOWED_MIME_TYPES:
            raise SecurityError(f"MIME type not allowed: {mime}")

        return True
```

2. **Path Traversal Protection**: Sanitize file paths to prevent directory traversal.

```python
# nanobot/knowledge/storage.py
def _sanitize_path(self, user_path: str) -> Path:
    """Sanitize user-provided path to prevent traversal."""
    # Resolve relative to storage directory
    full_path = (self.storage_path / "notes" / user_path).resolve()

    # Ensure path is within storage directory
    if not str(full_path).startswith(str(self.storage_path)):
        raise SecurityError("Path traversal attempt detected")

    return full_path
```

3. **Content Sanitization**: Sanitize Markdown content to prevent XSS or injection attacks.

```python
# nanobot/knowledge/sanitizer.py
import nh3  # HTML sanitizer

def sanitize_markdown(content: str) -> str:
    """Sanitize Markdown content to remove dangerous elements."""
    # Remove HTML tags
    sanitized = nh3.clean(content, tags=set(), attributes={})

    # Remove potential script injection
    sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)

    return sanitized
```

4. **Rate Limiting**: Implement rate limiting for resource-intensive operations.

```python
# nanobot/knowledge/rate_limiter.py
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    """Rate limiter for knowledge base operations."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests: defaultdict[str, list[datetime]] = defaultdict(list)

    def check_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit."""
        now = datetime.now()
        user_requests = self.requests[user_id]

        # Remove old requests outside window
        user_requests = [r for r in user_requests if now - r < self.window]
        self.requests[user_id] = user_requests

        # Check limit
        if len(user_requests) >= self.max_requests:
            return False

        # Record request
        user_requests.append(now)
        return True
```

### 12.7 Risk 6: Resource Exhaustion

**Description**: Concurrent operations or large datasets could exhaust system resources such as memory, file handles, or database connections.

**Countermeasures**:

1. **Connection Pooling**: Use connection pooling for database operations.

```python
# nanobot/knowledge/storage.py
import aiosqlite

class ConnectionPool:
    """Database connection pool."""

    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connections: list[aiosqlite.Connection] = []
        self.semaphore = asyncio.Semaphore(pool_size)

    async def acquire(self) -> aiosqlite.Connection:
        """Acquire a connection from the pool."""
        await self.semaphore.acquire()

        if self.connections:
            return self.connections.pop()
        else:
            return await aiosqlite.connect(self.db_path)

    async def release(self, conn: aiosqlite.Connection) -> None:
        """Release a connection back to the pool."""
        if len(self.connections) < self.pool_size:
            self.connections.append(conn)
        else:
            await conn.close()

        self.semaphore.release()
```

2. **Async Processing**: Use async/await for I/O-bound operations to avoid blocking.

```python
# nanobot/knowledge/search.py
async def search_large_dataset(self, query: str) -> list[Note]:
    """Search large dataset asynchronously."""
    results = []

    async for note in self._stream_notes():
        if self._matches_query(note, query):
            results.append(note)

        # Yield control to event loop periodically
        if len(results) % 100 == 0:
            await asyncio.sleep(0)

    return results
```

3. **Memory Limits**: Implement memory limits for content processing.

```python
# nanobot/knowledge/processor.py
class ContentProcessor:
    """Processes note content with memory limits."""

    MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10 MB

    async def process(self, content: str) -> str:
        """Process content with memory limits."""
        # Check content size
        if len(content.encode("utf-8")) > self.MAX_CONTENT_SIZE:
            raise ValueError("Content exceeds maximum size")

        # Process in chunks for large content
        chunk_size = 1024 * 1024  # 1 MB chunks
        result = []

        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            result.append(await self._process_chunk(chunk))

            # Yield control
            await asyncio.sleep(0)

        return "".join(result)
```

4. **Timeout Protection**: Add timeouts to all async operations.

```python
# nanobot/knowledge/storage.py
async def safe_execute(self, query: str, params: tuple, timeout: float = 5.0) -> Any:
    """Execute query with timeout protection."""
    try:
        return await asyncio.wait_for(
            self.db.execute(query, params),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        raise TimeoutError(f"Query timeout: {query}")
```

### 12.8 Risk Monitoring and Response

**Monitoring Strategy**:
- Log all backup operations, migration events, and security violations
- Track performance metrics for search and query operations
- Monitor database health and file system integrity
- Alert on abnormal patterns (e.g., failed migrations, corruption detection)

**Response Plan**:
1. **Data Corruption**: Alert user, attempt automatic restore from backup, offer manual restore options
2. **Performance Degradation**: Suggest indexing or archival of old notes, recommend pagination limits
3. **Integration Conflicts**: Disable knowledge base feature temporarily, provide conflict resolution steps
4. **Migration Failures**: Automatic rollback to previous version, notify user with detailed error message
5. **Security Violations**: Block operation, log violation, alert administrator
6. **Resource Exhaustion**: Throttle operations, suggest cleanup, restart service if needed

**Regular Maintenance**:
- Scheduled daily backups
- Weekly integrity checks
- Monthly cleanup of old versions
- Quarterly performance review and optimization
