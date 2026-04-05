from __future__ import annotations

import os
import re
import json
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, List, Optional, Tuple, Literal

import aiosqlite
from nanoid import generate as nanoid_generate

from .models import NoteCreate, NoteUpdate, Note, Tag, Link
from .exceptions import NoteNotFoundError, TagNotFoundError, LinkNotFoundError


class KnowledgeStore:
    def __init__(self, db_path: str, storage_path: str) -> None:
        self.db_path = db_path
        self.storage_path = storage_path
        self._db: Optional[aiosqlite.Connection] = None
        self._version_manager: Optional[Any] = None

    @property
    def version_manager(self) -> Optional[Any]:
        return self._version_manager

    @version_manager.setter
    def version_manager(self, value: Any) -> None:
        self._version_manager = value

    async def initialize(self) -> None:
        # Ensure storage directory exists
        os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = sqlite3.Row  # type: ignore
        # Enable foreign keys
        await self._db.execute("PRAGMA foreign_keys = ON")
        await self._db.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                created_at TEXT,
                updated_at TEXT,
                deleted_at TEXT,
                author TEXT,
                change_message TEXT,
                metadata TEXT
            );
            CREATE TABLE IF NOT EXISTS tags (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE,
                description TEXT,
                color TEXT
            );
            CREATE TABLE IF NOT EXISTS note_tags (
                note_id TEXT,
                tag_id TEXT,
                PRIMARY KEY (note_id, tag_id),
                FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS links (
                id TEXT PRIMARY KEY,
                source_id TEXT,
                target_id TEXT,
                link_text TEXT,
                FOREIGN KEY (source_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES notes(id) ON DELETE CASCADE
            );
            -- FTS index for fast full-text search on notes
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(title, content, note_id UNINDEXED);
            CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
              INSERT INTO notes_fts(note_id, title, content) VALUES (new.id, new.title, new.content);
            END;
            CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
              UPDATE notes_fts SET title = new.title, content = new.content WHERE note_id = old.id;
            END;
            CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
              DELETE FROM notes_fts WHERE note_id = old.id;
            END;
            """
        )
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    @asynccontextmanager
    async def _get_connection(self):
        """Return an async context manager for the database connection.
        
        Provides a compatibility layer for tests that expect a databases-style API.
        """
        class _ConnectionContext:
            def __init__(self2, db):
                self2._db = db
            
            async def fetch_all(self2, sql, params=None):
                if params is None:
                    params = ()
                cursor = await self2._db.execute(sql, params)
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
            
            async def fetch_one(self2, sql, params=None):
                if params is None:
                    params = ()
                cursor = await self2._db.execute(sql, params)
                row = await cursor.fetchone()
                return dict(row) if row else None
        
        yield _ConnectionContext(self._db)

    # --------- Helpers ---------
    def _now(self) -> str:
        return datetime.utcnow().isoformat(timespec="microseconds")

    async def _get_tags_for_note(self, note_id: str) -> List[Tag]:
        if not self._db:
            raise RuntimeError("Database not initialized")
        q = "SELECT t.id, t.name, t.description, t.color FROM tags t JOIN note_tags nt ON nt.tag_id = t.id WHERE nt.note_id = ?"
        cursor = await self._db.execute(q, (note_id,))
        rows = [dict(r) for r in await cursor.fetchall()]
        return [Tag(**r) for r in rows]  # type: ignore

    async def _get_or_create_tag_inline(self, name: str, description: str | None = None, color: str | None = None) -> Tag:
        """Get or create a tag without committing (for use inside transactions)."""
        if not self._db:
            raise RuntimeError("Database not initialized")
        tag = await self.get_tag_by_name(name)
        if tag is not None:
            return tag
        from nanoid import generate as nanoid_generate
        tag_id = nanoid_generate(size=8)
        await self._db.execute(
            "INSERT INTO tags(id, name, description, color) VALUES(?, ?, ?, ?)",
            (tag_id, name, description, color),
        )
        return Tag(id=tag_id, name=name, description=description, color=color)

    async def _get_note_row_by_id(self, note_id: str, include_deleted: bool) -> Optional[sqlite3.Row]:
        if not self._db:
            raise RuntimeError("Database not initialized")
        query = "SELECT * FROM notes WHERE id = ?"
        row = await self._db.execute(query, (note_id,))
        row = await row.fetchone()
        if not row:
            return None
        if not include_deleted and row["deleted_at"]:
            return None
        return row

    async def get_note_by_id(self, note_id: str, include_relations: bool = True, include_deleted: bool = False) -> Optional[Note]:
        row = await self._get_note_row_by_id(note_id, include_deleted)
        if row is None:
            return None
        note_dict = {
            "id": row["id"],
            "title": row["title"],
            "content": row["content"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "deleted_at": row["deleted_at"],
            "author": row["author"],
            "change_message": row["change_message"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
        }
        note = Note(**note_dict)  # type: ignore
        if include_relations:
            try:
                note.tags = await self._get_tags_for_note(note_id)  # type: ignore
            except Exception:
                pass
            try:
                outgoing, incoming = await self.get_links_for_note(note_id, direction="both")
                note.outgoing_links = outgoing  # type: ignore
                note.incoming_links = incoming  # type: ignore
            except Exception:
                pass
        return note

    async def get_note_by_title(self, title: str, case_sensitive: bool = False) -> Optional[Note]:
        if not self._db:
            raise RuntimeError("Database not initialized")
        if case_sensitive:
            query = "SELECT * FROM notes WHERE title = ? AND deleted_at IS NULL"
            row = await self._db.execute(query, (title,))
        else:
            query = "SELECT * FROM notes WHERE LOWER(title) = LOWER(?) AND deleted_at IS NULL"
            row = await self._db.execute(query, (title,))
        row = await row.fetchone()
        if not row:
            return None
        return await self.get_note_by_id(row["id"], include_relations=True, include_deleted=False)

    async def create_note(self, note_create: NoteCreate) -> Note:
        if not self._db:
            raise RuntimeError("Database not initialized")
        note_id = nanoid_generate(size=12)
        now = self._now()
        title = getattr(note_create, "title", "Untitled")
        content = getattr(note_create, "content", "")
        author = getattr(note_create, "author", None)
        change_message = getattr(note_create, "change_message", None)
        metadata = getattr(note_create, "metadata", None) or {}
        tag_names: List[str] = getattr(note_create, "tags", []) or []
        # Normalize tags
        tag_ids: List[str] = []
        try:
            await self._db.execute("BEGIN IMMEDIATE")
            await self._db.execute(
                "INSERT INTO notes(id, title, content, created_at, updated_at, author, change_message, metadata) VALUES(?,?,?,?,?,?,?,?)",
                (note_id, title, content, now, now, author, change_message, json.dumps(metadata) if metadata else None),
            )
            # Tags - use direct INSERT to avoid commit in create_tag
            for tname in tag_names:
                tag = await self._get_or_create_tag_inline(tname)
                tag_ids.append(tag.id)  # type: ignore
                await self._db.execute("INSERT OR IGNORE INTO note_tags(note_id, tag_id) VALUES(?, ?)", (note_id, tag.id))
            # Links from content
            targets = self._parse_links_from_content(content)
            for t in targets:
                # Try to find target by title; if not found, try to find by ID directly
                target_note = await self.get_note_by_title(t, case_sensitive=False)
                if target_note is not None:
                    await self._create_link(note_id, target_note.id, f"[[{t}]]")
                else:
                    # Try to create link with target title as ID (for forward references)
                    # The link will be stored even if target doesn't exist yet
                    try:
                        await self._create_link(note_id, t, f"[[{t}]]")
                    except Exception:
                        pass
            await self._db.commit()
        except Exception:
            try:
                await self._db.rollback()
            except Exception:
                pass
            raise
        return await self.get_note_by_id(note_id, include_relations=True)

    async def update_note(self, note_id: str, note_update: NoteUpdate, change_message: str | None = None, author: str | None = None) -> Note:
        if not self._db:
            raise RuntimeError("Database not initialized")
        
        # Save current state as a version before updating (if version manager is available)
        if self._version_manager is not None:
            try:
                await self._version_manager.save_version(
                    note_id=note_id,
                    change_description=change_message,
                    author=author,
                )
            except Exception:
                # Don't fail the update if version saving fails
                pass
        
        now = self._now()
        title = getattr(note_update, "title", None)
        content = getattr(note_update, "content", None)
        metadata_update = getattr(note_update, "metadata", None)
        try:
            await self._db.execute("BEGIN IMMEDIATE")
            # Update fields if provided
            if title is not None or content is not None or change_message is not None or author is not None or metadata_update is not None:
                fields = []
                params = []
                if title is not None:
                    fields.append("title = ?"); params.append(title)
                if content is not None:
                    fields.append("content = ?"); params.append(content)
                if change_message is not None:
                    fields.append("change_message = ?"); params.append(change_message)
                if author is not None:
                    fields.append("author = ?"); params.append(author)
                if metadata_update is not None:
                    # Merge with existing metadata
                    existing_note = await self.get_note_by_id(note_id, include_relations=False, include_deleted=True)
                    existing_meta = getattr(existing_note, "metadata", {}) if existing_note else {}
                    existing_meta.update(metadata_update)
                    fields.append("metadata = ?"); params.append(json.dumps(existing_meta))
                fields.append("updated_at = ?"); params.append(now)
                sql = f"UPDATE notes SET {', '.join(fields)} WHERE id = ?"
                params.append(note_id)
                await self._db.execute(sql, tuple(params))
            # Tags management
            if hasattr(note_update, "tags") and getattr(note_update, "tags") is not None:
                new_tags: List[str] = getattr(note_update, "tags") or []
                # Remove old tag associations
                await self._db.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
                for tname in new_tags:
                    tag = await self._get_or_create_tag_inline(tname)
                    await self._db.execute("INSERT OR IGNORE INTO note_tags(note_id, tag_id) VALUES(?, ?)", (note_id, tag.id))
            # Add tags
            if hasattr(note_update, "add_tags") and getattr(note_update, "add_tags"):
                for tname in getattr(note_update, "add_tags"):
                    tag = await self._get_or_create_tag_inline(tname)
                    await self._db.execute("INSERT OR IGNORE INTO note_tags(note_id, tag_id) VALUES(?, ?)", (note_id, tag.id))
            # Remove tags
            if hasattr(note_update, "remove_tags") and getattr(note_update, "remove_tags"):
                for tname in getattr(note_update, "remove_tags"):
                    tag = await self.get_tag_by_name(tname)
                    if tag:
                        await self._db.execute("DELETE FROM note_tags WHERE note_id = ? AND tag_id = ?", (note_id, tag.id))
            # Re-parse links based on new content
            if content is not None:
                # remove existing links from this note
                await self._db.execute("DELETE FROM links WHERE source_id = ?", (note_id,))
                for t in self._parse_links_from_content(content):
                    target = await self.get_note_by_title(t, case_sensitive=False)
                    if target is None:
                        # Skip links to notes that don't exist yet
                        continue
                    await self._create_link(note_id, target.id, f"[[{t}]]")
            if change_message or author:
                pass  # kept for potential audit trail in DB if needed
            await self._db.commit()
        except Exception:
            try:
                await self._db.rollback()
            except Exception:
                pass
            raise
        return await self.get_note_by_id(note_id, include_relations=True)

    async def delete_note(self, note_id: str, soft_delete: bool = True) -> None:
        if not self._db:
            raise RuntimeError("Database not initialized")
        now = self._now()
        if soft_delete:
            await self._db.execute("UPDATE notes SET deleted_at = ? WHERE id = ?", (now, note_id))
        else:
            # hard delete cascades via foreign keys
            await self._db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        await self._db.commit()

    async def list_notes(
        self,
        tag_filter: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "updated_at",
        order_direction: str = "desc",
    ) -> List[Note]:
        if not self._db:
            raise RuntimeError("Database not initialized")
        base = "SELECT n.* FROM notes n"
        joins = ""
        where = ["n.deleted_at IS NULL"]
        params: List = []
        if tag_filter:
            joins += " JOIN note_tags nt ON nt.note_id = n.id JOIN tags t ON t.id = nt.tag_id"
            placeholders = ",".join(["?"] * len(tag_filter))
            where.append(f"t.name IN ({placeholders})")
            params.extend(tag_filter)
        if date_from is not None:
            where.append("n.updated_at >= ?")
            params.append(date_from.isoformat(timespec='seconds'))
        if date_to is not None:
            where.append("n.updated_at <= ?")
            params.append(date_to.isoformat(timespec='seconds'))
        where_clause = "WHERE " + " AND ".join(where) if where else ""
        sql = f"{base} {joins} {where_clause} GROUP BY n.id ORDER BY n.{order_by} {order_direction.upper()} LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor = await self._db.execute(sql, tuple(params))
        rows = [dict(r) for r in await cursor.fetchall()]
        results: List[Note] = []
        for r in rows:
            # Parse metadata JSON if present
            if "metadata" in r:
                meta = r.get("metadata")
                if isinstance(meta, str) and meta:
                    r["metadata"] = json.loads(meta)
                elif meta is None:
                    r["metadata"] = {}
            note = Note(**r)  # type: ignore
            results.append(note)
        return results

    # Tag operations
    async def create_tag(self, name: str, description: str | None = None, color: str | None = None) -> Tag:
        if not self._db:
            raise RuntimeError("Database not initialized")
        tag_id = nanoid_generate(size=8)
        await self._db.execute(
            "INSERT INTO tags(id, name, description, color) VALUES(?, ?, ?, ?)",
            (tag_id, name, description, color),
        )
        await self._db.commit()
        row = await self._db.execute("SELECT * FROM tags WHERE id = ?", (tag_id,))
        row = await row.fetchone()
        return Tag(**dict(row))  # type: ignore

    async def get_tag_by_name(self, name: str) -> Optional[Tag]:
        if not self._db:
            raise RuntimeError("Database not initialized")
        row = await self._db.execute("SELECT * FROM tags WHERE name = ?", (name,))
        row = await row.fetchone()
        if not row:
            return None
        return Tag(**dict(row))  # type: ignore

    async def list_tags(self, prefix: str | None = None, include_count: bool = True) -> List[Tag]:
        if not self._db:
            raise RuntimeError("Database not initialized")
        if prefix:
            sql = "SELECT * FROM tags WHERE name LIKE ? ORDER BY name ASC"
            cursor = await self._db.execute(sql, (f"{prefix}%",))
            rows = [dict(r) for r in await cursor.fetchall()]
        else:
            cursor = await self._db.execute("SELECT * FROM tags ORDER BY name ASC")
            rows = [dict(r) for r in await cursor.fetchall()]
        tags = [Tag(**r) for r in rows]  # type: ignore
        # Optionally fetch counts (best effort)
        if include_count:
            for t in tags:
                try:
                    c_row = await self._db.execute("SELECT COUNT(*) as cnt FROM note_tags nt WHERE nt.tag_id = ?", (t.id,))
                    c = await c_row.fetchone()
                    setattr(t, "count", int(c[0]))  # type: ignore
                except Exception:
                    pass
        return tags

    async def rename_tag(self, old_name: str, new_name: str) -> Tag:
        tag = await self.get_tag_by_name(old_name)
        if tag is None:
            raise TagNotFoundError(f"Tag '{old_name}' not found")
        await self._db.execute("UPDATE tags SET name = ? WHERE id = ?", (new_name, tag.id))
        await self._db.commit()
        return await self.get_tag_by_name(new_name)  # type: ignore

    async def delete_tag(self, tag_name: str) -> None:
        tag = await self.get_tag_by_name(tag_name)
        if tag is None:
            raise TagNotFoundError(f"Tag '{tag_name}' not found")
        await self._db.execute("DELETE FROM note_tags WHERE tag_id = ?", (tag.id,))
        await self._db.execute("DELETE FROM tags WHERE id = ?", (tag.id,))
        await self._db.commit()

    # Link operations
    async def get_links_for_note(
        self, note_id: str, direction: Literal["outgoing", "incoming", "both"] = "both"
    ) -> List[Link]:
        if not self._db:
            raise RuntimeError("Database not initialized")
        results: List[Link] = []
        if direction in ("outgoing", "both"):
            cursor = await self._db.execute("SELECT * FROM links WHERE source_id = ?", (note_id,))
            rows = [dict(r) for r in await cursor.fetchall()]
            results.extend([Link(**r) for r in rows])  # type: ignore
        if direction in ("incoming", "both"):
            cursor = await self._db.execute("SELECT * FROM links WHERE target_id = ?", (note_id,))
            rows = [dict(r) for r in await cursor.fetchall()]
            results.extend([Link(**r) for r in rows])  # type: ignore
        return results

    async def _create_link(self, source_note_id: str, target_note_id: str, link_text: str) -> Link:
        if not self._db:
            raise RuntimeError("Database not initialized")
        link_id = nanoid_generate(size=12)
        # Temporarily disable FK to allow links to notes that don't exist yet
        await self._db.execute("PRAGMA foreign_keys = OFF")
        try:
            await self._db.execute(
                "INSERT INTO links(id, source_id, target_id, link_text) VALUES(?, ?, ?, ?)",
                (link_id, source_note_id, target_note_id, link_text),
            )
        finally:
            await self._db.execute("PRAGMA foreign_keys = ON")
        row = await self._db.execute("SELECT * FROM links WHERE id = ?", (link_id,))
        row = await row.fetchone()
        return Link(**dict(row))  # type: ignore

    async def _delete_link(self, link_id: str) -> None:
        await self._db.execute("DELETE FROM links WHERE id = ?", (link_id,))
        await self._db.commit()

    def _parse_links_from_content(self, content: str) -> List[str]:
        return [m for m in re.findall(r"\[\[(.*?)\]\]", content) if m]
