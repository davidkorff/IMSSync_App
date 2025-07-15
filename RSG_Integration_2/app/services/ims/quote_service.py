import logging
from typing import Dict, Any
from uuid import UUID
from datetime import datetime

from .base_service import BaseIMSService
from .auth_service import AuthService

logger = logging.getLogger(__name__)

class QuoteService(BaseIMSService):
    """Service for IMS quote and policy operations"""
    
    def __init__(self, auth_service: AuthService):
        super().__init__("quote_functions")
        self.auth_service = auth_service
    
    def create_submission_and_quote(self, insured_guid: UUID, data: Dict[str, Any]) -> Dict[str, UUID]:
        """Create a submission and quote together"""
        try:
            token = self.auth_service.get_token()
            
            # Create submission object
            submission = {
                'Insured': str(insured_guid),
                'ProducerContact': data.get("producer_guid", "00000000-0000-0000-0000-000000000000"),
                'Underwriter': data.get("underwriter_guid", "00000000-0000-0000-0000-000000000000"),
                'SubmissionDate': data.get("submission_date", datetime.now().strftime("%Y-%m-%d")),
                'ProducerLocation': data.get("producer_location_guid", "00000000-0000-0000-0000-000000000000"),
                'TACSR': data.get("tacsr_guid", "00000000-0000-0000-0000-000000000000"),
                'InHouseProducer': data.get("inhouse_producer_guid", "00000000-0000-0000-0000-000000000000")
            }
            
            # Create quote object with risk information
            quote = {
                'Submission': "00000000-0000-0000-0000-000000000000",  # Will be set by server
                'QuotingLocation': data.get("quoting_location_guid", "00000000-0000-0000-0000-000000000000"),
                'IssuingLocation': data.get("issuing_location_guid", "00000000-0000-0000-0000-000000000000"),
                'CompanyLocation': data.get("company_location_guid", "00000000-0000-0000-0000-000000000000"),
                'Line': data.get("line_guid", "00000000-0000-0000-0000-000000000000"),
                'StateID': data["state"],
                'ProducerContact': data.get("producer_guid", "00000000-0000-0000-0000-000000000000"),
                'QuoteStatusID': 1,  # Active/New
                'Effective': data["effective_date"],
                'Expiration': data["expiration_date"],
                'BillingTypeID': 1,  # Default billing type
                'FinanceCompany': "00000000-0000-0000-0000-000000000000",
                'NetRateQuoteID': 0,
                'QuoteDetail': {
                    'CompanyCommission': data.get("company_commission", 0),
                    'ProducerCommission': data.get("producer_commission", data.get("commission_rate", 0)),
                    'TermsOfPayment': 1,  # Default terms
                    'ProgramCode': data.get("program_code", ""),
                    'CompanyContactGuid': "00000000-0000-0000-0000-000000000000",
                    'RaterID': data.get("rater_id", 1),
                    'FactorSetGuid': "00000000-0000-0000-0000-000000000000",
                    'ProgramID': data.get("program_id", 0),
                    'LineGUID': data.get("line_guid", "00000000-0000-0000-0000-000000000000"),
                    'CompanyLocationGUID': data.get("company_location_guid", "00000000-0000-0000-0000-000000000000")
                },
                'ExpiringQuoteGuid': "00000000-0000-0000-0000-000000000000",
                'Underwriter': data.get("underwriter_guid", "00000000-0000-0000-0000-000000000000"),
                'ExpiringPolicyNumber': "",
                'ExpiringCompanyLocationGuid': "00000000-0000-0000-0000-000000000000",
                'PolicyTypeID': 1,  # Default policy type
                'RenewalOfQuoteGuid': "00000000-0000-0000-0000-000000000000",
                'InsuredBusinessTypeID': 9,  # LLC - Partnership
                'AccountNumber': "",
                'AdditionalInformation': [],
                'OnlineRaterID': 0,
                'CostCenterID': 0,
                'ProgramCode': data.get("program_code", ""),
                'RiskInformation': {
                    'PolicyName': data["insured_name"],
                    'CorporationName': data["insured_name"],
                    'DBA': "",
                    'Salutation': "",
                    'FirstName': "",
                    'MiddleName': "",
                    'LastName': "",
                    'SSN': "",
                    'FEIN': "",
                    'Address1': data["address_1"],
                    'Address2': data.get("address_2", ""),
                    'City': data["city"],
                    'State': data["state"],
                    'ISOCountryCode': "US",
                    'Region': "",
                    'ZipCode': data["zip"],
                    'ZipPlus': "",
                    'Phone': "",
                    'Fax': "",
                    'Mobile': "",
                    'BusinessType': 9  # LLC - Partnership
                },
                'ProgramID': data.get("program_id", 0)
            }
            
            # Try AddQuoteWithSubmission first, fall back to separate calls if not available
            try:
                response = self.client.service.AddQuoteWithSubmission(
                    submission=submission,
                    quote=quote,
                    _soapheaders=self.get_header(token)
                )
            except Exception as e:
                if "has no operation" in str(e):
                    logger.warning("AddQuoteWithSubmission not available, using separate calls")
                    # Fall back to creating submission and quote separately
                    return self._create_submission_and_quote_separately(insured_guid, data)
                else:
                    raise
            
            quote_guid = UUID(str(response))
            logger.info(f"Created submission and quote: {quote_guid}")
            
            # Return both submission and quote GUIDs (quote GUID is returned, submission is implicit)
            return {
                "quote_guid": quote_guid,
                "submission_guid": None  # Not returned by this method, but quote is linked to submission
            }
            
        except Exception as e:
            logger.error(f"Error creating submission and quote: {e}")
            raise
    
    def _create_submission_and_quote_separately(self, insured_guid: UUID, data: Dict[str, Any]) -> Dict[str, UUID]:
        """Create submission and quote using separate API calls (fallback method)"""
        try:
            token = self.auth_service.get_token()
            
            # Step 1: Create submission
            submission = {
                'Insured': str(insured_guid),
                'ProducerContact': data.get("producer_guid", "00000000-0000-0000-0000-000000000000"),
                'Underwriter': data.get("underwriter_guid", "00000000-0000-0000-0000-000000000000"),
                'SubmissionDate': data.get("submission_date", datetime.now().strftime("%Y-%m-%d")),
                'ProducerLocation': data.get("producer_location_guid", "00000000-0000-0000-0000-000000000000"),
                'TACSR': data.get("tacsr_guid", "00000000-0000-0000-0000-000000000000"),
                'InHouseProducer': data.get("inhouse_producer_guid", "00000000-0000-0000-0000-000000000000")
            }
            
            submission_response = self.client.service.AddSubmission(
                submission=submission,
                _soapheaders=self.get_header(token)
            )
            submission_guid = UUID(str(submission_response))
            logger.info(f"Created submission: {submission_guid}")
            
            # Step 2: Create quote with the submission
            quote_response = self.client.service.AddQuote(
                submissionGuid=str(submission_guid),
                companyLocationGuid=data.get("company_location_guid", "00000000-0000-0000-0000-000000000000"),
                lineOfCoverageGuid=data.get("line_guid", "00000000-0000-0000-0000-000000000000"),
                issuingStateCode=data["state"],
                _soapheaders=self.get_header(token)
            )
            quote_guid = UUID(str(quote_response))
            logger.info(f"Created quote: {quote_guid}")
            
            return {
                "quote_guid": quote_guid,
                "submission_guid": submission_guid
            }
            
        except Exception as e:
            logger.error(f"Error in fallback submission/quote creation: {e}")
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