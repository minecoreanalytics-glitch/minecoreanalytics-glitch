"""
Graph Engine - Core service for managing the Knowledge Graph.

This engine provides an in-memory graph representation of entity relationships.
For MVP, we use Python data structures instead of a full graph database (Neo4j, etc.).
"""

from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
from datetime import datetime

from ..models.graph_models import (
    GraphNode, GraphEdge, GraphPath, RelationshipInsight,
    RelationType, EntityType
)
from ..models.entities import Customer, Invoice, Contact, Interaction


class GraphEngine:
    """
    Knowledge Graph engine for managing entity relationships.

    Uses an adjacency list representation for efficient graph operations.
    """

    def __init__(self):
        """Initialize the graph engine."""
        self.nodes: Dict[str, GraphNode] = {}  # node_id -> GraphNode
        self.edges: Dict[str, List[GraphEdge]] = defaultdict(list)  # from_node -> [edges]
        self.reverse_edges: Dict[str, List[GraphEdge]] = defaultdict(list)  # to_node -> [edges]

    def add_node(self, node: GraphNode) -> None:
        """
        Add a node to the graph.

        Args:
            node: GraphNode to add
        """
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge, bidirectional: bool = False) -> None:
        """
        Add an edge (relationship) to the graph.

        Args:
            edge: GraphEdge to add
            bidirectional: If True, also add reverse edge
        """
        self.edges[edge.from_node].append(edge)
        self.reverse_edges[edge.to_node].append(edge)

        if bidirectional:
            reverse_edge = edge.reverse()
            self.edges[reverse_edge.from_node].append(reverse_edge)
            self.reverse_edges[reverse_edge.to_node].append(reverse_edge)

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_outgoing_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all edges originating from a node."""
        return self.edges.get(node_id, [])

    def get_incoming_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all edges pointing to a node."""
        return self.reverse_edges.get(node_id, [])

    def get_all_edges(self, node_id: str) -> List[GraphEdge]:
        """Get all edges (both incoming and outgoing) for a node."""
        return self.get_outgoing_edges(node_id) + self.get_incoming_edges(node_id)

    def get_neighbors(self, node_id: str, relation_type: Optional[RelationType] = None) -> List[str]:
        """
        Get neighboring node IDs.

        Args:
            node_id: Source node ID
            relation_type: Optional filter by relation type

        Returns:
            List of neighboring node IDs
        """
        edges = self.get_all_edges(node_id)

        if relation_type:
            edges = [e for e in edges if e.relation_type == relation_type]

        neighbors = set()
        for edge in edges:
            if edge.from_node == node_id:
                neighbors.add(edge.to_node)
            else:
                neighbors.add(edge.from_node)

        return list(neighbors)

    def get_related_entities(
        self,
        node_id: str,
        entity_type: Optional[EntityType] = None,
        relation_type: Optional[RelationType] = None,
        max_depth: int = 1
    ) -> List[GraphNode]:
        """
        Get related entities using BFS traversal.

        Args:
            node_id: Starting node ID
            entity_type: Optional filter by entity type
            relation_type: Optional filter by relation type
            max_depth: Maximum traversal depth

        Returns:
            List of related GraphNodes
        """
        if node_id not in self.nodes:
            return []

        visited = set()
        queue = deque([(node_id, 0)])  # (node_id, depth)
        related = []

        while queue:
            current_id, depth = queue.popleft()

            if current_id in visited:
                continue

            visited.add(current_id)

            # Add to results (excluding starting node)
            if current_id != node_id:
                node = self.nodes[current_id]
                if entity_type is None or node.entity_type == entity_type:
                    related.append(node)

            # Continue traversal if within depth limit
            if depth < max_depth:
                neighbors = self.get_neighbors(current_id, relation_type)
                for neighbor_id in neighbors:
                    if neighbor_id not in visited:
                        queue.append((neighbor_id, depth + 1))

        return related

    def calculate_relationship_strength(
        self,
        from_node_id: str,
        to_node_id: str
    ) -> float:
        """
        Calculate relationship strength between two nodes.

        Factors:
        - Direct connection strength
        - Number of shared connections
        - Recency of interactions

        Returns:
            Strength score from 0.0 to 1.0
        """
        # Check for direct connection
        direct_edges = [
            e for e in self.get_outgoing_edges(from_node_id)
            if e.to_node == to_node_id
        ]

        if direct_edges:
            # Use the strongest direct connection
            return max(e.strength for e in direct_edges)

        # Check for indirect connections (shared neighbors)
        from_neighbors = set(self.get_neighbors(from_node_id))
        to_neighbors = set(self.get_neighbors(to_node_id))
        shared_neighbors = from_neighbors & to_neighbors

        if shared_neighbors:
            # Strength based on number of shared connections (normalized)
            return min(len(shared_neighbors) / 10, 0.5)  # Max 0.5 for indirect

        return 0.0  # No connection

    def find_path(
        self,
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 3
    ) -> Optional[GraphPath]:
        """
        Find shortest path between two nodes using BFS.

        Args:
            start_node_id: Starting node ID
            end_node_id: Target node ID
            max_depth: Maximum path length

        Returns:
            GraphPath if found, None otherwise
        """
        if start_node_id not in self.nodes or end_node_id not in self.nodes:
            return None

        visited = set()
        queue = deque([(start_node_id, [start_node_id], [], 1.0)])  # (node, path, edges, strength)

        while queue:
            current_id, path, path_edges, path_strength = queue.popleft()

            if current_id == end_node_id:
                # Found path
                return GraphPath(
                    start_node=start_node_id,
                    end_node=end_node_id,
                    nodes=path,
                    edges=path_edges,
                    total_strength=path_strength
                )

            if len(path) > max_depth or current_id in visited:
                continue

            visited.add(current_id)

            # Explore neighbors
            for edge in self.get_outgoing_edges(current_id):
                next_id = edge.to_node
                if next_id not in visited:
                    new_path = path + [next_id]
                    new_edges = path_edges + [edge]
                    new_strength = path_strength * edge.strength  # Multiplicative strength
                    queue.append((next_id, new_path, new_edges, new_strength))

        return None  # No path found

    def get_graph_insights(self, node_id: str) -> List[RelationshipInsight]:
        """
        Generate insights about a node's relationships.

        Args:
            node_id: Node ID to analyze

        Returns:
            List of RelationshipInsights
        """
        insights = []

        if node_id not in self.nodes:
            return insights

        # Insight 1: Connected entity count by type
        related = self.get_related_entities(node_id, max_depth=1)
        entity_counts = defaultdict(int)
        for node in related:
            entity_counts[node.entity_type] += 1

        if entity_counts:
            insights.append(RelationshipInsight(
                insight_type="connected_entities",
                description=f"Connected to {sum(entity_counts.values())} entities",
                entities=[n.node_id for n in related],
                confidence=1.0,
                metadata={"counts": dict(entity_counts)}
            ))

        # Insight 2: Strong relationships
        all_edges = self.get_all_edges(node_id)
        strong_edges = [e for e in all_edges if e.strength >= 0.7]

        if strong_edges:
            strong_entity_ids = [
                e.to_node if e.from_node == node_id else e.from_node
                for e in strong_edges
            ]
            insights.append(RelationshipInsight(
                insight_type="strong_relationships",
                description=f"Has {len(strong_edges)} strong relationships",
                entities=strong_entity_ids,
                confidence=0.9,
                metadata={"threshold": 0.7}
            ))

        # Insight 3: Recent activity (for customers)
        node = self.nodes[node_id]
        if node.entity_type == EntityType.CUSTOMER:
            interaction_edges = [
                e for e in self.get_outgoing_edges(node_id)
                if e.relation_type == RelationType.CUSTOMER_INTERACTION
            ]

            if interaction_edges:
                # Check for recent interactions (last 30 days)
                now = datetime.now()
                recent_interactions = []
                for edge in interaction_edges:
                    created = edge.properties.get('created_at')
                    if created:
                        if isinstance(created, str):
                            try:
                                created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                            except:
                                continue
                        days_ago = (now - created).days if hasattr(created, 'days') else None
                        if days_ago is not None and days_ago <= 30:
                            recent_interactions.append(edge.to_node)

                if recent_interactions:
                    insights.append(RelationshipInsight(
                        insight_type="recent_activity",
                        description=f"{len(recent_interactions)} interactions in last 30 days",
                        entities=recent_interactions,
                        confidence=0.95,
                        metadata={"period_days": 30}
                    ))

        return insights

    def build_from_customer_data(
        self,
        customer: Customer,
        invoices: List[Invoice],
        contacts: List[Contact],
        interactions: List[Interaction]
    ) -> None:
        """
        Build graph from customer data entities.

        Args:
            customer: Customer entity
            invoices: List of invoices
            contacts: List of contacts
            interactions: List of interactions
        """
        # Add customer node
        customer_node = GraphNode(
            node_id=customer.customer_id,
            entity_type=EntityType.CUSTOMER,
            properties={
                "name": customer.customer_name,
                "status": customer.status,
                "mrr": customer.mrr,
                "industry": customer.industry,
                "country": customer.country
            },
            created_at=customer.created_at
        )
        self.add_node(customer_node)

        # Add invoice nodes and relationships
        for invoice in invoices:
            invoice_node = GraphNode(
                node_id=invoice.invoice_id,
                entity_type=EntityType.INVOICE,
                properties={
                    "amount": invoice.amount,
                    "currency": invoice.currency,
                    "status": invoice.status
                },
                created_at=invoice.created_at
            )
            self.add_node(invoice_node)

            # Calculate edge strength based on payment status
            strength = 1.0 if invoice.status == "paid" else 0.5
            edge = GraphEdge(
                from_node=customer.customer_id,
                to_node=invoice.invoice_id,
                relation_type=RelationType.CUSTOMER_INVOICE,
                strength=strength,
                properties={"status": invoice.status}
            )
            self.add_edge(edge, bidirectional=True)

        # Add contact nodes and relationships
        for contact in contacts:
            contact_node = GraphNode(
                node_id=contact.contact_id,
                entity_type=EntityType.CONTACT,
                properties={
                    "name": contact.name,
                    "email": contact.email,
                    "role": contact.role
                },
                created_at=contact.created_at
            )
            self.add_node(contact_node)

            edge = GraphEdge(
                from_node=customer.customer_id,
                to_node=contact.contact_id,
                relation_type=RelationType.CUSTOMER_CONTACT,
                strength=0.8,  # Contacts are generally strong relationships
                properties={"role": contact.role}
            )
            self.add_edge(edge, bidirectional=True)

        # Add interaction nodes and relationships
        for interaction in interactions:
            interaction_node = GraphNode(
                node_id=interaction.interaction_id,
                entity_type=EntityType.INTERACTION,
                properties={
                    "type": interaction.type,
                    "channel": interaction.channel,
                    "sentiment": interaction.sentiment
                },
                created_at=interaction.created_at
            )
            self.add_node(interaction_node)

            # Calculate edge strength based on sentiment
            sentiment_strength = {
                "positive": 1.0,
                "neutral": 0.7,
                "negative": 0.4
            }
            strength = sentiment_strength.get(interaction.sentiment, 0.5)

            edge = GraphEdge(
                from_node=customer.customer_id,
                to_node=interaction.interaction_id,
                relation_type=RelationType.CUSTOMER_INTERACTION,
                strength=strength,
                properties={
                    "sentiment": interaction.sentiment,
                    "created_at": interaction.created_at.isoformat() if interaction.created_at else None
                }
            )
            self.add_edge(edge, bidirectional=True)

    def get_stats(self) -> Dict[str, int]:
        """Get graph statistics."""
        total_edges = sum(len(edges) for edges in self.edges.values())
        return {
            "nodes": len(self.nodes),
            "edges": total_edges,
            "customers": sum(1 for n in self.nodes.values() if n.entity_type == EntityType.CUSTOMER),
            "invoices": sum(1 for n in self.nodes.values() if n.entity_type == EntityType.INVOICE),
            "contacts": sum(1 for n in self.nodes.values() if n.entity_type == EntityType.CONTACT),
            "interactions": sum(1 for n in self.nodes.values() if n.entity_type == EntityType.INTERACTION),
        }


# Global instance
_graph_engine_instance: Optional[GraphEngine] = None


def get_graph_engine() -> GraphEngine:
    """
    Get the global GraphEngine instance.

    Returns:
        GraphEngine instance
    """
    global _graph_engine_instance
    if _graph_engine_instance is None:
        _graph_engine_instance = GraphEngine()
    return _graph_engine_instance
