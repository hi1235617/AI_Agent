"""
Knowledge base migrations module.
Handles schema migrations and data migration between different KB versions.
"""
from typing import Optional
from pathlib import Path
from ..store import KnowledgeStore
from ..exceptions import MigrationError


class MigrationManager:
    """Manage database migrations."""
    
    def __init__(self, store: KnowledgeStore):
        self.store = store
    
    async def migrate(self, target_version: Optional[str] = None) -> None:
        """Run migrations to target version."""
        await migrate(self.store, target_version=target_version)
    
    async def get_current_version(self) -> Optional[str]:
        """Get current schema version."""
        return await get_schema_version(self.store)


async def migrate(store: KnowledgeStore, target_version: Optional[str] = None) -> None:
    """
    Migrate the knowledge base schema to the latest version or specified target version.
    
    Args:
        store: KnowledgeStore instance
        target_version: Target migration version (optional, defaults to latest)
    """
    # Get current schema version
    current_version = await get_schema_version(store)
    latest_version = "1.0.0"
    
    if current_version == latest_version:
        return  # Already up to date
    
    # Perform migration steps
    if not current_version or current_version < "1.0.0":
        await migrate_to_1_0_0(store)
    
    # Update schema version
    await set_schema_version(store, latest_version)


async def get_schema_version(store: KnowledgeStore) -> Optional[str]:
    """Get current schema version from the database."""
    try:
        async with store._get_connection() as conn:
            # Check if schema_version table exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
            """)
            await conn.commit()
            
            cursor = await conn.execute("SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1")
            row = await cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        raise MigrationError(f"Failed to get schema version: {str(e)}")


async def set_schema_version(store: KnowledgeStore, version: str) -> None:
    """Set schema version in the database."""
    from datetime import datetime
    try:
        async with store._get_connection() as conn:
            await conn.execute(
                "INSERT OR REPLACE INTO schema_version (version, applied_at) VALUES (?, ?)",
                (version, datetime.utcnow().isoformat())
            )
            await conn.commit()
    except Exception as e:
        raise MigrationError(f"Failed to set schema version: {str(e)}")


async def migrate_to_1_0_0(store: KnowledgeStore) -> None:
    """Migrate to schema version 1.0.0."""
    try:
        async with store._get_connection() as conn:
            # Add any missing columns/tables for version 1.0.0
            await conn.execute("ALTER TABLE notes ADD COLUMN IF NOT EXISTS metadata TEXT")
            await conn.execute("ALTER TABLE tags ADD COLUMN IF NOT EXISTS color TEXT")
            await conn.commit()
    except Exception as e:
        raise MigrationError(f"Migration to 1.0.0 failed: {str(e)}")


__all__ = ["migrate", "get_schema_version", "set_schema_version", "MigrationError", "MigrationManager"]