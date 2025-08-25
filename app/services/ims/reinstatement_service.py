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
            # Note: Triton_ProcessFlatReinstatement_WS only takes 3 parameters
            # It gets the premium and date from the database automatically
            params = [
                "OpportunityID", str(opportunity_id),
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
        Reinstate a cancelled policy using the cancellation quote GUID.
        
        Note: The Triton_ProcessFlatReinstatement_WS procedure only accepts OpportunityID,
        so this method is currently not supported by the wrapper procedure.
        
        Args:
            cancelled_quote_guid: The GUID of the cancelled quote to reinstate
            reinstatement_premium: The premium for the reinstated policy
            effective_date: The effective date of the reinstatement (MM/DD/YYYY format)
            comment: Description of the reinstatement
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (success, result_data, message)
        """
        try:
            # The Triton wrapper doesn't support CancelledQuoteGuid parameter
            # Would need to look up the opportunity_id from the quote first
            logger.warning(f"reinstate_policy_by_cancelled_quote_guid not fully implemented for wrapper procedure")
            logger.warning(f"Triton_ProcessFlatReinstatement_WS only accepts OpportunityID parameter")
            
            # For now, return an error indicating this method isn't supported
            return False, {}, "This method requires OpportunityID. Use reinstate_policy_by_opportunity_id instead."
                
        except Exception as e:
            error_msg = f"Error reinstating policy by cancelled quote guid: {str(e)}"
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
            
            # Check all Table elements - collect all tables with different names
            all_results = []
            
            # Check Table3 first (most complete for Triton responses)
            for table in root.findall('.//Table3'):
                all_results.append(('Table3', table))
            # Then Table2
            for table in root.findall('.//Table2'):
                all_results.append(('Table2', table))
            # Then Table1
            for table in root.findall('.//Table1'):
                all_results.append(('Table1', table))
            # Finally plain Table
            for table in root.findall('.//Table'):
                all_results.append(('Table', table))
            
            best_result = None
            best_score = 0
            
            for table_name, table in all_results:
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
                
                # Extract QuoteOptionGuid or NewQuoteOptionGuid (stored procedure returns it as NewQuoteOptionGuid)
                option_guid_elem = table.find('NewQuoteOptionGuid')
                if option_guid_elem is not None and option_guid_elem.text:
                    result_data['QuoteOptionGuid'] = option_guid_elem.text.strip()
                    result_data['NewQuoteOptionGuid'] = option_guid_elem.text.strip()
                else:
                    # Fallback to check for QuoteOptionGuid (alternative name)
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
                
                # Extract ControlNo
                control_no_elem = table.find('ControlNo')
                if control_no_elem is not None and control_no_elem.text:
                    result_data['ControlNo'] = control_no_elem.text.strip()
                
                # Extract ReinstatementNumber
                reinstatement_num_elem = table.find('ReinstatementNumber')
                if reinstatement_num_elem is not None and reinstatement_num_elem.text:
                    result_data['ReinstatementNumber'] = reinstatement_num_elem.text.strip()
                
                # Extract ReinstatementPremium
                reinstatement_premium_elem = table.find('ReinstatementPremium')
                if reinstatement_premium_elem is not None and reinstatement_premium_elem.text:
                    result_data['ReinstatementPremium'] = reinstatement_premium_elem.text.strip()
                
                # Extract ReinstatementEffectiveDate
                reinstatement_date_elem = table.find('ReinstatementEffectiveDate')
                if reinstatement_date_elem is not None and reinstatement_date_elem.text:
                    result_data['ReinstatementEffectiveDate'] = reinstatement_date_elem.text.strip()
                
                # Extract CancellationRefund
                cancellation_refund_elem = table.find('CancellationRefund')
                if cancellation_refund_elem is not None and cancellation_refund_elem.text:
                    result_data['CancellationRefund'] = cancellation_refund_elem.text.strip()
                
                # Extract NetPremiumChange
                net_change_elem = table.find('NetPremiumChange')
                if net_change_elem is not None and net_change_elem.text:
                    result_data['NetPremiumChange'] = net_change_elem.text.strip()
                
                # Score this result based on completeness
                score = 0
                if 'Result' in result_data:
                    score += 10
                if 'NewQuoteGuid' in result_data:
                    score += 5
                if 'NewQuoteOptionGuid' in result_data or 'QuoteOptionGuid' in result_data:
                    score += 5
                if 'Message' in result_data:
                    score += 2
                if 'ReinstatementPremium' in result_data:
                    score += 3
                
                # Prioritize Table3 and Table2 for Triton responses
                if table_name == 'Table3':
                    score += 20
                elif table_name == 'Table2':
                    score += 10
                elif table_name == 'Table1':
                    score += 5
                
                # Keep the best result
                if score > best_score:
                    best_score = score
                    best_result = result_data
                    logger.debug(f"Found {table_name} with score {score}: {result_data}")
            
            # Return the best result we found
            if best_result:
                logger.debug(f"Selected best reinstatement result (score {best_score}): {best_result}")
                return best_result
            
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