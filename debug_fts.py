import asyncio
from pathlib import Path
from nanobot.knowledge.store import KnowledgeStore
from nanobot.knowledge.models import NoteCreate
from nanobot.knowledge.graph import KnowledgeGraph
from nanobot.knowledge.search import SearchService

async def test():
    tmp = Path('./test_fts4')
    tmp.mkdir(exist_ok=True)
    db = tmp / 'test.db'
    store = KnowledgeStore(db_path=str(db), storage_path=str(tmp))
    await store.initialize()
    
    await store.create_note(NoteCreate(
        title='Python Async Guide',
        content='This guide covers async programming in Python. Async/await is used for I/O operations.'
    ))
    
    graph = KnowledgeGraph(store=store)
    await graph.build_graph()
    search = SearchService(store=store, graph=graph)
    
    # Debug: check _ensure_db
    print('store._db:', store._db)
    search._ensure_db()
    print('_ensure_db passed')
    
    # Run the query directly
    sql = 'SELECT nf.note_id AS note_id, -bm25(notes_fts) AS score FROM notes_fts nf JOIN notes n ON n.id = nf.note_id WHERE notes_fts MATCH ? AND n.deleted_at IS NULL ORDER BY score DESC LIMIT ?'
    cursor = await store._db.execute(sql, ('async', 10))
    rows = await cursor.fetchall()
    print('Query rows:', len(rows))
    for r in rows:
        d = dict(r)
        nid = d.get('note_id')
        score = d.get('score')
        print('  note_id=%s, score=%s' % (nid, score))
        # Now try to get the note
        try:
            note = await store.get_note_by_id(nid, include_relations=True, include_deleted=False)
            print('  Got note:', note.title)
        except Exception as e:
            print('  get_note_by_id error: %s: %s' % (type(e).__name__, e))
    
    # Now try the full method
    try:
        results = await search.fulltext_search('async', limit=10)
        print('fulltext_search results:', len(results))
    except Exception as e:
        print('fulltext_search exception: %s: %s' % (type(e).__name__, e))
    
    await store.close()
    import shutil
    shutil.rmtree(tmp)

asyncio.run(test())
