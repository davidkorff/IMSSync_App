"""
Standard transaction models for RSG Integration Service
All data sources transform to these standard models before processing
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class TransactionType(Enum):
    """Standard transaction types across all sources"""
    NEW_BUSINESS = "new_business"
    RENEWAL = "renewal"
    ENDORSEMENT = "endorsement"
    CANCELLATION = "cancellation"
    DECLINE = "decline"


class TransactionStatus(Enum):
    """Processing status of transactions"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class StandardAddress:
    """Standard address format"""
    street_1: str
    city: str
    state: str
    zip_code: str
    street_2: Optional[str] = None
    country: str = "US"


@dataclass
class StandardContact:
    """Standard contact information"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class StandardInsured:
    """Standard insured information"""
    name: str
    address: StandardAddress
    business_type: Optional[str] = None
    tax_id: Optional[str] = None
    dba: Optional[str] = None
    additional_named_insureds: Optional[str] = None
    scheduled_locations: Optional[str] = None


@dataclass
class StandardProducer:
    """Standard producer information"""
    id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    license_number: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class StandardAgency:
    """Standard agency information"""
    id: str
    name: str
    address: StandardAddress
    contact: StandardContact
    parent_agency: Optional[str] = None
    commission_rate: float = 0.0
    always_file_taxes: bool = False


@dataclass
class StandardUnderwriter:
    """Standard underwriter information"""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class StandardCoverage:
    """Standard coverage information"""
    coverage_type: str
    limits: Optional[str] = None
    deductible: Optional[str] = None
    premium: Optional[float] = None
    rating_unit: Optional[str] = None
    rating_count: Optional[float] = None
    territory: Optional[str] = None
    retroactive_date: Optional[date] = None


@dataclass
class StandardFinancials:
    """Standard financial information"""
    gross_premium: float
    base_premium: Optional[float] = None
    policy_fee: float = 0.0
    surplus_lines_tax: float = 0.0
    stamping_fee: float = 0.0
    other_fees: float = 0.0
    commission_percent: float = 0.0
    commission_amount: float = 0.0
    net_premium: Optional[float] = None
    credit_debit_factor: float = 1.0
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    
    def calculate_totals(self):
        """Calculate derived financial fields"""
        self.commission_amount = self.gross_premium * (self.commission_percent / 100)
        self.net_premium = self.gross_premium - self.commission_amount
        
        # Apply credit/debit factor
        if self.credit_debit_factor != 1.0:
            self.gross_premium *= self.credit_debit_factor
            self.commission_amount *= self.credit_debit_factor
            self.net_premium *= self.credit_debit_factor


@dataclass
class StandardBDXFields:
    """Standard BDX/Bordereaux fields"""
    umr: Optional[str] = None  # Unique Market Reference
    agreement_no: Optional[str] = None
    section_no: Optional[str] = None
    coverholder_name: Optional[str] = None
    slip_commission_percent: Optional[float] = None


@dataclass
class StandardSurplusLinesBroker:
    """Standard surplus lines broker information"""
    name: Optional[str] = None
    license_no: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None


@dataclass
class StandardTransaction:
    """
    Standard transaction format that all sources transform to
    This is the common format used throughout the processing pipeline
    """
    # Core identification
    source_system: str  # "triton", "xuber", etc.
    source_transaction_id: str
    transaction_type: TransactionType
    
    # Policy information
    policy_number: Optional[str] = None
    opportunity_name: Optional[str] = None
    program_name: str = ""
    program_code: str = ""
    effective_date: Optional[date] = None
    expiration_date: Optional[date] = None
    bound_date: Optional[date] = None
    paid_date: Optional[date] = None
    policy_sent_date: Optional[date] = None
    
    # Parties
    insured: Optional[StandardInsured] = None
    producer: Optional[StandardProducer] = None
    agency: Optional[StandardAgency] = None
    underwriter: Optional[StandardUnderwriter] = None
    assistant_underwriter: Optional[StandardUnderwriter] = None
    surplus_lines_broker: Optional[StandardSurplusLinesBroker] = None
    
    # Coverage and financials
    coverages: List[StandardCoverage] = field(default_factory=list)
    financials: Optional[StandardFinancials] = None
    
    # BDX fields
    bdx_fields: Optional[StandardBDXFields] = None
    
    # Additional information
    territory: Optional[str] = None
    business_type: Optional[str] = None
    is_tail_policy: bool = False
    is_renewal: bool = False
    previous_policy_number: Optional[str] = None
    
    # Counts and flags
    endorsement_count: int = 0
    midterm_endorsement_count: int = 0
    claim_count: int = 0
    has_claims: bool = False
    
    # Processing metadata
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    # Source-specific data (for debugging/auditing)
    source_data: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate required fields and return list of errors"""
        errors = []
        
        if not self.source_system:
            errors.append("source_system is required")
        
        if not self.source_transaction_id:
            errors.append("source_transaction_id is required")
        
        if not self.transaction_type:
            errors.append("transaction_type is required")
        
        if not self.program_name:
            errors.append("program_name is required")
        
        if not self.insured:
            errors.append("insured information is required")
        elif not self.insured.name:
            errors.append("insured name is required")
        
        if not self.producer:
            errors.append("producer information is required")
        
        if not self.agency:
            errors.append("agency information is required")
        
        if not self.financials:
            errors.append("financial information is required")
        
        if self.transaction_type in [TransactionType.NEW_BUSINESS, TransactionType.RENEWAL]:
            if not self.effective_date:
                errors.append("effective_date is required for new business/renewals")
            if not self.expiration_date:
                errors.append("expiration_date is required for new business/renewals")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if transaction is valid for processing"""
        return len(self.validate()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "source_system": self.source_system,
            "source_transaction_id": self.source_transaction_id,
            "transaction_type": self.transaction_type.value,
            "policy_number": self.policy_number,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "insured": {
                "name": self.insured.name if self.insured else None,
                "tax_id": self.insured.tax_id if self.insured else None,
                "business_type": self.insured.business_type if self.insured else None
            } if self.insured else None,
            "producer": {
                "name": self.producer.full_name if self.producer else None,
                "email": self.producer.email if self.producer else None,
                "license_number": self.producer.license_number if self.producer else None
            } if self.producer else None,
            "agency": {
                "id": self.agency.id if self.agency else None,
                "name": self.agency.name if self.agency else None
            } if self.agency else None,
            "financials": {
                "gross_premium": self.financials.gross_premium if self.financials else 0,
                "commission_amount": self.financials.commission_amount if self.financials else 0,
                "net_premium": self.financials.net_premium if self.financials else 0
            } if self.financials else None,
            "program_name": self.program_name,
            "program_code": self.program_code,
            "territory": self.territory
        }


# Factory functions for creating standard models from source data
def create_standard_address(**kwargs) -> StandardAddress:
    """Create StandardAddress from various source formats"""
    return StandardAddress(
        street_1=kwargs.get('street_1', ''),
        street_2=kwargs.get('street_2'),
        city=kwargs.get('city', ''),
        state=kwargs.get('state', ''),
        zip_code=kwargs.get('zip', kwargs.get('zip_code', '')),
        country=kwargs.get('country', 'US')
    )


def create_standard_contact(**kwargs) -> StandardContact:
    """Create StandardContact from various source formats"""
    return StandardContact(
        name=kwargs.get('name', ''),
        email=kwargs.get('email'),
        phone=kwargs.get('phone')
    )