import logging
import os
from typing import Dict, Any, List
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
    
    def create_quote_with_insured(self, data: Dict[str, Any]) -> Dict[str, UUID]:
        """Create insured, location, submission and quote in one call"""
        try:
            token = self.auth_service.get_token()
            
            # Create insured object
            ins = {
                'BusinessTypeID': 9,  # LLC - Partnership (hardcoded per IMS requirement)
                'Salutation': '',
                'FirstName': '',
                'MiddleName': '',
                'LastName': '',
                'CorporationName': data["insured_name"],
                'NameOnPolicy': data["insured_name"],
                'DBA': '',
                'FEIN': '',
                'SSN': '',
                'DateOfBirth': None,
                'RiskId': '',
                'Office': "00000000-0000-0000-0000-000000000000"
            }
            
            # Create insured location object
            insLocation = {
                'InsuredGuid': "00000000-0000-0000-0000-000000000000",  # Will be set by server
                'InsuredLocationGuid': "00000000-0000-0000-0000-000000000000",
                'LocationName': 'Primary',
                'Address1': data["address_1"],
                'Address2': data.get("address_2", ""),
                'City': data["city"],
                'County': '',
                'State': data["state"],
                'Zip': data["zip"],
                'ZipPlus': '',
                'ISOCountryCode': 'US',
                'Region': '',
                'Phone': '',
                'Fax': '',
                'Email': '',
                'Website': '',
                'DeliveryMethodID': 1,  # Default delivery method
                'LocationTypeID': 1,  # Primary location
                'MobileNumber': '',
                'OptOut': False
            }
            
            # Create submission object
            submission = {
                'Insured': "00000000-0000-0000-0000-000000000000",  # Will be set by server
                'ProducerContact': data.get("producer_guid", os.getenv("TRITON_DEFAULT_PRODUCER_GUID", "00000000-0000-0000-0000-000000000000")),
                'Underwriter': data.get("underwriter_guid", os.getenv("TRITON_DEFAULT_UNDERWRITER_GUID", "00000000-0000-0000-0000-000000000000")),
                'SubmissionDate': data.get("submission_date", datetime.now().strftime("%Y-%m-%d")),
                'ProducerLocation': data.get("producer_location_guid", os.getenv("TRITON_DEFAULT_PRODUCER_GUID", "00000000-0000-0000-0000-000000000000")),
                'TACSR': data.get("tacsr_guid", "00000000-0000-0000-0000-000000000000"),
                'InHouseProducer': data.get("inhouse_producer_guid", "00000000-0000-0000-0000-000000000000")
            }
            
            # Create quote object with risk information
            quote = {
                'Submission': "00000000-0000-0000-0000-000000000000",  # Will be set by server
                'QuotingLocation': data.get("quoting_location_guid", os.getenv("TRITON_QUOTING_LOCATION_GUID", "00000000-0000-0000-0000-000000000000")),
                'IssuingLocation': data.get("issuing_location_guid", os.getenv("TRITON_ISSUING_LOCATION_GUID", "00000000-0000-0000-0000-000000000000")),
                'CompanyLocation': data.get("company_location_guid", os.getenv("TRITON_COMPANY_LOCATION_GUID", "00000000-0000-0000-0000-000000000000")),
                'Line': data.get("line_guid", os.getenv("TRITON_PRIMARY_LINE_GUID", "00000000-0000-0000-0000-000000000000")),
                'StateID': data["state"],
                'ProducerContact': data.get("producer_guid", os.getenv("TRITON_DEFAULT_PRODUCER_GUID", "00000000-0000-0000-0000-000000000000")),
                'QuoteStatusID': 1,  # Active/New
                'Effective': data["effective_date"],
                'Expiration': data["expiration_date"],
                'BillingTypeID': 1,  # Default billing type
                'FinanceCompany': "00000000-0000-0000-0000-000000000000",
                'NetRateQuoteID': 0,
                'QuoteDetail': {
                    'CompanyCommission': data.get("company_commission", 0) / 100 if data.get("company_commission") else 0,
                    'ProducerCommission': data.get("commission_rate", 0) / 100 if data.get("commission_rate") else 0,
                    'TermsOfPayment': 1,  # Default terms
                    'ProgramCode': data.get("program_code", ""),
                    'CompanyContactGuid': "00000000-0000-0000-0000-000000000000",
                    'RaterID': data.get("rater_id", 0),  # Use 0 as default if no rater specified
                    'FactorSetGuid': "00000000-0000-0000-0000-000000000000",
                    'ProgramID': data.get("program_id", 0),
                    'LineGUID': data.get("line_guid", os.getenv("TRITON_PRIMARY_LINE_GUID", "00000000-0000-0000-0000-000000000000")),
                    'CompanyLocationGUID': data.get("company_location_guid", os.getenv("TRITON_COMPANY_LOCATION_GUID", "00000000-0000-0000-0000-000000000000"))
                },
                'ExpiringQuoteGuid': "00000000-0000-0000-0000-000000000000",
                'Underwriter': data.get("underwriter_guid", os.getenv("TRITON_DEFAULT_UNDERWRITER_GUID", "00000000-0000-0000-0000-000000000000")),
                'ExpiringPolicyNumber': "",
                'ExpiringCompanyLocationGuid': "00000000-0000-0000-0000-000000000000",
                'PolicyTypeID': 1,  # Default policy type
                'RenewalOfQuoteGuid': "00000000-0000-0000-0000-000000000000",
                'InsuredBusinessTypeID': 9,  # LLC - Partnership
                'AccountNumber': "",
                'AdditionalInformation': self._build_additional_info(data),
                'OnlineRaterID': 0,
                'CostCenterID': 0,
                'ProgramCode': data.get("program_code", ""),
                'RiskInformation': {
                    'PolicyName': data["insured_name"],
                    'CorporationName': data["insured_name"],
                    'DBA': '',
                    'Salutation': '',
                    'FirstName': '',
                    'MiddleName': '',
                    'LastName': '',
                    'SSN': '',
                    'FEIN': '',
                    'Address1': data["address_1"],
                    'Address2': data.get("address_2", ""),
                    'City': data["city"],
                    'State': data["state"],
                    'ISOCountryCode': 'US',
                    'Region': '',
                    'ZipCode': data["zip"],
                    'ZipPlus': '',
                    'Phone': '',
                    'Fax': '',
                    'Mobile': '',
                    'BusinessType': 9  # LLC - Partnership
                },
                'ProgramID': data.get("program_id", 0)
            }
            
            # Call AddQuoteWithInsured to create everything at once
            response = self.client.service.AddQuoteWithInsured(
                ins=ins,
                insLocation=insLocation,
                submission=submission,
                quote=quote,
                _soapheaders=self.get_header(token)
            )
            
            # Extract GUIDs from response
            result = {
                "insured_guid": UUID(str(response.InsuredGuid)),
                "insured_location_guid": UUID(str(response.InsuredLocationGuid)),
                "submission_guid": UUID(str(response.SubmissionGroupGuid)),
                "quote_guid": UUID(str(response.QuoteGuid))
            }
            
            logger.info(f"Created insured, location, submission and quote: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating quote with insured: {e}")
            raise
    
    def create_submission_and_quote(self, insured_guid: UUID, data: Dict[str, Any]) -> Dict[str, UUID]:
        """Create a submission and quote together (for existing insured)"""
        try:
            # Use the existing fallback method for cases where insured already exists
            return self._create_submission_and_quote_separately(insured_guid, data)
            
        except Exception as e:
            logger.error(f"Error creating submission and quote: {e}")
            raise
    
    def _create_submission_and_quote_separately(self, insured_guid: UUID, data: Dict[str, Any]) -> Dict[str, UUID]:
        """Create submission and quote using AddQuote (which creates both)"""
        try:
            token = self.auth_service.get_token()
            
            # Create submission object for AddQuote
            submission = {
                'Insured': str(insured_guid),
                'ProducerContact': data.get("producer_guid", os.getenv("TRITON_DEFAULT_PRODUCER_GUID", "00000000-0000-0000-0000-000000000000")),
                'Underwriter': data.get("underwriter_guid", os.getenv("TRITON_DEFAULT_UNDERWRITER_GUID", "00000000-0000-0000-0000-000000000000")),
                'SubmissionDate': data.get("submission_date", datetime.now().strftime("%Y-%m-%d")),
                'ProducerLocation': data.get("producer_location_guid", os.getenv("TRITON_DEFAULT_PRODUCER_GUID", "00000000-0000-0000-0000-000000000000")),
                'TACSR': data.get("tacsr_guid", "00000000-0000-0000-0000-000000000000"),
                'InHouseProducer': data.get("inhouse_producer_guid", "00000000-0000-0000-0000-000000000000")
            }
            
            # Create quote object (Submission field will be set by server)
            quote = {
                'Submission': "00000000-0000-0000-0000-000000000000",  # Will be set by server
                'QuotingLocation': data.get("quoting_location_guid", os.getenv("TRITON_QUOTING_LOCATION_GUID", "00000000-0000-0000-0000-000000000000")),
                'IssuingLocation': data.get("issuing_location_guid", os.getenv("TRITON_ISSUING_LOCATION_GUID", "00000000-0000-0000-0000-000000000000")),
                'CompanyLocation': data.get("company_location_guid", os.getenv("TRITON_COMPANY_LOCATION_GUID", "00000000-0000-0000-0000-000000000000")),
                'Line': data.get("line_guid", os.getenv("TRITON_PRIMARY_LINE_GUID", "00000000-0000-0000-0000-000000000000")),
                'StateID': data["state"],
                'ProducerContact': data.get("producer_guid", os.getenv("TRITON_DEFAULT_PRODUCER_GUID", "00000000-0000-0000-0000-000000000000")),
                'QuoteStatusID': 1,  # Active/New
                'Effective': data["effective_date"],
                'Expiration': data["expiration_date"],
                'BillingTypeID': 1,  # Default billing type
                'FinanceCompany': "00000000-0000-0000-0000-000000000000",
                'NetRateQuoteID': 0,
                'QuoteDetail': {
                    'CompanyCommission': data.get("company_commission", 0) / 100 if data.get("company_commission") else 0,
                    'ProducerCommission': data.get("commission_rate", 0) / 100 if data.get("commission_rate") else 0,
                    'TermsOfPayment': 1,  # Default terms
                    'ProgramCode': data.get("program_code", ""),
                    'CompanyContactGuid': "00000000-0000-0000-0000-000000000000",
                    'RaterID': data.get("rater_id", 0),  # Use 0 as default if no rater specified
                    'FactorSetGuid': "00000000-0000-0000-0000-000000000000",
                    'ProgramID': data.get("program_id", 0),
                    'LineGUID': data.get("line_guid", os.getenv("TRITON_PRIMARY_LINE_GUID", "00000000-0000-0000-0000-000000000000")),
                    'CompanyLocationGUID': data.get("company_location_guid", os.getenv("TRITON_COMPANY_LOCATION_GUID", "00000000-0000-0000-0000-000000000000"))
                },
                'ExpiringQuoteGuid': "00000000-0000-0000-0000-000000000000",
                'Underwriter': data.get("underwriter_guid", os.getenv("TRITON_DEFAULT_UNDERWRITER_GUID", "00000000-0000-0000-0000-000000000000")),
                'ExpiringPolicyNumber': "",
                'ExpiringCompanyLocationGuid': "00000000-0000-0000-0000-000000000000",
                'PolicyTypeID': 1,  # Default policy type
                'RenewalOfQuoteGuid': "00000000-0000-0000-0000-000000000000",
                'InsuredBusinessTypeID': 9,  # LLC - Partnership
                'AccountNumber': "",
                'AdditionalInformation': self._build_additional_info(data),
                'OnlineRaterID': 0,
                'CostCenterID': 0,
                'ProgramCode': data.get("program_code", ""),
                'RiskInformation': {
                    'PolicyName': data["insured_name"],
                    'CorporationName': data["insured_name"],
                    'DBA': None,
                    'Salutation': None,
                    'FirstName': None,
                    'MiddleName': None,
                    'LastName': None,
                    'SSN': None,
                    'FEIN': None,
                    'Address1': data["address_1"],
                    'Address2': data.get("address_2", None),
                    'City': data["city"],
                    'State': data["state"],
                    'ISOCountryCode': "US",
                    'Region': None,
                    'ZipCode': data["zip"],
                    'ZipPlus': None,
                    'Phone': None,
                    'Fax': None,
                    'Mobile': None,
                    'BusinessType': 9  # LLC - Partnership
                },
                'ProgramID': data.get("program_id", 0)
            }
            
            # AddQuote creates both submission and quote
            quote_response = self.client.service.AddQuote(
                submission=submission,
                quote=quote,
                _soapheaders=self.get_header(token)
            )
            quote_guid = UUID(str(quote_response))
            logger.info(f"Created submission and quote: {quote_guid}")
            
            return {
                "quote_guid": quote_guid,
                "submission_guid": None  # AddQuote doesn't return submission GUID separately
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
            
            # Try the simple BindQuote method first
            response = self.client.service.BindQuote(
                quoteGuid=str(quote_guid),
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Bound quote {quote_guid}")
            return {"success": True, "policy_guid": str(response)}
            
        except Exception as e:
            logger.error(f"Error binding quote: {e}")
            raise
    
    def bind_with_option_id(self, quote_option_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Bind a quote using the quote option ID (integer)
        
        This uses the Bind method which takes an integer quote option ID.
        Per documentation: If the QuoteOptionID does not reference an 
        InstallmentBillingQuoteOptionID, then will be billed as single pay.
        """
        try:
            token = self.auth_service.get_token()
            
            # Use the Bind method with quote option ID
            response = self.client.service.Bind(
                quoteOptionID=quote_option_id,
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Bound quote option {quote_option_id}")
            return {"success": True, "policy_guid": str(response)}
            
        except Exception as e:
            logger.error(f"Error binding quote option: {e}")
            raise
    
    def bind_single_pay(self, quote_guid: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        """Bind a quote as single pay (no installments) using BindQuoteWithInstallment
        
        Uses companyInstallmentID = -1 to force single pay billing
        """
        try:
            token = self.auth_service.get_token()
            
            # Use BindQuoteWithInstallment with -1 for single pay
            response = self.client.service.BindQuoteWithInstallment(
                quoteGuid=str(quote_guid),
                companyInstallmentID=-1,  # -1 forces single pay
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Bound quote {quote_guid} as single pay")
            return {"success": True, "policy_guid": str(response)}
            
        except Exception as e:
            logger.error(f"Error binding quote as single pay: {e}")
            raise
    
    def bind_single_pay_with_option(self, quote_option_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Bind a quote option as single pay (no installments) using BindWithInstallment
        
        Uses companyInstallmentID = -1 to force single pay billing
        """
        try:
            token = self.auth_service.get_token()
            
            # Use BindWithInstallment with -1 for single pay
            response = self.client.service.BindWithInstallment(
                quoteOptionID=quote_option_id,
                companyInstallmentID=-1,  # -1 forces single pay
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Bound quote option {quote_option_id} as single pay")
            return {"success": True, "policy_guid": str(response)}
            
        except Exception as e:
            logger.error(f"Error binding quote option as single pay: {e}")
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
    
    def import_excel_rater(self, quote_guid: UUID, file_bytes: bytes, file_name: str = "TritonData.xlsx", 
                          rater_id: int = 0, factor_set_guid: UUID = None, apply_fees: bool = False) -> Dict[str, Any]:
        """Import Excel rater data - can be used to store additional data"""
        try:
            token = self.auth_service.get_token()
            
            # Use default empty GUID if not provided
            if not factor_set_guid:
                factor_set_guid = UUID("00000000-0000-0000-0000-000000000000")
            
            response = self.client.service.ImportExcelRater(
                QuoteGuid=str(quote_guid),
                FileBytes=file_bytes,
                FileName=file_name,
                RaterID=rater_id,
                FactorSetGuid=str(factor_set_guid),
                ApplyFees=apply_fees,
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Imported Excel rater for quote {quote_guid}")
            
            # Parse response
            result = {
                "success": response.Success if hasattr(response, 'Success') else False,
                "error_message": response.ErrorMessage if hasattr(response, 'ErrorMessage') else None,
                "premiums": []
            }
            
            if hasattr(response, 'Premiums') and response.Premiums:
                for option in response.Premiums.OptionResult:
                    result["premiums"].append({
                        "option_guid": str(option.QuoteOptionGuid),
                        "premium_total": float(option.PremiumTotal),
                        "fee_total": float(option.FeeTotal)
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error importing Excel rater: {e}")
            raise
    
    def update_external_quote_id(self, quote_guid: UUID, external_quote_id: str, external_system_id: str = "TRITON") -> Dict[str, Any]:
        """Update external quote ID for integration tracking"""
        try:
            token = self.auth_service.get_token()
            self.client.service.UpdateExternalQuoteId(
                quoteGuid=str(quote_guid),
                externalQuoteId=external_quote_id,
                externalSystemId=external_system_id,
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Updated external quote ID for {quote_guid}: {external_quote_id} ({external_system_id})")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error updating external quote ID: {e}")
            raise
    
    def import_net_rate_xml(self, quote_guid: UUID, xml_data: str) -> List[str]:
        """Import NetRate XML data - can be used for storing additional data"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.ImportNetRateXml(
                quoteGuid=str(quote_guid),
                xml=xml_data,
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Imported XML data for quote {quote_guid}")
            # Response is array of strings (status messages)
            return response if response else []
            
        except Exception as e:
            logger.error(f"Error importing NetRate XML: {e}")
            raise
    
    def add_quote_option(self, quote_guid: UUID, line_guid: UUID = None) -> UUID:
        """Add a quote option to enable binding"""
        try:
            token = self.auth_service.get_token()
            
            # Use the line GUID from environment if not provided
            if not line_guid:
                line_guid = UUID(os.getenv("TRITON_PRIMARY_LINE_GUID", "07564291-CBFE-4BBE-88D1-0548C88ACED4"))
            
            response = self.client.service.AddQuoteOption(
                quoteGuid=str(quote_guid),
                lineGuid=str(line_guid),
                _soapheaders=self.get_header(token)
            )
            
            option_guid = UUID(str(response))
            logger.info(f"Added quote option {option_guid} to quote {quote_guid}")
            return option_guid
            
        except Exception as e:
            logger.error(f"Error adding quote option: {e}")
            raise
    
    def add_premium(self, quote_option_guid: UUID, premium: float, office_id: int = 1, charge_code: int = 1) -> Dict[str, Any]:
        """Add premium to a quote option
        
        Args:
            quote_option_guid: The GUID of the quote option to add premium to
            premium: The premium amount
            office_id: The office ID (default: 1)
            charge_code: The charge code (default: 1)
        
        Returns:
            Dict with success status
        """
        try:
            token = self.auth_service.get_token()
            
            # AddPremium doesn't return anything on success
            self.client.service.AddPremium(
                quoteOptionGuid=str(quote_option_guid),
                premium=premium,
                officeID=office_id,
                chargeCode=charge_code,
                _soapheaders=self.get_header(token)
            )
            
            logger.info(f"Added premium {premium} to quote option {quote_option_guid}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error adding premium: {e}")
            raise
    
    def _build_additional_info(self, data: Dict[str, Any]) -> List[str]:
        """Build additional information array for storing Triton data"""
        additional_info = []
        
        # Check if we have additional data to store
        if "additional_data" in data:
            triton_data = data["additional_data"]
            # Store each piece of Triton data as a key-value string
            additional_info.extend([
                f"TRITON:transaction_id={triton_data.get('transaction_id', '')}",
                f"TRITON:prior_transaction_id={triton_data.get('prior_transaction_id', '')}",
                f"TRITON:opportunity_id={triton_data.get('opportunity_id', '')}",
                f"TRITON:opportunity_type={triton_data.get('opportunity_type', '')}",
                f"TRITON:policy_fee={triton_data.get('policy_fee', '')}",
                f"TRITON:surplus_lines_tax={triton_data.get('surplus_lines_tax', '')}",
                f"TRITON:stamping_fee={triton_data.get('stamping_fee', '')}",
                f"TRITON:other_fee={triton_data.get('other_fee', '')}",
                f"TRITON:commission_percent={triton_data.get('commission_percent', '')}",
                f"TRITON:commission_amount={triton_data.get('commission_amount', '')}",
                f"TRITON:net_premium={triton_data.get('net_premium', '')}",
                f"TRITON:base_premium={triton_data.get('base_premium', '')}",
                f"TRITON:status={triton_data.get('status', '')}",
                f"TRITON:limit_prior={triton_data.get('limit_prior', '')}",
                f"TRITON:invoice_date={triton_data.get('invoice_date', '')}"
            ])
        
        return additional_info
    
    def _create_triton_excel_data(self, data: Dict[str, Any]) -> bytes:
        """Create Excel file with Triton data for ImportExcelRater (future use)"""
        # This is a placeholder for creating Excel data
        # Would need to implement with openpyxl or similar library
        # Example structure:
        # Sheet 1: Triton Data
        # Row 1: Headers (Field, Value)
        # Row 2+: Data rows
        # 
        # For now, return empty bytes
        # In production, would use:
        # import openpyxl
        # wb = openpyxl.Workbook()
        # ws = wb.active
        # ws.title = "Triton Data"
        # ... add data ...
        # return wb.save(as_bytes=True)
        
        logger.warning("Excel data creation not implemented - would need openpyxl library")
        return b""