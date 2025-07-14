"""
Triton Processor using complete microservice architecture
This demonstrates how all microservices work together in a real workflow
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal

from app.microservices import get_service
from app.microservices.insured import InsuredCreate
from app.microservices.quote import (
    SubmissionCreate, QuoteCreate, PremiumCreate, 
    BindRequest, RatingRequest
)
from app.microservices.policy import (
    CancellationRequest, EndorsementRequest, 
    ReinstatementRequest
)
from app.microservices.data_access import ProgramData, LookupType
from app.microservices.document import GenerateDocumentRequest, DocumentType

logger = logging.getLogger(__name__)


class TritonProcessorMicroservices:
    """
    Complete Triton processor using all microservices
    """
    
    def __init__(self, environment: Optional[str] = None):
        """Initialize with all microservices from registry"""
        # Get all services - they're created on demand
        self.insured_service = get_service('insured')
        self.producer_service = get_service('producer')
        self.quote_service = get_service('quote')
        self.policy_service = get_service('policy')
        self.invoice_service = get_service('invoice')
        self.document_service = get_service('document')
        self.data_access_service = get_service('data_access')
        
        # Load configuration
        self._load_config()
        
        logger.info("TritonProcessorMicroservices initialized with all services")
    
    def _load_config(self):
        """Load Triton-specific configuration"""
        import os
        self.config = {
            "default_producer_guid": os.getenv("TRITON_DEFAULT_PRODUCER_GUID", ""),
            "primary_line_guid": os.getenv("TRITON_PRIMARY_LINE_GUID", ""),
            "excess_line_guid": os.getenv("TRITON_EXCESS_LINE_GUID", ""),
            "default_underwriter_guid": os.getenv("TRITON_DEFAULT_UNDERWRITER_GUID", ""),
            "issuing_location_guid": os.getenv("TRITON_ISSUING_LOCATION_GUID", ""),
            "company_location_guid": os.getenv("TRITON_COMPANY_LOCATION_GUID", ""),
            "quoting_location_guid": os.getenv("TRITON_QUOTING_LOCATION_GUID", ""),
            "default_business_type_id": int(os.getenv("TRITON_DEFAULT_BUSINESS_TYPE_ID", "5"))
        }
    
    async def process_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Triton transaction based on type
        """
        transaction_type = data.get("transaction_type", "").upper()
        logger.info(f"Processing {transaction_type} transaction: {data.get('transaction_id')}")
        
        try:
            if transaction_type == "NEW BUSINESS":
                return await self.process_new_business(data)
            elif transaction_type == "CANCEL":
                return await self.process_cancellation(data)
            elif transaction_type == "MIDTERM_ENDORSEMENT":
                return await self.process_endorsement(data)
            elif transaction_type == "REINSTATEMENT":
                return await self.process_reinstatement(data)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported transaction type: {transaction_type}"
                }
        except Exception as e:
            logger.error(f"Error processing transaction: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_new_business(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process NEW BUSINESS transaction using all microservices
        """
        result = {
            "success": False,
            "ims_response": {},
            "invoice_details": {},
            "documents": [],
            "errors": [],
            "warnings": []
        }
        
        try:
            # Step 1: Find or create insured
            logger.info("Step 1: Processing insured")
            
            insured_data = InsuredCreate(
                name=data.get("insured_name"),
                tax_id=data.get("tax_id"),
                business_type_id=self.config["default_business_type_id"],
                address=data.get("address_1"),
                city=data.get("city"),
                state=data.get("state", data.get("insured_state")),
                zip_code=data.get("zip", data.get("insured_zip")),
                source="triton",
                external_id=data.get("transaction_id")
            )
            
            insured_response = await self.insured_service.find_or_create(insured_data)
            if not insured_response.success:
                result["errors"].append(f"Failed to process insured: {insured_response.error}")
                return result
            
            insured = insured_response.data
            result["ims_response"]["insured_guid"] = insured.guid
            logger.info(f"Insured processed: {insured.guid}")
            
            # Step 2: Get producer information
            logger.info("Step 2: Getting producer information")
            
            producer_guid = self.config["default_producer_guid"]
            producer_name = data.get("producer_name")
            
            if producer_name:
                producer_response = await self.producer_service.get_by_name(producer_name)
                if producer_response.success:
                    producer_guid = producer_response.data.producer_guid
                    logger.info(f"Found producer: {producer_guid}")
                else:
                    logger.warning(f"Producer not found: {producer_name}, using default")
            
            # Get underwriter
            underwriter_guid = self.config["default_underwriter_guid"]
            underwriter_name = data.get("underwriter_name")
            
            if underwriter_name:
                underwriter_response = await self.producer_service.find_underwriter_by_name(underwriter_name)
                if underwriter_response.success:
                    underwriter_guid = underwriter_response.data["underwriter_guid"]
                    logger.info(f"Found underwriter: {underwriter_guid}")
            
            # Step 3: Create submission
            logger.info("Step 3: Creating submission")
            
            submission_date = self._parse_date(data.get("bound_date")) or date.today()
            
            submission_data = SubmissionCreate(
                insured_guid=insured.guid,
                submission_date=submission_date,
                producer_contact_guid=producer_guid,
                producer_location_guid=producer_guid,
                underwriter_guid=underwriter_guid,
                source="triton",
                external_id=data.get("transaction_id")
            )
            
            submission_response = await self.quote_service.create_submission(submission_data)
            if not submission_response.success:
                result["errors"].append(f"Failed to create submission: {submission_response.error}")
                return result
            
            submission = submission_response.data
            result["ims_response"]["submission_guid"] = submission.guid
            logger.info(f"Submission created: {submission.guid}")
            
            # Step 4: Create quote
            logger.info("Step 4: Creating quote")
            
            effective_date = self._parse_date(data.get("effective_date")) or date.today()
            expiration_date = self._parse_date(data.get("expiration_date")) or date(effective_date.year + 1, effective_date.month, effective_date.day)
            
            quote_data = QuoteCreate(
                submission_guid=submission.guid,
                effective_date=effective_date,
                expiration_date=expiration_date,
                state=data.get("state", data.get("insured_state", "TX")),
                line_guid=self._determine_line_guid(data),
                quoting_location_guid=self.config["quoting_location_guid"],
                issuing_location_guid=self.config["issuing_location_guid"],
                company_location_guid=self.config["company_location_guid"],
                producer_contact_guid=producer_guid,
                external_quote_id=data.get("transaction_id"),
                external_system="triton"
            )
            
            quote_response = await self.quote_service.create_quote(quote_data)
            if not quote_response.success:
                result["errors"].append(f"Failed to create quote: {quote_response.error}")
                return result
            
            quote = quote_response.data
            result["ims_response"]["quote_guid"] = quote.guid
            logger.info(f"Quote created: {quote.guid}")
            
            # Step 5: Rate the quote (add premium)
            logger.info("Step 5: Rating quote")
            
            premium = self._extract_premium(data)
            rating_request = RatingRequest(
                quote_guid=quote.guid,
                rating_method="manual",
                manual_premium=premium
            )
            
            rating_response = await self.quote_service.rate_quote(rating_request)
            if not rating_response.success:
                result["errors"].append(f"Failed to rate quote: {rating_response.error}")
                return result
            
            rating = rating_response.data
            result["ims_response"]["quote_option_id"] = rating.quote_option_id
            result["ims_response"]["premium"] = str(rating.total_premium)
            logger.info(f"Quote rated: ${rating.total_premium}")
            
            # Add fees if present
            if data.get("policy_fee"):
                fee_data = PremiumCreate(
                    quote_guid=quote.guid,
                    quote_option_id=rating.quote_option_id,
                    amount=Decimal(str(data["policy_fee"])),
                    description="Policy Fee",
                    is_fee=True
                )
                await self.quote_service.add_premium(fee_data)
                logger.info(f"Added policy fee: ${data['policy_fee']}")
            
            # Step 6: Bind the policy
            logger.info("Step 6: Binding policy")
            
            bind_request = BindRequest(
                quote_option_id=rating.quote_option_id,
                policy_number_override=data.get("policy_number"),
                bind_date=self._parse_date(data.get("bound_date"))
            )
            
            bind_response = await self.quote_service.bind_quote(bind_request)
            if not bind_response.success:
                result["errors"].append(f"Failed to bind policy: {bind_response.error}")
                return result
            
            bind_result = bind_response.data
            result["ims_response"]["policy_number"] = bind_result.policy_number
            logger.info(f"Policy bound: {bind_result.policy_number}")
            
            # Step 7: Issue the policy
            logger.info("Step 7: Issuing policy")
            
            issue_response = await self.quote_service.issue_policy(bind_result.policy_number)
            if not issue_response.success:
                result["warnings"].append(f"Failed to issue policy: {issue_response.error}")
            else:
                logger.info("Policy issued successfully")
            
            # Step 8: Retrieve invoice
            logger.info("Step 8: Retrieving invoice")
            
            invoice_response = await self.invoice_service.get_latest_by_policy(bind_result.policy_number)
            if invoice_response.success and invoice_response.data:
                invoice = invoice_response.data
                result["invoice_details"] = {
                    "invoice_number": invoice.invoice_number,
                    "invoice_date": invoice.invoice_date.isoformat(),
                    "due_date": invoice.due_date.isoformat(),
                    "total_amount": str(invoice.total_amount),
                    "status": invoice.status.value
                }
                logger.info(f"Invoice retrieved: {invoice.invoice_number}")
            else:
                result["warnings"].append("Invoice not immediately available")
            
            # Step 9: Generate documents
            logger.info("Step 9: Generating documents")
            
            # Generate binder
            doc_request = GenerateDocumentRequest(
                document_type=DocumentType.BINDER,
                policy_number=bind_result.policy_number,
                format="PDF"
            )
            
            doc_response = await self.document_service.generate_document(doc_request)
            if doc_response.success:
                result["documents"].append({
                    "type": "binder",
                    "path": doc_response.data.document_path
                })
                logger.info("Binder document generated")
            
            # Step 10: Store Triton-specific data
            logger.info("Step 10: Storing Triton data")
            
            program_data = ProgramData(
                program="triton",
                quote_guid=quote.guid,
                external_id=data.get("transaction_id"),
                data=data
            )
            
            store_response = await self.data_access_service.store_program_data(program_data)
            if store_response.success:
                logger.info("Triton data stored successfully")
            else:
                result["warnings"].append("Failed to store Triton data")
            
            # Get lookup data example
            business_types = await self.data_access_service.get_lookup_data(LookupType.BUSINESS_TYPES)
            if business_types.success:
                logger.info(f"Loaded {business_types.data.count} business types from cache")
            
            result["success"] = True
            logger.info(f"NEW BUSINESS processing completed successfully. Policy: {bind_result.policy_number}")
            
        except Exception as e:
            logger.error(f"Error in NEW BUSINESS processing: {str(e)}")
            result["errors"].append(str(e))
        
        return result
    
    async def process_cancellation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process policy cancellation using microservices
        """
        result = {
            "success": False,
            "ims_response": {},
            "errors": []
        }
        
        try:
            policy_number = data.get("policy_number")
            if not policy_number:
                result["errors"].append("Policy number is required for cancellation")
                return result
            
            # Get control number
            control_response = await self.policy_service.get_control_number(policy_number)
            if not control_response.success:
                result["errors"].append(f"Failed to get control number: {control_response.error}")
                return result
            
            control_number = control_response.data["control_number"]
            
            # Create cancellation request
            cancel_request = CancellationRequest(
                control_number=control_number,
                cancellation_date=self._parse_date(data.get("cancellation_date")) or date.today(),
                cancellation_reason_id=data.get("cancellation_reason_id", 1),
                comments=data.get("comments", "Cancelled via Triton"),
                flat_cancel=data.get("flat_cancel", False)
            )
            
            # Process cancellation
            cancel_response = await self.policy_service.cancel_policy(cancel_request)
            if not cancel_response.success:
                result["errors"].append(f"Failed to cancel policy: {cancel_response.error}")
                return result
            
            cancel_result = cancel_response.data
            result["ims_response"] = {
                "policy_number": cancel_result.policy_number,
                "cancellation_date": cancel_result.cancellation_date.isoformat(),
                "return_premium": str(cancel_result.return_premium_amount) if cancel_result.return_premium_amount else "0",
                "ims_reference": cancel_result.ims_reference
            }
            
            result["success"] = True
            logger.info(f"Policy cancelled successfully: {policy_number}")
            
        except Exception as e:
            logger.error(f"Error in cancellation processing: {str(e)}")
            result["errors"].append(str(e))
        
        return result
    
    async def process_endorsement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process policy endorsement using microservices
        """
        result = {
            "success": False,
            "ims_response": {},
            "errors": []
        }
        
        try:
            policy_number = data.get("policy_number")
            if not policy_number:
                result["errors"].append("Policy number is required for endorsement")
                return result
            
            # Get control number
            control_response = await self.policy_service.get_control_number(policy_number)
            if not control_response.success:
                result["errors"].append(f"Failed to get control number: {control_response.error}")
                return result
            
            control_number = control_response.data["control_number"]
            
            # Create endorsement request
            endorse_request = EndorsementRequest(
                control_number=control_number,
                endorsement_effective_date=self._parse_date(data.get("endorsement_date")) or date.today(),
                endorsement_reason_id=data.get("endorsement_reason_id", 1),
                endorsement_comment=data.get("comment", "Endorsement via Triton"),
                premium_change=Decimal(str(data.get("premium_change", 0))) if data.get("premium_change") else None
            )
            
            # Process endorsement
            endorse_response = await self.policy_service.create_endorsement(endorse_request)
            if not endorse_response.success:
                result["errors"].append(f"Failed to create endorsement: {endorse_response.error}")
                return result
            
            endorse_result = endorse_response.data
            result["ims_response"] = {
                "policy_number": endorse_result.policy_number,
                "endorsement_number": endorse_result.endorsement_number,
                "endorsement_quote_guid": endorse_result.endorsement_quote_guid,
                "effective_date": endorse_result.endorsement_effective_date.isoformat(),
                "premium_change": str(endorse_result.premium_change) if endorse_result.premium_change else "0",
                "ims_reference": endorse_result.ims_reference
            }
            
            result["success"] = True
            logger.info(f"Endorsement created successfully: {endorse_result.endorsement_number}")
            
        except Exception as e:
            logger.error(f"Error in endorsement processing: {str(e)}")
            result["errors"].append(str(e))
        
        return result
    
    async def process_reinstatement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process policy reinstatement using microservices
        """
        result = {
            "success": False,
            "ims_response": {},
            "errors": []
        }
        
        try:
            policy_number = data.get("policy_number")
            if not policy_number:
                result["errors"].append("Policy number is required for reinstatement")
                return result
            
            # Get control number
            control_response = await self.policy_service.get_control_number(policy_number)
            if not control_response.success:
                result["errors"].append(f"Failed to get control number: {control_response.error}")
                return result
            
            control_number = control_response.data["control_number"]
            
            # Create reinstatement request
            reinstate_request = ReinstatementRequest(
                control_number=control_number,
                reinstatement_date=self._parse_date(data.get("reinstatement_date")) or date.today(),
                reinstatement_reason_id=data.get("reinstatement_reason_id", 1),
                comments=data.get("comments", "Reinstated via Triton"),
                payment_received=Decimal(str(data.get("payment_received"))) if data.get("payment_received") else None,
                check_number=data.get("check_number")
            )
            
            # Process reinstatement
            reinstate_response = await self.policy_service.reinstate_policy(reinstate_request)
            if not reinstate_response.success:
                result["errors"].append(f"Failed to reinstate policy: {reinstate_response.error}")
                return result
            
            reinstate_result = reinstate_response.data
            result["ims_response"] = {
                "policy_number": reinstate_result.policy_number,
                "reinstatement_date": reinstate_result.reinstatement_date.isoformat(),
                "reinstatement_amount": str(reinstate_result.reinstatement_amount) if reinstate_result.reinstatement_amount else "0",
                "invoice_number": reinstate_result.invoice_number,
                "ims_reference": reinstate_result.ims_reference
            }
            
            result["success"] = True
            logger.info(f"Policy reinstated successfully: {policy_number}")
            
        except Exception as e:
            logger.error(f"Error in reinstatement processing: {str(e)}")
            result["errors"].append(str(e))
        
        return result
    
    def _determine_line_guid(self, data: Dict[str, Any]) -> str:
        """Determine line GUID based on coverage type"""
        coverage_type = data.get("coverage_type", "").lower()
        limit_amount = data.get("limit_amount", "").lower()
        
        if "excess" in coverage_type or "excess" in limit_amount:
            return self.config["excess_line_guid"]
        
        return self.config["primary_line_guid"]
    
    def _extract_premium(self, data: Dict[str, Any]) -> Decimal:
        """Extract premium amount from data"""
        premium_fields = ["gross_premium", "net_premium", "total_premium", "base_premium", "premium"]
        
        for field in premium_fields:
            if data.get(field):
                try:
                    return Decimal(str(data[field]))
                except:
                    continue
        
        return Decimal("0")
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date from various formats"""
        if not date_str:
            return None
        
        formats = ["%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all microservices
        """
        health_status = {
            "overall": "healthy",
            "services": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check each service
        services = [
            ('insured', self.insured_service),
            ('producer', self.producer_service),
            ('quote', self.quote_service),
            ('policy', self.policy_service),
            ('invoice', self.invoice_service),
            ('document', self.document_service),
            ('data_access', self.data_access_service)
        ]
        
        unhealthy_count = 0
        
        for name, service in services:
            try:
                health = await service.health_check()
                health_status["services"][name] = {
                    "status": health.status.value,
                    "version": health.version,
                    "uptime": health.uptime_seconds,
                    "dependencies": health.dependencies
                }
                
                if health.status.value != "healthy":
                    unhealthy_count += 1
                    
            except Exception as e:
                health_status["services"][name] = {
                    "status": "error",
                    "error": str(e)
                }
                unhealthy_count += 1
        
        # Determine overall health
        if unhealthy_count == 0:
            health_status["overall"] = "healthy"
        elif unhealthy_count < len(services):
            health_status["overall"] = "degraded"
        else:
            health_status["overall"] = "unhealthy"
        
        return health_status