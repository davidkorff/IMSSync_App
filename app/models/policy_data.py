from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import date, datetime

class Contact(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

class Insured(BaseModel):
    name: str
    dba: Optional[str] = None
    contact: Contact
    tax_id: Optional[str] = None
    business_type: Optional[str] = None

class Location(BaseModel):
    address: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    description: Optional[str] = None

class Producer(BaseModel):
    name: str
    contact: Optional[Contact] = None
    commission: Optional[float] = None

class Coverage(BaseModel):
    type: str
    limit: float
    deductible: Optional[float] = None
    premium: Optional[float] = None

class PolicySubmission(BaseModel):
    policy_number: str
    effective_date: date
    expiration_date: date
    bound_date: date
    program: str
    line_of_business: str
    state: str
    insured: Insured
    locations: List[Location]
    producer: Producer
    underwriter: Optional[str] = None
    coverages: List[Coverage]
    premium: float
    billing_type: Optional[str] = None
    additional_data: Optional[Dict] = None

class IntegrationResponse(BaseModel):
    success: bool
    policy_number: Optional[str] = None
    submission_guid: Optional[str] = None
    quote_guid: Optional[str] = None
    insured_guid: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now) 