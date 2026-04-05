import asyncio
from pathlib import Path
from nanobot.knowledge.store import KnowledgeStore
from nanobot.knowledge.models import NoteCreate
from nanobot.knowledge.graph import KnowledgeGraph

async def test():
    tmp = Path('./test_graph_debug')
    tmp.mkdir(exist_ok=True)
    db = tmp / 'test.db'
    store = KnowledgeStore(db_path=str(db), storage_path=str(tmp))
    await store.initialize()
    
    note1 = await store.create_note(NoteCreate(title="Note 1", content="[[Note 2]] [[Note 3]]"))
    note2 = await store.create_note(NoteCreate(title="Note 2", content="[[Note 3]]"))
    note3 = await store.create_note(NoteCreate(title="Note 3", content="[[Note 4]]"))
    note4 = await store.create_note(NoteCreate(title="Note 4", content=""))
    
    print("Notes created:")
    print(f"  note1.id={note1.id}, note2.id={note2.id}, note3.id={note3.id}, note4.id={note4.id}")
    
    # Check links table
    cursor = await store._db.execute("SELECT * FROM links")
    rows = await cursor.fetchall()
    print(f"\nLinks table ({len(rows)} rows):")
    for r in rows:
        d = dict(r)
        print(f"  {d}")
    
    graph = KnowledgeGraph(store=store)
    g = await graph.build_graph()
    print(f"\nGraph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    print("Edges:")
    for u, v, data in g.edges(data=True):
        print(f"  {u} -> {v}: {data}")
    
    # Test get_neighbors at depth 1
    neighbors1 = await graph.get_neighbors(note1.id, depth=1)
    print(f"\nDepth 1: {len(neighbors1['nodes'])} nodes, {len(neighbors1['edges'])} edges")
    print(f"  nodes: {neighbors1['nodes']}")
    print(f"  edges: {neighbors1['edges']}")
    
    neighbors2 = await graph.get_neighbors(note1.id, depth=2)
    print(f"\nDepth 2: {len(neighbors2['nodes'])} nodes, {len(neighbors2['edges'])} edges")
    print(f"  nodes: {neighbors2['nodes']}")
    print(f"  edges: {neighbors2['edges']}")
    
    await store.close()
    import shutil
    shutil.rmtree(tmp)

asyncio.run(test())
