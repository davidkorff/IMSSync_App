"""
Models for Producer microservice
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator


class ProducerStatus(str, Enum):
    """Producer status values"""
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"
    TERMINATED = "Terminated"


class ProducerContact(BaseModel):
    """Producer contact model"""
    contact_guid: Optional[str] = None
    first_name: str
    last_name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None
    is_primary: bool = False
    is_underwriter: bool = False
    
    # Licensing info
    license_number: Optional[str] = None
    license_states: List[str] = Field(default_factory=list)
    
    class Config:
        orm_mode = True


class ProducerLocation(BaseModel):
    """Producer location model"""
    location_guid: Optional[str] = None
    location_code: Optional[str] = None
    location_name: Optional[str] = None
    address1: str
    address2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    phone: Optional[str] = None
    is_primary: bool = False
    
    # Contacts at this location
    contacts: List[ProducerContact] = Field(default_factory=list)
    
    class Config:
        orm_mode = True


class Producer(BaseModel):
    """Producer model"""
    producer_guid: Optional[str] = None
    producer_id: Optional[int] = None
    producer_name: str
    producer_code: Optional[str] = None
    tax_id: Optional[str] = None
    status: ProducerStatus
    
    # Commission info
    default_commission_rate: Optional[Decimal] = None
    
    # Locations
    locations: List[ProducerLocation] = Field(default_factory=list)
    
    # Primary contact info (denormalized for convenience)
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    
    # Underwriter assignment
    assigned_underwriter_guid: Optional[str] = None
    assigned_underwriter_name: Optional[str] = None
    
    # Timestamps
    created_date: datetime
    modified_date: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class ProducerCreate(BaseModel):
    """Model for creating a producer"""
    producer_name: str = Field(..., description="Producer/Agency name")
    producer_code: Optional[str] = Field(None, description="Producer code")
    tax_id: Optional[str] = Field(None, description="Tax ID")
    
    # Primary location
    address1: str = Field(..., description="Primary address")
    address2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    phone: Optional[str] = None
    
    # Primary contact
    contact_first_name: str = Field(..., description="Primary contact first name")
    contact_last_name: str = Field(..., description="Primary contact last name")
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    
    # Commission
    default_commission_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    
    # Source info
    source: Optional[str] = None
    external_id: Optional[str] = None


class ProducerContactCreate(BaseModel):
    """Model for creating a producer contact"""
    producer_guid: str = Field(..., description="Producer GUID")
    location_guid: Optional[str] = Field(None, description="Location GUID (if specific to location)")
    
    first_name: str
    last_name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: bool = False
    is_underwriter: bool = False
    
    # Licensing
    license_number: Optional[str] = None
    license_states: List[str] = Field(default_factory=list)


class ProducerSearch(BaseModel):
    """Producer search criteria"""
    producer_name: Optional[str] = None
    producer_code: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    state: Optional[str] = None
    status: Optional[ProducerStatus] = None
    has_underwriter: Optional[bool] = None
    
    # Pagination
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class UnderwriterInfo(BaseModel):
    """Underwriter information"""
    underwriter_guid: str
    underwriter_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    
    class Config:
        orm_mode = True