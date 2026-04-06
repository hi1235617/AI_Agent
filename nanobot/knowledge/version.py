from __future__ import annotations

import os
import json
import difflib
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from .store import KnowledgeStore
from .models import Version, Note
from .exceptions import VersionNotFoundError, NoteNotFoundError


class VersionManager:
    """
    Async version manager for knowledge notes.

    Features:
    - Save a version snapshot for a note
    - List versions for a note
    - Retrieve a specific version
    - Restore to a given version (optionally creating a snapshot of current state)
    - Delete version history (with optional retention policy)
    - Compute diffs between two versions using difflib

    Storage backend:
    - Version data persisted in the filesystem under versions_dir/<note_id>/version_<n>.json
      Each file contains: version_number, title, content, change_description, author, timestamp
    - The current note content/title is retrieved via the provided KnowledgeStore
    - If a database-backed approach is preferred, this class can be extended to support it
    in addition to the filesystem-based store.
    """

    def __init__(self, store: KnowledgeStore, versions_dir: str):
        self.store = store
        self.versions_dir = versions_dir
        self.max_versions_per_note: Optional[int] = None
        Path(self.versions_dir).mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # Internal helpers
    # -----------------------------
    async def _load_version_object(self, note_id: str, version_number: int) -> Version:
        """
        Load a Version object from the filesystem for a given note/version.
        """
        path = self._version_path(note_id, version_number)
        if not os.path.exists(path):
            raise VersionNotFoundError(f"Version {version_number} for note {note_id} not found")
        data = await asyncio.to_thread(self._read_json, path)

        # Prefer model's own constructor / factory if available
        if hasattr(Version, "from_dict"):
            return Version.from_dict(data)  # type: ignore[call-arg]
        # Fallback to direct construction (assumes typical fields)
        return Version(
            note_id=note_id,
            version_number=data.get("version_number", version_number),
            title=data.get("title"),
            content=data.get("content"),
            change_description=data.get("change_description"),
            author=data.get("author"),
            created_at=data.get("timestamp"),
        )

    @staticmethod
    def _read_json(path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _write_json(path: str, data: Dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _version_path(self, note_id: str, version_number: int) -> str:
        note_dir = os.path.join(self.versions_dir, str(note_id))
        return os.path.join(note_dir, f"version_{version_number}.json")

    def _ensure_note_dir(self, note_id: str) -> None:
        note_dir = os.path.join(self.versions_dir, str(note_id))
        Path(note_dir).mkdir(parents=True, exist_ok=True)

    async def _current_note(self, note_id: str) -> Note:
        note = await self.store.get_note_by_id(note_id, include_relations=True, include_deleted=False)
        if note is None:
            raise NoteNotFoundError(f"Note {note_id} not found")
        return note

    async def _update_current_note(self, note_id: str, title: Optional[str], content: Optional[str]) -> None:
        from .models import NoteUpdate
        update = NoteUpdate(title=title, content=content)
        await self.store.update_note(note_id, update)

    # -----------------------------
    # Public API
    # -----------------------------
    async def save_version(
        self,
        note_id: str,
        change_description: Optional[str] = None,
        author: Optional[str] = None,
    ) -> Version:
        """
        Save a new version snapshot for the given note.
        """
        # Retrieve current note state
        current_note: Note = await self._current_note(note_id)
        current_title = getattr(current_note, "title", None)
        current_content = getattr(current_note, "content", None)

        # Ensure storage path
        self._ensure_note_dir(note_id)
        note_dir = os.path.join(self.versions_dir, str(note_id))

        # Determine next version number
        max_ver = 0
        for fname in os.listdir(note_dir):
            if fname.startswith("version_") and fname.endswith(".json"):
                try:
                    num = int(fname[len("version_"):-len(".json")])
                    if num > max_ver:
                        max_ver = num
                except ValueError:
                    continue
        version_number = max_ver + 1

        timestamp = datetime.utcnow().isoformat() + "Z"
        data = {
            "version_number": version_number,
            "title": current_title,
            "content": current_content,
            "change_description": change_description,
            "author": author,
            "timestamp": timestamp,
        }

        path = self._version_path(note_id, version_number)
        await asyncio.to_thread(self._write_json, path, data)

        # Prune old versions if max_versions_per_note is set
        if self.max_versions_per_note is not None:
            await self._prune_versions(note_id)

        # Create Version model instance from data when possible
        if hasattr(Version, "from_dict"):
            return Version.from_dict(data)  # type: ignore[call-arg]
        return Version(
            id=f"version-{version_number}",
            note_id=note_id,
            version_number=version_number,
            title=current_title,
            content=current_content,
            change_description=change_description,
            author=author,
            created_at=timestamp,
        )

    async def list_versions(
        self,
        note_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Version]:
        """
        List versions for a note, with pagination.
        """
        note_dir = os.path.join(self.versions_dir, str(note_id))
        if not os.path.isdir(note_dir):
            return []

        version_numbers: List[int] = []
        for fname in os.listdir(note_dir):
            if fname.startswith("version_") and fname.endswith(".json"):
                try:
                    num = int(fname[len("version_"):-len(".json")])
                    version_numbers.append(num)
                except ValueError:
                    continue
        version_numbers.sort(reverse=True)  # descending by version (newest first)

        sliced = version_numbers[offset: offset + limit]
        versions: List[Version] = []
        for vn in sliced:
            ver = await self._load_version_object(note_id, vn)
            versions.append(ver)
        return versions

    async def get_version(self, note_id: str, version_number: int) -> Optional[Version]:
        """
        Retrieve a specific version. Returns Version or None if not found.
        """
        try:
            return await self._load_version_object(note_id, version_number)
        except VersionNotFoundError:
            return None

    async def restore_version(
        self,
        note_id: str,
        version_number: int,
        create_snapshot: bool = True,
    ) -> Note:
        """
        Restore the note to a specified version. If create_snapshot is True, record the
        current state as a new version before applying the restore.
        Returns the updated Note object.
        """
        # Load target version contents
        target_version = await self._load_version_object(note_id, version_number)

        # Optionally create a snapshot of the current state before restore
        if create_snapshot:
            await self.save_version(
                note_id,
                change_description=f"Snapshot before restore to version {version_number}",
                author=None,
            )

        # Temporarily disable version manager to prevent double-save during restore
        old_vm = getattr(self.store, "_version_manager", None)
        try:
            self.store._version_manager = None
            # Update current note with target content
            await self._update_current_note(
                note_id,
                title=getattr(target_version, "title", None),
                content=getattr(target_version, "content", None),
            )
        finally:
            self.store._version_manager = old_vm

        # Return the updated note
        note = await self.store.get_note_by_id(note_id, include_relations=True, include_deleted=False)
        if note is None:
            raise NoteNotFoundError(f"Note {note_id} not found after restore")
        return note

    async def _prune_versions(self, note_id: str) -> None:
        """Delete oldest versions to keep only max_versions_per_note."""
        if self.max_versions_per_note is None:
            return
        note_dir = os.path.join(self.versions_dir, str(note_id))
        if not os.path.exists(note_dir):
            return
        version_nums = []
        for fname in os.listdir(note_dir):
            if fname.startswith("version_") and fname.endswith(".json"):
                try:
                    num = int(fname[len("version_"):-len(".json")])
                    version_nums.append(num)
                except ValueError:
                    continue
        version_nums.sort()
        # Delete oldest versions beyond the limit
        while len(version_nums) > self.max_versions_per_note:
            oldest = version_nums.pop(0)
            path = self._version_path(note_id, oldest)
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    async def delete_version_history(self, note_id: str, keep_latest: Optional[int] = None) -> None:
        """
        Delete version history for a note. If keep_latest is provided, retain the latest N versions.
        """
        note_dir = os.path.join(self.versions_dir, str(note_id))
        if not os.path.isdir(note_dir):
            return

        version_numbers: List[int] = []
        for fname in os.listdir(note_dir):
            if fname.startswith("version_") and fname.endswith(".json"):
                try:
                    num = int(fname[len("version_"):-len(".json")])
                    version_numbers.append(num)
                except ValueError:
                    continue
        version_numbers.sort()

        to_keep: set[int] = set()
        if keep_latest is not None and keep_latest > 0:
            to_keep = set(version_numbers[-keep_latest:])

        # Delete files not in to_keep
        for vn in version_numbers:
            if vn not in to_keep:
                path = self._version_path(note_id, vn)
                try:
                    os.remove(path)
                except FileNotFoundError:
                    pass

        # If directory becomes empty, it's okay to leave it as is or clean up
        # We'll leave an empty directory as is to avoid surprises.

    async def get_version_diff(self, note_id: str, version1: int, version2: int) -> Dict[str, Any]:
        """
        Generate a structured diff between two versions using difflib.
        Returns a dictionary with a human-friendly diff string and some metadata.
        """
        old_ver = await self._load_version_object(note_id, version1)
        new_ver = await self._load_version_object(note_id, version2)

        old_text = (getattr(old_ver, "content", "") or "")
        new_text = (getattr(new_ver, "content", "") or "")

        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        diff_text = "\n".join(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"version_{version1}",
                tofile=f"version_{version2}",
                lineterm="",
            )
        )

        return {
            "note_id": note_id,
            "version1": version1,
            "version2": version2,
            "title_before": getattr(old_ver, "title", None),
            "title_after": getattr(new_ver, "title", None),
            "diff": diff_text,
        }
