"""
Graph models for Morpheus Knowledge Graph.

These models represent the in-memory graph structure for entity relationships.
For MVP, we use simple Python data structures instead of a full graph database.
"""

from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class RelationType(str, Enum):
    """Types of relationships between entities."""
    CUSTOMER_INVOICE = "customer_invoice"
    CUSTOMER_CONTACT = "customer_contact"
    CUSTOMER_INTERACTION = "customer_interaction"
    CONTACT_INTERACTION = "contact_interaction"  # Future use
    INVOICE_PAYMENT = "invoice_payment"  # Future use


class EntityType(str, Enum):
    """Types of entities in the graph."""
    CUSTOMER = "customer"
    INVOICE = "invoice"
    CONTACT = "contact"
    INTERACTION = "interaction"


class GraphNode(BaseModel):
    """
    Represents a node (entity) in the knowledge graph.
    """
    node_id: str  # Unique identifier (e.g., "CUST-001")
    entity_type: EntityType
    properties: Dict[str, Any] = {}  # Entity attributes
    created_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class GraphEdge(BaseModel):
    """
    Represents an edge (relationship) between two nodes.
    """
    from_node: str  # Source node ID
    to_node: str    # Target node ID
    relation_type: RelationType
    strength: float = 1.0  # Relationship strength (0.0 to 1.0)
    properties: Dict[str, Any] = {}  # Relationship attributes
    created_at: Optional[datetime] = None

    class Config:
        use_enum_values = True

    def reverse(self) -> 'GraphEdge':
        """Create a reverse edge (for bidirectional relationships)."""
        return GraphEdge(
            from_node=self.to_node,
            to_node=self.from_node,
            relation_type=self.relation_type,
            strength=self.strength,
            properties=self.properties,
            created_at=self.created_at
        )


class GraphPath(BaseModel):
    """
    Represents a path between two nodes in the graph.
    """
    start_node: str
    end_node: str
    nodes: List[str]  # List of node IDs in path
    edges: List[GraphEdge]  # List of edges traversed
    total_strength: float  # Combined strength of path

    class Config:
        arbitrary_types_allowed = True


class RelationshipInsight(BaseModel):
    """
    Represents an insight derived from graph relationships.
    """
    insight_type: str  # e.g., "connected_entities", "relationship_strength"
    description: str
    entities: List[str]  # Related entity IDs
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any] = {}
