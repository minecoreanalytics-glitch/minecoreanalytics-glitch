"""
Test Data Generator for Morpheus Platform

This script generates sample customer, invoice, contact, and interaction data
in BigQuery for testing purposes.

Usage:
    python3 scripts/generate_test_data.py

Requirements:
    - BigQuery project must exist
    - Service account credentials must be configured
    - Dataset 'customers' will be created if it doesn't exist
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import random
import json


def create_dataset_and_tables(client: bigquery.Client, project_id: str, dataset_id: str = "customers"):
    """Create dataset and tables if they don't exist."""

    dataset_ref = f"{project_id}.{dataset_id}"

    # Create dataset
    try:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        client.create_dataset(dataset, exists_ok=True)
        print(f"✓ Dataset {dataset_id} ready")
    except Exception as e:
        print(f"⚠ Error creating dataset: {e}")
        return False

    # Create customers table
    customers_schema = [
        bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
        bigquery.SchemaField("mrr", "FLOAT"),
        bigquery.SchemaField("industry", "STRING"),
        bigquery.SchemaField("country", "STRING"),
    ]

    customers_table = bigquery.Table(f"{dataset_ref}.customers", schema=customers_schema)
    client.create_table(customers_table, exists_ok=True)
    print(f"✓ Table customers ready")

    # Create invoices table
    invoices_schema = [
        bigquery.SchemaField("invoice_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("amount", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("currency", "STRING"),
        bigquery.SchemaField("due_date", "DATE"),
        bigquery.SchemaField("paid_date", "DATE"),
        bigquery.SchemaField("status", "STRING"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
    ]

    invoices_table = bigquery.Table(f"{dataset_ref}.invoices", schema=invoices_schema)
    client.create_table(invoices_table, exists_ok=True)
    print(f"✓ Table invoices ready")

    # Create contacts table
    contacts_schema = [
        bigquery.SchemaField("contact_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("email", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("role", "STRING"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
    ]

    contacts_table = bigquery.Table(f"{dataset_ref}.contacts", schema=contacts_schema)
    client.create_table(contacts_table, exists_ok=True)
    print(f"✓ Table contacts ready")

    # Create interactions table
    interactions_schema = [
        bigquery.SchemaField("interaction_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("channel", "STRING"),
        bigquery.SchemaField("subject", "STRING"),
        bigquery.SchemaField("sentiment", "STRING"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
    ]

    interactions_table = bigquery.Table(f"{dataset_ref}.interactions", schema=interactions_schema)
    client.create_table(interactions_table, exists_ok=True)
    print(f"✓ Table interactions ready")

    return True


def generate_test_data(client: bigquery.Client, project_id: str, dataset_id: str = "customers"):
    """Generate and insert test data."""

    dataset_ref = f"{project_id}.{dataset_id}"

    # Generate 5 test customers
    customers = []
    for i in range(1, 6):
        customers.append({
            "customer_id": f"CUST-{1000 + i}",
            "customer_name": ["Acme Corp", "TechStart Inc", "Global Solutions", "Digital Ventures", "Innovation Labs"][i-1],
            "status": random.choice(["active", "active", "active", "trial"]),
            "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
            "mrr": round(random.uniform(1000, 50000), 2),
            "industry": random.choice(["Technology", "Finance", "Healthcare", "Retail", "Manufacturing"]),
            "country": random.choice(["USA", "UK", "France", "Germany", "Canada"])
        })

    # Insert customers
    errors = client.insert_rows_json(f"{dataset_ref}.customers", customers)
    if not errors:
        print(f"✓ Inserted {len(customers)} customers")
    else:
        print(f"⚠ Errors inserting customers: {errors}")

    # Generate invoices for each customer
    invoices = []
    for customer in customers:
        num_invoices = random.randint(3, 8)
        for j in range(num_invoices):
            invoice_date = datetime.now() - timedelta(days=random.randint(0, 180))
            paid = random.random() > 0.2  # 80% paid

            invoices.append({
                "invoice_id": f"INV-{customer['customer_id']}-{j+1}",
                "customer_id": customer["customer_id"],
                "amount": round(random.uniform(500, 5000), 2),
                "currency": "USD",
                "due_date": (invoice_date + timedelta(days=30)).date().isoformat(),
                "paid_date": (invoice_date + timedelta(days=random.randint(1, 25))).date().isoformat() if paid else None,
                "status": "paid" if paid else "pending",
                "created_at": invoice_date.isoformat()
            })

    errors = client.insert_rows_json(f"{dataset_ref}.invoices", invoices)
    if not errors:
        print(f"✓ Inserted {len(invoices)} invoices")
    else:
        print(f"⚠ Errors inserting invoices: {errors}")

    # Generate contacts for each customer
    contacts = []
    for customer in customers:
        num_contacts = random.randint(2, 5)
        for j in range(num_contacts):
            contacts.append({
                "contact_id": f"CONT-{customer['customer_id']}-{j+1}",
                "customer_id": customer["customer_id"],
                "email": f"contact{j+1}@{customer['customer_name'].lower().replace(' ', '')}.com",
                "name": random.choice(["John Smith", "Jane Doe", "Bob Johnson", "Alice Williams", "Charlie Brown"]),
                "role": random.choice(["CEO", "CTO", "Product Manager", "Developer", "Designer"]),
                "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
            })

    errors = client.insert_rows_json(f"{dataset_ref}.contacts", contacts)
    if not errors:
        print(f"✓ Inserted {len(contacts)} contacts")
    else:
        print(f"⚠ Errors inserting contacts: {errors}")

    # Generate interactions for each customer
    interactions = []
    for customer in customers:
        num_interactions = random.randint(5, 15)
        for j in range(num_interactions):
            interaction_type = random.choice(["email", "call", "meeting", "support_ticket"])
            interactions.append({
                "interaction_id": f"INT-{customer['customer_id']}-{j+1}",
                "customer_id": customer["customer_id"],
                "type": interaction_type,
                "channel": random.choice(["email", "phone", "web", "chat"]),
                "subject": random.choice([
                    "Product inquiry",
                    "Support request",
                    "Feature request",
                    "Billing question",
                    "Technical issue"
                ]),
                "sentiment": random.choice(["positive", "positive", "neutral", "negative"]),
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 90))).isoformat()
            })

    errors = client.insert_rows_json(f"{dataset_ref}.interactions", interactions)
    if not errors:
        print(f"✓ Inserted {len(interactions)} interactions")
    else:
        print(f"⚠ Errors inserting interactions: {errors}")


def main():
    """Main function."""
    print("=" * 60)
    print("Morpheus Test Data Generator")
    print("=" * 60)

    # Get project ID
    project_id = input("\nEnter your BigQuery project ID: ").strip()
    if not project_id:
        print("❌ Project ID is required")
        return

    # Get credentials path
    credentials_path = input("Enter path to service account JSON key (press Enter to use default credentials): ").strip()

    # Initialize BigQuery client
    try:
        if credentials_path:
            client = bigquery.Client.from_service_account_json(credentials_path, project=project_id)
        else:
            client = bigquery.Client(project=project_id)
        print(f"✓ Connected to BigQuery project: {project_id}")
    except Exception as e:
        print(f"❌ Failed to connect to BigQuery: {e}")
        return

    # Create dataset and tables
    print("\n📊 Creating dataset and tables...")
    if not create_dataset_and_tables(client, project_id):
        return

    # Generate test data
    print("\n🔄 Generating test data...")
    generate_test_data(client, project_id)

    print("\n✅ Test data generation complete!")
    print(f"\n📝 Next steps:")
    print(f"   1. Update backend/core/config/htv_config.yaml with project_id: '{project_id}'")
    print(f"   2. Connect to BigQuery from the Data Nexus page")
    print(f"   3. Test the Customer 360 view with customer ID: CUST-1001")


if __name__ == "__main__":
    main()
