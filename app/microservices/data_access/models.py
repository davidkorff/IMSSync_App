"""
Models for Data Access microservice
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class LookupType(str, Enum):
    """Types of lookup data available"""
    BUSINESS_TYPES = "business_types"
    STATES = "states"
    LINES = "lines"
    COMPANIES = "companies"
    LOCATIONS = "locations"
    CANCELLATION_REASONS = "cancellation_reasons"
    ENDORSEMENT_REASONS = "endorsement_reasons"
    REINSTATEMENT_REASONS = "reinstatement_reasons"
    PAYMENT_TERMS = "payment_terms"
    BILLING_TYPES = "billing_types"


class QueryRequest(BaseModel):
    """Request model for executing queries"""
    query: str = Field(..., description="SQL query to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    timeout: Optional[int] = Field(30, description="Query timeout in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "SELECT * FROM Insureds WHERE State = @State",
                "parameters": {"State": "TX"},
                "timeout": 30
            }
        }


class QueryResponse(BaseModel):
    """Response model for query execution"""
    success: bool
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Result tables")
    row_count: int = Field(0, description="Total rows returned")
    execution_time_ms: float = Field(0, description="Query execution time")
    error: Optional[str] = None


class CommandRequest(BaseModel):
    """Request model for executing commands (stored procedures)"""
    command: str = Field(..., description="Stored procedure name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    timeout: Optional[int] = Field(60, description="Command timeout in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "command": "UpdateInsuredStatus_WS",
                "parameters": {
                    "InsuredGUID": "123e4567-e89b-12d3-a456-426614174000",
                    "Status": "Active"
                }
            }
        }


class CommandResponse(BaseModel):
    """Response model for command execution"""
    success: bool
    result: Any = Field(None, description="Command result")
    output_parameters: Dict[str, Any] = Field(default_factory=dict)
    return_value: Optional[Any] = None
    execution_time_ms: float = Field(0)
    error: Optional[str] = None


class ProgramData(BaseModel):
    """Model for storing program-specific data"""
    program: str = Field(..., description="Program name (e.g., 'triton', 'xuber')")
    quote_guid: str = Field(..., description="IMS Quote GUID")
    external_id: str = Field(..., description="External system ID")
    data: Dict[str, Any] = Field(..., description="Program-specific data")
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "program": "triton",
                "quote_guid": "123e4567-e89b-12d3-a456-426614174000",
                "external_id": "TRT-2024-001",
                "data": {
                    "vehicle_count": 5,
                    "driver_count": 3,
                    "coverage_type": "primary"
                }
            }
        }


class LookupData(BaseModel):
    """Model for lookup data results"""
    lookup_type: LookupType
    items: List[Dict[str, Any]]
    count: int
    cached: bool = False
    cache_expires: Optional[datetime] = None