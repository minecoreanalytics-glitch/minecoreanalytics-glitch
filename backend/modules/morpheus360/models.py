from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class PortfolioAccount(BaseModel):
    account_id: str
    name: str
    mrr: float
    health_score: float
    region: Optional[str] = None
    services: List[str] = []

class Portfolio(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    account_ids: List[str] = []
    # Metadata for filtering/UI
    description: Optional[str] = None

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    account_ids: Optional[List[str]] = []

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    account_ids: Optional[List[str]] = []
