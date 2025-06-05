from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union, Literal
from datetime import date, datetime
from enum import Enum

class TritonTransactionType(str, Enum):
    BINDING = "binding"
    MIDTERM_ENDORSEMENT = "midterm_endorsement"
    CANCELLATION = "cancellation"

class TritonAccountData(BaseModel):
    id: Optional[str] = None
    name: str
    street_1: str
    street_2: Optional[str] = None
    city: str
    state: str
    zip: str
    full_address: Optional[str] = None
    mailing_address: Optional[Dict[str, Any]] = None

class TritonProducerData(BaseModel):
    id: Optional[str] = None
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    agency_id: Optional[str] = None
    agency_name: Optional[str] = None
    agency: Optional[Dict[str, Any]] = None

class TritonPremiumData(BaseModel):
    annual_premium: float
    annual_premium_rounded: Optional[float] = None
    policy_fee: Optional[float] = None
    taxes_and_fees: Optional[Dict[str, Any]] = None
    grand_total: Optional[float] = None
    premium_entries: Optional[List[Dict[str, Any]]] = None
    commission_rate: Optional[float] = None
    invoice_line_items: Optional[List[Dict[str, Any]]] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[Union[str, date, datetime]] = None
    invoice_due_date: Optional[Union[str, date, datetime]] = None

class TritonExposureData(BaseModel):
    id: Optional[str] = None
    program_class_id: Optional[str] = None
    program_class_name: Optional[str] = None
    coverage_id: Optional[str] = None
    coverage_name: Optional[str] = None
    territory_id: Optional[str] = None
    territory_name: Optional[str] = None
    limit: Optional[Dict[str, Any]] = None
    deductible: Optional[Union[Dict[str, Any], float, int]] = None

class TritonEndorsementData(BaseModel):
    id: Optional[str] = None
    endorsement_id: Optional[str] = None
    endorsement_code: Optional[str] = None
    endorsement_name: Optional[str] = None
    input_text: Optional[str] = None
    input_value: Optional[Any] = None
    retroactive_date: Optional[Union[str, date, datetime]] = None

class TritonMidtermEndorsementData(BaseModel):
    id: Optional[str] = None
    endorsement_id: Optional[str] = None
    endorsement_code: Optional[str] = None
    endorsement_number: Optional[str] = None
    description: Optional[str] = None
    effective_from: Optional[Union[str, date, datetime]] = None
    premium: Optional[float] = None
    premium_description: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[Union[str, date, datetime]] = None
    paid_date: Optional[Union[str, date, datetime]] = None
    void_date: Optional[Union[str, date, datetime]] = None
    credit: Optional[bool] = None

class TritonBindingTransaction(BaseModel):
    """Model for policy binding transactions"""
    # Transaction metadata
    transaction_type: Literal["binding"] = "binding"
    transaction_id: Optional[str] = None
    transaction_date: Union[str, date, datetime]
    sent_at: Optional[Union[str, date, datetime]] = None
    
    # Policy details
    policy_number: str
    effective_date: Union[str, date, datetime]
    expiration_date: Union[str, date, datetime]
    retroactive_date: Optional[Union[str, date, datetime]] = None
    gl_retroactive_date: Optional[Union[str, date, datetime]] = None
    is_renewal: Optional[bool] = False
    
    # Insured, Producer, and Broker information
    account: TritonAccountData
    producer: TritonProducerData
    broker_information: Optional[Dict[str, Any]] = None
    
    # Program and Underwriter details
    program: Dict[str, Any]
    underwriter: Optional[Dict[str, Any]] = None
    
    # Premium information
    premium: TritonPremiumData
    
    # Coverages, limits, and endorsements
    exposures: List[TritonExposureData]
    endorsements: Optional[List[TritonEndorsementData]] = None

class TritonMidtermEndorsementTransaction(BaseModel):
    """Model for midterm endorsement transactions"""
    # Transaction metadata
    transaction_type: Literal["midterm_endorsement"] = "midterm_endorsement"
    transaction_id: Optional[str] = None
    transaction_date: Union[str, date, datetime]
    transaction_status: str
    sent_at: Optional[Union[str, date, datetime]] = None
    
    # Policy details
    policy_number: str
    effective_date: Union[str, date, datetime]
    expiration_date: Union[str, date, datetime]
    
    # Endorsement details
    endorsement: TritonMidtermEndorsementData
    
    # Invoice details if invoiced
    invoice_details: Optional[Dict[str, Any]] = None
    
    # Account and Producer details
    account: Dict[str, Any]
    producer: TritonProducerData

class TritonCancellationTransaction(BaseModel):
    """Model for policy cancellation transactions"""
    # Transaction metadata
    transaction_type: Literal["cancellation"] = "cancellation"
    transaction_id: Optional[str] = None
    transaction_date: Union[str, date, datetime]
    sent_at: Optional[Union[str, date, datetime]] = None
    
    # Policy details
    policy_number: str
    effective_date: Union[str, date, datetime]
    expiration_date: Union[str, date, datetime]
    cancellation_date: Union[str, date, datetime]
    cancellation_reason: str
    
    # Return premium calculations
    days_in_effect: Optional[int] = None
    return_premium_entries: Optional[List[Dict[str, Any]]] = None
    
    # Account and Producer details
    account: Dict[str, Any]
    producer: TritonProducerData
    
    # Original premium information
    original_premium: Optional[Dict[str, Any]] = None

# Type that can be any of the transaction types
TritonTransaction = Union[
    TritonBindingTransaction,
    TritonMidtermEndorsementTransaction,
    TritonCancellationTransaction
]