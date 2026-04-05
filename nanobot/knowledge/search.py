from __future__ import annotations

"""Knowledge search service.

This module provides a SearchService that offers full-text search (SQLite FTS5),
tag-based search, a placeholder semantic search, a hybrid search passthrough,
and an autocomplete API.

Notes:
- The full-text search uses the notes_fts virtual table and bm25 scoring.
- The implementation is designed to work with the existing KnowledgeStore from
  nanobot/knowledge/store.py and the models defined in nanobot/knowledge/models.py.
- Semantic search is left as a placeholder for future implementation.
"""

from typing import List, Optional, Literal
from dataclasses import dataclass

from .store import KnowledgeStore
from .graph import KnowledgeGraph
from .models import Note, SearchResult
from .exceptions import SearchError


@dataclass
class _Highlight:
    field: str
    text: str


class SearchService:
    def __init__(self, store: KnowledgeStore, graph: KnowledgeGraph) -> None:
        self.store = store
        self.graph = graph

    # --------- Helpers ---------
    def _ensure_db(self) -> None:
        if not getattr(self.store, "_db", None):
            raise SearchError(query=None, message="Knowledge store is not initialized (database not ready).")

    def _build_highlights(self, query: str, note: Note) -> List[str]:
        highlights: List[str] = []
        q = (query or "").lower()
        title = getattr(note, "title", "") or ""
        content = getattr(note, "content", "") or ""
        if q and q in (title or "").lower():
            highlights.append(title)
        if q:
            c_lower = content.lower()
            idx = c_lower.find(q)
            if idx != -1:
                # Simple snippet around the match
                start = max(0, idx - 60)
                end = min(len(content), idx + 60)
                snippet = content[start:end].replace("\n", " ")
                highlights.append(snippet)
        return highlights

    # --------- Public API ---------
    async def fulltext_search(
        self,
        query: str,
        tag_filter: Optional[List[str]] = None,
        limit: int = 20,
        min_score: float = 0.1,
        include_content: bool = False,
        offset: int = 0,
    ) -> List[SearchResult]:
        self._ensure_db()
        # Use FTS5 BM25 ranking on the notes_fts virtual table
        sql = (
            "SELECT nf.note_id AS note_id, -bm25(notes_fts) AS score "
            "FROM notes_fts nf JOIN notes n ON n.id = nf.note_id "
            "WHERE notes_fts MATCH ? AND n.deleted_at IS NULL "
            "ORDER BY score DESC LIMIT ? OFFSET ?"
        )
        try:
            cursor = await self.store._db.execute(sql, (query, limit + offset, offset))  # type: ignore[attr-defined]
            rows = [dict(r) for r in await cursor.fetchall()]  # type: ignore
        except Exception as exc:  # pragma: no cover - guard against DB issues
            raise SearchError(query=query) from exc

        # Normalize bm25 scores to 0-1 range (bm25 returns very small values)
        if rows:
            max_score = max(float(r.get("score", 0.0)) for r in rows)
            if max_score > 0:
                for row in rows:
                    row["score"] = float(row.get("score", 0.0)) / max_score

        results: List[SearchResult] = []
        # If a tag filter is provided, we'll filter on the Python side after fetching notes
        for row in rows:
            note_id = row.get("note_id")
            score = float(row.get("score", 0.0))
            if score < min_score:
                continue
            try:
                note: Note = await self.store.get_note_by_id(note_id, include_relations=True, include_deleted=False)  # type: ignore
            except Exception:
                continue
            if tag_filter:
                note_tag_names = [t.name for t in getattr(note, "tags", [])]  # type: ignore[attr-defined]
                if not any(t in note_tag_names for t in tag_filter):
                    continue
            highlights = self._build_highlights(query, note)
            results.append(SearchResult(note=note, score=score, match_highlights=highlights, match_type="fulltext"))  # type: ignore[arg-type]

        # Sort by score descending for relevance
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    async def tag_search(
        self,
        tags: List[str],
        match_all: bool = True,
        limit: int = 100,
        include_subtags: bool = True,
    ) -> List[SearchResult]:
        self._ensure_db()
        if not tags:
            return []
        # Build per-tag sets of note_ids
        id_sets: List[set[str]] = []
        for tname in tags:
            if include_subtags:
                sql = "SELECT DISTINCT nt.note_id FROM note_tags nt JOIN tags ta ON ta.id = nt.tag_id WHERE ta.name LIKE ?"
                param = (f"{tname}%",)
            else:
                sql = "SELECT DISTINCT nt.note_id FROM note_tags nt JOIN tags ta ON ta.id = nt.tag_id WHERE ta.name = ?"
                param = (tname,)
            try:
                cursor = await self.store._db.execute(sql, param)  # type: ignore[attr-defined]
                rows = [dict(r) for r in await cursor.fetchall()]
                ids = {r["note_id"] for r in rows}
                id_sets.append(ids)
            except Exception:
                id_sets.append(set())
        if not id_sets:
            return []
        if match_all:
            candidate_ids = set.intersection(*id_sets) if id_sets else set()
        else:
            candidate_ids = set().union(*id_sets) if id_sets else set()
        results: List[SearchResult] = []
        for nid in list(candidate_ids)[:limit]:
            try:
                note: Note = await self.store.get_note_by_id(nid, include_relations=True, include_deleted=False)  # type: ignore
            except Exception:
                continue
            score = 1.0
            highlights = [f"tag:{tg}" for tg in tags if any(t.name == tg for t in getattr(note, "tags", []))]  # type: ignore[attr-defined]
            results.append(SearchResult(note=note, score=score, match_highlights=highlights, match_type="tag"))  # type: ignore[arg-type]
        # Optional sort by a simple heuristic (score is constant here, could sort by updated_at)
        return results[:limit]

    async def semantic_search(
        self,
        query: str,
        limit: int = 20,
        min_similarity: float = 0.7,
    ) -> List[SearchResult]:
        # Fallback to full-text search with OR matching since semantic search is not yet implemented
        # Use OR matching to find notes containing ANY of the query terms
        terms = query.split()
        if len(terms) > 1:
            or_query = " OR ".join(terms)
        else:
            or_query = query
        return await self.fulltext_search(query=or_query, limit=limit, min_score=0.0)

    async def hybrid_search(
        self,
        query: str,
        tag_filter: Optional[List[str]] = None,
        limit: int = 20,
        fulltext_weight: float = 0.6,
        semantic_weight: float = 0.4,
    ) -> List[SearchResult]:
        # For now, only full-text search is implemented. Semantic component is a TODO.
        return await self.fulltext_search(query=query, tag_filter=tag_filter, limit=limit, min_score=0.0)

    async def autocomplete(
        self,
        prefix: str,
        field: Literal["title", "tag", "content"] = "title",
        limit: int = 10,
    ) -> List[str]:
        self._ensure_db()
        prefix_like = f"{prefix}%"
        suggestions: List[str] = []
        try:
            if field == "title":
                sql = "SELECT DISTINCT title FROM notes WHERE deleted_at IS NULL AND title LIKE ? LIMIT ?"
                cursor = await self.store._db.execute(sql, (prefix_like, limit))  # type: ignore[attr-defined]
                suggestions = [row[0] for row in await cursor.fetchall()]
            elif field == "tag":
                sql = "SELECT DISTINCT name FROM tags WHERE name LIKE ? LIMIT ?"
                cursor = await self.store._db.execute(sql, (prefix_like, limit))  # type: ignore[attr-defined]
                suggestions = [row[0] for row in await cursor.fetchall()]
            else:  # content
                sql = "SELECT DISTINCT substr(content, 1, 400) as snippet FROM notes WHERE content LIKE ? LIMIT ?"
                cursor = await self.store._db.execute(sql, (prefix_like, limit))  # type: ignore[attr-defined]
                suggestions = [row[0] for row in await cursor.fetchall()]
        except Exception as exc:  # pragma: no cover
            raise SearchError(query=prefix) from exc
        # Deduplicate while preserving order
        seen = set()
        out: List[str] = []
        for s in suggestions:
            if s and s not in seen:
                seen.add(s)
                out.append(str(s))
        return out[:limit]
