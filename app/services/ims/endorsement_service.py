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
    
    def create_flat_endorsement_triton(
        self,
        opportunity_id: int,
        endorsement_premium: float,
        effective_date: str,
        comment: str = "Midterm Endorsement",
        user_guid: Optional[str] = None,
        midterm_endt_id: Optional[int] = None,
        producer_email: Optional[str] = None,
        producer_name: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Create an endorsement using Triton_ProcessFlatEndorsement wrapper procedure.
        This wrapper calculates the total premium and calls the base ProcessFlatEndorsement.
        
        Args:
            opportunity_id: The opportunity ID for the policy
            endorsement_premium: The CHANGE in premium (can be positive or negative)
            effective_date: The effective date of the endorsement (MM/DD/YYYY format)
            comment: Description of the endorsement
            user_guid: Optional user GUID for the endorsement
            midterm_endt_id: Optional midterm endorsement ID to check for duplicates
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (success, result_data, message)
            result_data contains NewQuoteGuid, ControlNo, ExistingPremium, TotalPremium, etc.
        """
        try:
            # Get user guid from auth service if not provided
            if not user_guid:
                user_guid = self.auth_service.user_guid
            
            logger.info(f"Creating endorsement for opportunity_id: {opportunity_id}")
            logger.info(f"Endorsement premium change: ${endorsement_premium:,.2f}, Effective: {effective_date}")
            if midterm_endt_id:
                logger.info(f"Checking for duplicate with midterm_endt_id: {midterm_endt_id}")
            
            # Prepare parameters for the wrapper stored procedure
            params = [
                "OpportunityID", str(opportunity_id),
                "EndorsementPremium", str(endorsement_premium),
                "EndorsementEffectiveDate", effective_date,
                "EndorsementComment", comment
            ]
            
            # Add user guid if available
            if user_guid:
                params.extend(["UserGuid", str(user_guid)])
            
            # Add midterm_endt_id for duplicate check
            if midterm_endt_id:
                params.extend(["MidtermEndtID", str(midterm_endt_id)])
                
            # Add producer parameters for validation
            if producer_email:
                params.extend(["ProducerEmail", producer_email])
                
            if producer_name:
                params.extend(["ProducerName", producer_name])
            
            # Call the wrapper procedure (which calculates total and calls base procedure)
            success, result_xml, message = self.data_service.execute_dataset(
                procedure_name="Triton_ProcessFlatEndorsement",
                parameters=params
            )
            
            if not success:
                return False, {}, f"Failed to execute Triton_ProcessFlatEndorsement: {message}"
            
            # Parse the result
            result_data = self._parse_triton_endorsement_result(result_xml)
            
            # Log the raw XML if debug is needed
            if not result_data:
                logger.error(f"Failed to parse result. Raw XML: {result_xml[:500] if result_xml else 'None'}")
            
            # Check for success - Result could be 1 (int), "1" (string), or "Success" (from base procedure)
            result_str = str(result_data.get("Result", "")).lower() if result_data else ""
            if result_data and (result_str == "1" or result_str == "success"):
                # Handle both wrapper format and base procedure format
                new_quote_guid = result_data.get("NewQuoteGuid")
                control_no = result_data.get("ControlNo")
                existing_premium = result_data.get("ExistingPremium")
                total_premium = result_data.get("TotalPremium")
                
                # If these fields don't exist (base procedure was called), map from base format
                if not new_quote_guid and result_data.get("NewQuoteGuid"):
                    new_quote_guid = result_data.get("NewQuoteGuid")
                
                if new_quote_guid:
                    logger.info(f"Successfully created endorsement. NewQuoteGuid: {new_quote_guid}, "
                              f"ControlNo: {control_no}, Existing: ${existing_premium}, Total: ${total_premium}")
                    
                    return True, result_data, result_data.get("Message", result_data.get("Instructions", "Endorsement created successfully"))
                else:
                    # Base procedure was called but didn't return NewQuoteGuid
                    logger.error("Endorsement created but NewQuoteGuid not returned - likely base procedure was called directly")
                    return False, result_data, "Stored procedure Triton_ProcessFlatEndorsement not found - please deploy it to the database"
            else:
                # Check for ErrorMessage field (from base procedure errors)
                if result_data and result_data.get("ErrorMessage"):
                    error_msg = result_data.get("ErrorMessage")
                else:
                    error_msg = result_data.get("Message", "Unknown error") if result_data else "No result returned"
                
                if result_data:
                    logger.error(f"Failed to create endorsement. Result: {result_data.get('Result')}, Message: {error_msg}")
                    # Log all data for debugging
                    logger.debug(f"Full result data: {result_data}")
                else:
                    logger.error(f"Failed to create endorsement: {error_msg}")
                return False, result_data or {}, error_msg
                
        except Exception as e:
            error_msg = f"Error creating endorsement via wrapper: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, {}, error_msg
    
    def create_flat_endorsement(
        self,
        original_quote_guid: str,
        total_premium: float,
        effective_date: str,
        comment: str = "Midterm Endorsement",
        user_guid: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Create a flat endorsement using ProcessFlatEndorsement stored procedure.
        This creates an unbound endorsement that must be bound separately.
        
        Args:
            original_quote_guid: The GUID of the quote to endorse (latest in chain)
            total_premium: The TOTAL premium (existing + new) for the policy
            effective_date: The effective date of the endorsement (MM/DD/YYYY format)
            comment: Description of the endorsement
            user_guid: Optional user GUID for the endorsement
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (success, result_data, message)
            result_data contains NewQuoteGuid, EndorsementNumber, PremiumChange, etc.
        """
        try:
            # Get user guid from auth service if not provided
            if not user_guid:
                user_guid = self.auth_service.user_guid
            
            logger.info(f"Creating flat endorsement for quote: {original_quote_guid}")
            logger.info(f"Total premium: ${total_premium:,.2f}, Effective: {effective_date}")
            
            # Prepare parameters for stored procedure
            params = [
                "OriginalQuoteGuid", str(original_quote_guid),
                "NewPremium", str(total_premium),
                "EndorsementEffectiveDate", effective_date,
                "EndorsementComment", comment
            ]
            
            # Add user guid if available
            if user_guid:
                params.extend(["UserGuid", str(user_guid)])
            
            # Call the wrapper procedure (which will call the base procedure)
            success, result_xml, message = self.data_service.execute_dataset(
                procedure_name="Triton_ProcessFlatEndorsement",
                parameters=params
            )
            
            if not success:
                return False, {}, f"Failed to execute ProcessFlatEndorsement: {message}"
            
            # Parse the result
            result_data = self._parse_flat_endorsement_result(result_xml)
            
            if result_data and result_data.get("Result") == "Success":
                new_quote_guid = result_data.get("NewQuoteGuid")
                endorsement_num = result_data.get("EndorsementNumber")
                premium_change = result_data.get("PremiumChange")
                
                logger.info(f"Successfully created flat endorsement. NewQuoteGuid: {new_quote_guid}, "
                          f"Endorsement #{endorsement_num}, Premium change: ${premium_change}")
                
                return True, result_data, result_data.get("Instructions", "Endorsement created successfully")
            else:
                error_msg = result_data.get("ErrorMessage", "Unknown error") if result_data else "No result returned"
                logger.error(f"Failed to create flat endorsement: {error_msg}")
                return False, result_data or {}, error_msg
                
        except Exception as e:
            error_msg = f"Error creating flat endorsement: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, {}, error_msg
    
    def _parse_triton_endorsement_result(self, result_xml: str) -> Optional[Dict[str, Any]]:
        """
        Parse the result from Triton_ProcessFlatEndorsement wrapper procedure.
        The wrapper returns TWO result sets - we need the second one.
        
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
            
            # The wrapper procedure returns multiple result sets
            # First result set is from the base procedure (Result="Success")
            # Second result set is from the wrapper (Result=1)
            # We need to find the correct one
            
            # Find all table elements - they can be named Table, Table1, Table2, etc.
            tables = []
            for table_name in ['Table', 'Table1', 'Table2']:
                tables.extend(root.findall(f'.//{table_name}'))
            
            # Look for the table that has NewQuoteOptionGuid (wrapper's result - second table)
            # The wrapper returns TWO tables:
            # 1. First table (<Table>) from ProcessFlatEndorsement (base) - no QuoteOptionGuid
            # 2. Second table (<Table1>) from Triton_ProcessFlatEndorsement_WS (wrapper) - has NewQuoteOptionGuid
            for table in tables:
                result_data = {}
                has_quote_option_guid = False
                
                # Extract all fields from this table
                for child in table:
                    if child.text is not None:
                        # Check if this table has NewQuoteOptionGuid (wrapper's signature field)
                        if child.tag == 'NewQuoteOptionGuid':
                            has_quote_option_guid = True
                        
                        # Convert numeric fields
                        if child.tag in ['Result', 'ControlNo']:
                            try:
                                result_data[child.tag] = str(int(child.text.strip()))
                            except:
                                result_data[child.tag] = child.text.strip()
                        elif child.tag in ['ExistingPremium', 'EndorsementPremium', 'TotalPremium']:
                            try:
                                result_data[child.tag] = float(child.text.strip())
                            except:
                                result_data[child.tag] = child.text.strip()
                        else:
                            result_data[child.tag] = child.text.strip()
                    else:
                        result_data[child.tag] = None
                
                # If this table has NewQuoteOptionGuid, it's the wrapper's result (second table)
                if has_quote_option_guid:
                    # Map some fields for compatibility
                    if 'TotalPremium' in result_data:
                        result_data['NewPremium'] = result_data['TotalPremium']
                    if 'EndorsementPremium' in result_data and 'ExistingPremium' in result_data:
                        result_data['PremiumChange'] = result_data['EndorsementPremium']
                        result_data['OriginalPremium'] = result_data['ExistingPremium']
                    
                    logger.info(f"Found QuoteOptionGuid in wrapper result: {result_data.get('NewQuoteOptionGuid')}")
                    logger.debug(f"Found wrapper result set with QuoteOptionGuid: {result_data}")
                    return result_data
            
            # If we didn't find the wrapper result with QuoteOptionGuid, check for ControlNo as secondary indicator
            for table in tables:
                result_data = {}
                has_control_no = False
                
                # Extract all fields from this table
                for child in table:
                    if child.text is not None:
                        if child.tag == 'ControlNo':
                            has_control_no = True
                        result_data[child.tag] = child.text.strip()
                    else:
                        result_data[child.tag] = None
                
                # If this table has ControlNo and Result=1, it might be the wrapper's result
                if has_control_no and str(result_data.get('Result')) == '1':
                    # Map some fields for compatibility
                    if 'TotalPremium' in result_data:
                        result_data['NewPremium'] = result_data['TotalPremium']
                    if 'EndorsementPremium' in result_data and 'ExistingPremium' in result_data:
                        result_data['PremiumChange'] = result_data['EndorsementPremium']
                        result_data['OriginalPremium'] = result_data['ExistingPremium']
                    
                    logger.info(f"Found result with ControlNo (may be missing QuoteOptionGuid): {result_data}")
                    return result_data
            
            # Last resort: Look specifically for Table1 if we haven't found anything yet
            table1 = root.find('.//Table1')
            if table1 is not None:
                result_data = {}
                for child in table1:
                    if child.text is not None:
                        result_data[child.tag] = child.text.strip()
                    else:
                        result_data[child.tag] = None
                
                if 'NewQuoteOptionGuid' in result_data:
                    logger.info(f"Found Table1 with QuoteOptionGuid: {result_data.get('NewQuoteOptionGuid')}")
                    # Map fields for compatibility
                    if 'TotalPremium' in result_data:
                        result_data['NewPremium'] = result_data['TotalPremium']
                    if 'EndorsementPremium' in result_data and 'ExistingPremium' in result_data:
                        result_data['PremiumChange'] = result_data['EndorsementPremium']
                        result_data['OriginalPremium'] = result_data['ExistingPremium']
                    return result_data
            
            # Really last resort: use the first table found
            if tables:
                table = tables[0]
                result_data = {}
                for child in table:
                    if child.text is not None:
                        result_data[child.tag] = child.text.strip()
                    else:
                        result_data[child.tag] = None
                
                logger.warning(f"Using fallback result set (base procedure - no QuoteOptionGuid): {result_data}")
                return result_data
            
            return None
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse Triton endorsement result XML: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Triton endorsement result: {str(e)}")
            return None
    
    def _parse_flat_endorsement_result(self, result_xml: str) -> Optional[Dict[str, Any]]:
        """
        Parse the result from ProcessFlatEndorsement stored procedure.
        
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
            
            # Look for the result table
            table = root.find('.//Table')
            if table is None:
                return None
            
            result_data = {}
            
            # Extract all fields from the result
            for child in table:
                if child.text is not None:
                    result_data[child.tag] = child.text.strip()
                else:
                    result_data[child.tag] = None
            
            # Log the parsed result
            if result_data:
                logger.debug(f"Parsed ProcessFlatEndorsement result: {result_data}")
            
            return result_data
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse ProcessFlatEndorsement result XML: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing ProcessFlatEndorsement result: {str(e)}")
            return None
    
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