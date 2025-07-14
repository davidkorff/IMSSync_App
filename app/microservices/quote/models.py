"""
Models for Quote microservice
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator


class QuoteStatus(int, Enum):
    """Quote status values"""
    NEW = 1
    QUOTED = 2
    BOUND = 3
    DECLINED = 4
    EXPIRED = 5
    CANCELLED = 6


class SubmissionCreate(BaseModel):
    """Model for creating a submission"""
    insured_guid: str = Field(..., description="Insured GUID")
    submission_date: date = Field(..., description="Submission date")
    producer_contact_guid: str = Field(..., description="Producer contact GUID")
    producer_location_guid: str = Field(..., description="Producer location GUID")
    underwriter_guid: str = Field(..., description="Underwriter GUID")
    
    # Optional fields
    description: Optional[str] = Field(None, description="Submission description")
    source: Optional[str] = Field(None, description="Source system")
    external_id: Optional[str] = Field(None, description="External system ID")


class Submission(BaseModel):
    """Complete submission model"""
    guid: str = Field(..., description="Submission GUID")
    submission_id: Optional[int] = Field(None, description="IMS Submission ID")
    insured_guid: str
    submission_date: date
    producer_contact_guid: str
    producer_location_guid: str
    underwriter_guid: str
    created_date: datetime
    modified_date: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class QuoteCreate(BaseModel):
    """Model for creating a quote"""
    submission_guid: str = Field(..., description="Submission GUID")
    effective_date: date = Field(..., description="Policy effective date")
    expiration_date: date = Field(..., description="Policy expiration date")
    state: str = Field(..., description="State code", max_length=2)
    line_guid: str = Field(..., description="Line of business GUID")
    
    # Location GUIDs
    quoting_location_guid: str = Field(..., description="Quoting location GUID")
    issuing_location_guid: str = Field(..., description="Issuing location GUID")
    company_location_guid: str = Field(..., description="Company location GUID")
    
    # Optional fields
    producer_contact_guid: Optional[str] = None
    status_id: int = Field(QuoteStatus.NEW, description="Quote status")
    billing_type_id: int = Field(1, description="Billing type (1=Agency Bill)")
    external_quote_id: Optional[str] = None
    external_system: Optional[str] = None
    
    @validator('state')
    def validate_state(cls, v):
        if len(v) != 2:
            raise ValueError('State must be 2 characters')
        return v.upper()


class QuoteUpdate(BaseModel):
    """Model for updating a quote"""
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status_id: Optional[int] = None
    external_quote_id: Optional[str] = None
    risk_info: Optional[Dict[str, Any]] = None


class Quote(BaseModel):
    """Complete quote model"""
    guid: str = Field(..., description="Quote GUID")
    quote_id: Optional[int] = Field(None, description="IMS Quote ID")
    quote_number: Optional[str] = None
    submission_guid: str
    effective_date: date
    expiration_date: date
    state: str
    line_guid: str
    status_id: int
    status_description: Optional[str] = None
    
    # Premium info
    premium: Optional[Decimal] = None
    quote_option_id: Optional[str] = None
    
    # Policy info (if bound)
    policy_number: Optional[str] = None
    bound_date: Optional[date] = None
    
    # Timestamps
    created_date: datetime
    modified_date: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class QuoteOption(BaseModel):
    """Quote option model"""
    option_id: str = Field(..., description="Option ID")
    quote_guid: str
    option_number: int = Field(1, description="Option number")
    description: Optional[str] = None
    total_premium: Decimal = Field(Decimal('0'), description="Total premium")
    
    class Config:
        orm_mode = True


class PremiumCreate(BaseModel):
    """Model for adding premium"""
    quote_guid: str = Field(..., description="Quote GUID")
    quote_option_id: str = Field(..., description="Quote option ID")
    amount: Decimal = Field(..., description="Premium amount", gt=0)
    description: str = Field(..., description="Premium description")
    
    # Optional fields
    premium_type: str = Field("Base Premium", description="Type of premium")
    is_taxable: bool = Field(True, description="Whether premium is taxable")
    is_fee: bool = Field(False, description="Whether this is a fee")


class Premium(BaseModel):
    """Premium model"""
    premium_id: Optional[int] = None
    quote_guid: str
    quote_option_id: str
    amount: Decimal
    description: str
    premium_type: str
    is_taxable: bool
    is_fee: bool
    
    class Config:
        orm_mode = True


class BindRequest(BaseModel):
    """Request model for binding a quote"""
    quote_option_id: str = Field(..., description="Quote option ID to bind")
    policy_number_override: Optional[str] = Field(None, description="Override policy number")
    bind_date: Optional[date] = Field(None, description="Bind date (defaults to today)")
    
    # Payment info
    down_payment_received: bool = Field(False, description="Whether down payment received")
    payment_plan_id: Optional[int] = None


class BindResponse(BaseModel):
    """Response model for binding"""
    success: bool
    policy_number: str
    bound_date: date
    invoice_generated: bool = False
    invoice_number: Optional[str] = None
    errors: List[str] = Field(default_factory=list)


class RatingRequest(BaseModel):
    """Request model for rating a quote"""
    quote_guid: str = Field(..., description="Quote GUID")
    rating_method: str = Field("manual", description="Rating method: manual, excel, api")
    
    # For manual rating
    manual_premium: Optional[Decimal] = None
    
    # For Excel rating
    excel_template_path: Optional[str] = None
    rater_id: Optional[int] = None
    factor_set_guid: Optional[str] = None
    
    # Rating data
    rating_data: Dict[str, Any] = Field(default_factory=dict)


class RatingResponse(BaseModel):
    """Response model for rating"""
    success: bool
    quote_option_id: Optional[str] = None
    total_premium: Optional[Decimal] = None
    premium_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    rating_sheet_id: Optional[str] = None
    errors: List[str] = Field(default_factory=list)