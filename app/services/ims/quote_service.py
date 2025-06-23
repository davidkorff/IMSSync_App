"""
IMS Quote Service

This service handles all quote-related operations in IMS including:
- Creating submissions
- Creating quotes
- Managing quote options
- Premium operations
- Binding and issuing policies
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
import base64

from app.services.ims.base_service import BaseIMSService

logger = logging.getLogger(__name__)


class IMSQuoteService(BaseIMSService):
    """Service for managing quotes in IMS"""
    
    def create_submission(self, submission_data: Dict[str, Any]) -> str:
        """
        Create a new submission in IMS
        
        Args:
            submission_data: Dictionary containing submission information
            
        Returns:
            The submission GUID
        """
        self._log_operation("create_submission", {
            "insured_guid": submission_data.get("insured_guid")
        })
        
        # Validate required fields
        required_fields = ["insured_guid", "producer_contact_guid", "submission_date"]
        for field in required_fields:
            if not submission_data.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        try:
            submission_guid = self.soap_client.add_submission(submission_data)
            logger.info(f"Created submission: {submission_guid}")
            return submission_guid
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "create_submission")
                # Retry once
                return self.soap_client.add_submission(submission_data)
            raise
    
    def create_quote(self, quote_data: Dict[str, Any]) -> str:
        """
        Create a new quote in IMS
        
        Args:
            quote_data: Dictionary containing quote information
            
        Returns:
            The quote GUID
        """
        self._log_operation("create_quote", {
            "submission_guid": quote_data.get("submission_guid"),
            "effective_date": quote_data.get("effective_date")
        })
        
        # Validate required fields
        required_fields = ["submission_guid", "effective_date", "expiration_date", "state"]
        for field in required_fields:
            if not quote_data.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        # Set defaults if not provided
        quote_data.setdefault("status_id", 1)  # New
        quote_data.setdefault("billing_type_id", 1)  # Agency Bill
        
        try:
            quote_guid = self.soap_client.add_quote(quote_data)
            logger.info(f"Created quote: {quote_guid}")
            return quote_guid
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "create_quote")
                # Retry once
                return self.soap_client.add_quote(quote_data)
            raise
    
    def add_quote_option(self, quote_guid: str) -> int:
        """
        Add a quote option to a quote
        
        Args:
            quote_guid: The quote's GUID
            
        Returns:
            The quote option ID
        """
        self._log_operation("add_quote_option", {"quote_guid": quote_guid})
        
        try:
            option_id = self.soap_client.add_quote_option(quote_guid)
            logger.info(f"Added quote option {option_id} to quote {quote_guid}")
            return option_id
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "add_quote_option")
                # Retry once
                return self.soap_client.add_quote_option(quote_guid)
            raise
    
    def add_premium(self, quote_guid: str, option_id: int, 
                   premium_amount: float, description: str = "Premium") -> bool:
        """
        Add premium to a quote option
        
        Args:
            quote_guid: The quote's GUID
            option_id: The quote option ID
            premium_amount: The premium amount
            description: Premium description
            
        Returns:
            True if successful
        """
        self._log_operation("add_premium", {
            "quote_guid": quote_guid,
            "option_id": option_id,
            "amount": premium_amount
        })
        
        try:
            result = self.soap_client.add_premium(quote_guid, option_id, premium_amount, description)
            
            if result:
                logger.info(f"Added premium of {premium_amount} to quote option {option_id}")
            else:
                logger.error(f"Failed to add premium to quote option {option_id}")
                
            return result
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "add_premium")
                # Retry once
                return self.soap_client.add_premium(quote_guid, option_id, premium_amount, description)
            raise
    
    def import_excel_rater(self, quote_guid: str, excel_file_path: str,
                          rater_id: int, factor_set_guid: str, 
                          apply_fees: bool = True) -> Dict[str, Any]:
        """
        Import an Excel rater for a quote
        
        Args:
            quote_guid: The quote's GUID
            excel_file_path: Path to the Excel file
            rater_id: The rater ID
            factor_set_guid: The factor set GUID
            apply_fees: Whether to apply fees
            
        Returns:
            Dictionary with success status and premium information
        """
        self._log_operation("import_excel_rater", {
            "quote_guid": quote_guid,
            "file": excel_file_path,
            "rater_id": rater_id
        })
        
        try:
            # Read and encode the file
            with open(excel_file_path, "rb") as file:
                file_bytes = base64.b64encode(file.read()).decode("utf-8")
            
            result = self.soap_client.import_excel_rater(
                quote_guid, 
                file_bytes,
                excel_file_path.split("/")[-1],  # Just the filename
                rater_id,
                factor_set_guid,
                apply_fees
            )
            
            if result['success']:
                logger.info(f"Successfully imported Excel rater for quote {quote_guid}")
            else:
                logger.error(f"Failed to import Excel rater: {result.get('error_message')}")
                
            return result
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "import_excel_rater")
                # Retry once
                return self.import_excel_rater(quote_guid, excel_file_path, 
                                             rater_id, factor_set_guid, apply_fees)
            raise
    
    def bind_quote(self, quote_option_id: int) -> str:
        """
        Bind a quote to create a policy
        
        Args:
            quote_option_id: The quote option ID to bind
            
        Returns:
            The policy number
        """
        self._log_operation("bind_quote", {"quote_option_id": quote_option_id})
        
        try:
            policy_number = self.soap_client.bind(quote_option_id)
            logger.info(f"Bound quote option {quote_option_id}, created policy {policy_number}")
            return policy_number
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "bind_quote")
                # Retry once
                return self.soap_client.bind(quote_option_id)
            raise
    
    def issue_policy(self, policy_number: str) -> bool:
        """
        Issue a policy
        
        Args:
            policy_number: The policy number to issue
            
        Returns:
            True if successful
        """
        self._log_operation("issue_policy", {"policy_number": policy_number})
        
        try:
            result = self.soap_client.issue_policy(policy_number)
            
            if result:
                logger.info(f"Successfully issued policy {policy_number}")
            else:
                logger.error(f"Failed to issue policy {policy_number}")
                
            return result
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "issue_policy")
                # Retry once
                return self.soap_client.issue_policy(policy_number)
            raise
    
    def update_external_quote_id(self, quote_guid: str, 
                               external_id: str, external_system: str) -> bool:
        """
        Update the external quote ID for cross-system reference
        
        Args:
            quote_guid: The quote's GUID
            external_id: The external system's ID
            external_system: The name of the external system
            
        Returns:
            True if successful
        """
        self._log_operation("update_external_quote_id", {
            "quote_guid": quote_guid,
            "external_id": external_id,
            "external_system": external_system
        })
        
        try:
            result = self.soap_client.update_external_quote_id(
                quote_guid, external_id, external_system
            )
            
            if result:
                logger.info(f"Updated external quote ID for {quote_guid}: {external_system}/{external_id}")
            else:
                logger.error(f"Failed to update external quote ID for {quote_guid}")
                
            return result
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "update_external_quote_id")
                # Retry once
                return self.soap_client.update_external_quote_id(
                    quote_guid, external_id, external_system
                )
            raise
    
    def get_default_line_guid(self, source: str, coverage_type: str = "primary") -> str:
        """
        Get the default line GUID for a source system and coverage type
        
        Args:
            source: The source system name (e.g., 'triton', 'xuber')
            coverage_type: The coverage type ('primary' or 'excess')
            
        Returns:
            The line GUID
        """
        default_guid = "00000000-0000-0000-0000-000000000000"
        
        source_config = self._get_source_config(source)
        
        if coverage_type.lower() == "excess":
            line_guid = source_config.get("excess_line_guid", 
                                        source_config.get("default_line_guid", default_guid))
        else:
            line_guid = source_config.get("default_line_guid", default_guid)
        
        logger.info(f"Using line GUID for {source}/{coverage_type}: {line_guid}")
        return line_guid
    
    def get_rater_info(self, source: str, coverage_type: str = "primary") -> Tuple[int, str]:
        """
        Get rater ID and factor set GUID for a source and coverage type
        
        Args:
            source: The source system name
            coverage_type: The coverage type
            
        Returns:
            Tuple of (rater_id, factor_set_guid)
        """
        source_config = self._get_source_config(source)
        raters = source_config.get("raters", {})
        
        # Map coverage type to rater name
        rater_key = f"AHC {coverage_type.title()}"
        rater_info = raters.get(rater_key, {})
        
        rater_id = rater_info.get("rater_id", 1)
        factor_set_guid = rater_info.get("factor_set_guid", "00000000-0000-0000-0000-000000000000")
        
        logger.info(f"Using rater info for {source}/{coverage_type}: ID={rater_id}, FactorSet={factor_set_guid}")
        return rater_id, factor_set_guid
    
    def get_control_number(self, company_location_guid: str, 
                          line_guid: str, prefix: str = "") -> str:
        """
        Get a control number for a new policy
        
        Args:
            company_location_guid: The company location GUID
            line_guid: The line of business GUID
            prefix: Optional prefix for the control number
            
        Returns:
            The control number
        """
        self._log_operation("get_control_number", {
            "company_location_guid": company_location_guid,
            "line_guid": line_guid
        })
        
        body_content = f"""
        <GetControlNumber xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
            <companyLocationGuid>{company_location_guid}</companyLocationGuid>
            <lineGuid>{line_guid}</lineGuid>
            <prefix>{prefix}</prefix>
        </GetControlNumber>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.quote_functions_url,
                "http://tempuri.org/IMSWebServices/QuoteFunctions/GetControlNumber",
                body_content
            )
            
            if response and 'soap:Body' in response:
                control_response = response['soap:Body'].get('GetControlNumberResponse', {})
                control_number = control_response.get('GetControlNumberResult')
                
                if control_number:
                    logger.info(f"Got control number: {control_number}")
                    return control_number
            
            raise ValueError("Failed to get control number")
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "get_control_number")
                # Retry once
                return self.get_control_number(company_location_guid, line_guid, prefix)
            raise