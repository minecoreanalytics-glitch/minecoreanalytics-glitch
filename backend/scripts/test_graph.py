"""
Test script for Morpheus Knowledge Graph Engine.

This script tests graph building, traversal, and insights with sample data.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.engines.graph_engine import get_graph_engine
from core.models.entities import Customer, Invoice, Contact, Interaction
from core.models.graph_models import EntityType, RelationType


def test_knowledge_graph():
    """Test the knowledge graph engine."""

    print("=" * 70)
    print("Morpheus Knowledge Graph Test")
    print("=" * 70)

    # Create test data
    customer = Customer(
        customer_id="CUST-001",
        customer_name="Acme Corp",
        status="active",
        created_at=datetime.now() - timedelta(days=180),
        mrr=5000.0,
        industry="Technology",
        country="USA"
    )

    invoices = [
        Invoice(
            invoice_id="INV-001",
            customer_id="CUST-001",
            amount=5000.0,
            currency="USD",
            status="paid",
            created_at=datetime.now() - timedelta(days=30)
        ),
        Invoice(
            invoice_id="INV-002",
            customer_id="CUST-001",
            amount=5000.0,
            currency="USD",
            status="paid",
            created_at=datetime.now() - timedelta(days=60)
        ),
        Invoice(
            invoice_id="INV-003",
            customer_id="CUST-001",
            amount=5000.0,
            currency="USD",
            status="pending",
            created_at=datetime.now() - timedelta(days=5)
        ),
    ]

    contacts = [
        Contact(
            contact_id="CONT-001",
            customer_id="CUST-001",
            email="john@acmecorp.com",
            name="John Doe",
            role="CTO",
            created_at=datetime.now() - timedelta(days=180)
        ),
        Contact(
            contact_id="CONT-002",
            customer_id="CUST-001",
            email="jane@acmecorp.com",
            name="Jane Smith",
            role="CEO",
            created_at=datetime.now() - timedelta(days=180)
        ),
    ]

    interactions = [
        Interaction(
            interaction_id="INT-001",
            customer_id="CUST-001",
            type="meeting",
            channel="web",
            subject="Quarterly review",
            sentiment="positive",
            created_at=datetime.now() - timedelta(days=5)
        ),
        Interaction(
            interaction_id="INT-002",
            customer_id="CUST-001",
            type="email",
            channel="email",
            subject="Feature request",
            sentiment="neutral",
            created_at=datetime.now() - timedelta(days=10)
        ),
        Interaction(
            interaction_id="INT-003",
            customer_id="CUST-001",
            type="call",
            channel="phone",
            subject="Support inquiry",
            sentiment="positive",
            created_at=datetime.now() - timedelta(days=15)
        ),
        Interaction(
            interaction_id="INT-004",
            customer_id="CUST-001",
            type="support_ticket",
            channel="web",
            subject="Technical issue",
            sentiment="negative",
            created_at=datetime.now() - timedelta(days=20)
        ),
    ]

    # Initialize graph engine
    graph_engine = get_graph_engine()

    print("\n📊 Building Knowledge Graph...")
    print("-" * 70)

    # Build graph
    graph_engine.build_from_customer_data(customer, invoices, contacts, interactions)

    # Get stats
    stats = graph_engine.get_stats()
    print(f"Nodes created:       {stats['nodes']}")
    print(f"Edges created:       {stats['edges']}")
    print(f"  - Customers:       {stats['customers']}")
    print(f"  - Invoices:        {stats['invoices']}")
    print(f"  - Contacts:        {stats['contacts']}")
    print(f"  - Interactions:    {stats['interactions']}")

    # Test 1: Get neighbors
    print("\n🔍 Test 1: Direct Neighbors")
    print("-" * 70)

    neighbors = graph_engine.get_neighbors("CUST-001")
    print(f"Customer CUST-001 has {len(neighbors)} direct connections:")
    for neighbor_id in neighbors[:5]:  # Show first 5
        node = graph_engine.get_node(neighbor_id)
        if node:
            print(f"  - {neighbor_id} ({node.entity_type})")

    # Test 2: Get related entities by type
    print("\n🔍 Test 2: Related Entities by Type")
    print("-" * 70)

    invoices_nodes = graph_engine.get_related_entities(
        "CUST-001",
        entity_type=EntityType.INVOICE
    )
    print(f"Invoices: {len(invoices_nodes)}")

    contacts_nodes = graph_engine.get_related_entities(
        "CUST-001",
        entity_type=EntityType.CONTACT
    )
    print(f"Contacts: {len(contacts_nodes)}")

    interactions_nodes = graph_engine.get_related_entities(
        "CUST-001",
        entity_type=EntityType.INTERACTION
    )
    print(f"Interactions: {len(interactions_nodes)}")

    # Test 3: Relationship strength
    print("\n🔍 Test 3: Relationship Strength")
    print("-" * 70)

    # Test strength between customer and each invoice
    for invoice in invoices[:3]:
        strength = graph_engine.calculate_relationship_strength("CUST-001", invoice.invoice_id)
        status_emoji = "✅" if invoice.status == "paid" else "⏳"
        print(f"{invoice.invoice_id}: {strength:.2f} {status_emoji} ({invoice.status})")

    # Test 4: Graph insights
    print("\n🔍 Test 4: Knowledge Graph Insights")
    print("-" * 70)

    insights = graph_engine.get_graph_insights("CUST-001")
    print(f"Generated {len(insights)} insights:\n")

    for insight in insights:
        confidence_bar = "█" * int(insight.confidence * 10)
        print(f"  [{insight.insight_type}]")
        print(f"  {insight.description}")
        print(f"  Confidence: {confidence_bar} {insight.confidence:.2f}")
        print(f"  Entities: {len(insight.entities)}")
        if insight.metadata:
            print(f"  Metadata: {insight.metadata}")
        print()

    # Test 5: Path finding
    print("\n🔍 Test 5: Path Finding")
    print("-" * 70)

    # Find path from customer to first invoice
    if invoices:
        path = graph_engine.find_path("CUST-001", invoices[0].invoice_id)
        if path:
            print(f"Path from CUST-001 to {invoices[0].invoice_id}:")
            print(f"  Nodes: {' -> '.join(path.nodes)}")
            print(f"  Path strength: {path.total_strength:.2f}")
        else:
            print("No path found")

    # Test 6: Filtered relationships
    print("\n🔍 Test 6: Filtered Relationships")
    print("-" * 70)

    invoice_neighbors = graph_engine.get_neighbors(
        "CUST-001",
        relation_type=RelationType.CUSTOMER_INVOICE
    )
    print(f"Invoice relationships: {len(invoice_neighbors)}")

    interaction_neighbors = graph_engine.get_neighbors(
        "CUST-001",
        relation_type=RelationType.CUSTOMER_INTERACTION
    )
    print(f"Interaction relationships: {len(interaction_neighbors)}")

    print("\n" + "=" * 70)
    print("✅ Knowledge Graph Test Complete")
    print("=" * 70)


if __name__ == "__main__":
    test_knowledge_graph()
