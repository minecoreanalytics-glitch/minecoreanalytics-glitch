"""
Knowledge Graph API - Expose graph structure and insights.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from core.engines.data_engine import get_data_engine
from core.engines.graph_engine import get_graph_engine
from core.models.graph_models import EntityType


# Response Models
class GraphNode(BaseModel):
    """A node in the knowledge graph."""
    id: str
    type: str
    label: str
    properties: Dict[str, Any] = {}


class GraphEdge(BaseModel):
    """An edge connecting two nodes."""
    from_node: str
    to_node: str
    type: str
    strength: float


class GraphStats(BaseModel):
    """Statistics about the graph."""
    node_count: int
    edge_count: int
    by_entity_type: Dict[str, int]


class GraphInsight(BaseModel):
    """A graph-derived insight."""
    type: str
    description: str
    confidence: float
    entities_count: int
    metadata: Optional[Dict[str, Any]] = None


# Create router
router = APIRouter(
    prefix="/api/v1/graph",
    tags=["Knowledge Graph"]
)


def _build_graph_for_customer(customer_id: str):
    """
    Helper function to build the graph for a customer.
    Returns: (graph_engine, customer, invoices, contacts, interactions)
    """
    data_engine = get_data_engine()

    # Fetch customer data
    customer = data_engine.fetch_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    # Fetch related entities
    invoices = data_engine.fetch_invoices_for_customer(customer_id)
    contacts = data_engine.fetch_contacts_for_customer(customer_id)
    interactions = data_engine.fetch_interactions_for_customer(customer_id, limit=50)

    # Build graph
    graph_engine = get_graph_engine()
    graph_engine.build_from_customer_data(customer, invoices, contacts, interactions)

    return graph_engine, customer, invoices, contacts, interactions


@router.get("/{customer_id}/nodes", response_model=List[GraphNode])
async def get_graph_nodes(customer_id: str):
    """
    Get all nodes in the customer's knowledge graph.

    Returns a list of nodes with their properties.
    """
    try:
        graph_engine, customer, invoices, contacts, interactions = _build_graph_for_customer(customer_id)

        nodes = []
        for node_id, node_data in graph_engine.nodes.items():
            nodes.append(GraphNode(
                id=node_id,
                type=node_data.entity_type,
                label=node_data.label,
                properties=node_data.properties
            ))

        return nodes

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build graph: {str(e)}")


@router.get("/{customer_id}/edges", response_model=List[GraphEdge])
async def get_graph_edges(customer_id: str):
    """
    Get all edges (relationships) in the customer's knowledge graph.

    Returns a list of edges with their strength scores.
    """
    try:
        graph_engine, customer, invoices, contacts, interactions = _build_graph_for_customer(customer_id)

        edges = []
        for (from_node, to_node), edge_data in graph_engine.edges.items():
            edges.append(GraphEdge(
                from_node=from_node,
                to_node=to_node,
                type=edge_data.relation_type,
                strength=edge_data.strength
            ))

        return edges

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build graph: {str(e)}")


@router.get("/{customer_id}/stats", response_model=GraphStats)
async def get_graph_stats(customer_id: str):
    """
    Get statistics about the customer's knowledge graph.

    Returns node/edge counts and breakdown by entity type.
    """
    try:
        graph_engine, customer, invoices, contacts, interactions = _build_graph_for_customer(customer_id)

        stats = graph_engine.get_stats()

        return GraphStats(
            node_count=stats['nodes'],
            edge_count=stats['edges'],
            by_entity_type={
                'customers': stats['customers'],
                'invoices': stats['invoices'],
                'contacts': stats['contacts'],
                'interactions': stats['interactions']
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build graph: {str(e)}")


@router.get("/{customer_id}/insights", response_model=List[GraphInsight])
async def get_graph_insights(customer_id: str):
    """
    Get AI-generated insights from the customer's knowledge graph.

    Returns relationship insights with confidence scores.
    """
    try:
        graph_engine, customer, invoices, contacts, interactions = _build_graph_for_customer(customer_id)

        raw_insights = graph_engine.get_graph_insights(customer_id)

        insights = [
            GraphInsight(
                type=insight.insight_type,
                description=insight.description,
                confidence=insight.confidence,
                entities_count=len(insight.entities),
                metadata=insight.metadata
            )
            for insight in raw_insights
        ]

        return insights

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")
