"""
Models for Insured microservice
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class InsuredBase(BaseModel):
    """Base model for Insured"""
    name: str = Field(..., description="Corporation/business name")
    dba_name: Optional[str] = Field(None, description="DBA name")
    tax_id: Optional[str] = Field(None, description="FEIN/Tax ID")
    business_type: Optional[str] = Field(None, description="Business type description")
    business_type_id: Optional[int] = Field(None, description="Business type ID")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class InsuredCreate(InsuredBase):
    """Model for creating an insured"""
    address: Optional[str] = Field(None, description="Primary address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State code")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    phone: Optional[str] = Field(None, description="Primary phone")
    email: Optional[str] = Field(None, description="Primary email")
    website: Optional[str] = Field(None, description="Website URL")
    
    # Source system info
    source: Optional[str] = Field(None, description="Source system")
    external_id: Optional[str] = Field(None, description="External system ID")


class InsuredUpdate(BaseModel):
    """Model for updating an insured"""
    name: Optional[str] = None
    dba_name: Optional[str] = None
    tax_id: Optional[str] = None
    business_type: Optional[str] = None
    business_type_id: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None


class Insured(InsuredBase):
    """Complete insured model"""
    guid: str = Field(..., description="IMS GUID")
    insured_id: Optional[int] = Field(None, description="IMS Insured ID")
    created_date: datetime
    modified_date: Optional[datetime] = None
    
    # Relationships
    locations: List['InsuredLocation'] = Field(default_factory=list)
    contacts: List['InsuredContact'] = Field(default_factory=list)
    
    # Metadata
    active: bool = True
    has_submissions: bool = False
    policy_count: int = 0
    
    class Config:
        orm_mode = True


class InsuredLocation(BaseModel):
    """Insured location model"""
    location_id: Optional[int] = None
    address: str
    address2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    is_primary: bool = False
    description: Optional[str] = None
    
    class Config:
        orm_mode = True


class InsuredContact(BaseModel):
    """Insured contact model"""
    contact_id: Optional[int] = None
    first_name: str
    last_name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: bool = False
    contact_type: str = "General"
    
    class Config:
        orm_mode = True


class InsuredSearchCriteria(BaseModel):
    """Criteria for searching insureds"""
    name: Optional[str] = Field(None, description="Name to search (partial match)")
    tax_id: Optional[str] = Field(None, description="Tax ID to search")
    address: Optional[str] = Field(None, description="Address to search")
    city: Optional[str] = Field(None, description="City to search")
    state: Optional[str] = Field(None, description="State to search")
    zip_code: Optional[str] = Field(None, description="ZIP code to search")
    external_id: Optional[str] = Field(None, description="External ID to search")
    source: Optional[str] = Field(None, description="Source system")
    
    # Search options
    exact_match: bool = Field(False, description="Require exact name match")
    include_inactive: bool = Field(False, description="Include inactive insureds")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results")


class InsuredSearchResult(BaseModel):
    """Search result for insureds"""
    insureds: List[Insured]
    total_count: int
    search_criteria: InsuredSearchCriteria
    execution_time_ms: float