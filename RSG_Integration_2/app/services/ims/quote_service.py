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
        self.endpoint = IMS_CONFIG["endpoints"]["quote_functions"]
        self.timeout = IMS_CONFIG["timeout"]
        self.auth_service = get_auth_service()
        self.quote_config = QUOTE_CONFIG
        
    def add_quote_with_submission(
        self,
        insured_guid: str,
        producer_contact_guid: str,
        underwriter_guid: str,
        effective_date: str,
        expiration_date: str,
        state_id: str,
        producer_commission: float,
        submission_date: Optional[str] = None
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
            
            # Format commission rates
            company_commission = self.quote_config["default_company_commission"]
            producer_commission_str = str(producer_commission)
            if not producer_commission_str.startswith('.'):
                producer_commission_str = str(producer_commission / 100) if producer_commission > 1 else str(producer_commission)
            
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
        <Line>{self.quote_config["primary_line_guid"]}</Line>
        <StateID>{self._escape_xml(state_id)}</StateID>
        <ProducerContact>{producer_contact_guid}</ProducerContact>
        <QuoteStatusID>{self.quote_config["default_quote_status_id"]}</QuoteStatusID>
        <Effective>{effective_date}</Effective>
        <Expiration>{expiration_date}</Expiration>
        <BillingTypeID>{self.quote_config["default_billing_type_id"]}</BillingTypeID>
        <QuoteDetail>
          <CompanyCommission>{company_commission}</CompanyCommission>
          <ProducerCommission>{producer_commission_str}</ProducerCommission>
          <LineGUID>{self.quote_config["primary_line_guid"]}</LineGUID>
          <CompanyLocationGUID>{self.quote_config["company_location"]}</CompanyLocationGUID>
        </QuoteDetail>
        <Underwriter>{underwriter_guid}</Underwriter>
        <PolicyTypeID>{self.quote_config["default_policy_type_id"]}</PolicyTypeID>
        <InsuredBusinessTypeID>{self.quote_config["default_business_type_id"]}</InsuredBusinessTypeID>
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
            url = f"{self.base_url}{self.endpoint}"
            logger.info(f"Creating quote for insured: {insured_guid}")
            
            response = requests.post(
                url,
                data=soap_request,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse response
            return self._parse_quote_response(response.text)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP request failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
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
    
    def create_quote_from_payload(
        self,
        payload: Dict,
        insured_guid: str,
        producer_contact_guid: str,
        producer_location_guid: str,
        underwriter_guid: str
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
        # Extract required fields from payload
        effective_date = payload.get("effective_date", "")
        expiration_date = payload.get("expiration_date", "")
        state_id = payload.get("insured_state", "")
        commission_rate = payload.get("commission_rate", 0)
        
        # Validate required fields
        if not all([effective_date, expiration_date, state_id]):
            missing = []
            if not effective_date:
                missing.append("effective_date")
            if not expiration_date:
                missing.append("expiration_date")
            if not state_id:
                missing.append("insured_state")
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
        
        # Create the quote
        return self.add_quote_with_submission(
            insured_guid=insured_guid,
            producer_contact_guid=producer_contact_guid,
            underwriter_guid=underwriter_guid,
            effective_date=effective_date,
            expiration_date=expiration_date,
            state_id=state_id,
            producer_commission=commission_rate
        )
    
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