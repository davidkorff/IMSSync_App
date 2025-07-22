import logging
import json
from typing import Dict, Optional, Tuple, Any
from datetime import datetime

from app.services.ims.auth_service import get_auth_service
from app.services.ims.data_access_service import get_data_access_service
from config import IMS_CONFIG

logger = logging.getLogger(__name__)


class IMSPayloadProcessorService:
    """Service for processing Triton payloads and storing data in IMS."""
    
    # Supported transaction types
    TRANSACTION_TYPES = {
        "bind": "Bind the policy",
        "unbind": "Unbind the policy",
        "issue": "Issue the policy",
        "midterm_endorsement": "Process midterm endorsement",
        "cancellation": "Cancel the policy",
        "reinstatement": "Reinstate the policy"
    }
    
    def __init__(self):
        self.auth_service = get_auth_service()
        self.data_service = get_data_access_service()
        
    def process_payload(
        self, 
        payload: Dict[str, Any], 
        quote_guid: str, 
        quote_option_guid: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Process a Triton payload by storing data and updating IMS.
        
        Args:
            payload: The Triton transaction payload
            quote_guid: GUID of the quote
            quote_option_guid: GUID of the quote option
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (success, result_data, message)
        """
        try:
            # Validate transaction type
            transaction_type = payload.get("transaction_type", "").lower()
            if transaction_type not in self.TRANSACTION_TYPES:
                return False, None, f"Unsupported transaction type: {transaction_type}"
            
            logger.info(f"Processing {transaction_type} transaction for quote: {quote_guid}")
            
            # Build parameters for stored procedure
            parameters = self._build_stored_proc_params(payload, quote_guid, quote_option_guid)
            
            # Execute the stored procedure
            success, result_xml, message = self.data_service.execute_dataset(
                "spProcessTritonPayload_WS",
                parameters
            )
            
            if not success:
                return False, None, f"Failed to process payload: {message}"
            
            # Parse the result
            result_data = self._parse_processing_result(result_xml)
            
            if result_data.get("Status") == "Success":
                logger.info(f"Successfully processed payload for quote: {quote_guid}")
                return True, result_data, result_data.get("Message", "Payload processed successfully")
            else:
                error_msg = result_data.get("Message", "Unknown error occurred")
                logger.error(f"Payload processing failed: {error_msg}")
                return False, result_data, error_msg
                
        except Exception as e:
            error_msg = f"Unexpected error processing payload: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _build_stored_proc_params(
        self, 
        payload: Dict[str, Any], 
        quote_guid: str, 
        quote_option_guid: str
    ) -> list:
        """
        Build parameter list for the stored procedure.
        
        Args:
            payload: The Triton payload
            quote_guid: Quote GUID
            quote_option_guid: Quote option GUID
            
        Returns:
            List of parameters in name/value pairs
        """
        # Start with the GUIDs
        params = [
            "QuoteGuid", quote_guid,
            "QuoteOptionGuid", quote_option_guid
        ]
        
        # Add all payload fields
        param_mapping = [
            ("umr", "umr"),
            ("agreement_number", "agreement_number"),
            ("section_number", "section_number"),
            ("class_of_business", "class_of_business"),
            ("program_name", "program_name"),
            ("policy_number", "policy_number"),
            ("underwriter_name", "underwriter_name"),
            ("producer_name", "producer_name"),
            ("invoice_date", "invoice_date"),
            ("policy_fee", "policy_fee"),
            ("surplus_lines_tax", "surplus_lines_tax"),
            ("stamping_fee", "stamping_fee"),
            ("other_fee", "other_fee"),
            ("insured_name", "insured_name"),
            ("insured_state", "insured_state"),
            ("insured_zip", "insured_zip"),
            ("effective_date", "effective_date"),
            ("expiration_date", "expiration_date"),
            ("bound_date", "bound_date"),
            ("opportunity_type", "opportunity_type"),
            ("business_type", "business_type"),
            ("status", "status"),
            ("limit_amount", "limit_amount"),
            ("limit_prior", "limit_prior"),
            ("deductible_amount", "deductible_amount"),
            ("gross_premium", "gross_premium"),
            ("commission_rate", "commission_rate"),
            ("commission_percent", "commission_percent"),
            ("commission_amount", "commission_amount"),
            ("net_premium", "net_premium"),
            ("base_premium", "base_premium"),
            ("opportunity_id", "opportunity_id"),
            ("midterm_endt_id", "midterm_endt_id"),
            ("midterm_endt_description", "midterm_endt_description"),
            ("midterm_endt_effective_from", "midterm_endt_effective_from"),
            ("midterm_endt_endorsement_number", "midterm_endt_endorsement_number"),
            ("additional_insured", "additional_insured"),
            ("address_1", "address_1"),
            ("address_2", "address_2"),
            ("city", "city"),
            ("state", "state"),
            ("zip", "zip"),
            ("transaction_id", "transaction_id"),
            ("transaction_type", "transaction_type"),
            ("transaction_date", "transaction_date"),
            ("source_system", "source_system")
        ]
        
        for param_name, payload_key in param_mapping:
            value = payload.get(payload_key)
            
            # Handle special cases
            if param_name == "additional_insured" and isinstance(value, list):
                # Convert list to JSON string
                value = json.dumps(value) if value else None
            elif value == "":
                # Convert empty strings to None for SQL
                value = None
            
            # Convert value to string for the parameter list
            params.extend([param_name, str(value) if value is not None else ""])
        
        return params
    
    def _parse_processing_result(self, result_xml: str) -> Dict[str, Any]:
        """
        Parse the result from the stored procedure.
        
        Args:
            result_xml: XML result from ExecuteDataSet
            
        Returns:
            Dictionary with processing results
        """
        try:
            import xml.etree.ElementTree as ET
            
            result_data = {}
            
            if result_xml:
                root = ET.fromstring(result_xml)
                
                # Find the first Table element
                table = root.find('.//Table')
                if table is not None:
                    # Extract all fields from the result
                    for element in table:
                        result_data[element.tag] = element.text
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error parsing processing result: {str(e)}")
            return {"Status": "Error", "Message": f"Failed to parse result: {str(e)}"}
    
    def validate_payload(self, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate that the payload has required fields.
        
        Args:
            payload: The Triton payload
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        required_fields = [
            "transaction_type",
            "transaction_id",
            "policy_number",
            "insured_name",
            "net_premium"
        ]
        
        missing_fields = []
        for field in required_fields:
            if not payload.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate transaction type
        transaction_type = payload.get("transaction_type", "").lower()
        if transaction_type not in self.TRANSACTION_TYPES:
            return False, f"Invalid transaction type: {transaction_type}"
        
        return True, ""
    
    def get_transaction_info(self, transaction_type: str) -> str:
        """Get information about a transaction type."""
        return self.TRANSACTION_TYPES.get(transaction_type.lower(), "Unknown transaction type")


# Singleton instance
_payload_processor_service = None


def get_payload_processor_service() -> IMSPayloadProcessorService:
    """Get singleton instance of payload processor service."""
    global _payload_processor_service
    if _payload_processor_service is None:
        _payload_processor_service = IMSPayloadProcessorService()
    return _payload_processor_service