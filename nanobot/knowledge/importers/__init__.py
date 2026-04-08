"""
Knowledge base importers module.
Supports importing notes from various formats: Markdown, JSON, Obsidian, Notion, etc.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..models import NoteCreate
from ..exceptions import ImportError


class MarkdownImporter:
    """Markdown file importer."""
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    async def import_file(self, path: str) -> List[NoteCreate]:
        """Import notes from markdown file."""
        path_obj = Path(path)
        if not path_obj.exists():
            raise ImportError(f"File not found: {path}")
            
        content = path_obj.read_text(encoding="utf-8")
        title = path_obj.stem
        return [NoteCreate(title=title, content=content)]


async def import_notes(path: str, format: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
    """
    Import notes from a file or directory.
    
    Args:
        path: Path to import file or directory
        format: Import format (auto-detected if not provided)
        **kwargs: Additional import options
    
    Returns:
        List of imported note data
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise ImportError(f"Import path not found: {path}")
    
    # Simple JSON import implementation
    if format == "json" or path_obj.suffix.lower() == ".json":
        import json
        with open(path_obj, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        notes = []
        for item in data:
            if isinstance(item, dict) and "title" in item and "content" in item:
                notes.append(NoteCreate(
                    title=item["title"],
                    content=item["content"],
                    tags=item.get("tags", [])
                ))
        return notes
    
    # Markdown import
    if format == "md" or format == "markdown" or path_obj.suffix.lower() in (".md", ".markdown"):
        content = path_obj.read_text(encoding="utf-8")
        title = path_obj.stem
        return [NoteCreate(title=title, content=content)]
    
    raise ImportError(f"Unsupported import format: {format or path_obj.suffix}")


__all__ = ["import_notes", "ImportError", "MarkdownImporter"]