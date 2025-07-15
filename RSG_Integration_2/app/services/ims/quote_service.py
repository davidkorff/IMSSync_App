import logging
from typing import Dict, Any
from uuid import UUID

from .base_service import BaseIMSService
from .auth_service import AuthService

logger = logging.getLogger(__name__)

class QuoteService(BaseIMSService):
    """Service for IMS quote and policy operations"""
    
    def __init__(self, auth_service: AuthService):
        super().__init__("quote_functions")
        self.auth_service = auth_service
    
    def create_submission(self, insured_guid: UUID, data: Dict[str, Any]) -> UUID:
        """Create a submission for an insured"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.AddSubmission(
                insuredGuid=str(insured_guid),
                producerContactGuid=data.get("producer_guid", ""),
                underwriterUserGuid=data.get("underwriter_guid", ""),
                effectiveDate=data["effective_date"],
                expirationDate=data["expiration_date"],
                description=f"{data['program_name']} - {data['class_of_business']}",
                _soapheaders=self.get_header(token)
            )
            
            submission_guid = UUID(str(response))
            logger.info(f"Created submission: {submission_guid}")
            return submission_guid
            
        except Exception as e:
            logger.error(f"Error creating submission: {e}")
            raise
    
    def create_quote(self, submission_guid: UUID, data: Dict[str, Any]) -> UUID:
        """Create a quote under a submission"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.AddQuoteWithSubmission(
                submissionGuid=str(submission_guid),
                companyLocationGuid=data.get("company_location_guid", ""),
                lineOfCoverageGuid=data.get("line_of_coverage_guid", ""),
                issuingStateCode=data["state"],
                _soapheaders=self.get_header(token)
            )
            
            quote_guid = UUID(str(response))
            logger.info(f"Created quote: {quote_guid}")
            return quote_guid
            
        except Exception as e:
            logger.error(f"Error creating quote: {e}")
            raise
    
    def bind(self, quote_guid: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        """Bind a quote to create a policy"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.BindQuote(
                quoteGuid=str(quote_guid),
                bindDate=data["bound_date"],
                policyNumber=data.get("policy_number"),
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Bound quote {quote_guid}")
            return {"success": True, "policy_guid": str(response)}
            
        except Exception as e:
            logger.error(f"Error binding quote: {e}")
            raise
    
    def unbind(self, policy_guid: UUID) -> Dict[str, Any]:
        """Unbind a policy"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.UpdateQuoteStatus(
                quoteGuid=str(policy_guid),
                status="Unbound",
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Unbound policy {policy_guid}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error unbinding policy: {e}")
            raise
    
    def issue(self, policy_guid: UUID) -> Dict[str, Any]:
        """Issue a bound policy"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.IssuePolicy(
                quoteGuid=str(policy_guid),
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Issued policy {policy_guid}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error issuing policy: {e}")
            raise
    
    def create_endorsement(self, policy_guid: UUID, data: Dict[str, Any]) -> UUID:
        """Create a midterm endorsement"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.AddQuoteWithAutocalculateDetailsQuote(
                originalQuoteGuid=str(policy_guid),
                effectiveDate=data["effective_date"],
                description=data.get("description", "Midterm Endorsement"),
                transactionType="Endorsement",
                _soapheaders=self.get_header(token)
            )
            
            endorsement_guid = UUID(str(response))
            logger.info(f"Created endorsement: {endorsement_guid}")
            return endorsement_guid
            
        except Exception as e:
            logger.error(f"Error creating endorsement: {e}")
            raise
    
    def cancel(self, policy_guid: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a policy"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.UpdateQuoteStatusWithReasonAndComment(
                quoteGuid=str(policy_guid),
                status="Cancelled",
                reasonCode=data.get("reason_code", "CANC001"),
                comment=data.get("comment", "Policy cancelled"),
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Cancelled policy {policy_guid}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error cancelling policy: {e}")
            raise
    
    def import_excel_rater(self, quote_guid: UUID, excel_data: bytes) -> Dict[str, Any]:
        """Import Excel rater data"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.ImportExcelRater(
                quoteGuid=str(quote_guid),
                excelData=excel_data,
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Imported Excel rater for quote {quote_guid}")
            return {"success": True, "import_result": response}
            
        except Exception as e:
            logger.error(f"Error importing Excel rater: {e}")
            raise