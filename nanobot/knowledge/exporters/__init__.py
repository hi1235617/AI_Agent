"""
Knowledge base exporters module.
Supports exporting notes to various formats: Markdown, JSON, PDF, HTML, etc.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..exceptions import ExportError


class JsonExporter:
    """JSON file exporter."""
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    async def export(self, notes: List[Any], path: str) -> None:
        """Export notes to JSON file."""
        import json
        path_obj = Path(path)
        export_data = []
        for note in notes:
            export_data.append({
                "id": getattr(note, "id", ""),
                "title": getattr(note, "title", ""),
                "content": getattr(note, "content", ""),
                "tags": getattr(note, "tags", []),
                "created_at": getattr(note, "created_at", ""),
                "updated_at": getattr(note, "updated_at", "")
            })
        
        with open(path_obj, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)


async def export_notes(notes: List[Any], path: str, format: Optional[str] = None, **kwargs) -> None:
    """
    Export notes to a file or directory.
    
    Args:
        notes: List of notes to export
        path: Destination path
        format: Export format (auto-detected if not provided)
        **kwargs: Additional export options
    """
    path_obj = Path(path)
    
    # JSON export
    if format == "json" or path_obj.suffix.lower() == ".json":
        import json
        export_data = []
        for note in notes:
            export_data.append({
                "id": getattr(note, "id", ""),
                "title": getattr(note, "title", ""),
                "content": getattr(note, "content", ""),
                "tags": getattr(note, "tags", []),
                "created_at": getattr(note, "created_at", ""),
                "updated_at": getattr(note, "updated_at", "")
            })
        
        with open(path_obj, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        return
    
    # Markdown export
    if format == "md" or format == "markdown" or path_obj.suffix.lower() in (".md", ".markdown"):
        if path_obj.is_dir():
            # Export individual markdown files
            for note in notes:
                note_id = getattr(note, "id", "note")
                title = getattr(note, "title", "untitled").replace("/", "_").replace("\\", "_")
                filename = f"{note_id}_{title}.md"
                file_path = path_obj / filename
                content = f"# {getattr(note, 'title', '')}\n\n{getattr(note, 'content', '')}"
                file_path.write_text(content, encoding="utf-8")
        else:
            # Export all notes to a single markdown file
            content = []
            for note in notes:
                content.append(f"# {getattr(note, 'title', '')}\n")
                content.append(f"*ID: {getattr(note, 'id', '')}*\n")
                content.append(f"*Created: {getattr(note, 'created_at', '')}*\n\n")
                content.append(f"{getattr(note, 'content', '')}\n\n---\n\n")
            
            path_obj.write_text("\n".join(content), encoding="utf-8")
        return
    
    raise ExportError(f"Unsupported export format: {format or path_obj.suffix}")


__all__ = ["export_notes", "ExportError", "JsonExporter"]