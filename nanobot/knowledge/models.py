from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator


# Base model with common config (used by all knowledge models)
class BaseKnowledgeModel(BaseModel):
    # Enable ORM-like attribute population and forbid extra fields
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        from_attributes=True,
    )


class Tag(BaseKnowledgeModel):
    id: str = Field(..., description="Unique tag identifier")
    name: str = Field(min_length=1, description="Tag name (hierarchical names allowed)")
    description: Optional[str] = Field(default=None, description="Tag description")
    color: Optional[str] = Field(default=None, description="Tag color in hex format")
    created_at: Optional[datetime] = Field(default=None, description="Tag creation timestamp")
    note_count: Optional[int] = Field(default=None, description="Number of notes associated with this tag")


class Link(BaseKnowledgeModel):
    id: str = Field(..., description="Link identifier")
    source_note_id: str = Field(..., alias="source_id", description="Source note id")
    target_note_id: str = Field(..., alias="target_id", description="Target note id")
    link_text: str = Field(..., description="Link text representation")
    created_at: Optional[datetime] = Field(default=None, description="Link creation timestamp")


class Version(BaseKnowledgeModel):
    id: Optional[str] = Field(default=None, description="Version identifier")
    note_id: str = Field(..., description="Associated note id")
    version_number: int = Field(..., ge=1, description="Version number (positive integer)")
    title: str = Field(..., description="Version title")
    content: str = Field(..., description="Version content")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp for version")
    change_description: Optional[str] = Field(default=None, description="Description of changes in this version")
    author: Optional[str] = Field(default=None, description="Author of this version")


class Note(BaseKnowledgeModel):
    id: str = Field(..., description="Unique note identifier")
    title: str = Field(min_length=1, description="Note title")
    content: str = Field(default="", description="Note content in markdown format")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last modification timestamp")
    deleted_at: Optional[datetime] = Field(default=None, description="Soft delete timestamp")
    author: Optional[str] = Field(default=None, description="Author who created/last modified the note")
    change_message: Optional[str] = Field(default=None, description="Description of changes for this version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional user metadata")
    tags: List[Tag] = Field(default_factory=list, description="Associated tags")
    links: List[Link] = Field(default_factory=list, description="Outgoing links")
    backlinks: List[Link] = Field(default_factory=list, description="Incoming backlinks")

    @property
    def deleted(self) -> bool:
        """Whether this note has been soft-deleted."""
        return self.deleted_at is not None

    # Inherit base config to ensure extra fields are forbidden and aliases are supported


class NoteCreate(BaseKnowledgeModel):
    title: str = Field(min_length=1, description="Note title")
    content: str = Field(default="", description="Note content in markdown format")
    tags: Optional[List[str]] = Field(default=None, description="Associated tag names")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional user metadata")


class NoteUpdate(BaseKnowledgeModel):
    title: Optional[str] = Field(default=None, min_length=1, description="Note title")
    content: Optional[str] = Field(default=None, description="Note content in markdown format")
    tags: Optional[List[str]] = Field(default=None, description="Tag names to set for the note")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata to set on the note")
    add_tags: Optional[List[str]] = Field(default=None, description="Tags to add to the note")
    remove_tags: Optional[List[str]] = Field(default=None, description="Tags to remove from the note")
    change_message: Optional[str] = Field(default=None, description="Reason for update")
    author: Optional[str] = Field(default=None, description="Author performing the update")


class SearchResult(BaseKnowledgeModel):
    note: Note = Field(..., description="Linked note object for the search hit")
    score: float = Field(..., description="Relevance score between 0 and 1")
    match_highlights: List[str] = Field(default_factory=list, description="Highlights matching the search query")
    match_type: str = Field(..., description="Type of match (e.g., fulltext)")

    @field_validator("score")
    def _validate_score(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("score must be between 0 and 1")
        return v


__all__ = [
    "BaseKnowledgeModel",
    "Note",
    "NoteCreate",
    "NoteUpdate",
    "Tag",
    "Link",
    "Version",
    "SearchResult",
]
