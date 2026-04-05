import pytest
from nanobot.knowledge.graph import KnowledgeGraph
from nanobot.knowledge.models import NoteCreate


@pytest.fixture
async def knowledge_graph(knowledge_store):
    """Create a KnowledgeGraph instance for testing."""
    return KnowledgeGraph(store=knowledge_store)


@pytest.mark.asyncio
async def test_build_graph(knowledge_store, knowledge_graph):
    """Test building the knowledge graph from stored notes and links."""
    # Create test notes with links
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content="[[Note 2]]"))
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content="[[Note 3]]"))
    note3 = await knowledge_store.create_note(NoteCreate(title="Note 3", content="[[Note 1]]"))
    
    # Build graph
    graph = await knowledge_graph.build_graph()
    
    # Should have 3 nodes and 3 edges
    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 3
    
    # Check that all nodes are present
    assert note1.id in graph.nodes
    assert note2.id in graph.nodes
    assert note3.id in graph.nodes
    
    # Check edges
    assert graph.has_edge(note1.id, note2.id)
    assert graph.has_edge(note2.id, note3.id)
    assert graph.has_edge(note3.id, note1.id)


@pytest.mark.asyncio
async def test_get_neighbors(knowledge_store, knowledge_graph):
    """Test retrieving neighbor nodes for a note."""
    # Create a small graph
    # Note1 -> Note2 -> Note3 -> Note4
    # Note1 -> Note3
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content="[[Note 2]] [[Note 3]]"))
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content="[[Note 3]]"))
    note3 = await knowledge_store.create_note(NoteCreate(title="Note 3", content="[[Note 4]]"))
    note4 = await knowledge_store.create_note(NoteCreate(title="Note 4", content=""))
    
    # Get neighbors at depth 1 - visited nodes: note1, note2, note3
    # All edges between these: note1->note2, note1->note3, note2->note3
    neighbors_depth1 = await knowledge_graph.get_neighbors(note1.id, depth=1)
    assert len(neighbors_depth1["nodes"]) == 3  # note1 + note2 + note3
    assert len(neighbors_depth1["edges"]) == 3  # note1->note2, note1->note3, note2->note3
    
    # Get neighbors at depth 2 - all 4 notes
    # All edges: note1->note2, note1->note3, note2->note3, note3->note4
    neighbors_depth2 = await knowledge_graph.get_neighbors(note1.id, depth=2)
    assert len(neighbors_depth2["nodes"]) == 4  # all notes
    assert len(neighbors_depth2["edges"]) == 4  # note1->note2, note1->note3, note2->note3, note3->note4
    
    # Get only outgoing neighbors
    outgoing = await knowledge_graph.get_neighbors(note1.id, depth=1, direction="outgoing")
    assert len(outgoing["nodes"]) == 3  # note1, note2, note3
    
    # Get only incoming neighbors (note3 should have 2 incoming: note1 and note2)
    incoming = await knowledge_graph.get_neighbors(note3.id, depth=1, direction="incoming")
    assert len(incoming["nodes"]) == 3  # note3, note1, note2


@pytest.mark.asyncio
async def test_get_shortest_path(knowledge_store, knowledge_graph):
    """Test finding the shortest path between two notes."""
    # Create graph: Note1 -> Note2 -> Note3 -> Note4
    # Also Note1 -> Note4 (direct edge)
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content="[[Note 2]] [[Note 4]]"))
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content="[[Note 3]]"))
    note3 = await knowledge_store.create_note(NoteCreate(title="Note 3", content="[[Note 4]]"))
    note4 = await knowledge_store.create_note(NoteCreate(title="Note 4", content=""))
    
    # Shortest path from note1 to note4 should be direct (length 1)
    path = await knowledge_graph.get_shortest_path(note1.id, note4.id)
    assert path == [note1.id, note4.id]
    
    # Shortest path from note2 to note4 is length 2 (note2 -> note3 -> note4)
    path = await knowledge_graph.get_shortest_path(note2.id, note4.id)
    assert path == [note2.id, note3.id, note4.id]
    
    # No path between disconnected notes
    note5 = await knowledge_store.create_note(NoteCreate(title="Note 5", content=""))
    path = await knowledge_graph.get_shortest_path(note1.id, note5.id)
    assert path is None


@pytest.mark.asyncio
async def test_get_connected_components(knowledge_store, knowledge_graph):
    """Test finding connected components in the knowledge graph."""
    # Create two separate components
    # Component 1: note1 <-> note2 <-> note3
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content="[[Note 2]]"))
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content="[[Note 1]] [[Note 3]]"))
    note3 = await knowledge_store.create_note(NoteCreate(title="Note 3", content="[[Note 2]]"))
    
    # Component 2: note4 <-> note5
    note4 = await knowledge_store.create_note(NoteCreate(title="Note 4", content="[[Note 5]]"))
    note5 = await knowledge_store.create_note(NoteCreate(title="Note 5", content="[[Note 4]]"))
    
    # Isolated note
    note6 = await knowledge_store.create_note(NoteCreate(title="Note 6", content=""))
    
    # Get connected components with min_size=2
    components = await knowledge_graph.get_connected_components(min_size=2)
    assert len(components) == 2
    
    # Check component contents
    component_ids = [set(comp) for comp in components]
    assert {note1.id, note2.id, note3.id} in component_ids
    assert {note4.id, note5.id} in component_ids
    
    # Get all components including isolated notes (min_size=1)
    all_components = await knowledge_graph.get_connected_components(min_size=1)
    assert len(all_components) == 3  # 2 components + 1 isolated note


@pytest.mark.asyncio
async def test_export_graph_json(knowledge_store, knowledge_graph):
    """Test exporting graph data in JSON format."""
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content="[[Note 2]]"))
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content=""))
    
    export = await knowledge_graph.export_graph(format="json")
    
    # Should have nodes and edges
    assert "nodes" in export
    assert "edges" in export
    
    assert len(export["nodes"]) == 2
    assert len(export["edges"]) == 1
    
    # Check node data
    node_ids = [n["id"] for n in export["nodes"]]
    assert note1.id in node_ids
    assert note2.id in node_ids
    
    # Check edge data
    assert export["edges"][0]["from"] == note1.id
    assert export["edges"][0]["to"] == note2.id


@pytest.mark.asyncio
async def test_export_graph_dot(knowledge_store, knowledge_graph):
    """Test exporting graph data in DOT format for Graphviz."""
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content="[[Note 2]]"))
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content=""))
    
    dot_export = await knowledge_graph.export_graph(format="dot")
    
    # Should be a valid DOT format
    assert "digraph" in dot_export
    assert note1.id in dot_export
    assert note2.id in dot_export
    assert "->" in dot_export


@pytest.mark.asyncio
async def test_graph_caching(knowledge_store, knowledge_graph):
    """Test that graph is cached and only rebuilt when needed."""
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content=""))
    
    # First build
    graph1 = await knowledge_graph.build_graph()
    build_time1 = knowledge_graph._cache_updated_at
    
    # Build again without changes - should use cache
    graph2 = await knowledge_graph.build_graph()
    build_time2 = knowledge_graph._cache_updated_at
    
    assert graph1 is graph2  # Same object returned
    assert build_time2 == build_time1  # Cache not updated
    
    # Force rebuild
    graph3 = await knowledge_graph.build_graph(force_rebuild=True)
    build_time3 = knowledge_graph._cache_updated_at
    
    assert build_time3 > build_time1  # Cache was updated


@pytest.mark.asyncio
async def test_graph_updates_when_notes_change(knowledge_store, knowledge_graph):
    """Test that graph updates when notes are added/modified/deleted."""
    # Initial graph with 1 note
    note1 = await knowledge_store.create_note(NoteCreate(title="Note 1", content=""))
    await knowledge_graph.build_graph()
    assert knowledge_graph._graph_cache.number_of_nodes() == 1
    
    # Add new note
    note2 = await knowledge_store.create_note(NoteCreate(title="Note 2", content="[[Note 1]]"))
    
    # Rebuild graph
    await knowledge_graph.build_graph(force_rebuild=True)
    assert knowledge_graph._graph_cache.number_of_nodes() == 2
    assert knowledge_graph._graph_cache.number_of_edges() == 1
    
    # Delete note
    await knowledge_store.delete_note(note2.id, soft_delete=False)
    
    # Rebuild graph
    await knowledge_graph.build_graph(force_rebuild=True)
    assert knowledge_graph._graph_cache.number_of_nodes() == 1
    assert knowledge_graph._graph_cache.number_of_edges() == 0


@pytest.mark.asyncio
async def test_neighbor_query_with_different_depths(knowledge_store, knowledge_graph):
    """Test neighbor queries with different depth levels."""
    # Create a chain: A -> B -> C -> D -> E
    a = await knowledge_store.create_note(NoteCreate(title="A", content="[[B]]"))
    b = await knowledge_store.create_note(NoteCreate(title="B", content="[[C]]"))
    c = await knowledge_store.create_note(NoteCreate(title="C", content="[[D]]"))
    d = await knowledge_store.create_note(NoteCreate(title="D", content="[[E]]"))
    e = await knowledge_store.create_note(NoteCreate(title="E", content=""))
    
    # Depth 1: A, B - edges: A->B
    neighbors = await knowledge_graph.get_neighbors(a.id, depth=1)
    node_ids = [n["id"] for n in neighbors["nodes"]]
    assert set(node_ids) == {a.id, b.id}
    assert len(neighbors["edges"]) == 1
    
    # Depth 2: A, B, C - edges: A->B, B->C
    neighbors = await knowledge_graph.get_neighbors(a.id, depth=2)
    node_ids = [n["id"] for n in neighbors["nodes"]]
    assert set(node_ids) == {a.id, b.id, c.id}
    assert len(neighbors["edges"]) == 2
    
    # Depth 3: A, B, C, D - edges: A->B, B->C, C->D
    neighbors = await knowledge_graph.get_neighbors(a.id, depth=3)
    node_ids = [n["id"] for n in neighbors["nodes"]]
    assert set(node_ids) == {a.id, b.id, c.id, d.id}
    assert len(neighbors["edges"]) == 3
    
    # Depth 4: All nodes
    neighbors = await knowledge_graph.get_neighbors(a.id, depth=4)
    node_ids = [n["id"] for n in neighbors["nodes"]]
    assert set(node_ids) == {a.id, b.id, c.id, d.id, e.id}
    assert len(neighbors["edges"]) == 4


@pytest.mark.asyncio
async def test_circular_graph_pathfinding(knowledge_store, knowledge_graph):
    """Test pathfinding in a circular graph."""
    # Create a circular graph: 1 -> 2 -> 3 -> 4 -> 1
    # Also 1 -> 3 direct edge
    note1 = await knowledge_store.create_note(NoteCreate(title="1", content="[[2]] [[3]]"))
    note2 = await knowledge_store.create_note(NoteCreate(title="2", content="[[3]]"))
    note3 = await knowledge_store.create_note(NoteCreate(title="3", content="[[4]]"))
    note4 = await knowledge_store.create_note(NoteCreate(title="4", content="[[1]]"))
    
    # Shortest path from 1 to 4 should be 1 -> 3 -> 4 (length 2)
    path = await knowledge_graph.get_shortest_path(note1.id, note4.id)
    assert len(path) == 3
    assert path == [note1.id, note3.id, note4.id]
    
    # Shortest path from 4 to 2 should be 4 -> 1 -> 2 (length 2)
    path = await knowledge_graph.get_shortest_path(note4.id, note2.id)
    assert len(path) == 3
    assert path == [note4.id, note1.id, note2.id]


@pytest.mark.asyncio
async def test_node_metadata_in_graph(knowledge_store, knowledge_graph):
    """Test that node metadata is included in graph exports."""
    note = await knowledge_store.create_note(NoteCreate(
        title="Test Note",
        content="Content",
        tags=["tag1", "tag2"]
    ))
    
    export = await knowledge_graph.export_graph(format="json")
    
    # Node should include title and tags
    node = next(n for n in export["nodes"] if n["id"] == note.id)
    assert node["label"] == "Test Note"
    assert "tag1" in node["tags"]
    assert "tag2" in node["tags"]