"""
Quote Microservice Implementation
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal

from app.microservices.core import (
    BaseMicroservice, 
    ServiceConfig, 
    ServiceResponse,
    ServiceError
)
from app.microservices.core.exceptions import ValidationError
from .models import (
    Submission,
    SubmissionCreate,
    Quote,
    QuoteCreate,
    QuoteUpdate,
    QuoteOption,
    Premium,
    PremiumCreate,
    BindRequest,
    BindResponse,
    RatingRequest,
    RatingResponse,
    QuoteStatus
)


class QuoteService(BaseMicroservice):
    """
    Microservice for managing quotes and submissions in IMS
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        if not config:
            config = ServiceConfig(
                name="quote",
                version="1.0.0"
            )
        super().__init__(config)
    
    def _on_initialize(self):
        """Service-specific initialization"""
        self.logger.info("Quote service specific initialization")
    
    def _on_shutdown(self):
        """Service-specific shutdown"""
        self.logger.info("Quote service specific shutdown")
    
    async def create_submission(self, data: SubmissionCreate) -> ServiceResponse:
        """
        Create a new submission
        
        Args:
            data: Submission data
            
        Returns:
            ServiceResponse with Submission
        """
        self._log_operation("create_submission", {"insured_guid": data.insured_guid})
        
        try:
            # Call IMS to create submission
            result = self.soap_client.service.AddSubmission(
                SubmissionDate=data.submission_date.isoformat(),
                InsuredGUID=data.insured_guid,
                ProducerContactGUID=data.producer_contact_guid,
                UnderwriterGUID=data.underwriter_guid,
                ProducerLocationGUID=data.producer_location_guid
            )
            
            if not result:
                raise ServiceError("Failed to create submission - no response from IMS")
            
            submission_guid = str(result)
            
            # Create submission object
            submission = Submission(
                guid=submission_guid,
                insured_guid=data.insured_guid,
                submission_date=data.submission_date,
                producer_contact_guid=data.producer_contact_guid,
                producer_location_guid=data.producer_location_guid,
                underwriter_guid=data.underwriter_guid,
                created_date=datetime.now()
            )
            
            return ServiceResponse(
                success=True,
                data=submission,
                metadata={"action": "created"}
            )
            
        except Exception as e:
            return self._handle_error(e, "create_submission")
    
    async def create_quote(self, data: QuoteCreate) -> ServiceResponse:
        """
        Create a new quote
        
        Args:
            data: Quote data
            
        Returns:
            ServiceResponse with Quote
        """
        self._log_operation("create_quote", {
            "submission_guid": data.submission_guid,
            "effective_date": data.effective_date.isoformat()
        })
        
        try:
            # Call IMS to create quote with autocalculate details
            result = self.soap_client.service.AddQuoteWithAutocalculateDetailsQuote(
                SubmissionGuid=data.submission_guid,
                EffectiveDate=data.effective_date.isoformat(),
                ExpirationDate=data.expiration_date.isoformat(),
                QuoteStatusID=data.status_id,
                State=data.state,
                BillingTypeID=data.billing_type_id,
                LineGUID=data.line_guid,
                ProducerContactGUID=data.producer_contact_guid or data.submission_guid,
                QuotingLocationGUID=data.quoting_location_guid,
                IssuingLocationGUID=data.issuing_location_guid,
                CompanyLocationGUID=data.company_location_guid,
                OfficeGUID="00000000-0000-0000-0000-000000000000"  # Default
            )
            
            if not result:
                raise ServiceError("Failed to create quote - no response from IMS")
            
            quote_guid = str(result)
            
            # Update external ID if provided
            if data.external_quote_id:
                await self.update_external_id(
                    quote_guid, 
                    data.external_quote_id, 
                    data.external_system or "Unknown"
                )
            
            # Create quote object
            quote = Quote(
                guid=quote_guid,
                submission_guid=data.submission_guid,
                effective_date=data.effective_date,
                expiration_date=data.expiration_date,
                state=data.state,
                line_guid=data.line_guid,
                status_id=data.status_id,
                created_date=datetime.now()
            )
            
            return ServiceResponse(
                success=True,
                data=quote,
                metadata={"action": "created"}
            )
            
        except Exception as e:
            return self._handle_error(e, "create_quote")
    
    async def add_quote_option(self, quote_guid: str) -> ServiceResponse:
        """
        Add a quote option
        
        Args:
            quote_guid: Quote GUID
            
        Returns:
            ServiceResponse with option ID
        """
        self._log_operation("add_quote_option", {"quote_guid": quote_guid})
        
        try:
            # Call IMS to add quote option
            result = self.soap_client.service.AutoAddQuoteOptions(
                QuoteGuid=quote_guid
            )
            
            if not result:
                raise ServiceError("Failed to add quote option")
            
            # Extract option ID from result
            option_id = str(result)
            
            return ServiceResponse(
                success=True,
                data={"quote_option_id": option_id},
                metadata={"quote_guid": quote_guid}
            )
            
        except Exception as e:
            return self._handle_error(e, "add_quote_option")
    
    async def add_premium(self, data: PremiumCreate) -> ServiceResponse:
        """
        Add premium to a quote option
        
        Args:
            data: Premium data
            
        Returns:
            ServiceResponse with success status
        """
        self._log_operation("add_premium", {
            "quote_guid": data.quote_guid,
            "amount": str(data.amount)
        })
        
        try:
            # Determine if this is a historic charge (fee) or regular premium
            if data.is_fee:
                # Add as historic charge (fee)
                result = self.soap_client.service.AddPremiumHistoricCharge(
                    QuoteGuid=data.quote_guid,
                    QuoteOptionID=data.quote_option_id,
                    ChargeAmount=str(data.amount),
                    ChargeDescription=data.description,
                    IsTaxable=data.is_taxable
                )
            else:
                # Add as regular premium
                result = self.soap_client.service.AddPremium(
                    QuoteGuid=data.quote_guid,
                    QuoteOptionID=data.quote_option_id,
                    Premium=str(data.amount),
                    PremiumDescription=data.description
                )
            
            if result:
                return ServiceResponse(
                    success=True,
                    data={"premium_added": True},
                    metadata={
                        "quote_guid": data.quote_guid,
                        "amount": str(data.amount),
                        "is_fee": data.is_fee
                    }
                )
            else:
                return ServiceResponse(
                    success=False,
                    error="Failed to add premium"
                )
                
        except Exception as e:
            return self._handle_error(e, "add_premium")
    
    async def rate_quote(self, request: RatingRequest) -> ServiceResponse:
        """
        Rate a quote using various methods
        
        Args:
            request: Rating request
            
        Returns:
            ServiceResponse with RatingResponse
        """
        self._log_operation("rate_quote", {
            "quote_guid": request.quote_guid,
            "method": request.rating_method
        })
        
        try:
            if request.rating_method == "manual":
                return await self._rate_manual(request)
            elif request.rating_method == "excel":
                return await self._rate_excel(request)
            elif request.rating_method == "api":
                return await self._rate_api(request)
            else:
                return ServiceResponse(
                    success=False,
                    error=f"Unknown rating method: {request.rating_method}"
                )
                
        except Exception as e:
            return self._handle_error(e, "rate_quote")
    
    async def _rate_manual(self, request: RatingRequest) -> ServiceResponse:
        """Manual rating - direct premium pass-through"""
        try:
            if not request.manual_premium:
                raise ValidationError("Manual premium is required for manual rating")
            
            # Create quote option
            option_response = await self.add_quote_option(request.quote_guid)
            if not option_response.success:
                return option_response
            
            option_id = option_response.data["quote_option_id"]
            
            # Add premium
            premium_data = PremiumCreate(
                quote_guid=request.quote_guid,
                quote_option_id=option_id,
                amount=request.manual_premium,
                description="Premium from source system"
            )
            
            premium_response = await self.add_premium(premium_data)
            if not premium_response.success:
                return premium_response
            
            # Create response
            response = RatingResponse(
                success=True,
                quote_option_id=option_id,
                total_premium=request.manual_premium,
                premium_breakdown=[{
                    "description": "Base Premium",
                    "amount": str(request.manual_premium)
                }]
            )
            
            return ServiceResponse(
                success=True,
                data=response
            )
            
        except Exception as e:
            return self._handle_error(e, "_rate_manual")
    
    async def _rate_excel(self, request: RatingRequest) -> ServiceResponse:
        """Excel-based rating"""
        try:
            if not all([request.excel_template_path, request.rater_id, request.factor_set_guid]):
                raise ValidationError("Excel template, rater ID, and factor set GUID required")
            
            # Import Excel rater
            result = self.soap_client.service.ImportExcelRater(
                QuoteGuid=request.quote_guid,
                ExcelFilePath=request.excel_template_path,
                RaterID=request.rater_id,
                FactorSetGuid=request.factor_set_guid
            )
            
            if not result:
                raise ServiceError("Excel rating failed")
            
            # Parse result to extract premium info
            response = RatingResponse(
                success=True,
                quote_option_id=result.get("QuoteOptionID"),
                total_premium=Decimal(str(result.get("TotalPremium", 0))),
                rating_sheet_id=result.get("RatingSheetID")
            )
            
            return ServiceResponse(
                success=True,
                data=response
            )
            
        except Exception as e:
            return self._handle_error(e, "_rate_excel")
    
    async def _rate_api(self, request: RatingRequest) -> ServiceResponse:
        """API-based rating (placeholder)"""
        return ServiceResponse(
            success=False,
            error="API rating not yet implemented"
        )
    
    async def bind_quote(self, request: BindRequest) -> ServiceResponse:
        """
        Bind a quote to create a policy
        
        Args:
            request: Bind request
            
        Returns:
            ServiceResponse with BindResponse
        """
        self._log_operation("bind_quote", {"quote_option_id": request.quote_option_id})
        
        try:
            # Bind the quote
            if request.payment_plan_id:
                # Bind with installment plan
                result = self.soap_client.service.BindQuoteWithInstallment(
                    QuoteOptionID=request.quote_option_id,
                    InstallmentPlanID=request.payment_plan_id
                )
            else:
                # Regular bind
                result = self.soap_client.service.BindQuote(
                    QuoteOptionID=request.quote_option_id
                )
            
            if not result:
                raise ServiceError("Failed to bind quote")
            
            policy_number = str(result)
            
            # Create response
            response = BindResponse(
                success=True,
                policy_number=policy_number,
                bound_date=request.bind_date or date.today()
            )
            
            return ServiceResponse(
                success=True,
                data=response,
                metadata={"action": "bound"}
            )
            
        except Exception as e:
            return self._handle_error(e, "bind_quote")
    
    async def issue_policy(self, policy_number: str) -> ServiceResponse:
        """
        Issue a bound policy
        
        Args:
            policy_number: Policy number
            
        Returns:
            ServiceResponse indicating success
        """
        self._log_operation("issue_policy", {"policy_number": policy_number})
        
        try:
            # Issue the policy
            result = self.soap_client.service.IssuePolicy(
                PolicyNumber=policy_number
            )
            
            if result:
                return ServiceResponse(
                    success=True,
                    data={"issued": True},
                    metadata={"policy_number": policy_number}
                )
            else:
                return ServiceResponse(
                    success=False,
                    error=f"Failed to issue policy: {policy_number}"
                )
                
        except Exception as e:
            return self._handle_error(e, "issue_policy")
    
    async def update_external_id(
        self, 
        quote_guid: str, 
        external_id: str, 
        external_system: str
    ) -> ServiceResponse:
        """
        Update external quote ID for integration tracking
        
        Args:
            quote_guid: Quote GUID
            external_id: External system ID
            external_system: External system name
            
        Returns:
            ServiceResponse indicating success
        """
        self._log_operation("update_external_id", {
            "quote_guid": quote_guid,
            "external_id": external_id,
            "external_system": external_system
        })
        
        try:
            # Update external quote ID
            result = self.soap_client.service.UpdateExternalQuoteId(
                QuoteGuid=quote_guid,
                ExternalQuoteId=external_id,
                SystemId=external_system
            )
            
            return ServiceResponse(
                success=True,
                data={"updated": True},
                metadata={
                    "quote_guid": quote_guid,
                    "external_id": external_id
                }
            )
            
        except Exception as e:
            # Log but don't fail - this is supplementary
            self.logger.warning(f"Failed to update external ID: {str(e)}")
            return ServiceResponse(
                success=True,
                data={"updated": False},
                warnings=[f"Could not update external ID: {str(e)}"]
            )
    
    async def get_quote_by_guid(self, quote_guid: str) -> ServiceResponse:
        """
        Get quote details by GUID
        
        Args:
            quote_guid: Quote GUID
            
        Returns:
            ServiceResponse with Quote
        """
        self._log_operation("get_quote_by_guid", {"quote_guid": quote_guid})
        
        try:
            # Get quote information
            result = self.soap_client.service.GetQuoteInformation(
                QuoteGuid=quote_guid
            )
            
            if not result:
                return ServiceResponse(
                    success=False,
                    error=f"Quote not found: {quote_guid}"
                )
            
            # Map to model
            quote = self._map_ims_to_quote(result)
            
            return ServiceResponse(
                success=True,
                data=quote
            )
            
        except Exception as e:
            return self._handle_error(e, "get_quote_by_guid")
    
    async def update_quote_status(
        self, 
        quote_guid: str, 
        status_id: int, 
        reason: Optional[str] = None,
        comment: Optional[str] = None
    ) -> ServiceResponse:
        """
        Update quote status
        
        Args:
            quote_guid: Quote GUID
            status_id: New status ID
            reason: Optional reason
            comment: Optional comment
            
        Returns:
            ServiceResponse indicating success
        """
        self._log_operation("update_quote_status", {
            "quote_guid": quote_guid,
            "status_id": status_id
        })
        
        try:
            if reason and comment:
                result = self.soap_client.service.UpdateQuoteStatusWithReasonAndComment(
                    QuoteGuid=quote_guid,
                    QuoteStatusID=status_id,
                    Reason=reason,
                    Comment=comment
                )
            elif reason:
                result = self.soap_client.service.UpdateQuoteStatusWithReason(
                    QuoteGuid=quote_guid,
                    QuoteStatusID=status_id,
                    Reason=reason
                )
            elif comment:
                result = self.soap_client.service.UpdateQuoteStatusWithComment(
                    QuoteGuid=quote_guid,
                    QuoteStatusID=status_id,
                    Comment=comment
                )
            else:
                result = self.soap_client.service.UpdateQuoteStatus(
                    QuoteGuid=quote_guid,
                    QuoteStatusID=status_id
                )
            
            return ServiceResponse(
                success=True,
                data={"status_updated": True},
                metadata={
                    "quote_guid": quote_guid,
                    "new_status": status_id
                }
            )
            
        except Exception as e:
            return self._handle_error(e, "update_quote_status")
    
    def _map_ims_to_quote(self, ims_quote: Any) -> Quote:
        """Map IMS quote object to our model"""
        return Quote(
            guid=str(ims_quote.QuoteGUID),
            quote_id=getattr(ims_quote, 'QuoteID', None),
            quote_number=getattr(ims_quote, 'QuoteNumber', None),
            submission_guid=str(ims_quote.SubmissionGUID),
            effective_date=ims_quote.EffectiveDate,
            expiration_date=ims_quote.ExpirationDate,
            state=ims_quote.State,
            line_guid=str(ims_quote.LineGUID),
            status_id=ims_quote.QuoteStatusID,
            premium=getattr(ims_quote, 'Premium', None),
            policy_number=getattr(ims_quote, 'PolicyNumber', None),
            created_date=getattr(ims_quote, 'CreatedDate', datetime.now())
        )