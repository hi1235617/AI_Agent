from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from nanobot.agent.tools.base import Tool

# Simple global holder for a KnowledgeBase instance. The actual initialization
# is delegated to the KnowledgeBase provider in the project (via DI/singleton).
_KB_INSTANCE: Optional[Any] = None


async def _get_kb() -> Optional[Any]:
    """Resolve and initialize a KnowledgeBase instance.
    Tries a project-wide singleton first, then falls back to lazy instantiation.
    """
    global _KB_INSTANCE
    if _KB_INSTANCE is not None:
        return _KB_INSTANCE

    kb: Optional[Any] = None
    # Try to retrieve a globally provided knowledge base, if the project exposes one.
    try:
        import nanobot.knowledge as knowledge_module
        getter = getattr(knowledge_module, "get_knowledge_base", None)
        if callable(getter):
            res = getter()
            if asyncio.iscoroutine(res):
                kb = await res
            else:
                kb = res
    except Exception:
        kb = None

    # Fallback: attempt to instantiate KnowledgeBase directly
    if kb is None:
        try:
            from nanobot.knowledge import KnowledgeBase
            kb = KnowledgeBase(config=None, workspace_path=None)
            init = getattr(kb, "initialize", None)
            if callable(init):
                init_res = init()
                if asyncio.iscoroutine(init_res):
                    await init_res
        except Exception:
            kb = None

    _KB_INSTANCE = kb
    return kb


def _serialize(obj: Any) -> Any:
    """Safely serialize objects to JSON-friendly primitives for LLM consumption."""
    def _to_serial(o: Any) -> Any:
        if isinstance(o, (str, int, float, bool)) or o is None:
            return o
        if isinstance(o, dict):
            return {k: _to_serial(v) for k, v in o.items()}
        if isinstance(o, (list, tuple, set)):
            return [_to_serial(i) for i in o]
        if hasattr(o, "__dict__"):
            return {k: _to_serial(v) for k, v in o.__dict__.items()}
        return str(o)
    return _to_serial(obj)


class KnowledgeSearchTool(Tool):
    def __init__(self, store=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._store = store

    @property
    def name(self) -> str:
        return "knowledge_search"

    @property
    def description(self) -> str:
        return "搜索个人知识库中的笔记和文档。当用户的问题需要查找用户自己的笔记、文档或知识时使用此工具。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "要搜索的查询文本"},
                "limit": {"type": "integer", "default": 10, "description": "返回结果数量上限"},
                "search_type": {"type": "string", "enum": ["fulltext", "title"], "default": "fulltext", "description": "搜索类型"}
            },
            "required": ["query"]
        }

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs) -> Any:
        # Use injected store if available (for testing), otherwise use global KB
        kb = self._store
        if kb is None:
            kb = await _get_kb()
        if kb is None:
            return {"status": "error", "message": "Knowledge base 未配置或不可用。"}

        query = kwargs.get("query")
        limit = int(kwargs.get("limit", 10))
        min_score = float(kwargs.get("min_score", 0.1))
        search_type = kwargs.get("search_type", "fulltext")

        try:
            results = None
            if hasattr(kb, "search") and hasattr(kb.search, "fulltext_search"):
                results = await kb.search.fulltext_search(query=query, limit=limit, min_score=min_score)
            elif hasattr(kb, "search") and hasattr(kb.search, "tag_search"):
                results = await kb.search.tag_search(tags=[query], limit=limit)
            elif hasattr(kb, "search") and hasattr(kb.search, "semantic_search"):
                results = await kb.search.semantic_search(query, limit=limit)
            elif hasattr(kb, "search") and hasattr(kb.search, "search"):
                results = await kb.search.search(query, limit=limit)  # type: ignore
            else:
                results = []

            # Format results for LLM consumption
            formatted = []
            for r in results:
                note = getattr(r, "note", r)
                formatted.append({
                    "id": getattr(note, "id", ""),
                    "title": getattr(note, "title", ""),
                    "score": getattr(r, "score", 1.0),
                    "snippet": getattr(note, "content", "")[:200],
                })
            return formatted
        except Exception as e:
            return {"status": "error", "message": f"知识库搜索失败: {str(e)}"}


class KnowledgeCreateTool(Tool):
    def __init__(self, store=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._store = store

    @property
    def name(self) -> str:
        return "knowledge_create"

    @property
    def description(self) -> str:
        return "在个人知识库中创建新笔记。当用户要求保存信息、记录笔记、保存知识到知识库时使用此工具。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "笔记标题"},
                "content": {"type": "string", "description": "笔记内容"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "可选标签列表"}
            },
            "required": ["title", "content"]
        }

    @property
    def read_only(self) -> bool:
        return False

    async def execute(self, **kwargs) -> Any:
        kb = self._store
        if kb is None:
            kb = await _get_kb()
        if kb is None:
            return {"status": "error", "message": "Knowledge base 未配置或不可用。"}

        title = kwargs.get("title")
        content = kwargs.get("content")
        tags = kwargs.get("tags")

        if title is None or content is None:
            return {"status": "error", "message": "缺少必需参数: title 或 content"}

        try:
            from nanobot.knowledge.models import NoteCreate
            note_create = NoteCreate(title=title, content=content, tags=tags)
            note = await kb.create_note(note_create)
            return {
                "status": "success",
                "note": {
                    "id": getattr(note, "id", ""),
                    "title": getattr(note, "title", ""),
                    "content": getattr(note, "content", ""),
                }
            }
        except Exception as e:
            return {"status": "error", "message": f"创建笔记失败: {str(e)}"}


class KnowledgeUpdateTool(Tool):
    def __init__(self, store=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._store = store

    @property
    def name(self) -> str:
        return "knowledge_update"

    @property
    def description(self) -> str:
        return "更新个人知识库中的现有笔记。当用户要求修改、补充已有笔记时使用此工具。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "note_id": {"type": "string", "description": "要更新的笔记ID"},
                "title": {"type": "string", "description": "新的标题（可选)"},
                "content": {"type": "string", "description": "新的笔记内容（可选)"},
                "append": {"type": "string", "description": "附加文本追加到笔记末尾（可选)"},
                "add_tags": {"type": "array", "items": {"type": "string"}, "description": "要新增的标签（可选)"},
                "remove_tags": {"type": "array", "items": {"type": "string"}, "description": "要移除的标签（可选)"}
            },
            "required": ["note_id"]
        }

    @property
    def read_only(self) -> bool:
        return False

    async def execute(self, **kwargs) -> Any:
        kb = self._store
        if kb is None:
            kb = await _get_kb()
        if kb is None:
            return {"status": "error", "message": "Knowledge base 未配置或不可用。"}

        note_id = kwargs.get("note_id")
        title = kwargs.get("title")
        content = kwargs.get("content")
        append = kwargs.get("append")
        add_tags = kwargs.get("add_tags")
        remove_tags = kwargs.get("remove_tags")

        if not note_id:
            return {"status": "error", "message": "缺少必需参数: note_id"}

        try:
            from nanobot.knowledge.models import NoteUpdate
            note_update = NoteUpdate(
                title=title,
                content=content,
                add_tags=add_tags,
                remove_tags=remove_tags,
            )
            note = await kb.update_note(note_id, note_update)
            return {
                "status": "success",
                "note": {
                    "id": getattr(note, "id", ""),
                    "title": getattr(note, "title", ""),
                    "content": getattr(note, "content", ""),
                }
            }
        except Exception as e:
            return {"status": "error", "message": f"更新笔记失败: {str(e)}"}


class KnowledgeGetTool(Tool):
    def __init__(self, store=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._store = store

    @property
    def name(self) -> str:
        return "knowledge_get"

    @property
    def description(self) -> str:
        return "获取个人知识库中指定笔记的完整内容。当需要查看某篇笔记的具体内容时使用此工具。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "note_id": {"type": "string", "description": "笔记ID"},
                "version": {"type": "string", "description": "可选版本标识"}
            },
            "required": ["note_id"]
        }

    @property
    def read_only(self) -> bool:
        return True

    async def execute(self, **kwargs) -> Any:
        kb = self._store
        if kb is None:
            kb = await _get_kb()
        if kb is None:
            return {"status": "error", "message": "Knowledge base 未配置或不可用。"}

        note_id = kwargs.get("note_id")
        version = kwargs.get("version")
        if not note_id:
            return {"status": "error", "message": "缺少必需参数: note_id"}

        try:
            note = await kb.get_note_by_id(note_id, include_relations=True)
            return {
                "status": "success",
                "note": {
                    "id": getattr(note, "id", ""),
                    "title": getattr(note, "title", ""),
                    "content": getattr(note, "content", ""),
                }
            }
        except Exception as e:
            return {"status": "error", "message": f"获取笔记失败: {str(e)}"}
