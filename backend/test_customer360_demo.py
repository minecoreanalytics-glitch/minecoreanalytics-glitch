"""
Test script for Customer 360 Demo
Verifies that Morpheus 360 can pull real customer data from BigQuery
"""

import json
from google.cloud import bigquery
from google.oauth2 import service_account

# Load credentials
creds_path = 'temp_creds.json'
with open(creds_path, 'r') as f:
    creds_info = json.load(f)

credentials = service_account.Credentials.from_service_account_info(creds_info)
client = bigquery.Client(project='looker-studio-htv', credentials=credentials)

print("=" * 80)
print("MORPHEUS 360 - Customer Data Verification")
print("=" * 80)
print()

# Step 1: Get list of customers
print("Step 1: Fetching customer list from BigQuery...")
customers_query = """
SELECT DISTINCT `Account` as customer_id,
       CONCAT(`First Name`, ' ', `Last Name`) as name,
       COUNT(*) as product_count,
       SUM(SAFE_CAST(REGEXP_REPLACE(`Customer Price`, r'[^0-9.]', '') AS FLOAT64)) as total_mrr
FROM `looker-studio-htv.HTVallproductssales.Cleaned_LookerStudioBQ`
WHERE `Account` IS NOT NULL
GROUP BY `Account`, `First Name`, `Last Name`
ORDER BY total_mrr DESC
LIMIT 10
"""

customers_job = client.query(customers_query)
customers = list(customers_job.result())

print(f"✓ Found {len(customers)} customers")
print()

# Display customers
print("Top 10 Customers by MRR:")
print("-" * 80)
for i, customer in enumerate(customers, 1):
    print(f"{i}. ID: {customer.customer_id} | {customer.name} | MRR: ${customer.total_mrr:.2f} | Products: {customer.product_count}")
print()

# Step 2: Get detailed view for first customer
if customers:
    test_customer_id = str(customers[0].customer_id)
    print(f"Step 2: Fetching detailed 360 view for customer {test_customer_id}...")
    
    detail_query = f"""
    SELECT `Account`, `First Name`, `Last Name`, `Brand`,
           `Product Name`, `Service Type`, `Customer Price`,
           `Start Date`, `End Date`,
           COUNT(*) OVER (PARTITION BY `Account`) as total_products,
           SUM(SAFE_CAST(REGEXP_REPLACE(`Customer Price`, r'[^0-9.]', '') AS FLOAT64)) OVER (PARTITION BY `Account`) as total_mrr
    FROM `looker-studio-htv.HTVallproductssales.Cleaned_LookerStudioBQ`
    WHERE CAST(`Account` AS STRING) = '{test_customer_id}'
    ORDER BY `Start Date` DESC
    LIMIT 5
    """
    
    detail_job = client.query(detail_query)
    details = list(detail_job.result())
    
    if details:
        customer = details[0]
        print(f"✓ Customer Profile:")
        print(f"   Name: {customer['First Name']} {customer['Last Name']}")
        print(f"   ID: {customer.Account}")
        print(f"   Brand: {customer.Brand}")
        print(f"   Total Products: {customer.total_products}")
        print(f"   Total MRR: ${customer.total_mrr:.2f}")
        print()
        print(f"   Recent Products/Services:")
        for detail in details:
            print(f"   - {detail['Product Name']} ({detail['Service Type']})")
            # Extract numeric value from price string (handles "550.00 HTG", "9.99 USD", etc.)
            price_str = detail['Customer Price'] or '0'
            import re
            price_num = re.sub(r'[^0-9.]', '', price_str)
            price = float(price_num) if price_num else 0
            print(f"     Price: ${price:.2f}")
            print(f"     Period: {detail['Start Date']} to {detail['End Date']}")
        print()

print("=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print()
print("Next Steps:")
print("1. Start backend: cd backend && python main.py")
print("2. Start frontend: npm run dev")
print(f"3. Navigate to: http://localhost:3000/#/customer/360")
print(f"4. Or test API: curl http://localhost:8000/api/v1/customer/{test_customer_id}/360")
print()
