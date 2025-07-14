"""
Common models for microservices
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"


class ServiceResponse(BaseModel):
    """Standard response model for all services"""
    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "Example"},
                "error": None,
                "warnings": [],
                "metadata": {"request_id": "abc123"},
                "timestamp": "2024-01-15T10:30:00"
            }
        }


class ServiceHealth(BaseModel):
    """Service health check response"""
    service_name: str
    status: ServiceStatus
    version: str
    uptime_seconds: float
    last_check: datetime
    dependencies: Dict[str, ServiceStatus] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class PaginationParams(BaseModel):
    """Common pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=1000, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("asc", regex="^(asc|desc)$", description="Sort order")


class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool