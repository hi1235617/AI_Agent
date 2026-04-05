from __future__ import annotations

import re
import json
from typing import Any, Dict, List, Optional, Literal

import networkx as nx

from .store import KnowledgeStore
from .exceptions import GraphError


class KnowledgeGraph:
    """KnowledgeGraph

    A lightweight knowledge graph built on top of NetworkX DiGraph. The graph
    is constructed from the underlying KnowledgeStore which persists notes and
    their links. The graph is cached and can be force-rebuilt when the store
    has changed.
    """

    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store
        self._graph: Optional[nx.DiGraph] = None
        self._graph_cache: Optional[nx.DiGraph] = None
        self._cache_updated_at: Optional[str] = None

    @staticmethod
    def _now() -> str:
        from datetime import datetime
        return datetime.utcnow().isoformat(timespec="microseconds")

    async def build_graph(self, force_rebuild: bool = False) -> nx.DiGraph:
        """Build or return a cached directed graph of notes and links.

        If force_rebuild is True or the graph is not yet built, the method will
        fetch notes and outgoing links from the KnowledgeStore and construct a
        DiGraph. Each note becomes a node; each link becomes a directed edge
        from source to target with edge attributes like link_text.
        """
        if self._graph is not None and not force_rebuild:
            return self._graph

        # Ensure the store is initialized
        if getattr(self.store, "_db", None) is None:
            # Initialize the underlying DB; ignore if already initialized by a race
            try:
                await self.store.initialize()
            except Exception:
                # If initialization fails due to concurrent init or other reason,
                # we will proceed and let operations raise meaningful errors later.
                pass

        graph: nx.DiGraph = nx.DiGraph()

        # Fetch all notes
        try:
            notes: List[Any] = await self.store.list_notes(limit=10000)  # type: ignore[arg-type]
        except TypeError:
            # Older versions of store.list_notes might not accept limit kwarg in tests
            notes = await self.store.list_notes()  # type: ignore[call-arg]

        # Add all notes as nodes with metadata
        for n in notes:
            node_id = getattr(n, "id", None)  # type: ignore
            if not node_id:
                continue
            graph.add_node(node_id, title=getattr(n, "title", ""), tags=[t.name for t in getattr(n, "tags", [])])

        # Add edges from outgoing links for each note
        # Build a title-to-id mapping for resolving [[title]] links
        title_to_id: Dict[str, str] = {}
        for n in notes:
            nid = getattr(n, "id", None)
            ntitle = getattr(n, "title", None)
            if nid and ntitle:
                title_to_id[ntitle.lower()] = nid

        for n in notes:
            source_id = getattr(n, "id", None)  # type: ignore
            if not source_id:
                continue
            # First try to get links from the links table
            try:
                outgoing = await self.store.get_links_for_note(source_id, direction="outgoing")
            except Exception:
                outgoing = []
            for link in outgoing:
                target_id = getattr(link, "target_note_id", None) or getattr(link, "target_id", None)  # type: ignore
                if not target_id:
                    continue
                edge_attrs = {"link_text": getattr(link, "link_text", "")}
                graph.add_edge(source_id, target_id, **edge_attrs)

            # Also parse [[title]] links from content (for forward references)
            content = getattr(n, "content", "") or ""
            for match in re.finditer(r'\[\[(.+?)\]\]', content):
                target_title = match.group(1).strip().lower()
                if target_title in title_to_id:
                    target_id = title_to_id[target_title]
                    if source_id != target_id and not graph.has_edge(source_id, target_id):
                        graph.add_edge(source_id, target_id, link_text=f"[[{match.group(1)}]]")

        self._graph = graph
        self._graph_cache = graph
        self._cache_updated_at = self._now()
        return self._graph

    async def get_neighbors(
        self,
        note_id: str,
        depth: int = 1,
        direction: Literal["outgoing", "incoming", "both"] = "both",
    ) -> Dict[str, Any]:
        """Return neighboring note IDs for a given note up to a certain depth.

        - direction controls traversal: outgoing (follow edges from the node),
          incoming (follow edges to the node), or both.
        - depth controls how many hops away to explore.
        Returns a simple dictionary containing the source id, requested depth,
        direction and a list of neighbor IDs.
        """
        if self._graph is None:
            await self.build_graph()
        if self._graph is None:
            raise GraphError(graph_node=None, message="Graph could not be initialized")
        G = self._graph
        if G is None:
            raise GraphError(graph_node=None, message="Graph not initialized")
        if note_id not in G:
            raise GraphError(graph_node=note_id, message="Source note not found in graph")

        visited: set[str] = {note_id}
        frontier: List[str] = [note_id]
        current_depth = 0
        while current_depth < depth:
            next_frontier: List[str] = []
            for node in frontier:
                if direction in ("outgoing", "both"):
                    for nbr in G.successors(node):
                        if nbr not in visited:
                            visited.add(nbr)
                            next_frontier.append(nbr)
                if direction in ("incoming", "both"):
                    for nbr in G.predecessors(node):
                        if nbr not in visited:
                            visited.add(nbr)
                            next_frontier.append(nbr)
            frontier = next_frontier
            current_depth += 1

        # Collect all edges between visited nodes
        edges = []
        for u, v, data in G.edges(data=True):
            if u in visited and v in visited:
                edges.append({"from": u, "to": v, "link_text": data.get("link_text", "")})
        
        # Build node list with metadata
        nodes = []
        for nid in visited:
            node_data = G.nodes.get(nid, {})
            nodes.append({"id": nid, "label": node_data.get("title", nid)})
        
        return {
            "note_id": note_id,
            "depth": depth,
            "direction": direction,
            "nodes": nodes,
            "edges": edges,
        }

    async def get_shortest_path(self, source_note_id: str, target_note_id: str) -> Optional[List[str]]:
        """Return the shortest path as a list of note_ids from source to target.

        Returns None if no path exists or one of the nodes is missing.
        """
        if self._graph is None:
            await self.build_graph()
        if self._graph is None:
            raise GraphError(graph_node=None, message="Graph could not be initialized")
        G = self._graph
        if not G.has_node(source_note_id) or not G.has_node(target_note_id):
            raise GraphError(graph_node=None, message="One or both notes not found in graph")
        try:
            path = nx.shortest_path(G, source=source_note_id, target=target_note_id)
            return path
        except nx.NetworkXNoPath:
            return None
        except Exception as exc:  # pragma: no cover - unexpected errors
            raise GraphError(graph_node=source_note_id, message=str(exc))

    async def get_connected_components(self, min_size: int = 2) -> List[List[str]]:
        """Return weakly connected components as lists of note_ids.

        Components smaller than min_size are filtered out.
        """
        if self._graph is None:
            await self.build_graph()
        G = self._graph
        comps: List[List[str]] = []
        for comp in nx.weakly_connected_components(G):  # type: ignore[arg-type]
            if len(comp) >= min_size:
                comps.append(list(comp))
        return comps

    async def export_graph(self, format: Literal["json", "gexf", "dot"] = "json") -> Any:
        """Export the current graph in a given format.

        - json: returns a JSON string representing node-link data
        - gexf: returns a string containing GEXF XML
        - dot: returns a DOT-format string (requires pydot)
        """
        if self._graph is None:
            await self.build_graph()
        if self._graph is None:
            raise GraphError(graph_node=None, message="Graph could not be initialized")
        G = self._graph

        if format == "json":
            data = nx.node_link_data(G)
            # Convert source/target to from/to for test compatibility
            if "links" in data:
                for link in data["links"]:
                    if "source" in link:
                        link["from"] = link.pop("source")
                    if "target" in link:
                        link["to"] = link.pop("target")
            return data
        if format == "gexf":
            # generate_gexf yields lines; join into a single string
            try:
                lines = list(nx.generate_gexf(G))
                return "\n".join(lines)
            except Exception as exc:
                raise GraphError(graph_node=None, message=f"GEXF export failed: {exc}")
        if format == "dot":
            # Uses pydot backend if available
            try:
                from networkx.drawing.nx_pydot import to_pydot
                pydot = to_pydot(G)
                return pydot.to_string()
            except Exception as exc:
                raise GraphError(graph_node=None, message=f"DOT export failed: {exc}")
        raise GraphError(graph_node=None, message=f"Unsupported export format: {format}")
