import logging
import json
import re
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any
from xml.sax.saxutils import unescape

from app.services.ims.auth_service import get_auth_service
from config import IMS_CONFIG

logger = logging.getLogger(__name__)


class IMSDataAccessService:
    """Service for handling IMS DataAccess operations using stored procedures."""
    
    def __init__(self):
        self.base_url = IMS_CONFIG["base_url"]
        self.services_env = IMS_CONFIG.get("environments", {}).get("services", "/ims_one")
        self.endpoint = IMS_CONFIG["endpoints"]["data_access"]
        self.timeout = IMS_CONFIG["timeout"]
        self.auth_service = get_auth_service()
        self._last_soap_request = None
        self._last_soap_response = None
        self._last_url = None
        
    def execute_dataset(self, procedure_name: str, parameters: List[str]) -> Tuple[bool, Optional[str], str]:
        """
        Execute a stored procedure and return results as XML.
        
        Args:
            procedure_name: Name of the stored procedure (without _WS suffix)
            parameters: List of parameters as [param_name, param_value, ...]
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, result_xml, message)
        """
        try:
            # Ensure we have a valid token
            token = self.auth_service.token
            if not token:
                return False, None, "Failed to authenticate with IMS"
            
            # Build parameters XML
            params_xml = ""
            for param in parameters:
                params_xml += f"        <string>{self._escape_xml(str(param))}</string>\n"
            
            # Construct SOAP request
            soap_request = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <Token>{token}</Token>
      <Context>RSG_Integration</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <ExecuteDataSet xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <procedureName>{procedure_name}</procedureName>
      <parameters>
{params_xml.rstrip()}
      </parameters>
    </ExecuteDataSet>
  </soap:Body>
</soap:Envelope>'''
            
            # Prepare headers
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'http://tempuri.org/IMSWebServices/DataAccess/ExecuteDataSet'
            }
            
            # Make request
            url = f"{self.base_url}{self.services_env}{self.endpoint}"
            logger.info(f"Executing stored procedure: {procedure_name}")
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
            
            logger.debug(f"SOAP Response Status: {response.status_code}")
            logger.debug(f"SOAP Response:\n{response.text}")
            
            # Parse response
            return self._parse_dataset_response(response.text, procedure_name)
            
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
            elif self._last_soap_response:
                detailed_msg += f"\n\nSOAP Response Received:\n{self._last_soap_response}"
            return False, None, detailed_msg
        except Exception as e:
            error_msg = f"Unexpected error during dataset execution: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _parse_dataset_response(self, response_xml: str, procedure_name: str) -> Tuple[bool, Optional[str], str]:
        """
        Parse the ExecuteDataSet response XML.
        
        Args:
            response_xml: The SOAP response XML string
            procedure_name: The procedure that was executed
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, result_xml, message)
        """
        try:
            # Parse XML
            root = ET.fromstring(response_xml)
            
            # Define namespaces
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ims': 'http://tempuri.org/IMSWebServices/DataAccess'
            }
            
            # Find ExecuteDataSetResult
            result = root.find('.//ims:ExecuteDataSetResult', namespaces)
            
            if result is None:
                return False, None, "ExecuteDataSetResult not found in response"
            
            # The result contains escaped XML, need to unescape it
            result_xml = result.text
            if result_xml:
                # Unescape the XML content
                result_xml = unescape(result_xml)
                logger.debug(f"Procedure {procedure_name} returned: {result_xml}")
                return True, result_xml, f"Successfully executed {procedure_name}"
            else:
                return False, None, f"No results returned from {procedure_name}"
            
        except ET.ParseError as e:
            error_msg = f"Failed to parse XML response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Error processing dataset response: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def get_producer_by_email_or_name(self, producer_email: str, producer_name: str) -> Tuple[bool, Optional[Dict[str, str]], str]:
        """
        Get producer information by email first, then by name if email not found.
        
        Args:
            producer_email: Email address of the producer
            producer_name: Full name of the producer (fallback)
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, producer_info, message)
            producer_info contains: ProducerContactGUID, ProducerLocationGUID
        """
        try:
            # Execute the stored procedure with both parameters
            success, result_xml, message = self.execute_dataset(
                "getProducerGuid",
                ["producer_email", producer_email or "", "producer_name", producer_name or ""]
            )
            
            if not success:
                return False, None, message
            
            # Parse the result XML
            if result_xml:
                result_root = ET.fromstring(result_xml)
                
                # Find the Table element
                table = result_root.find('.//Table')
                if table is not None:
                    producer_info = {}
                    
                    # Extract ProducerContactGUID
                    contact_guid = table.find('ProducerContactGUID')
                    if contact_guid is not None and contact_guid.text:
                        producer_info['ProducerContactGUID'] = contact_guid.text
                    
                    # Extract ProducerLocationGUID
                    location_guid = table.find('ProducerLocationGUID')
                    if location_guid is not None and location_guid.text:
                        producer_info['ProducerLocationGUID'] = location_guid.text
                    
                    if producer_info:
                        lookup_method = "email" if producer_email else "name"
                        lookup_value = producer_email if producer_email else producer_name
                        logger.info(f"Found producer via {lookup_method} '{lookup_value}': {producer_info}")
                        return True, producer_info, f"Found producer: {lookup_value}"
                    else:
                        return False, None, f"Producer not found by email '{producer_email}' or name '{producer_name}'"
                else:
                    return False, None, f"No producer found with email '{producer_email}' or name '{producer_name}'"
            else:
                return False, None, "No results returned"
                
        except ET.ParseError as e:
            error_msg = f"Failed to parse producer results: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Error getting producer: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def get_producer_by_email(self, producer_email: str) -> Tuple[bool, Optional[Dict[str, str]], str]:
        """
        Get producer information by email.
        
        Args:
            producer_email: Email address of the producer
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, producer_info, message)
            producer_info contains: ProducerContactGUID, ProducerLocationGUID
        """
        try:
            # Execute the stored procedure
            success, result_xml, message = self.execute_dataset(
                "getProducerGuid",
                ["producer_email", producer_email]
            )
            
            if not success:
                return False, None, message
            
            # Parse the result XML
            if result_xml:
                result_root = ET.fromstring(result_xml)
                
                # Find the Table element
                table = result_root.find('.//Table')
                if table is not None:
                    producer_info = {}
                    
                    # Extract ProducerContactGUID
                    contact_guid = table.find('ProducerContactGUID')
                    if contact_guid is not None and contact_guid.text:
                        producer_info['ProducerContactGUID'] = contact_guid.text
                    
                    # Extract ProducerLocationGUID
                    location_guid = table.find('ProducerLocationGUID')
                    if location_guid is not None and location_guid.text:
                        producer_info['ProducerLocationGUID'] = location_guid.text
                    
                    if producer_info:
                        logger.info(f"Found producer with email '{producer_email}': {producer_info}")
                        return True, producer_info, f"Found producer: {producer_email}"
                    else:
                        return False, None, f"Producer with email '{producer_email}' not found"
                else:
                    return False, None, f"No producer found with email: {producer_email}"
            else:
                return False, None, "No results returned"
                
        except ET.ParseError as e:
            error_msg = f"Failed to parse producer results: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Error getting producer: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def process_producer_from_payload(self, payload: Dict) -> Tuple[bool, Optional[Dict[str, str]], str]:
        """
        Extract producer email and name from payload and get producer information.
        First tries email lookup, then falls back to name lookup.
        
        Args:
            payload: The Triton transaction payload
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, producer_info, message)
        """
        producer_email = payload.get("producer_email", "")
        producer_name = payload.get("producer_name", "")
        
        if not producer_email and not producer_name:
            return False, None, "No producer email or name found in payload"
        
        # Call the updated stored procedure with both email and name
        success, info, message = self.get_producer_by_email_or_name(producer_email, producer_name)
        
        # If failed and we have debugging info, create detailed error message
        if not success:
            detailed_message = f"{message}"
            if self._last_url:
                detailed_message += f"\n\nRequest URL: {self._last_url}"
            if self._last_soap_request:
                detailed_message += f"\n\nSOAP Request Sent:\n{self._last_soap_request}"
            if self._last_soap_response:
                detailed_message += f"\n\nSOAP Response Received:\n{self._last_soap_response}"
            return success, info, detailed_message
        
        return success, info, message
    
    def get_quote_by_policy_number(self, policy_number: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Find quote information by policy number.
        
        Args:
            policy_number: The policy number to search for
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, quote_info, message)
        """
        try:
            # Execute the stored procedure
            success, result_xml, message = self.execute_dataset(
                "spGetQuoteByPolicyNumber",
                ["PolicyNumber", policy_number]
            )
            
            if not success:
                return False, None, message
            
            # Parse the result
            result_dict = self._parse_single_row_result(result_xml)
            
            if not result_dict:
                return False, None, f"No quote found for policy number: {policy_number}"
            
            # Extract key fields
            quote_info = {
                "QuoteGuid": result_dict.get("QuoteGuid"),
                "PolicyNumber": result_dict.get("PolicyNumber"),
                "InsuredGuid": result_dict.get("InsuredGuid"),
                "Effective": result_dict.get("Effective"),
                "Expiration": result_dict.get("Expiration"),
                "QuoteStatusID": result_dict.get("QuoteStatusID"),
                "QuoteStatusName": result_dict.get("QuoteStatusName"),
                "StateID": result_dict.get("StateID"),
                "ProducerContactGuid": result_dict.get("ProducerContactGuid"),
                "UnderwriterGuid": result_dict.get("UnderwriterGuid"),
                "InsuredName": result_dict.get("insured_name"),
                "NetPremium": result_dict.get("net_premium"),
                "TritonStatus": result_dict.get("TritonStatus"),
                "LastTransactionId": result_dict.get("LastTransactionId"),
                "LastTransactionDate": result_dict.get("LastTransactionDate")
            }
            
            logger.info(f"Found quote {quote_info['QuoteGuid']} for policy {policy_number}")
            return True, quote_info, "Quote lookup successful"
            
        except Exception as e:
            error_msg = f"Error looking up quote by policy number: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def get_quote_by_option_id(self, option_id: int) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Find quote GUID by option_id (opportunity_id from Triton).
        
        Args:
            option_id: The option_id/opportunity_id to search for
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, quote_info, message)
            quote_info contains only QuoteGuid
        """
        try:
            # Execute the stored procedure
            success, result_xml, message = self.execute_dataset(
                "spGetQuoteByOptionID",
                ["OptionID", str(option_id)]
            )
            
            if not success:
                return False, None, message
            
            # Parse the result
            result_dict = self._parse_single_row_result(result_xml)
            
            if not result_dict or not result_dict.get("QuoteGuid"):
                return False, None, f"No quote found for option_id: {option_id}"
            
            # Return just the QuoteGuid
            quote_info = {
                "QuoteGuid": result_dict.get("QuoteGuid")
            }
            
            logger.info(f"Found quote {quote_info['QuoteGuid']} for option_id {option_id}")
            return True, quote_info, "Quote lookup successful"
            
        except Exception as e:
            error_msg = f"Error looking up quote by option_id: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _parse_single_row_result(self, result_xml: str) -> Optional[Dict[str, Any]]:
        """
        Parse XML result expecting a single row of data.
        
        Args:
            result_xml: The XML result from ExecuteDataSet
            
        Returns:
            Dict containing the row data or None if no row found
        """
        try:
            if not result_xml:
                return None
            
            # Fix common XML issues - escape unescaped ampersands
            # This handles cases where data from SQL contains & characters
            # that aren't properly escaped as &amp;
            # Replace & that aren't part of existing entities
            result_xml = re.sub(r'&(?!(?:amp|lt|gt|apos|quot);)', '&amp;', result_xml)
                
            # Parse the XML
            root = ET.fromstring(result_xml)
            
            # Find the first Table element (single row result)
            table = root.find('.//Table')
            if table is None:
                return None
            
            # Convert all child elements to a dictionary
            result = {}
            for child in table:
                if child.text is not None:
                    result[child.tag] = child.text
                else:
                    result[child.tag] = None
                    
            return result if result else None
            
        except ET.ParseError as e:
            logger.error(f"XML Parse Error in single row result: {str(e)}")
            logger.debug(f"Problematic XML (first 500 chars): {result_xml[:500] if result_xml else 'None'}")
            return None
        except Exception as e:
            logger.error(f"Error parsing single row result: {str(e)}")
            return None
    
    def store_triton_transaction(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Store transaction data using spStoreTritonTransaction_WS.
        
        Args:
            payload: The Triton transaction payload
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, result_data, message)
        """
        try:
            # Execute the stored procedure
            success, result_xml, message = self.execute_dataset(
                "spStoreTritonTransaction",
                [
                    "transaction_id", payload.get("transaction_id", ""),
                    "full_payload_json", json.dumps(payload),
                    "opportunity_id", str(payload.get("opportunity_id", "")),
                    "policy_number", payload.get("policy_number", ""),
                    "insured_name", payload.get("insured_name", ""),
                    "transaction_type", payload.get("transaction_type", ""),
                    "transaction_date", payload.get("transaction_date", ""),
                    "source_system", payload.get("source_system", "triton")
                ]
            )
            
            if not success:
                return False, None, message
            
            # Parse the result
            result_dict = self._parse_single_row_result(result_xml)
            
            if result_dict:
                logger.info(f"Transaction stored: {result_dict.get('Status')} - {result_dict.get('Message')}")
                return True, result_dict, result_dict.get("Message", "Transaction stored")
            else:
                return False, None, "No result returned from stored procedure"
                
        except Exception as e:
            error_msg = f"Error storing transaction: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def get_quote_by_opportunity_id(self, opportunity_id: int) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Find quote information by opportunity_id and check if bound.
        
        Args:
            opportunity_id: The opportunity_id to search for
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, quote_info, message)
        """
        try:
            # Execute the stored procedure
            success, result_xml, message = self.execute_dataset(
                "spGetQuoteByOpportunityID",
                ["OpportunityID", str(opportunity_id)]
            )
            
            if not success:
                return False, None, message
            
            # Parse the result
            result_dict = self._parse_single_row_result(result_xml)
            
            if not result_dict:
                return True, None, f"No quote found for opportunity_id: {opportunity_id}"
            
            logger.info(f"Found quote {result_dict.get('QuoteGuid')} for opportunity_id {opportunity_id}")
            return True, result_dict, "Quote lookup successful"
            
        except Exception as e:
            error_msg = f"Error looking up quote by opportunity_id: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def check_quote_bound_status(self, quote_guid: str) -> Tuple[bool, bool, str]:
        """
        Check if a quote is already bound.
        
        Args:
            quote_guid: The GUID of the quote to check
            
        Returns:
            Tuple[bool, bool, str]: (success, is_bound, message)
        """
        try:
            # Execute the stored procedure
            success, result_xml, message = self.execute_dataset(
                "spCheckQuoteBoundStatus",
                ["QuoteGuid", quote_guid]
            )
            
            if not success:
                return False, False, message
            
            # Parse the result
            result_dict = self._parse_single_row_result(result_xml)
            
            if not result_dict:
                return False, False, "No result returned from bound status check"
            
            is_bound = result_dict.get("IsBound") == "1"
            bound_message = result_dict.get("BoundMessage", "Unknown status")
            
            logger.info(f"Quote {quote_guid} bound status: {is_bound} - {bound_message}")
            return True, is_bound, bound_message
            
        except Exception as e:
            error_msg = f"Error checking bound status: {str(e)}"
            logger.error(error_msg)
            return False, False, error_msg
    
    def get_quote_by_expiring_policy_number(self, policy_number: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Find quote information by expiring policy number for renewals.
        
        Args:
            policy_number: The expiring policy number
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, quote_info, message)
        """
        try:
            # Execute the stored procedure
            success, result_xml, message = self.execute_dataset(
                "spGetQuoteByExpiringPolicyNumber",
                ["ExpiringPolicyNumber", policy_number]
            )
            
            if not success:
                return False, None, message
            
            # Parse the result
            result_dict = self._parse_single_row_result(result_xml)
            
            if not result_dict:
                return True, None, f"No quote found for policy number: {policy_number}"
            
            logger.info(f"Found expiring quote {result_dict.get('QuoteGuid')} for policy {policy_number}")
            return True, result_dict, "Expiring quote lookup successful"
            
        except Exception as e:
            error_msg = f"Error looking up expiring policy: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
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
    
    def get_invoice_data(self, quote_guid: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Get invoice data using ryan_rptInvoice_WS stored procedure.
        
        Args:
            quote_guid: The GUID of the quote to get invoice for
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, invoice_data, message)
        """
        try:
            # Execute the stored procedure
            success, result_xml, message = self.execute_dataset(
                "ryan_rptInvoice",
                ["QuoteGuid", quote_guid]
            )
            
            if not success:
                return False, None, message
            
            # Parse the invoice XML to JSON
            invoice_data = self._parse_invoice_xml_to_json(result_xml)
            
            if invoice_data:
                logger.info(f"Successfully retrieved invoice data for quote {quote_guid}")
                return True, invoice_data, "Invoice data retrieved successfully"
            else:
                return False, None, "No invoice data found"
                
        except Exception as e:
            error_msg = f"Error getting invoice data: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _parse_invoice_xml_to_json(self, result_xml: str) -> Optional[Dict[str, Any]]:
        """
        Parse invoice XML response into structured JSON.
        
        Args:
            result_xml: The XML result from ryan_rptInvoice
            
        Returns:
            Dict containing structured invoice data or None if parsing fails
        """
        try:
            if not result_xml:
                return None
                
            # Log the raw XML for debugging (first 1000 chars)
            logger.debug(f"Raw invoice XML (first 1000 chars): {result_xml[:1000]}")
            
            # Try to clean up common XML issues
            cleaned_xml = self._clean_xml_for_parsing(result_xml)
            
            # Parse the XML
            root = ET.fromstring(cleaned_xml)
            
            # Initialize result structure
            invoice_data = {
                "invoice_info": {},
                "financial": {},
                "insured": {},
                "producer": {},
                "company": {},
                "line_items": [],
                "payment_instructions": {},
                "dates": {}
            }
            
            # Parse main invoice table (Table)
            main_table = root.find('.//Table')
            if main_table is not None:
                # Extract invoice info
                invoice_data["invoice_info"]["invoice_num"] = self._get_xml_text(main_table, "InvoiceNum")
                invoice_data["invoice_info"]["office_invoice_num"] = self._get_xml_text(main_table, "OfficeInvoiceNum")
                invoice_data["invoice_info"]["policy_number"] = self._get_xml_text(main_table, "PolicyNumber")
                invoice_data["invoice_info"]["control_no"] = self._get_xml_text(main_table, "ControlNo")
                invoice_data["invoice_info"]["policy_type"] = self._get_xml_text(main_table, "PolicyType")
                invoice_data["invoice_info"]["line_name"] = self._get_xml_text(main_table, "LineName")
                
                # Extract financial info
                invoice_data["financial"]["premium"] = self._parse_float(self._get_xml_text(main_table, "Premium"))
                invoice_data["financial"]["commission_pct"] = self._parse_float(self._get_xml_text(main_table, "CommissionPct"))
                invoice_data["financial"]["commission_amount"] = self._parse_float(self._get_xml_text(main_table, "CommissionAmount"))
                invoice_data["financial"]["net_premium"] = self._parse_float(self._get_xml_text(main_table, "NetPremium"))
                invoice_data["financial"]["net_due"] = self._parse_float(self._get_xml_text(main_table, "NetDue"))
                
                # Extract dates
                invoice_data["dates"]["effective_date"] = self._get_xml_text(main_table, "EffectiveDate")
                invoice_data["dates"]["expiration_date"] = self._get_xml_text(main_table, "ExpirationDate")
                invoice_data["dates"]["invoice_date"] = self._get_xml_text(main_table, "InvoiceDate")
                invoice_data["dates"]["due_date"] = self._get_xml_text(main_table, "DueDate")
                invoice_data["dates"]["policy_period"] = self._get_xml_text(main_table, "PolicyPeriod")
                
                # Extract insured info
                invoice_data["insured"]["name"] = self._get_xml_text(main_table, "NamedInsured")
                invoice_data["insured"]["address"] = self._get_xml_text(main_table, "InsuredNameAddress")
                invoice_data["insured"]["id"] = self._get_xml_text(main_table, "InsuredID")
                
                # Extract producer info
                invoice_data["producer"]["name"] = self._get_xml_text(main_table, "ProducerName")
                invoice_data["producer"]["address"] = self._get_xml_text(main_table, "ProducerNameAddress")
                
                # Extract company info
                invoice_data["company"]["name"] = self._get_xml_text(main_table, "CompanyName")
                invoice_data["company"]["office_name"] = self._get_xml_text(main_table, "QuotingOfficeName")
                invoice_data["company"]["office_phone"] = self._get_xml_text(main_table, "QuotingOfficePhone")
                
                # Extract payment instructions
                invoice_data["payment_instructions"]["ach_wire"] = self._get_xml_text(main_table, "AchOrWireTransfer")
                invoice_data["payment_instructions"]["check_to_lockbox"] = self._get_xml_text(main_table, "CheckToLockbox")
                invoice_data["payment_instructions"]["make_check_payable_to"] = self._get_xml_text(main_table, "MakeCheckPayableTo")
            
            # Parse line items (Table5)
            for line_item in root.findall('.//Table5'):
                item = {
                    "invoice_num": self._get_xml_text(line_item, "InvoiceNum"),
                    "description": self._get_xml_text(line_item, "Description"),
                    "effective_date": self._get_xml_text(line_item, "EffectiveDate"),
                    "due_date": self._get_xml_text(line_item, "DueDate"),
                    "premium": self._parse_float(self._get_xml_text(line_item, "Premium")),
                    "fees": self._parse_float(self._get_xml_text(line_item, "Fees")),
                    "commission": self._parse_float(self._get_xml_text(line_item, "Commission")),
                    "gross_premium": self._parse_float(self._get_xml_text(line_item, "GrossPremium")),
                    "amount_due": self._parse_float(self._get_xml_text(line_item, "AmountDue")),
                    "net_amount_due": self._parse_float(self._get_xml_text(line_item, "NetAmountDue"))
                }
                invoice_data["line_items"].append(item)
            
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error parsing invoice XML: {str(e)}")
            
            # Save problematic XML for debugging
            try:
                import os
                from datetime import datetime
                
                # Create debug directory if it doesn't exist
                debug_dir = "debug_xml"
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)
                
                # Save the raw XML
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(debug_dir, f"invoice_xml_error_{timestamp}.xml")
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(result_xml)
                
                logger.error(f"Problematic XML saved to: {filename}")
                
                # Also log the specific location of the error if available
                if hasattr(e, 'position'):
                    line, column = e.position
                    logger.error(f"XML error at line {line}, column {column}")
                    
                    # Try to show the problematic section
                    lines = result_xml.split('\n')
                    if line <= len(lines):
                        logger.error(f"Problematic line: {lines[line-1]}")
                        
            except Exception as save_error:
                logger.warning(f"Could not save debug XML: {save_error}")
            
            return None
    
    def _get_xml_text(self, element: ET.Element, tag: str) -> Optional[str]:
        """Safely get text from XML element."""
        child = element.find(tag)
        return child.text if child is not None and child.text else None
    
    def _parse_float(self, value: Optional[str]) -> Optional[float]:
        """Safely parse float from string."""
        if value:
            try:
                return float(value)
            except ValueError:
                return None
        return None
    
    def get_latest_quote_by_opportunity_id(self, opportunity_id: int) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Get the latest quote in a chain by opportunity_id.
        First finds the most recent entry in tblTritonQuoteData,
        then follows the quote chain to find the latest.
        
        Args:
            opportunity_id: The opportunity ID to search for
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, quote_info, message)
            quote_info contains QuoteGuid, ControlNo, PolicyNumber, QuoteStatusID, EndorsementNum, ChainLevel
        """
        try:
            # Execute the stored procedure
            success, result_xml, message = self.execute_dataset(
                "spGetLatestQuoteByOpportunityID",
                ["OpportunityID", str(opportunity_id)]
            )
            
            if not success:
                return False, None, message
            
            # Parse the result
            result_dict = self._parse_single_row_result(result_xml)
            
            if not result_dict or not result_dict.get("QuoteGuid"):
                return False, None, f"No quote found for opportunity_id: {opportunity_id}"
            
            logger.info(f"Found latest quote {result_dict.get('QuoteGuid')} for opportunity_id {opportunity_id} (chain level: {result_dict.get('ChainLevel', 0)})")
            return True, result_dict, "Latest quote lookup successful"
            
        except Exception as e:
            error_msg = f"Error looking up latest quote by opportunity_id: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def get_policy_premium_total(self, control_no: int) -> Tuple[bool, float, str]:
        """
        Get the total premium from all invoices for a policy.
        
        Args:
            control_no: The control number of the policy
            
        Returns:
            Tuple[bool, float, str]: (success, total_premium, message)
        """
        try:
            # Execute the stored procedure
            success, result_xml, message = self.execute_dataset(
                "spGetPolicyPremiumTotal",
                ["ControlNo", str(control_no)]
            )
            
            if not success:
                return False, 0.0, message
            
            # Parse the result
            result_dict = self._parse_single_row_result(result_xml)
            
            if not result_dict:
                return True, 0.0, "No invoices found for policy"
            
            total_premium = float(result_dict.get("TotalPremium", 0))
            invoice_count = int(result_dict.get("InvoiceCount", 0))
            
            logger.info(f"Found {invoice_count} invoices with total premium ${total_premium:,.2f} for control_no {control_no}")
            return True, total_premium, f"Found {invoice_count} invoices"
            
        except Exception as e:
            error_msg = f"Error getting policy premium total: {str(e)}"
            logger.error(error_msg)
            return False, 0.0, error_msg
    
    def get_quote_producer_contact_guid(self, quote_guid: str) -> Tuple[bool, Optional[str], str]:
        """
        Get the ProducerContactGuid from tblQuotes for a given QuoteGuid.
        
        Args:
            quote_guid: The quote GUID to look up
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, producer_contact_guid, message)
        """
        try:
            # Execute a simple query to get the ProducerContactGuid
            query = """
                SELECT ProducerContactGuid 
                FROM tblQuotes 
                WHERE QuoteGuid = @QuoteGuid
            """
            
            success, result_xml, message = self.execute_dataset(
                "ExecuteDataSet",
                ["Query", query, "QuoteGuid", quote_guid]
            )
            
            if not success:
                return False, None, message
            
            # Parse the result
            result_dict = self._parse_single_row_result(result_xml)
            
            if not result_dict:
                return False, None, f"No quote found with QuoteGuid: {quote_guid}"
            
            producer_contact_guid = result_dict.get("ProducerContactGuid")
            
            if producer_contact_guid:
                logger.info(f"Found ProducerContactGuid {producer_contact_guid} for quote {quote_guid}")
                return True, producer_contact_guid, "Producer lookup successful"
            else:
                return False, None, f"No ProducerContactGuid found for quote {quote_guid}"
                
        except Exception as e:
            error_msg = f"Error getting producer contact guid: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def change_producer(self, quote_guid: str, new_producer_contact_guid: str) -> Tuple[bool, str]:
        """
        Change the producer for a quote using spChangeProducer_Triton.
        
        Args:
            quote_guid: The quote to update
            new_producer_contact_guid: The new producer contact GUID
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            logger.info(f"Changing producer for quote {quote_guid} to {new_producer_contact_guid}")
            
            # Execute the stored procedure - IMS will add the _WS suffix
            success, result, message = self.execute_command(
                "spChangeProducer_Triton",
                [
                    "QuoteGuid", quote_guid,
                    "NewProducerContactGuid", new_producer_contact_guid
                ]
            )
            
            if success:
                logger.info(f"Successfully changed producer for quote {quote_guid}")
                return True, "Producer changed successfully"
            else:
                logger.error(f"Failed to change producer: {message}")
                return False, message
                
        except Exception as e:
            error_msg = f"Error changing producer: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _clean_xml_for_parsing(self, xml_string: str) -> str:
        """
        Clean XML string to handle common issues that cause parsing errors.
        
        Args:
            xml_string: Raw XML string
            
        Returns:
            Cleaned XML string
        """
        try:
            # Remove any BOM (Byte Order Mark)
            if xml_string.startswith('\ufeff'):
                xml_string = xml_string[1:]
            
            # Replace common problematic characters
            # Replace control characters except tab, newline, carriage return
            import re
            xml_string = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', xml_string)
            
            # Handle unescaped ampersands that aren't part of entities
            xml_string = re.sub(r'&(?!(?:amp|lt|gt|apos|quot);)', '&amp;', xml_string)
            
            # Remove any content before the first '<'
            first_tag = xml_string.find('<')
            if first_tag > 0:
                xml_string = xml_string[first_tag:]
            
            # Log if we made any changes
            if xml_string != xml_string:
                logger.debug("XML was cleaned for parsing")
            
            return xml_string
            
        except Exception as e:
            logger.warning(f"Error cleaning XML: {str(e)}")
            # Return original if cleaning fails
            return xml_string


# Singleton instance
_data_access_service = None


def get_data_access_service() -> IMSDataAccessService:
    """Get singleton instance of data access service."""
    global _data_access_service
    if _data_access_service is None:
        _data_access_service = IMSDataAccessService()
    return _data_access_service