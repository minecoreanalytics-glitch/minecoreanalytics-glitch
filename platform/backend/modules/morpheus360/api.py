"""
Morpheus 360 Module - Customer Success Intelligence.
This is a business-specific module that uses Morpheus Core.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import re
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
    activity_level: Optional[str] = None
    days_since_last_activity: Optional[int] = None
    plan_tier: Optional[str] = None
    product_count: Optional[int] = None
    last_activity: Optional[str] = None
    health_explanation: Optional[str] = None
    health_factors: Optional[Dict[str, Any]] = None
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

_TABLE_INDEX_CACHE: Dict[str, Dict[str, Any]] = {}
_TABLE_INDEX_TTL_SECONDS = 300


def _clamp_score(value: float) -> float:
    """Clamp numeric score to 0-100."""
    return max(0.0, min(100.0, float(value)))


def _status_to_score(account_status: str) -> float:
    """Map account status to a normalized reliability score."""
    status = (account_status or "").strip().lower()
    mapping = {
        "active": 95.0,
        "pending": 70.0,
        "on-hold": 45.0,
        "hold": 45.0,
        "suspended": 35.0,
        "cancelled": 20.0,
        "canceled": 20.0,
    }
    return mapping.get(status, 0.0)


def _recency_to_experience_score(days_since_last_activity: Optional[int]) -> float:
    """Translate activity recency into a customer-experience signal."""
    if days_since_last_activity is None:
        return 0.0
    if days_since_last_activity <= 30:
        return 95.0
    if days_since_last_activity <= 60:
        return 80.0
    if days_since_last_activity <= 120:
        return 60.0
    return 40.0


def _plan_tier_score(plan_tier: str) -> float:
    """Normalize plan tier into a 0-100 score."""
    tier = (plan_tier or "").upper()
    if tier == "BIZ":
        return 95.0
    if tier in {"REZ", "RES"} or "RES" in tier or "REZ" in tier:
        return 75.0
    if tier:
        return 65.0
    return 0.0


def _mrr_to_score(total_mrr: float) -> float:
    """Convert MRR to normalized score (saturates at ~5k)."""
    return _clamp_score((float(total_mrr) / 5000.0) * 100.0)


def _lifetime_to_score(lifetime_payments: float) -> float:
    """Convert lifetime payments to normalized score (saturates at ~50k)."""
    return _clamp_score((float(lifetime_payments) / 50000.0) * 100.0)


def _weighted_score(components: List[Dict[str, float]]) -> float:
    """Compute weighted average score from component objects."""
    total_weight = sum(float(c.get("weight", 0.0)) for c in components)
    if total_weight <= 0:
        return 0.0
    weighted_sum = sum(float(c.get("score", 0.0)) * float(c.get("weight", 0.0)) for c in components)
    return _clamp_score(weighted_sum / total_weight)


def _normalize_percent_or_ratio(value: Optional[float]) -> Optional[float]:
    """
    Normalize values expressed either as ratio (0-1) or percent (0-100) to 0-1.
    Returns None when value is missing/invalid.
    """
    if value is None:
        return None
    try:
        v = float(value)
    except Exception:
        return None
    if v < 0:
        return None
    if v <= 1:
        return v
    if v <= 100:
        return v / 100.0
    return None


def _higher_better_score(value: Optional[float]) -> Optional[float]:
    """Convert ratio/percent to 0-100 where higher values are better."""
    ratio = _normalize_percent_or_ratio(value)
    if ratio is None:
        return None
    return _clamp_score(ratio * 100.0)


def _lower_better_score(value: Optional[float]) -> Optional[float]:
    """Convert ratio/percent to 0-100 where lower values are better."""
    ratio = _normalize_percent_or_ratio(value)
    if ratio is None:
        return None
    return _clamp_score((1.0 - ratio) * 100.0)


def _first_response_minutes_to_score(minutes: Optional[float]) -> Optional[float]:
    """Map first-response time (minutes, lower is better) to 0-100."""
    if minutes is None:
        return None
    try:
        m = max(0.0, float(minutes))
    except Exception:
        return None
    if m <= 15:
        return 95.0
    if m <= 60:
        return 85.0
    if m <= 180:
        return 70.0
    if m <= 720:
        return 50.0
    return 30.0


def _resolution_minutes_to_score(minutes: Optional[float]) -> Optional[float]:
    """Map resolution time (minutes, lower is better) to 0-100."""
    if minutes is None:
        return None
    try:
        m = max(0.0, float(minutes))
    except Exception:
        return None
    if m <= 120:
        return 95.0
    if m <= 480:
        return 85.0
    if m <= 1440:
        return 70.0
    if m <= 4320:
        return 50.0
    return 30.0


def _events_to_score(events: Optional[float], max_events: float = 10.0) -> Optional[float]:
    """Convert event count to 0-100 where fewer events are better."""
    if events is None:
        return None
    try:
        e = max(0.0, float(events))
    except Exception:
        return None
    if max_events <= 0:
        return None
    return _clamp_score(100.0 - min(100.0, (e / max_events) * 100.0))


def _safe_identifier(identifier: str) -> Optional[str]:
    """
    Validate BigQuery identifier segments to avoid SQL injection in dynamic table/column names.
    Returns a sanitized identifier or None if invalid.
    """
    value = (identifier or "").strip()
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        return value
    return None


def _fetch_kommo_sentiment_signal(
    client: bigquery.Client,
    customer_id: str,
) -> Dict[str, Any]:
    """
    Fetch sentiment signal from Kommo conversations.
    Falls back to 0 when no matching data exists.
    """
    neutral = {
        "score": 0.0,
        "count": 0,
        "source_table": None,
        "source_key": None,
    }

    try:
        project_id = _safe_identifier(client.project or "looker-studio-htv")
        if not project_id:
            return neutral

        metadata_sql = f"""
        SELECT table_name, column_name
        FROM `{project_id}.kommo_data.INFORMATION_SCHEMA.COLUMNS`
        """
        metadata_rows = list(client.query(metadata_sql).result())
        if not metadata_rows:
            return neutral

        table_columns: Dict[str, set] = {}
        for row in metadata_rows:
            table_name = _safe_identifier(str(row["table_name"]))
            column_name = _safe_identifier(str(row["column_name"]))
            if not table_name or not column_name:
                continue
            table_columns.setdefault(table_name, set()).add(column_name.lower())

        key_candidates = [
            "account_id",
            "customer_id",
            "bs_account_id",
            "client_id",
            "account",
            "subscriber_id",
            "contact_account_id",
        ]
        sentiment_candidates = [
            "sentiment",
            "sentiment_label",
            "sentiment_score",
            "conversation_sentiment",
            "tone",
            "polarity",
        ]

        ranked_tables = sorted(
            table_columns.keys(),
            key=lambda t: (
                0 if ("conversation" in t.lower() or "message" in t.lower()) else 1,
                t.lower(),
            ),
        )

        for table_name in ranked_tables:
            cols = table_columns[table_name]
            sentiment_col = next((c for c in sentiment_candidates if c in cols), None)
            key_col = next((c for c in key_candidates if c in cols), None)
            if not sentiment_col or not key_col:
                continue

            safe_table = _safe_identifier(table_name)
            safe_sentiment = _safe_identifier(sentiment_col)
            safe_key = _safe_identifier(key_col)
            if not safe_table or not safe_sentiment or not safe_key:
                continue

            sentiment_sql = f"""
            WITH scoped AS (
              SELECT LOWER(TRIM(CAST({safe_sentiment} AS STRING))) AS sentiment_raw
              FROM `{project_id}.kommo_data.{safe_table}`
              WHERE CAST({safe_key} AS STRING) = @customer_id
            ),
            classified AS (
              SELECT
                sentiment_raw,
                CASE
                  WHEN sentiment_raw IN ('positive', 'pos', 'good', 'happy', 'resolved') THEN 'positive'
                  WHEN sentiment_raw IN ('neutral', 'mixed', 'normal') THEN 'neutral'
                  WHEN sentiment_raw IN ('negative', 'neg', 'bad', 'angry', 'frustrated', 'escalated') THEN 'negative'
                  ELSE NULL
                END AS sentiment_bucket,
                CASE
                  WHEN sentiment_raw IN ('positive', 'pos', 'good', 'happy', 'resolved') THEN 1.0
                  WHEN sentiment_raw IN ('neutral', 'mixed', 'normal') THEN 0.5
                  WHEN sentiment_raw IN ('negative', 'neg', 'bad', 'angry', 'frustrated', 'escalated') THEN 0.0
                  WHEN SAFE_CAST(sentiment_raw AS FLOAT64) IS NOT NULL THEN
                    CASE
                      WHEN SAFE_CAST(sentiment_raw AS FLOAT64) BETWEEN -1 AND 1 THEN (SAFE_CAST(sentiment_raw AS FLOAT64) + 1) / 2
                      WHEN SAFE_CAST(sentiment_raw AS FLOAT64) BETWEEN 0 AND 1 THEN SAFE_CAST(sentiment_raw AS FLOAT64)
                      WHEN SAFE_CAST(sentiment_raw AS FLOAT64) BETWEEN 0 AND 100 THEN SAFE_CAST(sentiment_raw AS FLOAT64) / 100
                      ELSE NULL
                    END
                  ELSE NULL
                END AS sentiment_numeric
              FROM scoped
            )
            SELECT
              COUNT(1) AS conversation_count,
              AVG(sentiment_numeric) AS sentiment_ratio,
              SUM(CASE WHEN sentiment_bucket = 'positive' THEN 1 ELSE 0 END) AS positive_count,
              SUM(CASE WHEN sentiment_bucket = 'neutral' THEN 1 ELSE 0 END) AS neutral_count,
              SUM(CASE WHEN sentiment_bucket = 'negative' THEN 1 ELSE 0 END) AS negative_count
            FROM classified
            """
            cfg = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("customer_id", "STRING", str(customer_id))
                ]
            )
            result_rows = list(client.query(sentiment_sql, job_config=cfg).result())
            if not result_rows:
                continue

            result = result_rows[0]
            conversation_count = int(result["conversation_count"] or 0)
            sentiment_ratio = result["sentiment_ratio"]
            if conversation_count <= 0 or sentiment_ratio is None:
                continue
            positive_count = int(result["positive_count"] or 0)
            neutral_count = int(result["neutral_count"] or 0)
            negative_count = int(result["negative_count"] or 0)
            classified_count = positive_count + neutral_count + negative_count
            negative_rate = (float(negative_count) / float(classified_count)) if classified_count > 0 else None

            return {
                "score": _clamp_score(float(sentiment_ratio) * 100.0),
                "count": conversation_count,
                "positive_count": positive_count,
                "neutral_count": neutral_count,
                "negative_count": negative_count,
                "negative_rate": negative_rate,
                "source_table": safe_table,
                "source_key": safe_key,
            }

        return neutral
    except Exception as e:
        print(f"Kommo sentiment lookup failed for customer {customer_id}: {e}")
        return neutral


def _list_project_datasets(client: bigquery.Client, project_id: str) -> List[str]:
    """List safe dataset IDs for a BigQuery project."""
    safe_project = _safe_identifier(project_id)
    if not safe_project:
        return []
    dataset_ids: List[str] = []
    try:
        for dataset in client.list_datasets(project=safe_project):
            dataset_id = _safe_identifier(getattr(dataset, "dataset_id", ""))
            if dataset_id:
                dataset_ids.append(dataset_id)
    except Exception as e:
        print(f"Dataset discovery failed for project {safe_project}: {e}")
        return []
    return dataset_ids


def _build_table_index(
    client: bigquery.Client,
    project_id: str,
    dataset_ids: List[str],
) -> List[Dict[str, Any]]:
    """
    Build a searchable table index:
    [
      {
        "dataset": "<dataset>",
        "table": "<table>",
        "columns": {"lower_col": "OriginalColName", ...}
      }, ...
    ]
    """
    safe_project = _safe_identifier(project_id)
    if not safe_project:
        return []

    table_index: List[Dict[str, Any]] = []
    for dataset_id in dataset_ids:
        safe_dataset = _safe_identifier(dataset_id)
        if not safe_dataset:
            continue
        metadata_sql = f"""
        SELECT table_name, column_name
        FROM `{safe_project}.{safe_dataset}.INFORMATION_SCHEMA.COLUMNS`
        """
        try:
            rows = list(client.query(metadata_sql).result())
        except Exception:
            continue

        grouped: Dict[str, Dict[str, str]] = {}
        for row in rows:
            safe_table = _safe_identifier(str(row["table_name"]))
            safe_col = _safe_identifier(str(row["column_name"]))
            if not safe_table or not safe_col:
                continue
            grouped.setdefault(safe_table, {})[safe_col.lower()] = safe_col

        for table_name, columns in grouped.items():
            if not columns:
                continue
            table_index.append(
                {
                    "dataset": safe_dataset,
                    "table": table_name,
                    "columns": columns,
                }
            )
    return table_index


def _ordered_metric_tables(
    table_index: List[Dict[str, Any]],
    key_candidates: List[str],
    metric_candidates: List[str],
    preferred_datasets: Optional[List[str]] = None,
    table_keywords: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """Find tables containing both account key and metric column, ordered by priority."""
    dataset_rank: Dict[str, int] = {
        ds: idx for idx, ds in enumerate(preferred_datasets or [])
    }
    keyword_list = [k.lower() for k in (table_keywords or []) if k]
    ordered: List[Tuple[int, int, str, str, str, str]] = []

    for entry in table_index:
        cols = entry.get("columns", {})
        key_col = next((cols[k] for k in key_candidates if k in cols), None)
        metric_col = next((cols[m] for m in metric_candidates if m in cols), None)
        if not key_col or not metric_col:
            continue

        dataset = str(entry.get("dataset") or "")
        table = str(entry.get("table") or "")
        table_l = table.lower()
        keyword_penalty = 0
        if keyword_list:
            keyword_penalty = 0 if any(k in table_l for k in keyword_list) else 1
        ordered.append(
            (
                dataset_rank.get(dataset, 10_000),
                keyword_penalty,
                dataset,
                table,
                key_col,
                metric_col,
            )
        )

    ordered.sort()
    return [
        {
            "dataset": ds,
            "table": tb,
            "key_col": key_col,
            "metric_col": metric_col,
        }
        for _, _, ds, tb, key_col, metric_col in ordered
    ]


def _query_metric_numeric_from_tables(
    client: bigquery.Client,
    project_id: str,
    customer_id: str,
    table_index: List[Dict[str, Any]],
    key_candidates: List[str],
    metric_candidates: List[str],
    agg: str = "avg",
    preferred_datasets: Optional[List[str]] = None,
    table_keywords: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Fetch numeric metric from the first matching table/column.
    agg supports: avg, sum
    """
    safe_project = _safe_identifier(project_id)
    if not safe_project:
        return None

    ordered_tables = _ordered_metric_tables(
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=metric_candidates,
        preferred_datasets=preferred_datasets,
        table_keywords=table_keywords,
    )
    agg_expr = "SUM" if agg == "sum" else "AVG"

    for match in ordered_tables:
        safe_dataset = _safe_identifier(match["dataset"])
        safe_table = _safe_identifier(match["table"])
        safe_key = _safe_identifier(match["key_col"])
        safe_metric = _safe_identifier(match["metric_col"])
        if not safe_dataset or not safe_table or not safe_key or not safe_metric:
            continue

        sql = f"""
        SELECT
          {agg_expr}(SAFE_CAST({safe_metric} AS FLOAT64)) AS metric_value,
          COUNTIF(SAFE_CAST({safe_metric} AS FLOAT64) IS NOT NULL) AS sample_count
        FROM `{safe_project}.{safe_dataset}.{safe_table}`
        WHERE CAST({safe_key} AS STRING) = @customer_id
        """
        cfg = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("customer_id", "STRING", str(customer_id))
            ]
        )
        try:
            rows = list(client.query(sql, job_config=cfg).result())
        except Exception:
            continue
        if not rows:
            continue
        row = rows[0]
        value = row.get("metric_value")
        sample_count = int(row.get("sample_count") or 0)
        if value is None or sample_count <= 0:
            continue
        try:
            parsed_value = float(value)
        except Exception:
            continue
        return {
            "value": parsed_value,
            "sample_count": sample_count,
            "source_dataset": safe_dataset,
            "source_table": safe_table,
            "source_key": safe_key,
            "source_metric": safe_metric,
        }
    return None


def _query_metric_timestamp_from_tables(
    client: bigquery.Client,
    project_id: str,
    customer_id: str,
    table_index: List[Dict[str, Any]],
    key_candidates: List[str],
    metric_candidates: List[str],
    preferred_datasets: Optional[List[str]] = None,
    table_keywords: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Fetch most recent timestamp-like signal from matching tables."""
    safe_project = _safe_identifier(project_id)
    if not safe_project:
        return None

    ordered_tables = _ordered_metric_tables(
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=metric_candidates,
        preferred_datasets=preferred_datasets,
        table_keywords=table_keywords,
    )

    for match in ordered_tables:
        safe_dataset = _safe_identifier(match["dataset"])
        safe_table = _safe_identifier(match["table"])
        safe_key = _safe_identifier(match["key_col"])
        safe_metric = _safe_identifier(match["metric_col"])
        if not safe_dataset or not safe_table or not safe_key or not safe_metric:
            continue

        sql = f"""
        SELECT
          MAX(SAFE_CAST({safe_metric} AS TIMESTAMP)) AS metric_ts,
          COUNTIF(SAFE_CAST({safe_metric} AS TIMESTAMP) IS NOT NULL) AS sample_count
        FROM `{safe_project}.{safe_dataset}.{safe_table}`
        WHERE CAST({safe_key} AS STRING) = @customer_id
        """
        cfg = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("customer_id", "STRING", str(customer_id))
            ]
        )
        try:
            rows = list(client.query(sql, job_config=cfg).result())
        except Exception:
            continue
        if not rows:
            continue
        row = rows[0]
        value = row.get("metric_ts")
        sample_count = int(row.get("sample_count") or 0)
        if value is None or sample_count <= 0:
            continue
        return {
            "value": value,
            "sample_count": sample_count,
            "source_dataset": safe_dataset,
            "source_table": safe_table,
            "source_key": safe_key,
            "source_metric": safe_metric,
        }
    return None


def _network_latency_ms_to_score(latency_ms: Optional[float]) -> Optional[float]:
    """Map latency in ms to 0-100 (lower is better)."""
    if latency_ms is None:
        return None
    try:
        l_ms = max(0.0, float(latency_ms))
    except Exception:
        return None
    if l_ms <= 20:
        return 95.0
    if l_ms <= 50:
        return 85.0
    if l_ms <= 100:
        return 70.0
    if l_ms <= 200:
        return 50.0
    return 30.0


def _network_downtime_minutes_to_score(minutes: Optional[float]) -> Optional[float]:
    """Map downtime minutes to 0-100 (lower is better)."""
    if minutes is None:
        return None
    try:
        m = max(0.0, float(minutes))
    except Exception:
        return None
    if m <= 30:
        return 95.0
    if m <= 120:
        return 85.0
    if m <= 480:
        return 70.0
    if m <= 1440:
        return 50.0
    return 30.0


def _network_activity_days_to_score(days_since_last: Optional[int]) -> Optional[float]:
    """Map network activity recency (days) to 0-100."""
    if days_since_last is None:
        return None
    if days_since_last <= 1:
        return 95.0
    if days_since_last <= 3:
        return 85.0
    if days_since_last <= 7:
        return 70.0
    if days_since_last <= 30:
        return 50.0
    return 30.0


def _equipment_age_months_to_lifecycle_score(age_months: Optional[float]) -> Optional[float]:
    """Map equipment age to lifecycle score (newer generally healthier)."""
    if age_months is None:
        return None
    try:
        a = max(0.0, float(age_months))
    except Exception:
        return None
    if a <= 12:
        return 95.0
    if a <= 24:
        return 85.0
    if a <= 48:
        return 70.0
    if a <= 72:
        return 55.0
    return 35.0


def _capacity_utilization_to_score(utilization: Optional[float]) -> Optional[float]:
    """
    Convert utilization (0-1 or 0-100) to capacity score.
    Lower utilization means more headroom.
    """
    ratio = _normalize_percent_or_ratio(utilization)
    if ratio is None:
        return None
    if ratio <= 0.5:
        return 95.0
    if ratio <= 0.7:
        return 85.0
    if ratio <= 0.85:
        return 70.0
    if ratio <= 0.95:
        return 50.0
    return 30.0


def _csat_nps_to_score(raw_value: Optional[float], source_metric: Optional[str] = None) -> Optional[float]:
    """
    Normalize CSAT/NPS variants to 0-100:
    - Ratio [0,1] -> x100
    - Percent [0,100] -> same
    - NPS [-100,100] -> shifted to [0,100]
    """
    if raw_value is None:
        return None
    try:
        value = float(raw_value)
    except Exception:
        return None
    if 0.0 <= value <= 1.0:
        return _clamp_score(value * 100.0)
    metric_name = (source_metric or "").lower()
    if "nps" in metric_name and -100.0 <= value <= 100.0:
        return _clamp_score((value + 100.0) / 2.0)
    if -100.0 <= value < 0.0:
        return _clamp_score((value + 100.0) / 2.0)
    if 0.0 <= value <= 100.0:
        return _clamp_score(value)
    return None


def _fetch_domain_signal_inputs(
    client: bigquery.Client,
    customer_id: str,
) -> Tuple[Dict[str, Optional[float]], Dict[str, Dict[str, Any]]]:
    """
    Fetch domain signals for Network, Customer Experience, and Equipment
    from available BigQuery tables. No proxy or simulated values.
    """
    signals: Dict[str, Optional[float]] = {
        "cx_csat_nps_score": None,
        "cx_complaint_rate": None,
        "cx_first_response_minutes": None,
        "cx_resolution_minutes": None,
        "cx_proactive_outreach_success": None,
        "cx_engagement_level": None,
        "cx_churn_warning_intensity": None,
        "cx_support_billing_friction_events": None,
        "network_service_continuity": None,
        "network_failure_free_ops": None,
        "network_timing_stability": None,
        "network_activity_freshness": None,
        "network_footprint_stability": None,
        "equipment_lifecycle_maturity": None,
        "equipment_operational_stability": None,
        "equipment_load_balance": None,
        "equipment_capacity": None,
        "equipment_availability": None,
    }
    sources: Dict[str, Dict[str, Any]] = {}

    project_id = _safe_identifier(client.project or "looker-studio-htv")
    if not project_id:
        return signals, sources

    dataset_ids = _list_project_datasets(client, project_id)
    if not dataset_ids:
        return signals, sources

    preferred_order = [
        "kommo_data",
        "htv_analytics",
        "telehaiti_dataset",
        "data_integration",
        "billing_data_dataset",
        "revenue_htv",
        "HTVallproductssales",
        "prepaid_alez",
    ]
    ordered_dataset_ids = [
        *[ds for ds in preferred_order if ds in dataset_ids],
        *sorted([ds for ds in dataset_ids if ds not in preferred_order]),
    ]

    cache_key = f"{project_id}:{','.join(ordered_dataset_ids)}"
    cache_entry = _TABLE_INDEX_CACHE.get(cache_key)
    table_index: List[Dict[str, Any]]
    now_utc = datetime.utcnow()
    if cache_entry:
        cached_at = cache_entry.get("ts")
        if isinstance(cached_at, datetime):
            age_seconds = (now_utc - cached_at).total_seconds()
            if age_seconds < _TABLE_INDEX_TTL_SECONDS:
                table_index = list(cache_entry.get("table_index") or [])
            else:
                table_index = _build_table_index(
                    client=client,
                    project_id=project_id,
                    dataset_ids=ordered_dataset_ids,
                )
                _TABLE_INDEX_CACHE[cache_key] = {"ts": now_utc, "table_index": table_index}
        else:
            table_index = _build_table_index(
                client=client,
                project_id=project_id,
                dataset_ids=ordered_dataset_ids,
            )
            _TABLE_INDEX_CACHE[cache_key] = {"ts": now_utc, "table_index": table_index}
    else:
        table_index = _build_table_index(
            client=client,
            project_id=project_id,
            dataset_ids=ordered_dataset_ids,
        )
        _TABLE_INDEX_CACHE[cache_key] = {"ts": now_utc, "table_index": table_index}

    if not table_index:
        return signals, sources

    key_candidates = [
        "account_id",
        "accountid",
        "customer_id",
        "bs_account_id",
        "account",
        "account_no",
        "account_number",
        "subscriber_id",
        "client_id",
        "contact_account_id",
    ]

    cx_datasets = ["kommo_data", "data_integration", "htv_analytics", "billing_data_dataset"]
    network_datasets = ["htv_analytics", "telehaiti_dataset", "data_integration", "revenue_htv"]
    equipment_datasets = ["telehaiti_dataset", "htv_analytics", "data_integration"]

    def assign_signal(signal_key: str, value: Optional[float], source: Optional[Dict[str, Any]]) -> None:
        if value is None:
            return
        signals[signal_key] = float(value)
        if source:
            sources[signal_key] = source

    # Customer Experience signals
    cx_csat = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "csat_nps_score",
            "csat_score",
            "nps_score",
            "customer_satisfaction_score",
            "satisfaction_score",
            "csat",
            "nps",
        ],
        agg="avg",
        preferred_datasets=cx_datasets,
        table_keywords=["survey", "feedback", "support", "kommo", "customer"],
    )
    assign_signal(
        "cx_csat_nps_score",
        _csat_nps_to_score(cx_csat["value"], cx_csat.get("source_metric")) if cx_csat else None,
        cx_csat,
    )

    cx_complaint_rate = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "complaint_rate",
            "complaints_rate",
            "customer_complaint_rate",
            "support_complaint_rate",
        ],
        agg="avg",
        preferred_datasets=cx_datasets,
        table_keywords=["complaint", "support", "ticket", "kommo"],
    )
    if cx_complaint_rate:
        assign_signal("cx_complaint_rate", cx_complaint_rate["value"], cx_complaint_rate)
    else:
        complaint_count = _query_metric_numeric_from_tables(
            client=client,
            project_id=project_id,
            customer_id=customer_id,
            table_index=table_index,
            key_candidates=key_candidates,
            metric_candidates=["complaint_count", "complaints", "complaint_events", "negative_ticket_count"],
            agg="sum",
            preferred_datasets=cx_datasets,
            table_keywords=["complaint", "support", "ticket"],
        )
        interaction_count = _query_metric_numeric_from_tables(
            client=client,
            project_id=project_id,
            customer_id=customer_id,
            table_index=table_index,
            key_candidates=key_candidates,
            metric_candidates=[
                "ticket_count",
                "support_ticket_count",
                "case_count",
                "conversation_count",
                "interaction_count",
                "total_interactions",
            ],
            agg="sum",
            preferred_datasets=cx_datasets,
            table_keywords=["support", "ticket", "conversation", "interaction", "kommo"],
        )
        if complaint_count and interaction_count and float(interaction_count["value"]) > 0:
            derived_rate = float(complaint_count["value"]) / float(interaction_count["value"])
            assign_signal(
                "cx_complaint_rate",
                derived_rate,
                {
                    "derived_from": ["complaint_count", "interaction_count"],
                    "complaint_source": complaint_count,
                    "interaction_source": interaction_count,
                },
            )

    cx_first_response_minutes = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "first_response_minutes",
            "first_response_time_minutes",
            "first_reply_minutes",
            "response_time_minutes",
            "first_response_time_min",
            "first_response_time",
        ],
        agg="avg",
        preferred_datasets=cx_datasets,
        table_keywords=["support", "ticket", "conversation", "kommo"],
    )
    if cx_first_response_minutes:
        assign_signal("cx_first_response_minutes", cx_first_response_minutes["value"], cx_first_response_minutes)
    else:
        cx_first_response_hours = _query_metric_numeric_from_tables(
            client=client,
            project_id=project_id,
            customer_id=customer_id,
            table_index=table_index,
            key_candidates=key_candidates,
            metric_candidates=["first_response_hours", "response_time_hours", "first_reply_hours"],
            agg="avg",
            preferred_datasets=cx_datasets,
            table_keywords=["support", "ticket", "conversation", "kommo"],
        )
        if cx_first_response_hours:
            assign_signal(
                "cx_first_response_minutes",
                float(cx_first_response_hours["value"]) * 60.0,
                cx_first_response_hours,
            )

    cx_resolution_minutes = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "resolution_minutes",
            "resolution_time_minutes",
            "time_to_resolution_minutes",
            "resolve_time_minutes",
            "resolution_time",
        ],
        agg="avg",
        preferred_datasets=cx_datasets,
        table_keywords=["support", "ticket", "case", "kommo"],
    )
    if cx_resolution_minutes:
        assign_signal("cx_resolution_minutes", cx_resolution_minutes["value"], cx_resolution_minutes)
    else:
        cx_resolution_hours = _query_metric_numeric_from_tables(
            client=client,
            project_id=project_id,
            customer_id=customer_id,
            table_index=table_index,
            key_candidates=key_candidates,
            metric_candidates=["resolution_hours", "time_to_resolution_hours", "resolve_time_hours"],
            agg="avg",
            preferred_datasets=cx_datasets,
            table_keywords=["support", "ticket", "case", "kommo"],
        )
        if cx_resolution_hours:
            assign_signal(
                "cx_resolution_minutes",
                float(cx_resolution_hours["value"]) * 60.0,
                cx_resolution_hours,
            )

    cx_proactive_outreach_success = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "proactive_outreach_success",
            "outreach_success_rate",
            "proactive_success_rate",
            "followup_success_rate",
            "campaign_success_rate",
        ],
        agg="avg",
        preferred_datasets=cx_datasets,
        table_keywords=["outreach", "campaign", "followup", "kommo"],
    )
    assign_signal(
        "cx_proactive_outreach_success",
        cx_proactive_outreach_success["value"] if cx_proactive_outreach_success else None,
        cx_proactive_outreach_success,
    )

    cx_engagement_level = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "engagement_level",
            "engagement_rate",
            "portal_usage_rate",
            "app_usage_rate",
            "active_usage_rate",
            "usage_rate",
        ],
        agg="avg",
        preferred_datasets=cx_datasets,
        table_keywords=["engagement", "usage", "portal", "app", "kommo"],
    )
    assign_signal("cx_engagement_level", cx_engagement_level["value"] if cx_engagement_level else None, cx_engagement_level)

    cx_churn_warning_intensity = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "churn_warning_intensity",
            "warning_intensity",
            "churn_warning_rate",
            "churn_alert_rate",
            "risk_signal_rate",
        ],
        agg="avg",
        preferred_datasets=cx_datasets,
        table_keywords=["churn", "warning", "risk", "alert"],
    )
    assign_signal(
        "cx_churn_warning_intensity",
        cx_churn_warning_intensity["value"] if cx_churn_warning_intensity else None,
        cx_churn_warning_intensity,
    )

    cx_support_billing_friction_events = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "support_billing_friction_events",
            "friction_events",
            "friction_event_count",
            "billing_disputes_count",
            "dispute_count",
            "support_ticket_count",
        ],
        agg="sum",
        preferred_datasets=cx_datasets,
        table_keywords=["support", "billing", "friction", "dispute", "ticket"],
    )
    assign_signal(
        "cx_support_billing_friction_events",
        cx_support_billing_friction_events["value"] if cx_support_billing_friction_events else None,
        cx_support_billing_friction_events,
    )

    # Network signals
    network_service_continuity = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "service_continuity",
            "service_continuity_score",
            "uptime_ratio",
            "uptime_percent",
            "network_uptime",
            "availability_ratio",
            "availability_percent",
        ],
        agg="avg",
        preferred_datasets=network_datasets,
        table_keywords=["network", "uptime", "service", "connectivity", "availability"],
    )
    assign_signal(
        "network_service_continuity",
        _higher_better_score(network_service_continuity["value"]) if network_service_continuity else None,
        network_service_continuity,
    )
    if signals["network_service_continuity"] is None:
        network_downtime = _query_metric_numeric_from_tables(
            client=client,
            project_id=project_id,
            customer_id=customer_id,
            table_index=table_index,
            key_candidates=key_candidates,
            metric_candidates=["downtime_minutes", "outage_duration_minutes", "downtime_total_minutes"],
            agg="sum",
            preferred_datasets=network_datasets,
            table_keywords=["network", "downtime", "outage"],
        )
        assign_signal(
            "network_service_continuity",
            _network_downtime_minutes_to_score(network_downtime["value"]) if network_downtime else None,
            network_downtime,
        )

    network_failure_free_ops = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "failure_free_ops",
            "failure_free_operations",
            "failure_rate",
            "packet_loss_rate",
            "error_rate",
            "incident_rate",
        ],
        agg="avg",
        preferred_datasets=network_datasets,
        table_keywords=["network", "failure", "error", "packet", "incident"],
    )
    if network_failure_free_ops:
        metric_name = str(network_failure_free_ops.get("source_metric", "")).lower()
        if any(token in metric_name for token in ["failure", "error", "loss", "incident", "outage", "drop"]):
            converted = _lower_better_score(network_failure_free_ops["value"])
        else:
            converted = _higher_better_score(network_failure_free_ops["value"])
        assign_signal("network_failure_free_ops", converted, network_failure_free_ops)
    else:
        network_failure_count = _query_metric_numeric_from_tables(
            client=client,
            project_id=project_id,
            customer_id=customer_id,
            table_index=table_index,
            key_candidates=key_candidates,
            metric_candidates=[
                "failure_count",
                "failed_events_count",
                "incident_count",
                "packet_loss_events",
                "outage_count",
            ],
            agg="sum",
            preferred_datasets=network_datasets,
            table_keywords=["network", "failure", "incident", "outage"],
        )
        assign_signal(
            "network_failure_free_ops",
            _events_to_score(network_failure_count["value"], max_events=20.0) if network_failure_count else None,
            network_failure_count,
        )

    network_timing_stability = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "timing_stability",
            "timing_stability_score",
            "latency_stability_score",
            "jitter_stability_score",
        ],
        agg="avg",
        preferred_datasets=network_datasets,
        table_keywords=["network", "timing", "latency", "jitter"],
    )
    assign_signal(
        "network_timing_stability",
        _higher_better_score(network_timing_stability["value"]) if network_timing_stability else None,
        network_timing_stability,
    )
    if signals["network_timing_stability"] is None:
        network_latency = _query_metric_numeric_from_tables(
            client=client,
            project_id=project_id,
            customer_id=customer_id,
            table_index=table_index,
            key_candidates=key_candidates,
            metric_candidates=["avg_latency_ms", "latency_ms", "round_trip_ms", "rtt_ms", "jitter_ms"],
            agg="avg",
            preferred_datasets=network_datasets,
            table_keywords=["network", "latency", "jitter"],
        )
        assign_signal(
            "network_timing_stability",
            _network_latency_ms_to_score(network_latency["value"]) if network_latency else None,
            network_latency,
        )

    network_activity_freshness = _query_metric_timestamp_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "last_network_activity",
            "last_seen",
            "last_online",
            "heartbeat_at",
            "updated_at",
            "event_timestamp",
            "timestamp",
            "created_at",
        ],
        preferred_datasets=network_datasets,
        table_keywords=["network", "event", "activity", "heartbeat", "status"],
    )
    if network_activity_freshness and network_activity_freshness.get("value"):
        try:
            ts_value = network_activity_freshness["value"]
            days_since = max(0, (datetime.utcnow().date() - ts_value.date()).days)
            assign_signal(
                "network_activity_freshness",
                _network_activity_days_to_score(days_since),
                network_activity_freshness,
            )
        except Exception:
            pass

    network_footprint_stability = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "footprint_stability",
            "footprint_stability_score",
            "coverage_stability",
            "location_stability_score",
        ],
        agg="avg",
        preferred_datasets=network_datasets,
        table_keywords=["network", "footprint", "coverage", "location"],
    )
    assign_signal(
        "network_footprint_stability",
        _higher_better_score(network_footprint_stability["value"]) if network_footprint_stability else None,
        network_footprint_stability,
    )
    if signals["network_footprint_stability"] is None:
        footprint_events = _query_metric_numeric_from_tables(
            client=client,
            project_id=project_id,
            customer_id=customer_id,
            table_index=table_index,
            key_candidates=key_candidates,
            metric_candidates=[
                "location_change_count",
                "site_switch_count",
                "flap_count",
                "handover_failures",
                "reconnect_count",
            ],
            agg="sum",
            preferred_datasets=network_datasets,
            table_keywords=["network", "location", "handover", "reconnect"],
        )
        assign_signal(
            "network_footprint_stability",
            _events_to_score(footprint_events["value"], max_events=15.0) if footprint_events else None,
            footprint_events,
        )

    # Equipment signals
    equipment_lifecycle = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "lifecycle_maturity",
            "lifecycle_score",
            "device_health_score",
            "firmware_compliance_rate",
        ],
        agg="avg",
        preferred_datasets=equipment_datasets,
        table_keywords=["equipment", "device", "asset", "firmware"],
    )
    assign_signal(
        "equipment_lifecycle_maturity",
        _higher_better_score(equipment_lifecycle["value"]) if equipment_lifecycle else None,
        equipment_lifecycle,
    )
    if signals["equipment_lifecycle_maturity"] is None:
        equipment_age = _query_metric_numeric_from_tables(
            client=client,
            project_id=project_id,
            customer_id=customer_id,
            table_index=table_index,
            key_candidates=key_candidates,
            metric_candidates=[
                "device_age_months",
                "equipment_age_months",
                "asset_age_months",
                "firmware_age_months",
            ],
            agg="avg",
            preferred_datasets=equipment_datasets,
            table_keywords=["equipment", "device", "asset", "firmware"],
        )
        assign_signal(
            "equipment_lifecycle_maturity",
            _equipment_age_months_to_lifecycle_score(equipment_age["value"]) if equipment_age else None,
            equipment_age,
        )

    equipment_operational = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "operational_stability",
            "operational_stability_score",
            "device_stability_score",
        ],
        agg="avg",
        preferred_datasets=equipment_datasets,
        table_keywords=["equipment", "device", "operations", "stability"],
    )
    assign_signal(
        "equipment_operational_stability",
        _higher_better_score(equipment_operational["value"]) if equipment_operational else None,
        equipment_operational,
    )
    if signals["equipment_operational_stability"] is None:
        equipment_incidents = _query_metric_numeric_from_tables(
            client=client,
            project_id=project_id,
            customer_id=customer_id,
            table_index=table_index,
            key_candidates=key_candidates,
            metric_candidates=["reboot_count", "crash_count", "fault_count", "alarm_count", "error_count"],
            agg="sum",
            preferred_datasets=equipment_datasets,
            table_keywords=["equipment", "device", "fault", "crash", "reboot"],
        )
        assign_signal(
            "equipment_operational_stability",
            _events_to_score(equipment_incidents["value"], max_events=20.0) if equipment_incidents else None,
            equipment_incidents,
        )

    equipment_load_balance = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "load_balance",
            "load_balance_score",
            "balance_index",
            "distribution_score",
            "cpu_load_balance",
        ],
        agg="avg",
        preferred_datasets=equipment_datasets,
        table_keywords=["equipment", "device", "load", "balance", "capacity"],
    )
    assign_signal(
        "equipment_load_balance",
        _higher_better_score(equipment_load_balance["value"]) if equipment_load_balance else None,
        equipment_load_balance,
    )

    equipment_capacity = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "capacity",
            "capacity_score",
            "capacity_headroom",
            "utilization_percent",
            "capacity_utilization",
        ],
        agg="avg",
        preferred_datasets=equipment_datasets,
        table_keywords=["equipment", "capacity", "utilization", "load"],
    )
    if equipment_capacity:
        metric_name = str(equipment_capacity.get("source_metric", "")).lower()
        if "utilization" in metric_name:
            converted_capacity = _capacity_utilization_to_score(equipment_capacity["value"])
        else:
            converted_capacity = _higher_better_score(equipment_capacity["value"])
        assign_signal("equipment_capacity", converted_capacity, equipment_capacity)

    equipment_availability = _query_metric_numeric_from_tables(
        client=client,
        project_id=project_id,
        customer_id=customer_id,
        table_index=table_index,
        key_candidates=key_candidates,
        metric_candidates=[
            "availability",
            "availability_score",
            "availability_percent",
            "uptime_percent",
            "uptime_ratio",
            "device_availability",
        ],
        agg="avg",
        preferred_datasets=equipment_datasets,
        table_keywords=["equipment", "availability", "uptime", "device"],
    )
    assign_signal(
        "equipment_availability",
        _higher_better_score(equipment_availability["value"]) if equipment_availability else None,
        equipment_availability,
    )

    return signals, sources


def _compute_cns_domains(
    payment_method_score: float,
    failure_penalty: float,
    service_count: int,
    timing_points: float,
    account_age_months: int,
    account_status: str,
    churn_probability: float,
    days_since_last_activity: Optional[int],
    total_mrr: float,
    plan_tier: str,
    lifetime_payments: float,
    kommo_sentiment_score: Optional[float] = None,
    kommo_negative_sentiment_rate: Optional[float] = None,
    cx_csat_nps_score: Optional[float] = None,
    cx_complaint_rate: Optional[float] = None,
    cx_first_response_minutes: Optional[float] = None,
    cx_resolution_minutes: Optional[float] = None,
    cx_proactive_outreach_success: Optional[float] = None,
    cx_engagement_level: Optional[float] = None,
    cx_churn_warning_intensity: Optional[float] = None,
    cx_support_billing_friction_events: Optional[float] = None,
    network_service_continuity: Optional[float] = None,
    network_failure_free_ops: Optional[float] = None,
    network_timing_stability: Optional[float] = None,
    network_activity_freshness: Optional[float] = None,
    network_footprint_stability: Optional[float] = None,
    equipment_lifecycle_maturity: Optional[float] = None,
    equipment_operational_stability: Optional[float] = None,
    equipment_load_balance: Optional[float] = None,
    equipment_capacity: Optional[float] = None,
    equipment_availability: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compute domain-level CNS scores (0-100).
    Missing inputs are scored as 0. No proxy or inferred values are used.
    """

    def component(comp_id: str, label: str, score: float, weight: float) -> Dict[str, float]:
        return {
            "id": comp_id,
            "label": label,
            "score": round(_clamp_score(score), 2),
            "weight": float(weight),
        }

    def _score_or_zero(score: Optional[float]) -> float:
        if score is None:
            return 0.0
        return _clamp_score(score)

    failed_payments_10m = max(0.0, float(failure_penalty) / 20.0)

    payment_score_100 = _clamp_score((float(payment_method_score) / 50.0) * 100.0)
    failure_score_100 = _clamp_score(100.0 - (failed_payments_10m * 20.0))
    timing_score_100 = _clamp_score((float(timing_points) / 10.0) * 100.0)
    tenure_score_100 = _clamp_score((float(account_age_months) / 24.0) * 100.0)
    adoption_score_100 = _clamp_score((float(service_count) / 25.0) * 100.0)
    status_score_100 = _status_to_score(account_status)
    activity_score_100 = _recency_to_experience_score(days_since_last_activity)
    retention_score_100 = _clamp_score(100.0 - float(churn_probability))
    mrr_score_100 = _mrr_to_score(total_mrr)
    lifetime_score_100 = _lifetime_to_score(lifetime_payments)
    plan_score_100 = _plan_tier_score(plan_tier)
    sentiment_analysis_score_100 = _score_or_zero(kommo_sentiment_score)

    billing_components = [
        component("payment_method_quality", "Payment Method Quality", payment_score_100, 30),
        component("failed_payment_control", "Failed Payment Control", failure_score_100, 25),
        component("billing_punctuality", "Billing Punctuality", timing_score_100, 20),
        component("revenue_strength", "Revenue Strength", mrr_score_100, 15),
        component("payment_coverage", "Payment Coverage", lifetime_score_100, 10),
    ]
    network_components = [
        component("service_continuity", "Service Continuity", _score_or_zero(network_service_continuity), 30),
        component("failure_free_ops", "Failure-Free Ops", _score_or_zero(network_failure_free_ops), 25),
        component("timing_stability", "Timing Stability", _score_or_zero(network_timing_stability), 20),
        component("activity_freshness", "Activity Freshness", _score_or_zero(network_activity_freshness), 15),
        component("footprint_stability", "Footprint Stability", _score_or_zero(network_footprint_stability), 10),
    ]
    csat_nps_score_100 = _score_or_zero(cx_csat_nps_score)
    complaint_rate_score_100 = _score_or_zero(_lower_better_score(cx_complaint_rate))
    first_response_time_score_100 = _score_or_zero(_first_response_minutes_to_score(cx_first_response_minutes))
    resolution_time_score_100 = _score_or_zero(_resolution_minutes_to_score(cx_resolution_minutes))
    proactive_outreach_success_score_100 = _score_or_zero(_higher_better_score(cx_proactive_outreach_success))
    engagement_level_score_100 = _score_or_zero(_higher_better_score(cx_engagement_level))
    churn_warning_intensity_score_100 = _score_or_zero(_lower_better_score(cx_churn_warning_intensity))
    support_billing_friction_score_100 = _score_or_zero(_events_to_score(cx_support_billing_friction_events, max_events=10.0))

    customer_experience_components = [
        component("csat_nps_score", "CSAT/NPS Score", csat_nps_score_100, 20),
        component("complaint_rate", "Complaint Rate", complaint_rate_score_100, 15),
        component("first_response_time", "First Response Time", first_response_time_score_100, 12),
        component("resolution_time", "Resolution Time", resolution_time_score_100, 15),
        component("proactive_outreach_success", "Proactive Outreach Success", proactive_outreach_success_score_100, 8),
        component("engagement_level", "Engagement Level (Usage/Portal/App)", engagement_level_score_100, 10),
        component("churn_warning_intensity", "Churn Warning Intensity", churn_warning_intensity_score_100, 12),
        component("support_billing_friction_events", "Support + Billing Friction Events", support_billing_friction_score_100, 8),
        component("kommo_sentiment_analysis", "Kommo Sentiment Analysis (Modifier)", sentiment_analysis_score_100, 0),
    ]
    equipment_components = [
        component("lifecycle_maturity", "Lifecycle Maturity", _score_or_zero(equipment_lifecycle_maturity), 25),
        component("operational_stability", "Operational Stability", _score_or_zero(equipment_operational_stability), 25),
        component("load_balance", "Load Balance", _score_or_zero(equipment_load_balance), 20),
        component("capacity", "Capacity", _score_or_zero(equipment_capacity), 15),
        component("availability", "Availability", _score_or_zero(equipment_availability), 15),
    ]

    billing_health_score = _weighted_score(billing_components)
    network_health_score = _weighted_score(network_components)
    customer_experience_base_score = _weighted_score(customer_experience_components[:8])
    customer_experience_score = _clamp_score(
        ((customer_experience_base_score * 90.0) + (sentiment_analysis_score_100 * 10.0)) / 100.0
    )
    equipment_health_score = _weighted_score(equipment_components)

    domain_breakdown = {
        "billing": {
            "score": round(billing_health_score, 2),
            "weight": 30.0,
            "components": billing_components,
        },
        "network": {
            "score": round(network_health_score, 2),
            "weight": 25.0,
            "components": network_components,
        },
        "customer_experience": {
            "score": round(customer_experience_score, 2),
            "weight": 25.0,
            "base_score": round(customer_experience_base_score, 2),
            "sentiment_modifier_weight": 10.0,
            "components": customer_experience_components,
        },
        "equipment": {
            "score": round(equipment_health_score, 2),
            "weight": 20.0,
            "components": equipment_components,
        },
    }

    # Final CNS is a weighted sum on a 0-100 scale.
    cns = _clamp_score(
        (
            (billing_health_score * 30.0)
            + (network_health_score * 25.0)
            + (customer_experience_score * 25.0)
            + (equipment_health_score * 20.0)
        )
        / 100.0
    )

    return {
        "billing_health_score": billing_health_score,
        "network_health_score": network_health_score,
        "customer_experience_score": customer_experience_score,
        "equipment_health_score": equipment_health_score,
        "tenure_score": tenure_score_100,
        "domain_breakdown": domain_breakdown,
        "cns": cns,
    }


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
                MAX(bc.Status) as account_status,
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
                        ELSE 0
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
            bm.account_status,
            COALESCE(pb.payment_method_score, 0) as payment_method_score,
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
        payment_method_score = row['payment_method_score'] or 0
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
        status_val = str(row.get('account_status') or "Active")
        
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
        
        # Activity recency
        try:
            from datetime import date
            last_dt = row['last_transaction_date']
            days_since_last = (date.today() - last_dt).days if last_dt else None
        except Exception:
            days_since_last = None

        if days_since_last is None:
            activity_level = "Unknown"
        elif days_since_last <= 30:
            activity_level = "High"
        elif days_since_last <= 60:
            activity_level = "Mid"
        else:
            activity_level = "Low"

        timing_points_local = max(0, 10 - (payment_timing_penalty / 2))
        kommo_sentiment_signal = _fetch_kommo_sentiment_signal(client, str(customer_id))
        domain_signal_inputs, domain_signal_sources = _fetch_domain_signal_inputs(
            client=client,
            customer_id=str(customer_id),
        )

        domain_scores = _compute_cns_domains(
            payment_method_score=float(payment_method_score),
            failure_penalty=float(failure_penalty),
            service_count=int(service_count),
            timing_points=float(timing_points_local),
            account_age_months=int(account_age_months),
            account_status=status_val,
            churn_probability=float(churn_probability),
            days_since_last_activity=days_since_last,
            total_mrr=float(total_mrr),
            plan_tier=str(plan_tier),
            lifetime_payments=float(row.get('lifetime_payments') or 0),
            kommo_sentiment_score=float(kommo_sentiment_signal.get("score", 0.0)),
            kommo_negative_sentiment_rate=kommo_sentiment_signal.get("negative_rate"),
            cx_csat_nps_score=domain_signal_inputs.get("cx_csat_nps_score"),
            cx_complaint_rate=domain_signal_inputs.get("cx_complaint_rate"),
            cx_first_response_minutes=domain_signal_inputs.get("cx_first_response_minutes"),
            cx_resolution_minutes=domain_signal_inputs.get("cx_resolution_minutes"),
            cx_proactive_outreach_success=domain_signal_inputs.get("cx_proactive_outreach_success"),
            cx_engagement_level=domain_signal_inputs.get("cx_engagement_level"),
            cx_churn_warning_intensity=domain_signal_inputs.get("cx_churn_warning_intensity"),
            cx_support_billing_friction_events=domain_signal_inputs.get("cx_support_billing_friction_events"),
            network_service_continuity=domain_signal_inputs.get("network_service_continuity"),
            network_failure_free_ops=domain_signal_inputs.get("network_failure_free_ops"),
            network_timing_stability=domain_signal_inputs.get("network_timing_stability"),
            network_activity_freshness=domain_signal_inputs.get("network_activity_freshness"),
            network_footprint_stability=domain_signal_inputs.get("network_footprint_stability"),
            equipment_lifecycle_maturity=domain_signal_inputs.get("equipment_lifecycle_maturity"),
            equipment_operational_stability=domain_signal_inputs.get("equipment_operational_stability"),
            equipment_load_balance=domain_signal_inputs.get("equipment_load_balance"),
            equipment_capacity=domain_signal_inputs.get("equipment_capacity"),
            equipment_availability=domain_signal_inputs.get("equipment_availability"),
        )
        cns = domain_scores["cns"]

        # Human-readable explanation (same signals as portfolio)
        reasons = []
        if failure_penalty and failure_penalty > 0:
            reasons.append(f"{int(failure_penalty/20)} failed payments (10m)")
        if payment_method_score >= 45:
            reasons.append("paid by credit card")
        elif payment_method_score <= 15:
            reasons.append("high-risk payment method")
        if service_count >= 20:
            reasons.append("high product adoption")
        elif service_count <= 3:
            reasons.append("low product adoption")
        if timing_points_local <= 4:
            reasons.append("late payment timing")
        if account_age_months >= 24:
            reasons.append("long tenure")
        elif account_age_months <= 3:
            reasons.append("new account")

        explanation = "; ".join(reasons) if reasons else "stable signals"

        return Customer360Response(
            customer_id=str(row['customer_id']),
            name=row['name'],
            status=status_val,
            activity_level=activity_level,
            days_since_last_activity=days_since_last,
            plan_tier=str(row.get('plan_tier') or ''),
            product_count=int(row.get('service_count') or 0),
            last_activity=row['last_transaction_date'].isoformat() if row.get('last_transaction_date') else None,
            health_explanation=explanation,
            health_factors={
                "payment_method_score": float(payment_method_score),
                "failed_payments_10m": int(failure_penalty / 20) if failure_penalty else 0,
                "service_count": int(service_count),
                "plan_tier": str(row.get('plan_tier') or ''),
                "account_age_months": int(account_age_months),
                "timing_points": float(timing_points_local),
                "kommo_sentiment_score": float(kommo_sentiment_signal.get("score", 0.0)),
                "kommo_conversation_count": int(kommo_sentiment_signal.get("count", 0)),
                "kommo_negative_sentiment_rate": kommo_sentiment_signal.get("negative_rate"),
                "kommo_source_table": kommo_sentiment_signal.get("source_table"),
                "kommo_source_key": kommo_sentiment_signal.get("source_key"),
                "cx_csat_nps_score_input": domain_signal_inputs.get("cx_csat_nps_score"),
                "cx_complaint_rate_input": domain_signal_inputs.get("cx_complaint_rate"),
                "cx_first_response_minutes_input": domain_signal_inputs.get("cx_first_response_minutes"),
                "cx_resolution_minutes_input": domain_signal_inputs.get("cx_resolution_minutes"),
                "cx_proactive_outreach_success_input": domain_signal_inputs.get("cx_proactive_outreach_success"),
                "cx_engagement_level_input": domain_signal_inputs.get("cx_engagement_level"),
                "cx_churn_warning_intensity_input": domain_signal_inputs.get("cx_churn_warning_intensity"),
                "cx_support_billing_friction_events_input": domain_signal_inputs.get("cx_support_billing_friction_events"),
                "network_service_continuity_input": domain_signal_inputs.get("network_service_continuity"),
                "network_failure_free_ops_input": domain_signal_inputs.get("network_failure_free_ops"),
                "network_timing_stability_input": domain_signal_inputs.get("network_timing_stability"),
                "network_activity_freshness_input": domain_signal_inputs.get("network_activity_freshness"),
                "network_footprint_stability_input": domain_signal_inputs.get("network_footprint_stability"),
                "equipment_lifecycle_maturity_input": domain_signal_inputs.get("equipment_lifecycle_maturity"),
                "equipment_operational_stability_input": domain_signal_inputs.get("equipment_operational_stability"),
                "equipment_load_balance_input": domain_signal_inputs.get("equipment_load_balance"),
                "equipment_capacity_input": domain_signal_inputs.get("equipment_capacity"),
                "equipment_availability_input": domain_signal_inputs.get("equipment_availability"),
                "domain_signal_sources": domain_signal_sources,
                "billing_health_score": float(domain_scores["billing_health_score"]),
                "network_health_score": float(domain_scores["network_health_score"]),
                "customer_experience_score": float(domain_scores["customer_experience_score"]),
                "equipment_health_score": float(domain_scores["equipment_health_score"]),
                "tenure_score": float(domain_scores["tenure_score"]),
                "domain_breakdown": domain_scores["domain_breakdown"],
            },
            created_at=row['first_transaction_date'].isoformat() if row['first_transaction_date'] else None,
            industry=row['industry'] or "Unknown",
            country="HT",
            metrics=CustomerMetrics(
                cns=float(cns),
                # Keep `health_score` as a compatibility alias, mapped to CNS.
                health_score=float(cns),
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
                MAX(bc.Status) as account_status,
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
                        ELSE 0
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
            bm.account_status,
            COALESCE(pb.payment_method_score, 0) as payment_method_score,
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
            payment_method_score = row['payment_method_score'] or 0
            failure_penalty = row['failure_penalty'] or 0
            plan_tier = row['plan_tier'] or ''
            account_status = row.get('account_status') or ''
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
            account_status_text = str(account_status) if account_status else "Active"
            
            # Human-readable explanation (deterministic)
            reasons = []
            if failure_penalty and failure_penalty > 0:
                reasons.append(f"{int(failure_penalty/20)} failed payments (10m)")
            if payment_method_score >= 45:
                reasons.append("paid by credit card")
            elif payment_method_score <= 15:
                reasons.append("high-risk payment method")
            if service_count >= 20:
                reasons.append("high product adoption")
            elif service_count <= 3:
                reasons.append("low product adoption")
            if timing_points <= 4:
                reasons.append("late payment timing")
            if account_age_months >= 24:
                reasons.append("long tenure")
            elif account_age_months <= 3:
                reasons.append("new account")

            explanation = "; ".join(reasons) if reasons else "stable signals"

            # Activity recency
            try:
                from datetime import date
                last_dt = row['last_transaction_date']
                days_since_last = (date.today() - last_dt).days if last_dt else None
            except Exception:
                days_since_last = None

            if days_since_last is None:
                activity_level = "Unknown"
            elif days_since_last <= 30:
                activity_level = "High"
            elif days_since_last <= 60:
                activity_level = "Mid"
            else:
                activity_level = "Low"

            domain_scores = _compute_cns_domains(
                payment_method_score=float(payment_method_score),
                failure_penalty=float(failure_penalty),
                service_count=int(service_count),
                timing_points=float(timing_points),
                account_age_months=int(account_age_months),
                account_status=account_status_text,
                churn_probability=float(churn_probability),
                days_since_last_activity=days_since_last,
                total_mrr=float(total_mrr),
                plan_tier=str(plan_tier),
                lifetime_payments=float(row.get('lifetime_payments') or 0),
            )

            portfolio.append({
                "customer_id": str(row['customer_id']),
                "name": row['name'],
                "status": account_status_text,
                "activity_level": activity_level,
                "days_since_last_activity": days_since_last,
                "mrr": float(total_mrr),
                "lifetime_value": float(row['lifetime_payments'] or 0),
                # Keep `health_score` as a compatibility alias, mapped to CNS.
                "health_score": float(domain_scores["cns"]),
                "cns": float(domain_scores["cns"]),
                "churn_probability": float(churn_probability),
                "industry": row['industry'] or "Unknown",
                "product_count": int(service_count),
                "last_activity": str(row['last_transaction_date']) if row['last_transaction_date'] else None,
                "health_explanation": explanation,
                "health_factors": {
                    "payment_method_score": float(payment_method_score),
                    "failed_payments_10m": int(failure_penalty / 20) if failure_penalty else 0,
                    "service_count": int(service_count),
                    "plan_tier": str(plan_tier),
                    "account_age_months": int(account_age_months),
                    "timing_points": float(timing_points),
                    "billing_health_score": float(domain_scores["billing_health_score"]),
                    "network_health_score": float(domain_scores["network_health_score"]),
                    "customer_experience_score": float(domain_scores["customer_experience_score"]),
                    "equipment_health_score": float(domain_scores["equipment_health_score"]),
                    "tenure_score": float(domain_scores["tenure_score"]),
                    "domain_breakdown": domain_scores["domain_breakdown"],
                }
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
