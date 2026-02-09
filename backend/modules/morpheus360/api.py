"""
Morpheus 360 Module - Customer Success Intelligence.
This is a business-specific module that uses Morpheus Core.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from google.cloud import bigquery

from .models import Portfolio, PortfolioCreate, PortfolioUpdate
from .service import portfolio_service

# ... (rest of the file remains, I will append the new routes)


# Response models for the API
class InvoiceSummary(BaseModel):
    """Summary of a single invoice."""
    invoice_id: str
    amount: float
    currency: str
    status: str
    due_date: Optional[str] = None
    paid_date: Optional[str] = None


class CustomerMetrics(BaseModel):
    """Customer health and success metrics."""
    cns: float  # Client Net Score
    health_score: float
    churn_probability: float
    mrr: Optional[float] = None


class GraphInsightSummary(BaseModel):
    """Summary of a knowledge graph insight."""
    type: str
    description: str
    confidence: float
    entities_count: int


class Customer360Response(BaseModel):
    """Complete 360-degree view of a customer."""
    customer_id: str
    name: str
    status: str
    created_at: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    metrics: CustomerMetrics
    invoices: List[InvoiceSummary]
    recent_activity: List[Dict[str, Any]]
    graph_insights: List[GraphInsightSummary] = []  # Knowledge Graph insights


# Create the router for this module
# Using /api/v1 prefix to maintain backward compatibility with existing frontend
router = APIRouter(
    prefix="/api/v1",
    tags=["Morpheus 360"]
)


@router.get("/customer/{customer_id}/360", response_model=Customer360Response)
async def get_customer_360(customer_id: str):
    """
    Get a complete 360-degree view of a customer with sophisticated health scoring.
    Uses the same scoring algorithm as the portfolio view.
    """
    try:
        import os
        from google.auth import default
        
        # Security: Use Application Default Credentials (ADC) or env vars
        # This works automatically with GOOGLE_APPLICATION_CREDENTIALS or Cloud Run identity
        client = bigquery.Client(project='looker-studio-htv')
        
        # Use the SAME sophisticated scoring as portfolio
        # We also need to fetch recent transactions for invoices
        # 1. Get Aggregated Metrics
        query_metrics = f"""
        WITH latest_month AS (
            SELECT MAX(trans_date) as latest_date
            FROM `looker-studio-htv.billing_data_dataset.billing_consolidated`
        ),
        billing_metrics AS (
            SELECT 
                bc.account_id,
                CONCAT(bc.first_name, ' ', bc.last_name) as name,
                bc.brand as industry,
                COUNT(DISTINCT bc.xdr_id) as service_count,
                SUM(CASE WHEN bc.trans_type = 'Subscription' THEN bc.total_revenue ELSE 0 END) - 
                SUM(CASE WHEN bc.trans_type = 'Credit' THEN ABS(bc.total_revenue) ELSE 0 END) as total_mrr,
                MIN(bc.trans_date) as first_transaction_date,
                MAX(bc.trans_date) as last_transaction_date,
                MAX(bc.tariff) as plan_tier,
                AVG(
                    CASE 
                        WHEN EXTRACT(DAY FROM bc.trans_date) >= 28 THEN 0
                        WHEN EXTRACT(DAY FROM bc.trans_date) >= 25 THEN 5
                        WHEN EXTRACT(DAY FROM bc.trans_date) >= 20 THEN 10
                        ELSE 20
                    END
                ) as payment_timing_penalty
            FROM `looker-studio-htv.billing_data_dataset.billing_consolidated` bc, latest_month
            WHERE bc.account_id = {customer_id}
              AND DATE_TRUNC(bc.trans_date, MONTH) = DATE_TRUNC(latest_month.latest_date, MONTH)
            GROUP BY bc.account_id, bc.first_name, bc.last_name, bc.brand
        ),
        payment_behavior AS (
            SELECT
                Account_ID,
                AVG(
                    CASE LOWER(Payment_Type)
                        WHEN 'cc' THEN 50
                        WHEN 'check' THEN 30
                        WHEN 'cash' THEN 10
                        WHEN 'wire' THEN 10
                        ELSE 10
                    END
                ) as payment_method_score,
                SUM(CASE WHEN Result = 'Failed' AND Payment_Date >= DATE_SUB(CURRENT_DATE(), INTERVAL 10 MONTH) THEN 1 ELSE 0 END) * 20 as failure_penalty,
                SUM(COALESCE(Total_Applied_USD, 0)) as lifetime_payments
            FROM `looker-studio-htv.billing_data_dataset.billingcollections`
            WHERE Account_ID = {customer_id}
            GROUP BY Account_ID
        )
        SELECT 
            bm.account_id as customer_id,
            bm.name,
            bm.industry,
            bm.service_count,
            bm.total_mrr,
            bm.first_transaction_date,
            bm.last_transaction_date,
            bm.payment_timing_penalty,
            bm.plan_tier,
            COALESCE(pb.payment_method_score, 10) as payment_method_score,
            COALESCE(pb.failure_penalty, 0) as failure_penalty,
            COALESCE(pb.lifetime_payments, 0) as lifetime_payments,
            DATE_DIFF(CURRENT_DATE(), bm.first_transaction_date, MONTH) as account_age_months
        FROM billing_metrics bm
        LEFT JOIN payment_behavior pb ON bm.account_id = pb.Account_ID
        """
        
        query_job = client.query(query_metrics)
        results = list(query_job.result())
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
        
        row = results[0]
        
        # 2. Fetch recent transactions for Invoices
        query_invoices = f"""
        SELECT 
            xdr_id as invoice_id,
            total_revenue as amount,
            trans_date as date,
            'USD' as currency,
            'paid' as status
        FROM `looker-studio-htv.billing_data_dataset.billing_consolidated`
        WHERE account_id = {customer_id}
          AND total_revenue > 0
        ORDER BY trans_date DESC
        LIMIT 5
        """
        query_job_inv = client.query(query_invoices)
        results_inv = list(query_job_inv.result())
        
        invoices = []
        for inv in results_inv:
            invoices.append(InvoiceSummary(
                invoice_id=str(inv.invoice_id),
                amount=float(inv.amount),
                currency=inv.currency,
                status=inv.status,
                due_date=inv.date.isoformat() if inv.date else None,
                paid_date=inv.date.isoformat() if inv.date else None
            ))

        # Calculate sophisticated health score (SAME as portfolio)
        service_count = row['service_count'] or 0
        total_mrr = row['total_mrr'] or 0
        payment_timing_penalty = row['payment_timing_penalty'] or 0
        payment_method_score = row['payment_method_score'] or 10
        failure_penalty = row['failure_penalty'] or 0
        plan_tier = row['plan_tier'] or ''
        account_age_months = row['account_age_months'] or 0
        
        # 5-factor scoring
        payment_method_points = payment_method_score
        failure_points = -min(100, failure_penalty)
        service_points = min(25, service_count * 1)
        tier_points = 15 if plan_tier == 'BIZ' else 10 if plan_tier else 5
        age_points = min(20, account_age_months / 6)
        timing_points = max(0, 10 - (payment_timing_penalty / 2))
        
        health_score = (
            payment_method_points +
            service_points +
            tier_points +
            age_points +
            timing_points +
            failure_points
        )
        
        health_score = min(100, max(0, (health_score / 120) * 100))
        base_churn = 100 - health_score
        failure_boost = min(30, failure_penalty / 2)
        churn_probability = min(100, base_churn + failure_boost)
        cns = health_score * 0.8  # CNS based on health
        
        # Recent activity (mix of real invoices + synthetic signals for now)
        recent_activity = []
        # Add real invoice activity
        for inv in invoices:
             recent_activity.append({
                "type": "payment",
                "channel": "billing",
                "subject": f"Payment processed - ${inv.amount:,.2f}",
                "sentiment": "positive",
                "timestamp": inv.paid_date
            })
        
        return Customer360Response(
            customer_id=str(row['customer_id']),
            name=row['name'],
            status="Active",
            created_at=row['first_transaction_date'].isoformat() if row['first_transaction_date'] else None,
            industry=row['industry'] or "Unknown",
            country="HT",
            metrics=CustomerMetrics(
                cns=float(cns),
                health_score=float(health_score),
                churn_probability=float(churn_probability),
                mrr=float(total_mrr)
            ),
            invoices=invoices,
            recent_activity=recent_activity,
            graph_insights=[]
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_customer_360: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/customers", response_model=List[Dict[str, Any]])
async def list_customers(limit: int = 50, offset: int = 0):
    """
    List all customers with basic information.

    Args:
        limit: Maximum number of customers to return
        offset: Number of customers to skip

    Returns:
        List of customer summaries
    """
    try:
        # For MVP, query BigQuery directly
        import os
        import json
        from google.oauth2 import service_account
        
        # Load credentials from temp_creds.json (in production, this should be from env or secret)
        creds_path = '/app/temp_creds.json'
        with open(creds_path, 'r') as f:
            creds_info = json.load(f)
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        client = bigquery.Client(project='looker-studio-htv', credentials=credentials)
        
        # Query distinct customers from the table
        query = f"""
        SELECT DISTINCT `Account` as customer_id, 
               CONCAT(`First Name`, ' ', `Last Name`) as name,
               'Active' as status,
               CAST(`Customer Price` AS FLOAT64) as mrr,
               `Brand` as industry,
               'HT' as country
        FROM `looker-studio-htv.HTVallproductssales.Cleaned_LookerStudioBQ`
        WHERE `Account` IS NOT NULL
        ORDER BY `Account`
        LIMIT {limit} OFFSET {offset}
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        customers = []
        for row in results:
            customers.append({
                "customer_id": str(row.customer_id),
                "name": row.name,
                "status": row.status,
                "mrr": row.mrr,
                "industry": row.industry,
                "country": row.country
            })
        
        return customers

    except Exception as e:
        print(f"Error in list_customers: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/morpheus360/portfolio", response_model=List[Dict[str, Any]])
async def get_agent_portfolio(limit: int = 1000):
    """
    Get agent's portfolio with health scores for all clients.
    
    Uses billing_consolidated table:
    - MRR = SUM of subscriptions (MRC) grouped by account_id
    - Each xdr_id is a service/transaction
    - Payment timing score based on days from month end
    """
    try:
        import os
        import json
        from google.oauth2 import service_account
        
        # Try Docker path first, then local path
        if os.path.exists('/app/temp_creds.json'):
            creds_path = '/app/temp_creds.json'
        else:
            creds_path = 'temp_creds.json'
        
        with open(creds_path, 'r') as f:
            creds_info = json.load(f)
        
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        client = bigquery.Client(project='looker-studio-htv', credentials=credentials)
        
        # Sophisticated health scoring using billing_consolidated + billingcollections
        # Scoring factors:
        # 1. Payment method (cc=50, check=30, cash/wire=10)
        # 2. Transaction success (minus 20 per failure in last 10 months)
        # 3. Number of services (more = better)
        # 4. Plan tier (BIZ > others)
        # 5. Account age (older = more stable)
        # Safety: cap to avoid runaway queries
        limit = max(1, min(int(limit), 5000))

        query = f"""
        WITH latest_month AS (
            SELECT MAX(trans_date) as latest_date
            FROM `looker-studio-htv.billing_data_dataset.billing_consolidated`
        ),
        billing_metrics AS (
            SELECT 
                bc.account_id,
                CONCAT(bc.first_name, ' ', bc.last_name) as name,
                bc.brand as industry,
                COUNT(DISTINCT bc.xdr_id) as service_count,
                -- MRR = Subscription revenue - Credits (refunds/adjustments)
                SUM(CASE WHEN bc.trans_type = 'Subscription' THEN bc.total_revenue ELSE 0 END) - 
                SUM(CASE WHEN bc.trans_type = 'Credit' THEN ABS(bc.total_revenue) ELSE 0 END) as total_mrr,
                MIN(bc.trans_date) as first_transaction_date,
                MAX(bc.trans_date) as last_transaction_date,
                MAX(bc.tariff) as plan_tier,
                -- Payment timing score
                AVG(
                    CASE 
                        WHEN EXTRACT(DAY FROM bc.trans_date) >= 28 THEN 0
                        WHEN EXTRACT(DAY FROM bc.trans_date) >= 25 THEN 5
                        WHEN EXTRACT(DAY FROM bc.trans_date) >= 20 THEN 10
                        ELSE 20
                    END
                ) as payment_timing_penalty
            FROM `looker-studio-htv.billing_data_dataset.billing_consolidated` bc, latest_month
            WHERE bc.account_id IS NOT NULL
              AND DATE_TRUNC(bc.trans_date, MONTH) = DATE_TRUNC(latest_month.latest_date, MONTH)
            GROUP BY bc.account_id, bc.first_name, bc.last_name, bc.brand
        ),
        payment_behavior AS (
            SELECT
                Account_ID,
                -- Payment method score (avg across transactions)
                AVG(
                    CASE LOWER(Payment_Type)
                        WHEN 'cc' THEN 50
                        WHEN 'check' THEN 30
                        WHEN 'cash' THEN 10
                        WHEN 'wire' THEN 10
                        ELSE 10
                    END
                ) as payment_method_score,
                -- Failed transaction penalty (last 10 months only)
                SUM(CASE WHEN Result = 'Failed' AND Payment_Date >= DATE_SUB(CURRENT_DATE(), INTERVAL 10 MONTH) THEN 1 ELSE 0 END) * 20 as failure_penalty,
                -- Total lifetime payments (globally paid)
                SUM(COALESCE(Total_Applied_USD, 0)) as lifetime_payments
            FROM `looker-studio-htv.billing_data_dataset.billingcollections`
            WHERE Account_ID IS NOT NULL
            GROUP BY Account_ID
        )
        SELECT 
            bm.account_id as customer_id,
            bm.name,
            bm.industry,
            bm.service_count,
            bm.total_mrr,
            bm.first_transaction_date,
            bm.last_transaction_date,
            bm.payment_timing_penalty,
            bm.plan_tier,
            COALESCE(pb.payment_method_score, 10) as payment_method_score,
            COALESCE(pb.failure_penalty, 0) as failure_penalty,
            COALESCE(pb.lifetime_payments, 0) as lifetime_payments,
            DATE_DIFF(CURRENT_DATE(), bm.first_transaction_date, MONTH) as account_age_months
        FROM billing_metrics bm
        INNER JOIN payment_behavior pb ON bm.account_id = pb.Account_ID
        WHERE bm.total_mrr > 0
          AND pb.lifetime_payments > 0
          AND (bm.plan_tier = 'REZ' OR bm.plan_tier LIKE '%RES%')
        ORDER BY bm.total_mrr DESC
        LIMIT {limit}
        """
        
        query_job = client.query(query)
        results = list(query_job.result())
        
        portfolio = []
        for row in results:
            service_count = row['service_count'] or 0
            total_mrr = row['total_mrr'] or 0
            payment_timing_penalty = row['payment_timing_penalty'] or 0
            payment_method_score = row['payment_method_score'] or 10
            failure_penalty = row['failure_penalty'] or 0
            plan_tier = row['plan_tier'] or ''
            account_age_months = row['account_age_months'] or 0
            
            # Sophisticated health score calculation:
            # 1. Payment Method (credit card best, cash worst) - MAX 50 points
            payment_method_points = payment_method_score
            
            # 2. Transaction Success (penalty for failures) - MAX penalty 100 points
            failure_points = -min(100, failure_penalty)
            
            # 3. Number of Services (engagement) - MAX 25 points
            service_points = min(25, service_count * 1)
            
            # 4. Plan Tier (BIZ = premium) - MAX 15 points
            tier_points = 15 if plan_tier == 'BIZ' else 10 if plan_tier else 5
            
            # 5. Account Age (loyalty/stability) - MAX 20 points
            age_points = min(20, account_age_months / 6)  # 1 point per 6 months, max 20
            
            # 6. Payment Timing - MAX 10 points
            timing_points = max(0, 10 - (payment_timing_penalty / 2))
            
            # Calculate total health score (max 130 base, failures can reduce)
            health_score = (
                payment_method_points +  # 50
                service_points +         # 25
                tier_points +            # 15
                age_points +             # 20
                timing_points +          # 10
                failure_points           # -penalties
            )
            
            # Normalize to 0-100 scale
            health_score = min(100, max(0, (health_score / 120) * 100))
            
            # Churn probability: inverse of health with adjustments for failures
            base_churn = 100 - health_score
            failure_boost = min(30, failure_penalty / 2)  # Failures increase churn risk
            churn_probability = min(100, base_churn + failure_boost)
            
            portfolio.append({
                "customer_id": str(row['customer_id']),
                "name": row['name'],
                "status": "Active",
                "mrr": float(total_mrr),
                "lifetime_value": float(row['lifetime_payments'] or 0),
                "health_score": float(health_score),
                "churn_probability": float(churn_probability),
                "industry": row['industry'] or "Unknown",
                "product_count": int(service_count),
                "last_activity": str(row['last_transaction_date']) if row['last_transaction_date'] else None
            })
        
        return portfolio

    except Exception as e:
        print(f"Error in get_agent_portfolio: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# --- Portfolio CRUD Routes ---

@router.post("/portfolios", response_model=Portfolio)
async def create_portfolio(portfolio: PortfolioCreate):
    return portfolio_service.create_portfolio(
        name=portfolio.name,
        description=portfolio.description,
        agent_id=portfolio.agent_id,
        account_ids=portfolio.account_ids or []
    )

@router.get("/portfolios", response_model=List[Portfolio])
async def list_portfolios():
    return portfolio_service.list_portfolios()

@router.get("/portfolios/{portfolio_id}", response_model=Portfolio)
async def get_portfolio(portfolio_id: str):
    p = portfolio_service.get_portfolio(portfolio_id)
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return p

@router.put("/portfolios/{portfolio_id}", response_model=Portfolio)
async def update_portfolio(portfolio_id: str, portfolio: PortfolioUpdate):
    p = portfolio_service.update_portfolio(
        portfolio_id=portfolio_id,
        name=portfolio.name,
        description=portfolio.description,
        agent_id=portfolio.agent_id,
        account_ids=portfolio.account_ids
    )
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return p

@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(portfolio_id: str):
    if not portfolio_service.delete_portfolio(portfolio_id):
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {"status": "success"}

@router.get("/portfolios/{portfolio_id}/accounts")
async def get_portfolio_accounts(portfolio_id: str):
    p = portfolio_service.get_portfolio(portfolio_id)
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    if not p.account_ids:
        return []
        
    # In a real scenario, we'd query BigQuery for these specific IDs
    # For now, let's reuse the logic from get_agent_portfolio but filtered
    all_accounts = await get_agent_portfolio(limit=1000)
    filtered = [a for a in all_accounts if a['customer_id'] in p.account_ids]
    return filtered
