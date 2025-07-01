from pydantic import BaseModel, Field, root_validator
from typing import List, Dict, Optional, Any, Union, Literal
from datetime import date, datetime
import json
from enum import Enum

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

class TransactionType(str, Enum):
    NEW = "new"
    UPDATE = "update"

class TransactionStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Transaction(BaseModel):
    transaction_id: str = Field(..., description="Unique identifier for the transaction")
    type: TransactionType
    source: str = Field(..., description="Source system identifier (e.g., 'triton')")
    status: TransactionStatus = TransactionStatus.RECEIVED
    raw_data: Union[Dict[str, Any], str] = Field(..., description="Raw transaction data (JSON or XML)")
    processed_data: Optional[Dict[str, Any]] = None
    received_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @root_validator(pre=True)
    def parse_raw_data(cls, values):
        # If raw_data is provided as a string, try to parse it
        if isinstance(values.get("raw_data"), str):
            try:
                # Try to parse as JSON
                values["raw_data"] = json.loads(values["raw_data"])
            except json.JSONDecodeError:
                # Keep as string if it's not valid JSON (could be XML)
                pass
        return values

class TransactionResponse(BaseModel):
    transaction_id: str
    status: TransactionStatus
    message: str
    created_at: datetime = Field(default_factory=datetime.now)

class IntegrationResponse(BaseModel):
    success: bool
    policy_number: Optional[str] = None
    submission_guid: Optional[str] = None
    quote_guid: Optional[str] = None
    insured_guid: Optional[str] = None
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now) 