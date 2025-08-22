import logging
import xml.etree.ElementTree as ET
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from app.services.ims.base_service import BaseIMSService
from app.services.ims.auth_service import get_auth_service
from app.services.ims.data_access_service import get_data_access_service
from config import IMS_CONFIG

logger = logging.getLogger(__name__)


class IMSCancellationService(BaseIMSService):
    """Service for processing policy cancellations in IMS."""
    
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
    
    def cancel_policy_by_opportunity_id(
        self, 
        opportunity_id: int,
        cancellation_type: str = "flat",  # "flat" or "earned"
        effective_date: str = None,
        reason_code: int = None,
        comment: str = "Policy Cancellation",
        refund_amount: float = None,
        policy_effective_date: str = None,  # For flat cancel detection
        market_segment_code: str = None,    # For auto-apply fees
        policy_fee: float = None            # Policy fee to apply as negative
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Cancel a policy using opportunity ID via stored procedure.
        
        Args:
            opportunity_id: The opportunity ID to cancel
            cancellation_type: Type of cancellation ("flat" for full refund, "earned" for pro-rata)
            effective_date: The effective date of the cancellation (MM/DD/YYYY format)
            reason_code: The cancellation reason code (required)
            comment: Description of the cancellation
            refund_amount: Amount to refund (for flat cancellations)
            
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
            
            # Default reason code if not provided (typically there's a default cancellation reason)
            if reason_code is None:
                reason_code = 30  # Common default for "Insured Request"
            
            logger.info(f"Cancelling policy for opportunity ID: {opportunity_id}")
            logger.info(f"Cancellation details - Type: {cancellation_type}, Effective: {effective_date}, Reason: {reason_code}")
            
            # Prepare parameters for stored procedure (as alternating name/value pairs)
            params = [
                "OpportunityID", str(opportunity_id),
                "CancellationDate", effective_date,
                "ReturnPremium", str(refund_amount if refund_amount is not None else 0),
                "CancellationReason", comment,
                "UserGuid", str(user_guid)
            ]
            
            # Add optional parameters for fee application
            if policy_effective_date:
                params.extend(["PolicyEffectiveDate", policy_effective_date])
            if market_segment_code:
                params.extend(["MarketSegmentCode", market_segment_code])
            if policy_fee is not None:
                params.extend(["PolicyFee", str(policy_fee)])
            
            # Call the stored procedure (IMS adds _WS suffix automatically)
            # Using ProcessFlatCancellation wrapper for consistency with endorsements
            success, result_xml, message = self.data_service.execute_dataset(
                procedure_name="Triton_ProcessFlatCancellation",
                parameters=params
            )
            
            if not success:
                return False, {}, f"Failed to execute cancellation procedure: {message}"
            
            # Parse the result
            result_data = self._parse_cancellation_procedure_result(result_xml)
            
            # Log the raw result for debugging
            if not result_data:
                logger.error(f"Failed to parse cancellation result. Raw XML: {result_xml[:500] if result_xml else 'None'}")
            else:
                logger.debug(f"Parsed cancellation result: {result_data}")
            
            # Check for success - Result could be 1 (int), "1" (string), or "Success" (from base procedure)
            result_str = str(result_data.get("Result", "")).lower() if result_data else ""
            if result_data and (result_str == "1" or result_str == "success"):
                cancellation_guid = result_data.get('CancellationQuoteGuid') or result_data.get('NewQuoteGuid')
                logger.info(f"Successfully cancelled policy. CancellationQuoteGuid: {cancellation_guid}")
                return True, result_data, result_data.get("Message", result_data.get("Instructions", "Policy cancelled successfully"))
            else:
                error_msg = result_data.get("Message", "Unknown error") if result_data else "No result returned"
                logger.error(f"Failed to cancel policy: {error_msg}")
                if result_data:
                    logger.error(f"Full result data: {result_data}")
                return False, result_data or {}, error_msg
                
        except Exception as e:
            error_msg = f"Error cancelling policy: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, {}, error_msg
    
    def cancel_policy_by_quote_guid(
        self,
        quote_guid: str,
        cancellation_type: str = "flat",
        effective_date: str = None,
        reason_code: int = None,
        comment: str = "Policy Cancellation",
        refund_amount: float = None
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Cancel a policy using quote GUID via stored procedure.
        
        Args:
            quote_guid: The GUID of the quote to cancel
            cancellation_type: Type of cancellation ("flat" for full refund, "earned" for pro-rata)
            effective_date: The effective date of the cancellation (MM/DD/YYYY format)
            reason_code: The cancellation reason code (required)
            comment: Description of the cancellation
            refund_amount: Amount to refund (for flat cancellations)
            
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
            
            # Default reason code if not provided
            if reason_code is None:
                reason_code = 30  # Common default for "Insured Request"
            
            logger.info(f"Cancelling policy for quote: {quote_guid}")
            
            # When we have a quote_guid directly, call the base ProcessFlatCancellation
            # Prepare parameters for stored procedure (as alternating name/value pairs)
            params = [
                "OriginalQuoteGuid", str(quote_guid),
                "CancellationDate", effective_date,
                "ReturnPremium", str(refund_amount if refund_amount is not None else 0),
                "CancellationReason", comment,
                "UserGuid", str(user_guid)
            ]
            
            # Call the base stored procedure directly since we have the QuoteGuid
            # (IMS adds _WS suffix automatically)
            success, result_xml, message = self.data_service.execute_dataset(
                procedure_name="ProcessFlatCancellation",
                parameters=params
            )
            
            if not success:
                return False, {}, f"Failed to execute cancellation procedure: {message}"
            
            # Parse the result
            result_data = self._parse_cancellation_procedure_result(result_xml)
            
            # Log the raw result for debugging
            if not result_data:
                logger.error(f"Failed to parse cancellation result. Raw XML: {result_xml[:500] if result_xml else 'None'}")
            else:
                logger.debug(f"Parsed cancellation result: {result_data}")
            
            # Check for success - Result could be 1 (int), "1" (string), or "Success" (from base procedure)
            result_str = str(result_data.get("Result", "")).lower() if result_data else ""
            if result_data and (result_str == "1" or result_str == "success"):
                cancellation_guid = result_data.get('CancellationQuoteGuid') or result_data.get('NewQuoteGuid')
                logger.info(f"Successfully cancelled policy. CancellationQuoteGuid: {cancellation_guid}")
                return True, result_data, result_data.get("Message", result_data.get("Instructions", "Policy cancelled successfully"))
            else:
                error_msg = result_data.get("Message", "Unknown error") if result_data else "No result returned"
                logger.error(f"Failed to cancel policy: {error_msg}")
                return False, result_data or {}, error_msg
                
        except Exception as e:
            error_msg = f"Error cancelling policy: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, {}, error_msg
    
    def _parse_cancellation_procedure_result(self, result_xml: str) -> Optional[Dict[str, Any]]:
        """
        Parse the result from Triton_CancelPolicy_WS stored procedure.
        
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
            
            # Check Table3 first (most complete for Triton cancellations)
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
                
                # Extract CancellationQuoteGuid or NewQuoteGuid (the new quote created for cancellation)
                cancellation_guid_elem = table.find('CancellationQuoteGuid')
                if cancellation_guid_elem is not None and cancellation_guid_elem.text:
                    result_data['CancellationQuoteGuid'] = cancellation_guid_elem.text.strip()
                else:
                    # Check for NewQuoteGuid (from Triton_ProcessFlatCancellation_WS)
                    new_guid_elem = table.find('NewQuoteGuid')
                    if new_guid_elem is not None and new_guid_elem.text:
                        result_data['CancellationQuoteGuid'] = new_guid_elem.text.strip()
                        result_data['NewQuoteGuid'] = new_guid_elem.text.strip()
                
                # Extract NewQuoteOptionGuid (from Triton_ProcessFlatCancellation_WS)
                option_guid_elem = table.find('NewQuoteOptionGuid')
                if option_guid_elem is not None and option_guid_elem.text:
                    result_data['NewQuoteOptionGuid'] = option_guid_elem.text.strip()
                
                # Extract QuoteOptionGuid (alternative name)
                if 'NewQuoteOptionGuid' not in result_data:
                    option_guid_elem = table.find('QuoteOptionGuid')
                    if option_guid_elem is not None and option_guid_elem.text:
                        result_data['QuoteOptionGuid'] = option_guid_elem.text.strip()
                
                # Extract OriginalQuoteGuid
                original_guid_elem = table.find('OriginalQuoteGuid')
                if original_guid_elem is not None and original_guid_elem.text:
                    result_data['OriginalQuoteGuid'] = original_guid_elem.text.strip()
                
                # Extract PolicyNumber
                policy_num_elem = table.find('PolicyNumber')
                if policy_num_elem is not None and policy_num_elem.text:
                    result_data['PolicyNumber'] = policy_num_elem.text.strip()
                
                # Extract RefundAmount if available (check both RefundAmount and ReturnPremium)
                refund_elem = table.find('RefundAmount')
                if refund_elem is not None and refund_elem.text:
                    result_data['RefundAmount'] = refund_elem.text.strip()
                else:
                    # Also check for ReturnPremium (from Triton_ProcessFlatCancellation_WS)
                    return_elem = table.find('ReturnPremium')
                    if return_elem is not None and return_elem.text:
                        result_data['RefundAmount'] = return_elem.text.strip()
                        result_data['ReturnPremium'] = return_elem.text.strip()
                
                # Extract QuoteOptionGuid if available
                option_guid_elem = table.find('QuoteOptionGuid')
                if option_guid_elem is not None and option_guid_elem.text:
                    result_data['QuoteOptionGuid'] = option_guid_elem.text.strip()
                
                # Score this result based on completeness
                score = 0
                if 'Result' in result_data:
                    score += 10
                if 'NewQuoteGuid' in result_data or 'CancellationQuoteGuid' in result_data:
                    score += 5
                if 'NewQuoteOptionGuid' in result_data or 'QuoteOptionGuid' in result_data:
                    score += 5
                if 'Message' in result_data:
                    score += 2
                if 'ReturnPremium' in result_data or 'RefundAmount' in result_data:
                    score += 3
                
                # Prioritize Table3 and Table2 for Triton responses
                if table_name == 'Table3':
                    score += 20
                elif table_name == 'Table2':
                    score += 10
                
                # Keep the best result
                if score > best_score:
                    best_score = score
                    best_result = result_data
                    logger.debug(f"Found {table_name} with score {score}: {result_data}")
            
            # Return the best result we found
            if best_result:
                logger.debug(f"Selected best cancellation result (score {best_score}): {best_result}")
                return best_result
            
            # If no recognized format, log what we found
            logger.warning(f"Unrecognized cancellation result format. XML: {result_xml}")
            return None
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse cancellation procedure result XML: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing cancellation procedure result: {str(e)}")
            return None


# Singleton instance
_cancellation_service = None


def get_cancellation_service() -> IMSCancellationService:
    """Get singleton instance of cancellation service."""
    global _cancellation_service
    if _cancellation_service is None:
        _cancellation_service = IMSCancellationService()
    return _cancellation_service