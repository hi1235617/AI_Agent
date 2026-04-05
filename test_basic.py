import asyncio
from pathlib import Path
from nanobot.knowledge.store import KnowledgeStore
from nanobot.knowledge.models import NoteCreate

async def test_basic():
    print("Testing KnowledgeStore basic functionality...")
    # 创建临时测试数据库
    tmp_path = Path("./test_temp")
    tmp_path.mkdir(exist_ok=True)
    db_path = tmp_path / "test.db"
    
    # 初始化store
    store = KnowledgeStore(db_path=str(db_path), storage_path=str(tmp_path))
    await store.initialize()
    
    print(f"Store instance type: {type(store)}")
    print(f"Store methods: {[m for m in dir(store) if not m.startswith('_')]}")
    
    # 测试调用create_note
    try:
        note = await store.create_note(NoteCreate(
            title="Test Note",
            content="Test content"
        ))
        print(f"Create note success: {note.id}, {note.title}")
        return True
    except AttributeError as e:
        print(f"AttributeError: {e}")
        print(f"hasattr(store, 'create_note'): {hasattr(store, 'create_note')}")
        return False
    finally:
        await store.close()
        # 清理临时文件
        import shutil
        shutil.rmtree(tmp_path)

if __name__ == "__main__":
    success = asyncio.run(test_basic())
    exit(0 if success else 1)