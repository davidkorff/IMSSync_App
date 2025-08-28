import logging
import requests
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Tuple
from datetime import datetime, date

from app.services.ims.auth_service import get_auth_service
from config import IMS_CONFIG, QUOTE_CONFIG

logger = logging.getLogger(__name__)


class IMSQuoteService:
    """Service for handling IMS Quote operations."""
    
    def __init__(self):
        self.base_url = IMS_CONFIG["base_url"]
        self.services_env = IMS_CONFIG.get("environments", {}).get("services", "/ims_one")
        self.endpoint = IMS_CONFIG["endpoints"]["quote_functions"]
        self.timeout = IMS_CONFIG["timeout"]
        self.auth_service = get_auth_service()
        self.quote_config = QUOTE_CONFIG
        self._last_soap_request = None
        self._last_soap_response = None
        self._last_url = None
        
    def add_quote_with_submission(
        self,
        insured_guid: str,
        producer_contact_guid: str,
        underwriter_guid: str,
        effective_date: str,
        expiration_date: str,
        state_id: str,
        producer_commission: float,
        submission_date: Optional[str] = None,
        policy_type_id: int = 1,
        expiring_quote_guid: Optional[str] = None,
        expiring_policy_number: Optional[str] = None,
        renewal_of_quote_guid: Optional[str] = None,
        line_guid: Optional[str] = None
    ) -> Tuple[bool, Optional[str], str]:
        """
        Add a new quote with submission using the AddQuoteWithSubmission method.
        
        Args:
            insured_guid: GUID of the insured
            producer_contact_guid: GUID of the producer contact
            underwriter_guid: GUID of the underwriter (user)
            effective_date: Policy effective date (YYYY-MM-DD)
            expiration_date: Policy expiration date (YYYY-MM-DD)
            state_id: State code (e.g., "MI")
            producer_commission: Producer commission rate (e.g., 0.175)
            submission_date: Optional submission date (defaults to today)
            policy_type_id: 1 for new business, 2 for renewal
            expiring_quote_guid: GUID of expiring quote (renewals only)
            expiring_policy_number: Expiring policy number (renewals only)
            renewal_of_quote_guid: GUID of quote being renewed (renewals only)
            line_guid: Optional Line GUID (defaults to primary line from config)
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, quote_guid, message)
        """
        try:
            # Ensure we have a valid token
            token = self.auth_service.token
            if not token:
                return False, None, "Failed to authenticate with IMS"
            
            # Use today's date if submission_date not provided
            if not submission_date:
                submission_date = date.today().strftime("%Y-%m-%d")
            
            # Use provided line_guid or default from config
            if not line_guid:
                line_guid = self.quote_config["primary_line_guid"]
            
            # Format commission rates
            company_commission = self.quote_config["default_company_commission"]
            producer_commission_str = str(producer_commission)
            if not producer_commission_str.startswith('.'):
                producer_commission_str = str(producer_commission / 100) if producer_commission > 1 else str(producer_commission)
            
            # Build renewal fields if applicable
            renewal_fields = ""
            if policy_type_id == 2:  # Renewal
                if expiring_quote_guid:
                    renewal_fields += f"        <ExpiringQuoteGuid>{expiring_quote_guid}</ExpiringQuoteGuid>\n"
                if expiring_policy_number:
                    renewal_fields += f"        <ExpiringPolicyNumber>{self._escape_xml(expiring_policy_number)}</ExpiringPolicyNumber>\n"
                if renewal_of_quote_guid:
                    renewal_fields += f"        <RenewalOfQuoteGuid>{renewal_of_quote_guid}</RenewalOfQuoteGuid>\n"
            
            # Construct SOAP request
            soap_request = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
      <Token>{token}</Token>
      <Context>RSG_Integration</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <AddQuoteWithSubmission xmlns="http://tempuri.org/IMSWebServices/QuoteFunctions">
      <submission>
        <Insured>{insured_guid}</Insured>
        <ProducerContact>{producer_contact_guid}</ProducerContact>
        <Underwriter>{underwriter_guid}</Underwriter>
        <SubmissionDate>{submission_date}</SubmissionDate>
      </submission>
      <quote>
        <QuotingLocation>{self.quote_config["quoting_location"]}</QuotingLocation>
        <IssuingLocation>{self.quote_config["issuing_location"]}</IssuingLocation>
        <CompanyLocation>{self.quote_config["company_location"]}</CompanyLocation>
        <Line>{line_guid}</Line>
        <StateID>{self._escape_xml(state_id)}</StateID>
        <ProducerContact>{producer_contact_guid}</ProducerContact>
        <QuoteStatusID>{self.quote_config["default_quote_status_id"]}</QuoteStatusID>
        <Effective>{effective_date}</Effective>
        <Expiration>{expiration_date}</Expiration>
        <BillingTypeID>{self.quote_config["default_billing_type_id"]}</BillingTypeID>
        <QuoteDetail>
          <CompanyCommission>{company_commission}</CompanyCommission>
          <ProducerCommission>{producer_commission_str}</ProducerCommission>
          <LineGUID>{line_guid}</LineGUID>
          <CompanyLocationGUID>{self.quote_config["company_location"]}</CompanyLocationGUID>
        </QuoteDetail>
        <Underwriter>{underwriter_guid}</Underwriter>
        <PolicyTypeID>{policy_type_id}</PolicyTypeID>
        <InsuredBusinessTypeID>{self.quote_config["default_business_type_id"]}</InsuredBusinessTypeID>
{renewal_fields.rstrip()}
      </quote>
    </AddQuoteWithSubmission>
  </soap:Body>
</soap:Envelope>'''
            
            # Prepare headers
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/IMSWebServices/QuoteFunctions/AddQuoteWithSubmission'
            }
            
            # Make request
            url = f"{self.base_url}{self.services_env}{self.endpoint}"
            logger.info(f"Creating quote for insured: {insured_guid}")
            logger.debug(f"SOAP Request URL: {url}")
            logger.debug(f"SOAP Request:\n{soap_request}")
            
            # Store request details for error reporting
            self._last_url = url
            self._last_soap_request = soap_request
            
            response = requests.post(
                url,
                data=soap_request,
                headers=headers,
                timeout=self.timeout
            )
            
            # Store response for error reporting
            self._last_soap_response = response.text
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse response
            return self._parse_quote_response(response.text)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP request failed: {str(e)}"
            logger.error(error_msg)
            # Build detailed error message with SOAP details
            detailed_msg = error_msg
            if self._last_url:
                detailed_msg += f"\n\nRequest URL: {self._last_url}"
            if self._last_soap_request:
                detailed_msg += f"\n\nSOAP Request Sent:\n{self._last_soap_request}"
            if hasattr(e, 'response') and e.response is not None:
                detailed_msg += f"\n\nHTTP Response Status: {e.response.status_code}"
                detailed_msg += f"\n\nHTTP Response Body:\n{e.response.text}"
            return False, None, detailed_msg
        except Exception as e:
            error_msg = f"Unexpected error during quote creation: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _parse_quote_response(self, response_xml: str) -> Tuple[bool, Optional[str], str]:
        """
        Parse the AddQuoteWithSubmission response XML.
        
        Args:
            response_xml: The SOAP response XML string
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, quote_guid, message)
        """
        try:
            # Parse XML
            root = ET.fromstring(response_xml)
            
            # Define namespaces
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ims': 'http://tempuri.org/IMSWebServices/QuoteFunctions'
            }
            
            # Find AddQuoteWithSubmissionResult
            result = root.find('.//ims:AddQuoteWithSubmissionResult', namespaces)
            
            if result is None:
                return False, None, "AddQuoteWithSubmissionResult not found in response"
            
            quote_guid = result.text
            
            # Check for null GUID (creation failed)
            if not quote_guid or quote_guid == "00000000-0000-0000-0000-000000000000":
                return False, None, "Failed to create quote - received null GUID"
            
            logger.info(f"Successfully created quote with GUID: {quote_guid}")
            return True, quote_guid, f"Quote created successfully: {quote_guid}"
            
        except ET.ParseError as e:
            error_msg = f"Failed to parse XML response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Error processing quote response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _determine_line_guid(self, payload: Dict) -> str:
        """
        Determine the appropriate Line GUID based on payload data.
        
        Current logic:
        - Check class_of_business or program_name for indicators
        - Default to primary line if no specific rule matches
        
        Args:
            payload: The Triton transaction payload
            
        Returns:
            str: The appropriate Line GUID
        """
        # Get potential determining fields
        class_of_business = payload.get("class_of_business", "").lower()
        program_name = payload.get("program_name", "").lower()
        
        # Get line GUIDs from environment
        import os
        primary_line_guid = os.getenv("TRITON_PRIMARY_LINE_GUID", "07564291-CBFE-4BBE-88D1-0548C88ACED4")
        excess_line_guid = os.getenv("TRITON_EXCESS_LINE_GUID", "08798559-321C-4FC0-98ED-A61B92215F31")
        
        # Determine based on business rules
        # TODO: Refine these rules based on actual business requirements
        # Example rules (these need to be confirmed with business):
        
        # Check for excess indicators in program name
        if "excess" in program_name or "umbrella" in program_name:
            logger.info(f"Selected Excess Line GUID based on program_name: {program_name}")
            return excess_line_guid
        
        # Check for excess indicators in class of business
        if "excess" in class_of_business or "umbrella" in class_of_business:
            logger.info(f"Selected Excess Line GUID based on class_of_business: {class_of_business}")
            return excess_line_guid
        
        # Check for specific programs that should use excess line
        # Add more specific rules as needed
        
        # Default to primary line
        logger.info(f"Selected Primary Line GUID (default) for program: {program_name}, class: {class_of_business}")
        return primary_line_guid
    
    def create_quote_from_payload(
        self,
        payload: Dict,
        insured_guid: str,
        producer_contact_guid: str,
        producer_location_guid: str,
        underwriter_guid: str,
        renewal_of_quote_guid: Optional[str] = None
    ) -> Tuple[bool, Optional[str], str]:
        """
        Create a quote using data from Triton payload and previously obtained GUIDs.
        
        Args:
            payload: The Triton transaction payload
            insured_guid: GUID of the insured
            producer_contact_guid: GUID of the producer contact
            producer_location_guid: GUID of the producer location (for future use)
            underwriter_guid: GUID of the underwriter
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, quote_guid, message)
        """
        # Determine the appropriate Line GUID
        line_guid = self._determine_line_guid(payload)
        logger.info(f"Using Line GUID: {line_guid}")
        
        # Extract required fields from payload
        effective_date = payload.get("effective_date", "")
        expiration_date = payload.get("expiration_date", "")
        state_id = payload.get("state", "")  # Use 'state' for the quote's state
        commission_rate = payload.get("commission_rate", 0)
        
        logger.info(f"DEBUG: create_quote_from_payload - Using state: {state_id} (from 'state' field)")
        logger.info(f"DEBUG: Payload has state={payload.get('state')}, insured_state={payload.get('insured_state')}")
        
        # Convert dates from MM/DD/YYYY to YYYY-MM-DD format
        if effective_date:
            try:
                # Parse MM/DD/YYYY and convert to YYYY-MM-DD
                dt = datetime.strptime(effective_date, "%m/%d/%Y")
                effective_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                # Try to parse as YYYY-MM-DD if already in that format
                try:
                    datetime.strptime(effective_date, "%Y-%m-%d")
                except ValueError:
                    return False, None, f"Invalid effective date format: {effective_date}. Expected MM/DD/YYYY or YYYY-MM-DD"
        
        if expiration_date:
            try:
                # Parse MM/DD/YYYY and convert to YYYY-MM-DD
                dt = datetime.strptime(expiration_date, "%m/%d/%Y")
                expiration_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                # Try to parse as YYYY-MM-DD if already in that format
                try:
                    datetime.strptime(expiration_date, "%Y-%m-%d")
                except ValueError:
                    return False, None, f"Invalid expiration date format: {expiration_date}. Expected MM/DD/YYYY or YYYY-MM-DD"
        
        # Validate required fields
        if not all([effective_date, expiration_date, state_id]):
            missing = []
            if not effective_date:
                missing.append("effective_date")
            if not expiration_date:
                missing.append("expiration_date")
            if not state_id:
                missing.append("state")
            return False, None, f"Missing required fields: {', '.join(missing)}"
        
        # Convert commission rate to decimal if needed
        if isinstance(commission_rate, (int, float)):
            if commission_rate > 1:
                commission_rate = commission_rate / 100
        else:
            try:
                commission_rate = float(commission_rate)
                if commission_rate > 1:
                    commission_rate = commission_rate / 100
            except:
                commission_rate = 0.175  # Default to 17.5%
        
        # Determine policy type and renewal fields
        opportunity_type = payload.get("opportunity_type", "").lower()
        policy_type_id = 2 if opportunity_type == "renewal" else 1
        expiring_policy_number = payload.get("expiring_policy_number")
        
        # Create the quote with the determined line GUID
        success, quote_guid, message = self.add_quote_with_submission(
            insured_guid=insured_guid,
            producer_contact_guid=producer_contact_guid,
            underwriter_guid=underwriter_guid,
            effective_date=effective_date,
            expiration_date=expiration_date,
            state_id=state_id,
            producer_commission=commission_rate,
            policy_type_id=policy_type_id,
            expiring_quote_guid=renewal_of_quote_guid if policy_type_id == 2 else None,
            expiring_policy_number=expiring_policy_number if policy_type_id == 2 else None,
            renewal_of_quote_guid=renewal_of_quote_guid if policy_type_id == 2 else None,
            line_guid=line_guid
        )
        
        # Return with any captured error details
        return success, quote_guid, message
    
    def _escape_xml(self, value: str) -> str:
        """Escape special XML characters."""
        if not value:
            return ""
        return (value
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


# Singleton instance
_quote_service = None


def get_quote_service() -> IMSQuoteService:
    """Get singleton instance of quote service."""
    global _quote_service
    if _quote_service is None:
        _quote_service = IMSQuoteService()
    return _quote_service