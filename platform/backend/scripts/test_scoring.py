"""
Test script for Morpheus Scoring Engine.

This script tests the CNS and churn probability calculations with sample data.
"""

import sys
from pathlib import Path

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.engines.scoring_engine import get_scoring_engine
from datetime import datetime, timedelta


def test_scoring_engine():
    """Test the scoring engine with various customer scenarios."""

    engine = get_scoring_engine()

    print("=" * 70)
    print("Morpheus Scoring Engine Test")
    print("=" * 70)

    # Scenario 1: Healthy customer with good payment and engagement
    print("\n📊 Scenario 1: Healthy Customer (High MRR, Good Payment, Active)")
    print("-" * 70)

    healthy_customer = {
        "customer_id": "CUST-001",
        "mrr": 5000,
        "status": "active",
        "created_at": (datetime.now() - timedelta(days=180)).isoformat(),
        "invoices": [
            {"invoice_id": "INV-1", "amount": 5000, "status": "paid"},
            {"invoice_id": "INV-2", "amount": 5000, "status": "paid"},
            {"invoice_id": "INV-3", "amount": 5000, "status": "paid"},
            {"invoice_id": "INV-4", "amount": 5000, "status": "paid"},
        ],
        "interactions": [
            {"type": "email", "sentiment": "positive", "created_at": (datetime.now() - timedelta(days=5)).isoformat()},
            {"type": "call", "sentiment": "positive", "created_at": (datetime.now() - timedelta(days=10)).isoformat()},
            {"type": "meeting", "sentiment": "positive", "created_at": (datetime.now() - timedelta(days=15)).isoformat()},
            {"type": "email", "sentiment": "neutral", "created_at": (datetime.now() - timedelta(days=20)).isoformat()},
            {"type": "call", "sentiment": "positive", "created_at": (datetime.now() - timedelta(days=25)).isoformat()},
        ],
        "contacts": []
    }

    cns = engine.calculate_cns(healthy_customer)
    churn = engine.calculate_churn_probability(healthy_customer)
    health = engine.calculate_health_score(healthy_customer)

    print(f"CNS Score:          {cns:.3f} {'🟢' if cns > 0.7 else '🟡' if cns > 0.4 else '🔴'}")
    print(f"Churn Probability:  {churn:.3f} {'🔴' if churn > 0.6 else '🟡' if churn > 0.3 else '🟢'}")
    print(f"Health Score:       {health:.3f} {'🟢' if health > 0.7 else '🟡' if health > 0.4 else '🔴'}")

    # Scenario 2: At-risk customer with payment issues
    print("\n📊 Scenario 2: At-Risk Customer (Payment Issues, Low Engagement)")
    print("-" * 70)

    atrisk_customer = {
        "customer_id": "CUST-002",
        "mrr": 2000,
        "status": "active",
        "created_at": (datetime.now() - timedelta(days=60)).isoformat(),
        "invoices": [
            {"invoice_id": "INV-1", "amount": 2000, "status": "overdue"},
            {"invoice_id": "INV-2", "amount": 2000, "status": "pending"},
            {"invoice_id": "INV-3", "amount": 2000, "status": "paid"},
            {"invoice_id": "INV-4", "amount": 2000, "status": "paid"},
        ],
        "interactions": [
            {"type": "support_ticket", "sentiment": "negative", "created_at": (datetime.now() - timedelta(days=5)).isoformat()},
            {"type": "support_ticket", "sentiment": "negative", "created_at": (datetime.now() - timedelta(days=40)).isoformat()},
        ],
        "contacts": []
    }

    cns = engine.calculate_cns(atrisk_customer)
    churn = engine.calculate_churn_probability(atrisk_customer)
    health = engine.calculate_health_score(atrisk_customer)

    print(f"CNS Score:          {cns:.3f} {'🟢' if cns > 0.7 else '🟡' if cns > 0.4 else '🔴'}")
    print(f"Churn Probability:  {churn:.3f} {'🔴' if churn > 0.6 else '🟡' if churn > 0.3 else '🟢'}")
    print(f"Health Score:       {health:.3f} {'🟢' if health > 0.7 else '🟡' if health > 0.4 else '🔴'}")

    # Scenario 3: New customer with limited data
    print("\n📊 Scenario 3: New Customer (Limited History)")
    print("-" * 70)

    new_customer = {
        "customer_id": "CUST-003",
        "mrr": 3000,
        "status": "trial",
        "created_at": (datetime.now() - timedelta(days=15)).isoformat(),
        "invoices": [
            {"invoice_id": "INV-1", "amount": 3000, "status": "paid"},
        ],
        "interactions": [
            {"type": "email", "sentiment": "positive", "created_at": (datetime.now() - timedelta(days=3)).isoformat()},
            {"type": "meeting", "sentiment": "positive", "created_at": (datetime.now() - timedelta(days=10)).isoformat()},
        ],
        "contacts": []
    }

    cns = engine.calculate_cns(new_customer)
    churn = engine.calculate_churn_probability(new_customer)
    health = engine.calculate_health_score(new_customer)

    print(f"CNS Score:          {cns:.3f} {'🟢' if cns > 0.7 else '🟡' if cns > 0.4 else '🔴'}")
    print(f"Churn Probability:  {churn:.3f} {'🔴' if churn > 0.6 else '🟡' if churn > 0.3 else '🟢'}")
    print(f"Health Score:       {health:.3f} {'🟢' if health > 0.7 else '🟡' if health > 0.4 else '🔴'}")

    # Scenario 4: High-risk customer
    print("\n📊 Scenario 4: High-Risk Customer (Multiple Red Flags)")
    print("-" * 70)

    highrisk_customer = {
        "customer_id": "CUST-004",
        "mrr": 500,
        "status": "active",
        "created_at": (datetime.now() - timedelta(days=400)).isoformat(),
        "invoices": [
            {"invoice_id": "INV-1", "amount": 500, "status": "overdue"},
            {"invoice_id": "INV-2", "amount": 500, "status": "overdue"},
            {"invoice_id": "INV-3", "amount": 500, "status": "pending"},
            {"invoice_id": "INV-4", "amount": 500, "status": "paid"},
            {"invoice_id": "INV-5", "amount": 500, "status": "paid"},
        ],
        "interactions": [
            {"type": "support_ticket", "sentiment": "negative", "created_at": (datetime.now() - timedelta(days=70)).isoformat()},
            {"type": "email", "sentiment": "negative", "created_at": (datetime.now() - timedelta(days=80)).isoformat()},
        ],
        "contacts": []
    }

    cns = engine.calculate_cns(highrisk_customer)
    churn = engine.calculate_churn_probability(highrisk_customer)
    health = engine.calculate_health_score(highrisk_customer)

    print(f"CNS Score:          {cns:.3f} {'🟢' if cns > 0.7 else '🟡' if cns > 0.4 else '🔴'}")
    print(f"Churn Probability:  {churn:.3f} {'🔴' if churn > 0.6 else '🟡' if churn > 0.3 else '🟢'}")
    print(f"Health Score:       {health:.3f} {'🟢' if health > 0.7 else '🟡' if health > 0.4 else '🔴'}")

    # Scenario 5: Enterprise customer
    print("\n📊 Scenario 5: Enterprise Customer (High MRR, Long Tenure)")
    print("-" * 70)

    enterprise_customer = {
        "customer_id": "CUST-005",
        "mrr": 25000,
        "status": "active",
        "created_at": (datetime.now() - timedelta(days=800)).isoformat(),
        "invoices": [
            {"invoice_id": f"INV-{i}", "amount": 25000, "status": "paid"}
            for i in range(1, 11)
        ],
        "interactions": [
            {"type": "meeting", "sentiment": "positive", "created_at": (datetime.now() - timedelta(days=7)).isoformat()},
            {"type": "email", "sentiment": "positive", "created_at": (datetime.now() - timedelta(days=14)).isoformat()},
            {"type": "call", "sentiment": "neutral", "created_at": (datetime.now() - timedelta(days=21)).isoformat()},
            {"type": "meeting", "sentiment": "positive", "created_at": (datetime.now() - timedelta(days=28)).isoformat()},
            {"type": "email", "sentiment": "positive", "created_at": (datetime.now() - timedelta(days=35)).isoformat()},
            {"type": "call", "sentiment": "positive", "created_at": (datetime.now() - timedelta(days=42)).isoformat()},
        ],
        "contacts": []
    }

    cns = engine.calculate_cns(enterprise_customer)
    churn = engine.calculate_churn_probability(enterprise_customer)
    health = engine.calculate_health_score(enterprise_customer)

    print(f"CNS Score:          {cns:.3f} {'🟢' if cns > 0.7 else '🟡' if cns > 0.4 else '🔴'}")
    print(f"Churn Probability:  {churn:.3f} {'🔴' if churn > 0.6 else '🟡' if churn > 0.3 else '🟢'}")
    print(f"Health Score:       {health:.3f} {'🟢' if health > 0.7 else '🟡' if health > 0.4 else '🔴'}")

    print("\n" + "=" * 70)
    print("✅ Scoring Engine Test Complete")
    print("=" * 70)
    print("\nScoring Weights:")
    print(f"  CNS:   {engine.CNS_WEIGHTS}")
    print(f"  Churn: {engine.CHURN_WEIGHTS}")


if __name__ == "__main__":
    test_scoring_engine()
