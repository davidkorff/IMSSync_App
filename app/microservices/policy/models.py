"""
Models for Policy microservice
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator


class PolicyStatus(str, Enum):
    """Policy status values"""
    ACTIVE = "Active"
    CANCELLED = "Cancelled"
    EXPIRED = "Expired"
    PENDING = "Pending"
    REINSTATED = "Reinstated"
    NON_RENEWED = "Non-Renewed"


class CancellationReason(int, Enum):
    """Common cancellation reasons"""
    NON_PAYMENT = 1
    INSURED_REQUEST = 2
    UNDERWRITING = 3
    FRAUD = 4
    OTHER = 99


class EndorsementReason(int, Enum):
    """Common endorsement reasons"""
    COVERAGE_CHANGE = 1
    LOCATION_CHANGE = 2
    VEHICLE_CHANGE = 3
    DRIVER_CHANGE = 4
    LIMIT_CHANGE = 5
    OTHER = 99


class ReinstatementReason(int, Enum):
    """Common reinstatement reasons"""
    PAYMENT_RECEIVED = 1
    ERROR_CORRECTION = 2
    COURT_ORDER = 3
    OTHER = 99


class Policy(BaseModel):
    """Policy model"""
    policy_id: Optional[int] = None
    policy_number: str
    quote_guid: str
    quote_number: Optional[str] = None
    
    # Insured info
    insured_guid: str
    insured_name: str
    
    # Policy details
    effective_date: date
    expiration_date: date
    status: PolicyStatus
    line_of_business: str
    state: str
    
    # Premium info
    total_premium: Decimal
    written_premium: Optional[Decimal] = None
    
    # Dates
    bound_date: date
    issued_date: Optional[date] = None
    cancelled_date: Optional[date] = None
    
    # Control info
    control_number: Optional[str] = None
    
    # Timestamps
    created_date: datetime
    modified_date: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class PolicySearch(BaseModel):
    """Policy search criteria"""
    policy_number: Optional[str] = None
    control_number: Optional[str] = None
    insured_name: Optional[str] = None
    insured_guid: Optional[str] = None
    quote_guid: Optional[str] = None
    effective_date_from: Optional[date] = None
    effective_date_to: Optional[date] = None
    status: Optional[PolicyStatus] = None
    state: Optional[str] = None
    
    # Pagination
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class CancellationRequest(BaseModel):
    """Request model for policy cancellation"""
    control_number: str = Field(..., description="Policy control number")
    cancellation_date: date = Field(..., description="Cancellation effective date")
    cancellation_reason_id: int = Field(..., description="Cancellation reason ID")
    comments: str = Field(..., description="Cancellation comments")
    
    # Optional fields
    user_guid: Optional[str] = Field(None, description="User performing cancellation")
    return_premium: bool = Field(True, description="Whether to return premium")
    flat_cancel: bool = Field(False, description="Flat cancellation (no return premium)")
    
    @validator('cancellation_date')
    def validate_cancellation_date(cls, v, values):
        # Add validation logic if needed
        return v


class CancellationResponse(BaseModel):
    """Response model for policy cancellation"""
    success: bool
    policy_number: str
    cancellation_date: date
    return_premium_amount: Optional[Decimal] = None
    cancellation_id: Optional[str] = None
    ims_reference: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class EndorsementRequest(BaseModel):
    """Request model for policy endorsement"""
    control_number: str = Field(..., description="Policy control number")
    endorsement_effective_date: date = Field(..., description="Endorsement effective date")
    endorsement_reason_id: int = Field(..., description="Endorsement reason ID")
    endorsement_comment: str = Field(..., description="Endorsement comment")
    
    # Optional fields
    user_guid: Optional[str] = Field(None, description="User creating endorsement")
    calculation_type: str = Field("P", description="P=Pro-rata, S=Short-rate, F=Flat")
    copy_exposures: bool = Field(True, description="Copy exposures from current term")
    copy_premiums: bool = Field(False, description="Copy premiums from current term")
    
    # Premium changes
    premium_change: Optional[Decimal] = Field(None, description="Premium adjustment amount")
    
    @validator('calculation_type')
    def validate_calculation_type(cls, v):
        if v not in ['P', 'S', 'F']:
            raise ValueError('Calculation type must be P, S, or F')
        return v


class EndorsementResponse(BaseModel):
    """Response model for policy endorsement"""
    success: bool
    policy_number: str
    endorsement_number: Optional[str] = None
    endorsement_quote_guid: Optional[str] = None
    endorsement_effective_date: date
    premium_change: Optional[Decimal] = None
    new_total_premium: Optional[Decimal] = None
    ims_reference: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ReinstatementRequest(BaseModel):
    """Request model for policy reinstatement"""
    control_number: str = Field(..., description="Policy control number")
    reinstatement_date: date = Field(..., description="Reinstatement effective date")
    reinstatement_reason_id: int = Field(..., description="Reinstatement reason ID")
    comments: str = Field(..., description="Reinstatement comments")
    
    # Optional fields
    user_guid: Optional[str] = Field(None, description="User performing reinstatement")
    generate_invoice: bool = Field(True, description="Generate reinstatement invoice")
    payment_received: Optional[Decimal] = Field(None, description="Payment amount received")
    check_number: Optional[str] = Field(None, description="Check/payment reference number")
    
    @validator('reinstatement_date')
    def validate_reinstatement_date(cls, v, values):
        # Add validation logic if needed
        return v


class ReinstatementResponse(BaseModel):
    """Response model for policy reinstatement"""
    success: bool
    policy_number: str
    reinstatement_date: date
    reinstatement_amount: Optional[Decimal] = None
    invoice_number: Optional[str] = None
    invoice_amount: Optional[Decimal] = None
    ims_reference: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)