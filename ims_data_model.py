"""
IMS Data Model - Common data model for policy data being imported into IMS
"""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Optional, Any


@dataclass
class InsuredParty:
    """Represents an insured party with all necessary contact information"""
    name: str
    corporation_name: Optional[str] = None
    dba: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    zip_plus: Optional[str] = None
    country_code: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    ssn: Optional[str] = None
    fein: Optional[str] = None
    business_type: Optional[int] = None


@dataclass
class PolicyParty:
    """Represents a party to the policy (producer, underwriter, etc.)"""
    name: str
    contact_info: Optional[Dict[str, str]] = None
    location: Optional[str] = None


@dataclass
class PolicyLimit:
    """Represents a policy limit"""
    type: str
    amount: str
    aggregate: Optional[str] = None


@dataclass
class PolicyDeductible:
    """Represents a policy deductible"""
    type: str
    amount: str


@dataclass
class PolicyCommission:
    """Represents commission information"""
    producer_percentage: Optional[float] = None
    company_percentage: Optional[float] = None
    terms_of_payment: Optional[int] = None


@dataclass
class PolicyData:
    """
    Common data model for policy data being imported into IMS
    
    All source-specific gatherers should output data in this format
    """
    # Policy Identification
    policy_number: str
    program: str
    line_of_business: str
    
    # Dates
    effective_date: date
    expiration_date: date
    bound_date: date
    
    # Insured Information
    insured: InsuredParty
    
    # Parties
    producer: PolicyParty
    underwriter: PolicyParty
    company_location: Optional[str] = None
    
    # Policy Details
    limits: List[PolicyLimit] = field(default_factory=list)
    deductibles: List[PolicyDeductible] = field(default_factory=list)
    commission: Optional[PolicyCommission] = None
    
    # Financial Information
    premium: float
    
    # Additional Data
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Convert string dates to date objects if necessary"""
        if isinstance(self.effective_date, str):
            try:
                parts = self.effective_date.split('/')
                self.effective_date = date(int(parts[2]), int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                pass
                
        if isinstance(self.expiration_date, str):
            try:
                parts = self.expiration_date.split('/')
                self.expiration_date = date(int(parts[2]), int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                pass
                
        if isinstance(self.bound_date, str):
            try:
                parts = self.bound_date.split('/')
                self.bound_date = date(int(parts[2]), int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                pass 