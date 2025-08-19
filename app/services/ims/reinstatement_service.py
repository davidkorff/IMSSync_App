import logging
import xml.etree.ElementTree as ET
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from app.services.ims.base_service import BaseIMSService
from app.services.ims.auth_service import get_auth_service
from app.services.ims.data_access_service import get_data_access_service
from config import IMS_CONFIG

logger = logging.getLogger(__name__)


class IMSReinstatementService(BaseIMSService):
    """Service for processing policy reinstatements in IMS."""
    
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
    
    def reinstate_policy_by_opportunity_id(
        self, 
        opportunity_id: int,
        reinstatement_premium: float,
        effective_date: str = None,
        comment: str = "Policy Reinstatement"
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Reinstate a cancelled policy using opportunity ID via stored procedure.
        
        Args:
            opportunity_id: The opportunity ID to reinstate
            reinstatement_premium: The premium for the reinstated policy
            effective_date: The effective date of the reinstatement (MM/DD/YYYY format)
            comment: Description of the reinstatement
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (success, result_data, message)
        """
        try:
            # Get user guid from auth service
            user_guid = self.auth_service.user_guid
            
            if not user_guid:
                return False, {}, "Authentication required - no user GUID available"
            
            # Default effective date to today if not provided
            if not effective_date:
                effective_date = datetime.now().strftime("%m/%d/%Y")
            
            logger.info(f"Reinstating policy for opportunity ID: {opportunity_id}")
            logger.info(f"Reinstatement details - Premium: ${reinstatement_premium:,.2f}, Effective: {effective_date}")
            
            # Prepare parameters for stored procedure (as alternating name/value pairs)
            params = [
                "OpportunityID", str(opportunity_id),
                "ReinstatementPremium", str(reinstatement_premium),
                "ReinstatementEffectiveDate", effective_date,
                "ReinstatementComment", comment,
                "UserGuid", str(user_guid)
            ]
            
            # Call the stored procedure (IMS adds _WS suffix automatically)
            success, result_xml, message = self.data_service.execute_dataset(
                procedure_name="Triton_ProcessFlatReinstatement",
                parameters=params
            )
            
            if not success:
                return False, {}, f"Failed to execute reinstatement procedure: {message}"
            
            # Parse the result
            result_data = self._parse_reinstatement_procedure_result(result_xml)
            
            if result_data and result_data.get("Result") == "1":
                logger.info(f"Successfully reinstated policy. NewQuoteGuid: {result_data.get('NewQuoteGuid')}")
                return True, result_data, result_data.get("Message", "Policy reinstated successfully")
            else:
                error_msg = result_data.get("Message", "Unknown error") if result_data else "No result returned"
                logger.error(f"Failed to reinstate policy: {error_msg}")
                return False, result_data or {}, error_msg
                
        except Exception as e:
            error_msg = f"Error reinstating policy: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, {}, error_msg
    
    def reinstate_policy_by_cancelled_quote_guid(
        self,
        cancelled_quote_guid: str,
        reinstatement_premium: float,
        effective_date: str = None,
        comment: str = "Policy Reinstatement"
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Reinstate a cancelled policy using the cancellation quote GUID via stored procedure.
        
        Args:
            cancelled_quote_guid: The GUID of the cancelled quote to reinstate
            reinstatement_premium: The premium for the reinstated policy
            effective_date: The effective date of the reinstatement (MM/DD/YYYY format)
            comment: Description of the reinstatement
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (success, result_data, message)
        """
        try:
            # Get user guid from auth service
            user_guid = self.auth_service.user_guid
            
            if not user_guid:
                return False, {}, "Authentication required - no user GUID available"
            
            # Default effective date to today if not provided
            if not effective_date:
                effective_date = datetime.now().strftime("%m/%d/%Y")
            
            logger.info(f"Reinstating cancelled policy quote: {cancelled_quote_guid}")
            logger.info(f"Reinstatement details - Premium: ${reinstatement_premium:,.2f}, Effective: {effective_date}")
            
            # Prepare parameters for stored procedure (as alternating name/value pairs)
            params = [
                "CancelledQuoteGuid", str(cancelled_quote_guid),
                "ReinstatementPremium", str(reinstatement_premium),
                "ReinstatementEffectiveDate", effective_date,
                "ReinstatementComment", comment,
                "UserGuid", str(user_guid)
            ]
            
            # Call the stored procedure (IMS adds _WS suffix automatically)
            success, result_xml, message = self.data_service.execute_dataset(
                procedure_name="Triton_ProcessFlatReinstatement",
                parameters=params
            )
            
            if not success:
                return False, {}, f"Failed to execute reinstatement procedure: {message}"
            
            # Parse the result
            result_data = self._parse_reinstatement_procedure_result(result_xml)
            
            if result_data and result_data.get("Result") == "1":
                logger.info(f"Successfully reinstated policy. NewQuoteGuid: {result_data.get('NewQuoteGuid')}")
                return True, result_data, result_data.get("Message", "Policy reinstated successfully")
            else:
                error_msg = result_data.get("Message", "Unknown error") if result_data else "No result returned"
                logger.error(f"Failed to reinstate policy: {error_msg}")
                return False, result_data or {}, error_msg
                
        except Exception as e:
            error_msg = f"Error reinstating policy: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, {}, error_msg
    
    def _parse_reinstatement_procedure_result(self, result_xml: str) -> Optional[Dict[str, Any]]:
        """
        Parse the result from Triton_ProcessFlatReinstatement_WS stored procedure.
        
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
            
            # Check all Table elements - look for Table1 first (common for reinstatements)
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
                
                # Extract NewQuoteGuid (the new quote created for reinstatement)
                new_guid_elem = table.find('NewQuoteGuid')
                if new_guid_elem is not None and new_guid_elem.text:
                    result_data['NewQuoteGuid'] = new_guid_elem.text.strip()
                
                # Extract QuoteOptionGuid
                option_guid_elem = table.find('QuoteOptionGuid')
                if option_guid_elem is not None and option_guid_elem.text:
                    result_data['QuoteOptionGuid'] = option_guid_elem.text.strip()
                
                # Extract OriginalQuoteGuid
                original_guid_elem = table.find('OriginalQuoteGuid')
                if original_guid_elem is not None and original_guid_elem.text:
                    result_data['OriginalQuoteGuid'] = original_guid_elem.text.strip()
                
                # Extract CancellationQuoteGuid
                cancellation_guid_elem = table.find('CancellationQuoteGuid')
                if cancellation_guid_elem is not None and cancellation_guid_elem.text:
                    result_data['CancellationQuoteGuid'] = cancellation_guid_elem.text.strip()
                
                # Extract PolicyNumber
                policy_num_elem = table.find('PolicyNumber')
                if policy_num_elem is not None and policy_num_elem.text:
                    result_data['PolicyNumber'] = policy_num_elem.text.strip()
                
                # Extract ReinstatementNumber
                reinstatement_num_elem = table.find('ReinstatementNumber')
                if reinstatement_num_elem is not None and reinstatement_num_elem.text:
                    result_data['ReinstatementNumber'] = reinstatement_num_elem.text.strip()
                
                # Extract ReinstatementPremium
                reinstatement_premium_elem = table.find('ReinstatementPremium')
                if reinstatement_premium_elem is not None and reinstatement_premium_elem.text:
                    result_data['ReinstatementPremium'] = reinstatement_premium_elem.text.strip()
                
                # Extract CancellationRefund
                cancellation_refund_elem = table.find('CancellationRefund')
                if cancellation_refund_elem is not None and cancellation_refund_elem.text:
                    result_data['CancellationRefund'] = cancellation_refund_elem.text.strip()
                
                # Extract NetPremiumChange
                net_change_elem = table.find('NetPremiumChange')
                if net_change_elem is not None and net_change_elem.text:
                    result_data['NetPremiumChange'] = net_change_elem.text.strip()
                
                # If we got structured data with Result field, return it
                if 'Result' in result_data:
                    logger.debug(f"Parsed structured reinstatement result: {result_data}")
                    return result_data
            
            # If no recognized format, log what we found
            logger.warning(f"Unrecognized reinstatement result format. XML: {result_xml}")
            return None
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse reinstatement procedure result XML: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing reinstatement procedure result: {str(e)}")
            return None


# Singleton instance
_reinstatement_service = None


def get_reinstatement_service() -> IMSReinstatementService:
    """Get singleton instance of reinstatement service."""
    global _reinstatement_service
    if _reinstatement_service is None:
        _reinstatement_service = IMSReinstatementService()
    return _reinstatement_service