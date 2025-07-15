import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.models.triton_models import TritonPayload, ProcessingResult
from app.services.ims import AuthService, InsuredService, QuoteService, InvoiceService
from app.utils.policy_store import policy_store

logger = logging.getLogger(__name__)

class TritonProcessor:
    def __init__(self):
        self.auth_service = AuthService()
        self.insured_service = InsuredService(self.auth_service)
        self.quote_service = QuoteService(self.auth_service)
        self.invoice_service = InvoiceService(self.auth_service)
    
    async def process_transaction(self, payload: TritonPayload) -> ProcessingResult:
        """Main entry point for processing Triton transactions"""
        logger.info(f"Processing {payload.transaction_type} transaction: {payload.transaction_id}")
        
        try:
            if payload.transaction_type == "Bind":
                return await self._process_bind(payload)
            elif payload.transaction_type == "Unbind":
                return await self._process_unbind(payload)
            elif payload.transaction_type == "Issue":
                return await self._process_issue(payload)
            elif payload.transaction_type == "Midterm Endorsement":
                return await self._process_midterm_endorsement(payload)
            elif payload.transaction_type == "Cancellation":
                return await self._process_cancellation(payload)
            else:
                raise ValueError(f"Unknown transaction type: {payload.transaction_type}")
                
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            return ProcessingResult(
                success=False,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response={},
                ims_responses=[],
                errors=[str(e)]
            )
    
    async def _process_bind(self, payload: TritonPayload) -> ProcessingResult:
        """Process a Bind transaction"""
        ims_responses = []
        errors = []
        warnings = []
        
        try:
            # Step 1: Search for existing insured
            insured_guid = self.insured_service.find_by_name_and_address(
                name=payload.insured_name,
                address=payload.address_1,
                city=payload.city,
                state=payload.state,
                zip_code=payload.zip
            )
            
            # Step 2: Create insured if not found
            if not insured_guid:
                logger.info(f"Creating new insured: {payload.insured_name}")
                insured_data = {
                    "insured_name": payload.insured_name,
                    "business_type": payload.business_type,
                    "address_1": payload.address_1,
                    "address_2": payload.address_2,
                    "city": payload.city,
                    "state": payload.state,
                    "zip": payload.zip
                }
                insured_guid = self.insured_service.create_with_location(insured_data)
                ims_responses.append({
                    "action": "create_insured",
                    "result": {"insured_guid": str(insured_guid)}
                })
            else:
                ims_responses.append({
                    "action": "find_insured",
                    "result": {"insured_guid": str(insured_guid)}
                })
            
            # Step 3: Create submission
            submission_data = {
                "effective_date": payload.effective_date,
                "expiration_date": payload.expiration_date,
                "program_name": payload.program_name,
                "class_of_business": payload.class_of_business,
                "producer_name": payload.producer_name,
                "underwriter_name": payload.underwriter_name
            }
            submission_guid = self.quote_service.create_submission(insured_guid, submission_data)
            ims_responses.append({
                "action": "create_submission",
                "result": {"submission_guid": str(submission_guid)}
            })
            
            # Step 4: Create quote
            quote_data = {
                "state": payload.state,
                "limit_amount": payload.limit_amount,
                "deductible_amount": payload.deductible_amount,
                "premium": payload.gross_premium
            }
            quote_guid = self.quote_service.create_quote(submission_guid, quote_data)
            ims_responses.append({
                "action": "create_quote",
                "result": {"quote_guid": str(quote_guid)}
            })
            
            # Step 5: Bind the quote
            bind_data = {
                "bound_date": payload.bound_date,
                "policy_number": payload.policy_number
            }
            bind_result = self.quote_service.bind(quote_guid, bind_data)
            ims_responses.append({
                "action": "bind_quote",
                "result": bind_result
            })
            
            # Step 6: Get invoice details
            invoice_details = self.invoice_service.get_invoice(quote_guid)
            
            # Store policy mapping
            policy_guid = bind_result.get("policy_guid")
            if policy_guid:
                policy_store.store_policy(
                    policy_number=payload.policy_number,
                    policy_guid=UUID(policy_guid),
                    transaction_id=payload.transaction_id,
                    additional_data={
                        "insured_guid": str(insured_guid),
                        "submission_guid": str(submission_guid),
                        "quote_guid": str(quote_guid)
                    }
                )
            
            service_response = {
                "insured_guid": str(insured_guid),
                "submission_guid": str(submission_guid),
                "quote_guid": str(quote_guid),
                "policy_guid": policy_guid,
                "status": "bound"
            }
            
            return ProcessingResult(
                success=True,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response=service_response,
                ims_responses=ims_responses,
                invoice_details=invoice_details,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Error in bind processing: {e}")
            errors.append(str(e))
            return ProcessingResult(
                success=False,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response={},
                ims_responses=ims_responses,
                errors=errors
            )
    
    async def _process_unbind(self, payload: TritonPayload) -> ProcessingResult:
        """Process an Unbind transaction"""
        ims_responses = []
        errors = []
        
        try:
            # Need to get policy GUID from somewhere - might need to store mapping
            # For now, we'll assume we have a way to look it up
            policy_guid = await self._get_policy_guid(payload.policy_number)
            
            if not policy_guid:
                raise ValueError(f"Policy not found: {payload.policy_number}")
            
            unbind_result = self.quote_service.unbind(policy_guid)
            ims_responses.append({
                "action": "unbind_policy",
                "result": unbind_result
            })
            
            service_response = {
                "policy_guid": str(policy_guid),
                "status": "unbound"
            }
            
            return ProcessingResult(
                success=True,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response=service_response,
                ims_responses=ims_responses,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error in unbind processing: {e}")
            errors.append(str(e))
            return ProcessingResult(
                success=False,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response={},
                ims_responses=ims_responses,
                errors=errors
            )
    
    async def _process_issue(self, payload: TritonPayload) -> ProcessingResult:
        """Process an Issue transaction"""
        ims_responses = []
        errors = []
        
        try:
            policy_guid = await self._get_policy_guid(payload.policy_number)
            
            if not policy_guid:
                raise ValueError(f"Policy not found: {payload.policy_number}")
            
            issue_result = self.quote_service.issue(policy_guid)
            ims_responses.append({
                "action": "issue_policy",
                "result": issue_result
            })
            
            service_response = {
                "policy_guid": str(policy_guid),
                "status": "issued",
                "issue_date": issue_result.get("issue_date")
            }
            
            return ProcessingResult(
                success=True,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response=service_response,
                ims_responses=ims_responses,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error in issue processing: {e}")
            errors.append(str(e))
            return ProcessingResult(
                success=False,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response={},
                ims_responses=ims_responses,
                errors=errors
            )
    
    async def _process_midterm_endorsement(self, payload: TritonPayload) -> ProcessingResult:
        """Process a Midterm Endorsement transaction"""
        ims_responses = []
        errors = []
        
        try:
            policy_guid = await self._get_policy_guid(payload.policy_number)
            
            if not policy_guid:
                raise ValueError(f"Policy not found: {payload.policy_number}")
            
            # Create endorsement
            endorsement_data = {
                "effective_date": payload.midterm_endt_effective_from,
                "description": payload.midterm_endt_description,
                "endorsement_number": payload.midterm_endt_endorsement_number
            }
            endorsement_guid = self.quote_service.create_endorsement(policy_guid, endorsement_data)
            ims_responses.append({
                "action": "create_endorsement",
                "result": {"endorsement_guid": str(endorsement_guid)}
            })
            
            # Bind the endorsement
            bind_data = {
                "bound_date": payload.bound_date,
                "policy_number": payload.policy_number
            }
            bind_result = self.quote_service.bind(endorsement_guid, bind_data)
            ims_responses.append({
                "action": "bind_endorsement",
                "result": bind_result
            })
            
            # Get invoice details
            invoice_details = self.invoice_service.get_invoice(endorsement_guid)
            
            service_response = {
                "policy_guid": str(policy_guid),
                "endorsement_guid": str(endorsement_guid),
                "status": "endorsed"
            }
            
            return ProcessingResult(
                success=True,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response=service_response,
                ims_responses=ims_responses,
                invoice_details=invoice_details,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error in endorsement processing: {e}")
            errors.append(str(e))
            return ProcessingResult(
                success=False,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response={},
                ims_responses=ims_responses,
                errors=errors
            )
    
    async def _process_cancellation(self, payload: TritonPayload) -> ProcessingResult:
        """Process a Cancellation transaction"""
        ims_responses = []
        errors = []
        
        try:
            policy_guid = await self._get_policy_guid(payload.policy_number)
            
            if not policy_guid:
                raise ValueError(f"Policy not found: {payload.policy_number}")
            
            cancellation_data = {
                "reason_code": "CANC001",
                "comment": f"Cancellation requested - Transaction ID: {payload.transaction_id}"
            }
            cancel_result = self.quote_service.cancel(policy_guid, cancellation_data)
            ims_responses.append({
                "action": "cancel_policy",
                "result": cancel_result
            })
            
            # Get final invoice details
            invoice_details = self.invoice_service.get_invoice(policy_guid)
            
            service_response = {
                "policy_guid": str(policy_guid),
                "status": "cancelled",
                "cancellation_date": cancel_result.get("cancellation_date")
            }
            
            return ProcessingResult(
                success=True,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response=service_response,
                ims_responses=ims_responses,
                invoice_details=invoice_details,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error in cancellation processing: {e}")
            errors.append(str(e))
            return ProcessingResult(
                success=False,
                transaction_id=payload.transaction_id,
                transaction_type=payload.transaction_type,
                service_response={},
                ims_responses=ims_responses,
                errors=errors
            )
    
    async def _get_policy_guid(self, policy_number: str) -> Optional[UUID]:
        """Get policy GUID from policy number"""
        policy_guid = policy_store.get_policy_guid(policy_number)
        if not policy_guid:
            logger.warning(f"Policy not found in store: {policy_number}")
        return policy_guid