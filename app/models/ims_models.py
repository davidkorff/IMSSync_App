from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class IMSAuthToken(BaseModel):
    token: str
    expires_at: datetime

class IMSInsured(BaseModel):
    insured_guid: UUID
    name: str
    address_1: str
    address_2: Optional[str] = None
    city: str
    state: str
    zip: str
    business_type: Optional[str] = None
    tax_id: Optional[str] = None

class IMSQuote(BaseModel):
    quote_guid: UUID
    submission_guid: UUID
    insured_guid: UUID
    producer_guid: UUID
    policy_number: Optional[str] = None
    effective_date: str
    expiration_date: str
    status: str
    premium: float

class IMSInvoice(BaseModel):
    invoice_guid: UUID
    policy_guid: UUID
    invoice_number: str
    invoice_date: datetime
    amount_due: float
    amount_paid: float
    balance: float
    line_items: List[dict]