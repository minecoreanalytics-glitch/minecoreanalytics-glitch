"""
Core entity models for Morpheus platform.
These represent the business entities that modules can use.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class Customer(BaseModel):
    """Customer entity model."""
    customer_id: str
    customer_name: str
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    mrr: Optional[float] = None
    industry: Optional[str] = None
    country: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Invoice(BaseModel):
    """Invoice entity model."""
    invoice_id: str
    customer_id: str
    amount: float
    currency: Optional[str] = "USD"
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None
        }


class Contact(BaseModel):
    """Contact entity model."""
    contact_id: str
    customer_id: str
    email: str
    name: str
    role: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class Interaction(BaseModel):
    """Interaction entity model."""
    interaction_id: str
    customer_id: str
    type: str  # email, call, meeting, etc.
    channel: Optional[str] = None
    subject: Optional[str] = None
    sentiment: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
