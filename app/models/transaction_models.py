from pydantic import BaseModel, Field, root_validator
from typing import List, Dict, Optional, Any, Union, Literal
from datetime import date, datetime
import json
from enum import Enum
import uuid

class TransactionType(str, Enum):
    NEW = "new"
    UPDATE = "update"

class TransactionStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class IMSProcessingStatus(str, Enum):
    PENDING = "pending"
    INSURED_CREATED = "insured_created"
    SUBMISSION_CREATED = "submission_created"
    QUOTE_CREATED = "quote_created"
    RATED = "rated"
    BOUND = "bound"
    ISSUED = "issued"
    ERROR = "error"

class IMSEntity(BaseModel):
    """Base class for IMS entities with GUID tracking"""
    guid: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None

class IMSInsured(IMSEntity):
    """Tracks insured entity in IMS"""
    name: str
    tax_id: Optional[str] = None
    business_type_id: Optional[int] = None

class IMSSubmission(IMSEntity):
    """Tracks submission entity in IMS"""
    insured_guid: str
    submission_date: date
    producer_contact_guid: Optional[str] = None
    underwriter_guid: Optional[str] = None
    producer_location_guid: Optional[str] = None

class IMSQuote(IMSEntity):
    """Tracks quote entity in IMS"""
    submission_guid: str
    quote_number: Optional[str] = None
    effective_date: date
    expiration_date: date
    state: str
    line_guid: Optional[str] = None
    status_id: Optional[int] = None
    premium: Optional[float] = None
    quote_option_id: Optional[int] = None

class IMSPolicy(IMSEntity):
    """Tracks policy entity in IMS"""
    quote_guid: str
    policy_number: str
    bound_date: date
    status: str = "Active"
    
class TransactionProcessingData(BaseModel):
    """Tracks the IMS processing steps for a transaction"""
    status: IMSProcessingStatus = IMSProcessingStatus.PENDING
    insured: Optional[IMSInsured] = None
    submission: Optional[IMSSubmission] = None
    quote: Optional[IMSQuote] = None
    policy: Optional[IMSPolicy] = None
    last_error: Optional[str] = None
    excel_rater_file_path: Optional[str] = None
    excel_rater_id: Optional[int] = None
    factor_set_guid: Optional[str] = None
    processing_logs: List[str] = Field(default_factory=list)
    
    def add_log(self, message: str):
        """Add a processing log entry with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.processing_logs.append(f"[{timestamp}] {message}")
    
    def update_status(self, status: IMSProcessingStatus, message: Optional[str] = None):
        """Update the processing status with an optional log message"""
        self.status = status
        if message:
            self.add_log(message)

class Transaction(BaseModel):
    """Comprehensive transaction model with IMS integration tracking"""
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    external_id: Optional[str] = None
    type: TransactionType
    source: str = Field(..., description="Source system identifier (e.g., 'triton')")
    status: TransactionStatus = TransactionStatus.RECEIVED
    raw_data: Union[Dict[str, Any], str] = Field(..., description="Raw transaction data (JSON or XML)")
    parsed_data: Optional[Dict[str, Any]] = None
    processed_data: Optional[Dict[str, Any]] = None
    received_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    ims_processing: TransactionProcessingData = Field(default_factory=TransactionProcessingData)
    
    def update_status(self, status: TransactionStatus, message: Optional[str] = None):
        """Update the transaction status"""
        self.status = status
        if status == TransactionStatus.COMPLETED or status == TransactionStatus.FAILED:
            self.processed_at = datetime.now()
        
        if message:
            if status == TransactionStatus.FAILED:
                self.error_message = message
                self.ims_processing.last_error = message
            self.ims_processing.add_log(message)
    
    @root_validator(pre=True)
    def parse_raw_data(cls, values):
        """Parse raw_data if it's a string"""
        if isinstance(values.get("raw_data"), str):
            try:
                # Try to parse as JSON
                values["parsed_data"] = json.loads(values["raw_data"])
            except json.JSONDecodeError:
                # Keep as string if it's not valid JSON (could be XML)
                pass
        elif isinstance(values.get("raw_data"), dict):
            values["parsed_data"] = values["raw_data"]
            
        return values

class TransactionResponse(BaseModel):
    """API response for transaction operations"""
    transaction_id: str
    status: TransactionStatus
    message: str
    ims_status: Optional[IMSProcessingStatus] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
class TransactionSearchParams(BaseModel):
    """Parameters for searching transactions"""
    source: Optional[str] = None
    status: Optional[TransactionStatus] = None
    external_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = 100
    offset: int = 0