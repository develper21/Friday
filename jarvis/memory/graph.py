"""
Memory graph compatibility module.
"""

from typing import Dict, List, Any, Optional

FIXED_BRANCH_IDS = ["diary", "knowledge", "preferences", "meals"]

class GraphMemoryStore:
    """Graph memory store compatibility stub"""
    def __init__(self, db_path=None):
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[Dict[str, Any]] = []
    
    def add_node(self, node_id: str, node_type: str, content: str, **kwargs):
        """Add a node to the graph"""
        self._nodes[node_id] = {
            'type': node_type,
            'content': content,
            **kwargs
        }
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a node by ID"""
        return self._nodes.get(node_id)
    
    def query(self, query: str, branch_id: str = None) -> List[Dict[str, Any]]:
        """Query the graph"""
        return []
