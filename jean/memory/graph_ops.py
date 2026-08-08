"""
Memory graph operations compatibility module.
"""

from typing import Generator, Dict, Any

def update_graph_from_dialogue(db, dialogue: str, graph):
    """Update graph from dialogue (compatibility stub)"""
    pass

def consolidate_all_populated_nodes(graph) -> Generator[Dict[str, Any], None, None]:
    """Consolidate nodes (compatibility stub)"""
    yield {"node_id": "stub", "delta": 0}
