"""
Models for Document microservice
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Document type values"""
    QUOTE = "Quote"
    BINDER = "Binder"
    POLICY = "Policy"
    INVOICE = "Invoice"
    ENDORSEMENT = "Endorsement"
    CANCELLATION = "Cancellation"
    CERTIFICATE = "Certificate"
    LOSS_RUN = "LossRun"
    APPLICATION = "Application"
    OTHER = "Other"


class DocumentStatus(str, Enum):
    """Document status values"""
    DRAFT = "Draft"
    PENDING = "Pending"
    APPROVED = "Approved"
    SENT = "Sent"
    ARCHIVED = "Archived"


class Document(BaseModel):
    """Document model"""
    document_id: Optional[int] = None
    document_guid: Optional[str] = None
    document_name: str
    document_type: DocumentType
    status: DocumentStatus
    
    # Related entities
    policy_number: Optional[str] = None
    quote_guid: Optional[str] = None
    insured_guid: Optional[str] = None
    
    # File info
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    
    # Metadata
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    version: int = 1
    
    # Timestamps
    created_date: datetime
    modified_date: Optional[datetime] = None
    sent_date: Optional[datetime] = None
    
    # User info
    created_by: Optional[str] = None
    modified_by: Optional[str] = None
    
    class Config:
        orm_mode = True


class DocumentCreate(BaseModel):
    """Model for creating a document"""
    document_name: str = Field(..., description="Document name")
    document_type: DocumentType = Field(..., description="Document type")
    
    # Related entities (at least one required)
    policy_number: Optional[str] = None
    quote_guid: Optional[str] = None
    insured_guid: Optional[str] = None
    
    # File info
    file_path: Optional[str] = Field(None, description="File path if uploading")
    content: Optional[bytes] = Field(None, description="File content if uploading")
    
    # Metadata
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DocumentSearch(BaseModel):
    """Document search criteria"""
    document_name: Optional[str] = None
    document_type: Optional[DocumentType] = None
    status: Optional[DocumentStatus] = None
    policy_number: Optional[str] = None
    quote_guid: Optional[str] = None
    insured_guid: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    
    # Pagination
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class GenerateDocumentRequest(BaseModel):
    """Request model for generating a document"""
    document_type: DocumentType = Field(..., description="Type of document to generate")
    
    # Source data (depends on document type)
    policy_number: Optional[str] = None
    quote_guid: Optional[str] = None
    
    # Template info
    template_name: Optional[str] = Field(None, description="Template to use")
    
    # Options
    format: str = Field("PDF", description="Output format: PDF, DOCX, HTML")
    include_forms: bool = Field(True, description="Include policy forms")
    send_to_insured: bool = Field(False, description="Email to insured")
    send_to_agent: bool = Field(False, description="Email to agent")
    
    # Custom data for template
    custom_data: Dict[str, Any] = Field(default_factory=dict)


class GenerateDocumentResponse(BaseModel):
    """Response model for document generation"""
    success: bool
    document_id: Optional[int] = None
    document_guid: Optional[str] = None
    document_path: Optional[str] = None
    document_url: Optional[str] = None
    emails_sent: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class UploadDocumentRequest(BaseModel):
    """Request model for uploading a document"""
    document_name: str = Field(..., description="Document name")
    document_type: DocumentType = Field(..., description="Document type")
    
    # Related entity (at least one required)
    policy_number: Optional[str] = None
    quote_guid: Optional[str] = None
    insured_guid: Optional[str] = None
    
    # File data
    file_name: str = Field(..., description="Original file name")
    file_content: bytes = Field(..., description="File content")
    mime_type: str = Field(..., description="MIME type")
    
    # Metadata
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Options
    notify: bool = Field(False, description="Notify relevant parties")


class UploadDocumentResponse(BaseModel):
    """Response model for document upload"""
    success: bool
    document_id: Optional[int] = None
    document_guid: Optional[str] = None
    file_path: Optional[str] = None
    notifications_sent: int = 0
    errors: List[str] = Field(default_factory=list)