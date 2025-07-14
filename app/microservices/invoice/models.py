"""
Models for Invoice microservice
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator


class InvoiceStatus(str, Enum):
    """Invoice status values"""
    PENDING = "Pending"
    SENT = "Sent"
    PAID = "Paid"
    PARTIAL = "Partial"
    OVERDUE = "Overdue"
    CANCELLED = "Cancelled"
    VOID = "Void"


class InvoiceLineItem(BaseModel):
    """Invoice line item model"""
    description: str
    amount: Decimal
    quantity: int = 1
    unit_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    line_item_order: int = 0
    is_taxable: bool = True
    
    class Config:
        orm_mode = True


class PaymentInfo(BaseModel):
    """Payment information model"""
    payment_terms: str = Field("Net 30", description="Payment terms")
    due_date: date
    
    # ACH Info
    ach_enabled: bool = False
    ach_bank_name: Optional[str] = None
    ach_routing_number: Optional[str] = None
    ach_account_number: Optional[str] = None
    ach_account_name: Optional[str] = None
    
    # Wire Info
    wire_enabled: bool = False
    wire_bank_name: Optional[str] = None
    wire_swift_code: Optional[str] = None
    wire_routing_number: Optional[str] = None
    wire_account_number: Optional[str] = None
    
    # Check Info
    check_enabled: bool = True
    check_payable_to: Optional[str] = None
    check_mail_to_name: Optional[str] = None
    check_mail_to_street: Optional[str] = None
    check_mail_to_city: Optional[str] = None
    check_mail_to_state: Optional[str] = None
    check_mail_to_zip: Optional[str] = None
    
    # Online Payment
    online_payment_url: Optional[str] = None
    
    class Config:
        orm_mode = True


class BillingInfo(BaseModel):
    """Billing information model"""
    billing_name: str
    attention_to: Optional[str] = None
    address1: str
    address2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    class Config:
        orm_mode = True


class Invoice(BaseModel):
    """Complete invoice model"""
    invoice_id: Optional[int] = None
    invoice_number: str
    invoice_date: date
    due_date: date
    
    # Amounts
    subtotal: Decimal
    tax_total: Decimal = Decimal("0")
    total_amount: Decimal
    amount_paid: Decimal = Decimal("0")
    balance_due: Decimal
    
    # Status
    status: InvoiceStatus
    
    # Policy info
    policy_number: str
    quote_number: Optional[str] = None
    effective_date: date
    expiration_date: date
    coverage_type: Optional[str] = None
    carrier_name: Optional[str] = None
    
    # Limits
    limit_per_occurrence: Optional[str] = None
    limit_aggregate: Optional[str] = None
    deductible: Optional[str] = None
    
    # Insured info
    insured_name: str
    insured_tax_id: Optional[str] = None
    
    # Line items
    line_items: List[InvoiceLineItem] = Field(default_factory=list)
    
    # Billing and payment info
    billing_info: Optional[BillingInfo] = None
    payment_info: Optional[PaymentInfo] = None
    
    # Agent info
    agency_name: Optional[str] = None
    agent_name: Optional[str] = None
    agent_email: Optional[str] = None
    agent_phone: Optional[str] = None
    commission_rate: Optional[Decimal] = None
    commission_amount: Optional[Decimal] = None
    
    # Timestamps
    created_date: datetime
    modified_date: Optional[datetime] = None
    sent_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class InvoiceSearch(BaseModel):
    """Invoice search criteria"""
    invoice_number: Optional[str] = None
    policy_number: Optional[str] = None
    quote_number: Optional[str] = None
    insured_name: Optional[str] = None
    status: Optional[InvoiceStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    
    # Pagination
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class GenerateInvoiceRequest(BaseModel):
    """Request model for generating an invoice"""
    policy_number: str = Field(..., description="Policy number")
    invoice_type: str = Field("New", description="Type: New, Endorsement, Cancellation, Reinstatement")
    
    # Optional overrides
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    custom_line_items: List[InvoiceLineItem] = Field(default_factory=list)
    
    # Options
    send_to_insured: bool = Field(False, description="Email to insured")
    send_to_agent: bool = Field(False, description="Email to agent")
    generate_pdf: bool = Field(True, description="Generate PDF")


class GenerateInvoiceResponse(BaseModel):
    """Response model for invoice generation"""
    success: bool
    invoice_number: Optional[str] = None
    invoice_id: Optional[int] = None
    pdf_path: Optional[str] = None
    emails_sent: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class AddPaymentRequest(BaseModel):
    """Request model for adding payment to invoice"""
    invoice_number: str = Field(..., description="Invoice number")
    payment_amount: Decimal = Field(..., description="Payment amount", gt=0)
    payment_date: date = Field(..., description="Payment date")
    payment_method: str = Field(..., description="Payment method: Check, ACH, Wire, Card, Cash")
    
    # Payment details
    check_number: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None
    
    # Processing options
    apply_to_oldest: bool = Field(True, description="Apply to oldest invoices first")
    send_receipt: bool = Field(False, description="Send payment receipt")
    
    @validator('payment_method')
    def validate_payment_method(cls, v):
        valid_methods = ['Check', 'ACH', 'Wire', 'Card', 'Cash']
        if v not in valid_methods:
            raise ValueError(f'Payment method must be one of: {", ".join(valid_methods)}')
        return v


class AddPaymentResponse(BaseModel):
    """Response model for payment addition"""
    success: bool
    payment_id: Optional[str] = None
    remaining_balance: Decimal
    invoice_status: Optional[InvoiceStatus] = None
    receipt_sent: bool = False
    errors: List[str] = Field(default_factory=list)