"""Exception classes for the Knowledge Base module."""
from __future__ import annotations


class KnowledgeBaseError(Exception):
    """Base exception for knowledge base errors."""
    pass


class NoteNotFoundError(KnowledgeBaseError):
    """Raised when a note with the given identifier is not found."""
    def __init__(self, note_id: str | int, message: str | None = None):
        if message is None:
            message = f"Note with id '{note_id}' not found."
        super().__init__(message)
        self.note_id = note_id


class TagNotFoundError(KnowledgeBaseError):
    """Raised when a tag is not found in the knowledge base."""
    def __init__(self, tag_name: str, message: str | None = None):
        if message is None:
            message = f"Tag '{tag_name}' not found."
        super().__init__(message)
        self.tag_name = tag_name


class LinkNotFoundError(KnowledgeBaseError):
    """Raised when a link (reference) is not found in a note or graph."""
    def __init__(self, link_identifier: str, message: str | None = None):
        if message is None:
            message = f"Link '{link_identifier}' not found."
        super().__init__(message)
        self.link_identifier = link_identifier


class VersionNotFoundError(KnowledgeBaseError):
    """Raised when a specific version of a note or entity is not found."""
    def __init__(self, version: str | int, message: str | None = None):
        if message is None:
            message = f"Version '{version}' not found."
        super().__init__(message)
        self.version = version


class StorageError(KnowledgeBaseError):
    """Raised for storage-related errors in knowledge base persistence."""
    def __init__(self, storage_target: str, message: str | None = None):
        if message is None:
            message = f"Storage error for '{storage_target}'."
        super().__init__(message)
        self.storage_target = storage_target


class SearchError(KnowledgeBaseError):
    """Raised when a search operation fails within the knowledge base."""
    def __init__(self, query: str | None = None, message: str | None = None):
        if message is None:
            if query:
                message = f"Search failed for query: {query}"
            else:
                message = "Search operation failed."
        super().__init__(message)
        self.query = query


class GraphError(KnowledgeBaseError):
    """Raised for errors related to knowledge graph operations."""
    def __init__(self, graph_node: str | None = None, message: str | None = None):
        if message is None:
            if graph_node:
                message = f"Graph error at node '{graph_node}'."
            else:
                message = "Graph operation failed."
        super().__init__(message)
        self.graph_node = graph_node


class ImportError(KnowledgeBaseError):
    """Raised when an import operation fails."""
    def __init__(self, message: str):
        super().__init__(message)


class ExportError(KnowledgeBaseError):
    """Raised when an export operation fails."""
    def __init__(self, message: str):
        super().__init__(message)


class MigrationError(KnowledgeBaseError):
    """Raised when a migration operation fails."""
    def __init__(self, message: str):
        super().__init__(message)
