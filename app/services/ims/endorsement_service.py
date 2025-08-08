import logging
import xml.etree.ElementTree as ET
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from app.services.ims.base_service import BaseIMSService
from app.services.ims.auth_service import get_auth_service
from app.services.ims.data_access_service import get_data_access_service
from config import IMS_CONFIG

logger = logging.getLogger(__name__)


class IMSEndorsementService(BaseIMSService):
    """Service for processing policy endorsements in IMS."""
    
    def __init__(self):
        super().__init__()
        self.base_url = IMS_CONFIG["base_url"]
        self.services_env = IMS_CONFIG.get("environments", {}).get("services", "/ims_one")
        self.endpoint = IMS_CONFIG["endpoints"]["quote_functions"]
        self.timeout = IMS_CONFIG["timeout"]
        self.auth_service = get_auth_service()
        self.data_service = get_data_access_service()
        self._last_soap_request = None
        self._last_soap_response = None
        self._last_url = None
    
    def endorse_policy_by_opportunity_id(
        self, 
        opportunity_id: int,
        endorsement_premium: float,
        effective_date: str,
        comment: str = "Midterm Endorsement",
        bind_endorsement: bool = True,
        terrorism_premium: float = 0,
        endorsement_calc_type: str = "F"
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Create a policy endorsement using opportunity ID via stored procedure.
        
        Args:
            opportunity_id: The opportunity ID to endorse
            endorsement_premium: The new premium for the endorsement
            effective_date: The effective date of the endorsement (MM/DD/YYYY format)
            comment: Description of the endorsement
            bind_endorsement: Whether to immediately bind the endorsement (default: True)
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (success, result_data, message)
        """
        try:
            # Get user guid from auth service
            user_guid = self.auth_service.user_guid
            
            if not user_guid:
                return False, {}, "Authentication required - no user GUID available"
            
            logger.info(f"Creating endorsement for opportunity ID: {opportunity_id}")
            logger.info(f"Endorsement details - Premium: ${endorsement_premium}, Effective: {effective_date}")
            
            # Prepare parameters for stored procedure (as alternating name/value pairs)
            params = [
                "OpportunityID", str(opportunity_id),
                "UserGuid", str(user_guid),
                "TransEffDate", effective_date,
                "EndorsementPremium", str(endorsement_premium),
                "TerrorismPremium", str(terrorism_premium),
                "Comment", comment,
                "EndorsementCalcType", endorsement_calc_type,
                "BindEndorsement", "1" if bind_endorsement else "0"
            ]
            
            # Call the stored procedure (IMS adds _WS suffix automatically)
            success, result_xml, message = self.data_service.execute_dataset(
                procedure_name="Triton_EndorsePolicy",
                parameters=params
            )
            
            if not success:
                return False, {}, f"Failed to execute endorsement procedure: {message}"
            
            # Parse the result
            result_data = self._parse_endorsement_procedure_result(result_xml)
            
            if result_data and result_data.get("Result") == "1":
                logger.info(f"Successfully created endorsement. QuoteGuid: {result_data.get('EndorsementQuoteGuid')}")
                return True, result_data, result_data.get("Message", "Endorsement created successfully")
            else:
                error_msg = result_data.get("Message", "Unknown error") if result_data else "No result returned"
                logger.error(f"Failed to create endorsement: {error_msg}")
                return False, result_data or {}, error_msg
                
        except Exception as e:
            error_msg = f"Error creating endorsement: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, {}, error_msg
    
    def endorse_policy_by_quote_guid(
        self,
        quote_guid: str,
        endorsement_premium: float,
        effective_date: str,
        comment: str = "Midterm Endorsement",
        bind_endorsement: bool = True
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Create a policy endorsement using quote GUID via stored procedure.
        
        Args:
            quote_guid: The GUID of the quote to endorse
            endorsement_premium: The new premium for the endorsement
            effective_date: The effective date of the endorsement (MM/DD/YYYY format)
            comment: Description of the endorsement
            bind_endorsement: Whether to immediately bind the endorsement (default: True)
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (success, result_data, message)
        """
        try:
            # Get user guid from auth service
            user_guid = self.auth_service.user_guid
            
            if not user_guid:
                return False, {}, "Authentication required - no user GUID available"
            
            logger.info(f"Creating endorsement for quote: {quote_guid}")
            
            # Prepare parameters for stored procedure (as alternating name/value pairs)
            params = [
                "QuoteGuid", str(quote_guid),
                "UserGuid", str(user_guid),
                "TransEffDate", effective_date,
                "EndorsementPremium", str(endorsement_premium),
                "Comment", comment,
                "BindEndorsement", "1" if bind_endorsement else "0"
            ]
            
            # Call the stored procedure (IMS adds _WS suffix automatically)
            success, result_xml, message = self.data_service.execute_dataset(
                procedure_name="Triton_EndorsePolicy",
                parameters=params
            )
            
            if not success:
                return False, {}, f"Failed to execute endorsement procedure: {message}"
            
            # Parse the result
            result_data = self._parse_endorsement_procedure_result(result_xml)
            
            if result_data and result_data.get("Result") == "1":
                logger.info(f"Successfully created endorsement. New QuoteGuid: {result_data.get('EndorsementQuoteGuid')}")
                return True, result_data, result_data.get("Message", "Endorsement created successfully")
            else:
                error_msg = result_data.get("Message", "Unknown error") if result_data else "No result returned"
                logger.error(f"Failed to create endorsement: {error_msg}")
                return False, result_data or {}, error_msg
                
        except Exception as e:
            error_msg = f"Error creating endorsement: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, {}, error_msg
    
    def _parse_endorsement_procedure_result(self, result_xml: str) -> Optional[Dict[str, Any]]:
        """
        Parse the result from Triton_EndorsePolicy_WS stored procedure.
        
        Args:
            result_xml: The XML result from ExecuteDataSet
            
        Returns:
            Dict containing the result data or None if parsing fails
        """
        try:
            if not result_xml:
                return None
                
            # Parse the XML
            root = ET.fromstring(result_xml)
            
            # Check all Table elements - look for Table1 first (common for endorsements)
            tables = root.findall('.//Table1')
            if not tables:
                tables = root.findall('.//Table2')  # Then Table2
            if not tables:
                tables = root.findall('.//Table')  # Fall back to Table
            
            for table in tables:
                # Try to extract structured fields
                result_data = {}
                
                # Extract Result (0 or 1)
                result_elem = table.find('Result')
                if result_elem is not None and result_elem.text:
                    result_data['Result'] = result_elem.text.strip()
                
                # Extract Message
                message_elem = table.find('Message')
                if message_elem is not None and message_elem.text:
                    result_data['Message'] = message_elem.text.strip()
                
                # Extract EndorsementQuoteGuid (the new quote created)
                endorsement_guid_elem = table.find('EndorsementQuoteGuid')
                if endorsement_guid_elem is not None and endorsement_guid_elem.text:
                    result_data['EndorsementQuoteGuid'] = endorsement_guid_elem.text.strip()
                
                # Extract OriginalQuoteGuid
                original_guid_elem = table.find('OriginalQuoteGuid')
                if original_guid_elem is not None and original_guid_elem.text:
                    result_data['OriginalQuoteGuid'] = original_guid_elem.text.strip()
                
                # Extract PolicyNumber
                policy_num_elem = table.find('PolicyNumber')
                if policy_num_elem is not None and policy_num_elem.text:
                    result_data['PolicyNumber'] = policy_num_elem.text.strip()
                
                # Extract EndorsementNumber
                endorsement_num_elem = table.find('EndorsementNumber')
                if endorsement_num_elem is not None and endorsement_num_elem.text:
                    result_data['EndorsementNumber'] = endorsement_num_elem.text.strip()
                
                # Extract QuoteOptionGuid if available
                option_guid_elem = table.find('QuoteOptionGuid')
                if option_guid_elem is not None and option_guid_elem.text:
                    result_data['QuoteOptionGuid'] = option_guid_elem.text.strip()
                
                # Extract InvoiceNumber if endorsement was bound
                invoice_elem = table.find('InvoiceNumber')
                if invoice_elem is not None and invoice_elem.text:
                    result_data['InvoiceNumber'] = invoice_elem.text.strip()
                
                # If we got structured data with Result field, return it
                if 'Result' in result_data:
                    logger.debug(f"Parsed structured endorsement result: {result_data}")
                    return result_data
            
            # If no recognized format, log what we found
            logger.warning(f"Unrecognized endorsement result format. XML: {result_xml}")
            return None
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse endorsement procedure result XML: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing endorsement procedure result: {str(e)}")
            return None


# Singleton instance
_endorsement_service = None


def get_endorsement_service() -> IMSEndorsementService:
    """Get singleton instance of endorsement service."""
    global _endorsement_service
    if _endorsement_service is None:
        _endorsement_service = IMSEndorsementService()
    return _endorsement_service