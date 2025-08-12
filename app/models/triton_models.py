from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import date
from uuid import UUID

class AdditionalInsured(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None

class TritonPayload(BaseModel):
    umr: Optional[str] = None
    agreement_number: Optional[str] = None
    section_number: Optional[str] = None
    class_of_business: str
    program_name: str
    policy_number: str
    underwriter_name: str
    producer_name: str
    producer_email: Optional[str] = None
    invoice_date: str
    policy_fee: float
    surplus_lines_tax: Optional[str] = ""
    stamping_fee: Optional[str] = ""
    other_fee: Optional[str] = ""
    insured_name: str
    insured_state: str
    insured_zip: str
    effective_date: str
    expiration_date: str
    bound_date: str
    opportunity_type: str
    business_type: str
    status: str
    limit_amount: str
    limit_prior: str
    deductible_amount: str
    gross_premium: float
    commission_rate: float
    commission_percent: float
    commission_amount: float
    net_premium: float
    base_premium: float
    opportunity_id: int
    midterm_endt_id: Optional[int] = None
    midterm_endt_description: Optional[str] = None
    midterm_endt_effective_from: Optional[str] = ""
    midterm_endt_endorsement_number: Optional[int] = None
    additional_insured: List[AdditionalInsured] = Field(default_factory=list)
    address_1: str
    address_2: Optional[str] = ""
    city: str
    state: str
    zip: str
    transaction_id: str
    prior_transaction_id: Optional[str] = None
    transaction_type: Literal["Bind", "Unbind", "Issue", "Midterm Endorsement", "Cancellation"]

class ProcessingResult(BaseModel):
    success: bool
    transaction_id: str
    transaction_type: str
    service_response: dict
    ims_responses: List[dict]
    invoice_details: Optional[dict] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)