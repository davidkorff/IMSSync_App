"""
Transformer for Triton data - handles both nested and flat structures
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class TritonTransformer:
    """
    Transforms Triton data into IMS-compatible format
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with optional configuration"""
        self.config = config or {}
    
    def determine_line_of_business(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Determine the appropriate IMS line of business and its GUID based on Triton data
        
        Returns:
            Tuple of (line_of_business_name, line_guid)
        """
        # Default values with valid IMS GUIDs
        default_lob = "AHC Primary"
        default_guid = self.config.get("default_line_guid", "07564291-CBFE-4BBE-88D1-0548C88ACED4")  # AHC Primary LineGUID
        
        # This logic will need to be updated based on Triton's actual data structure
        # For now, using a simple example
        if "coverages" in data and isinstance(data["coverages"], list):
            for coverage in data["coverages"]:
                coverage_type = coverage.get("type", "").lower()
                if "excess" in coverage_type:
                    # Map to AHC Excess
                    lob = "AHC Excess"
                    guid = self.config.get("excess_line_guid", default_guid)
                    logger.info(f"Determined line of business: {lob}")
                    return lob, guid
        
        # Default to Primary
        logger.info(f"Using default line of business: {default_lob}")
        return default_lob, default_guid
    
    def map_producer(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Map Triton producer to IMS producer GUID
        """
        # Default producer
        default_producer_guid = self.config.get("default_producer_guid")
        
        # Extract producer info from Triton data
        if "producer" in data and isinstance(data["producer"], dict):
            producer_data = data["producer"]
            producer_id = producer_data.get("id")
            producer_name = producer_data.get("name")
            
            if producer_id:
                # TODO: Implement lookup from mapping table
                # This would query a database table that maps Triton producer IDs to IMS GUIDs
                logger.info(f"Looking up producer mapping for Triton producer ID: {producer_id}")
                # producer_guid = db.query_producer_mapping(producer_id)
                # if producer_guid:
                #     return producer_guid
        
        logger.info(f"Using default producer GUID: {default_producer_guid}")
        return default_producer_guid
    
    def _is_flat_structure(self, data: Dict[str, Any]) -> bool:
        """
        Detect if the data is in flat format (like TEST.json)
        """
        # Check for flat structure indicators
        flat_indicators = ['insured_name', 'insured_state', 'producer_name', 'gross_premium']
        nested_indicators = ['insured', 'producer', 'locations', 'coverages']
        
        flat_count = sum(1 for key in flat_indicators if key in data)
        nested_count = sum(1 for key in nested_indicators if key in data and isinstance(data[key], (dict, list)))
        
        return flat_count > nested_count
    
    def _transform_flat_to_nested(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert flat structure to nested structure for processing
        """
        # Import the flat transformer
        from app.integrations.triton.flat_transformer import TritonFlatTransformer
        flat_transformer = TritonFlatTransformer(self.config)
        return flat_transformer.transform_to_ims_format(data)
    
    def transform_to_ims_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Triton data to IMS format - handles both flat and nested structures
        """
        logger.info("Transforming Triton data to IMS format")
        
        # Check if this is a flat structure
        if self._is_flat_structure(data):
            logger.info("Detected flat structure, using flat transformer")
            return self._transform_flat_to_nested(data)
        
        # Check transaction type and route accordingly
        transaction_type = data.get("transaction_type", "").lower()
        
        if transaction_type == "cancellation":
            return self._transform_cancellation(data)
        elif transaction_type in ["endorsement", "midterm_endorsement"]:
            return self._transform_endorsement(data)
        elif transaction_type == "reinstatement":
            return self._transform_reinstatement(data)
        else:
            # Default to binding/new policy transformation
            return self._transform_binding(data)
    
    def _transform_binding(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform binding/new policy data"""
        # Determine line of business
        line_of_business, line_guid = self.determine_line_of_business(data)
        
        # Map producer
        producer_guid = self.map_producer(data)
        
        # Extract basic policy info
        policy_number = data.get("policy_number", "")
        effective_date = data.get("effective_date")
        expiration_date = data.get("expiration_date")
        
        # Extract insured info
        insured_data = {}
        if "insured" in data and isinstance(data["insured"], dict):
            insured = data["insured"]
            insured_data = {
                "name": insured.get("name", ""),
                "tax_id": insured.get("tax_id"),
                "business_type_id": 1,  # Default to Corporation
                "dba": insured.get("dba")
            }
            
            # Extract contact info if available
            if "contact" in insured and isinstance(insured["contact"], dict):
                contact = insured["contact"]
                insured_data.update({
                    "contact_name": contact.get("name"),
                    "contact_email": contact.get("email"),
                    "contact_phone": contact.get("phone")
                })
        elif "account" in data and isinstance(data["account"], dict):
            # Handle account structure (like in Triton binding transactions)
            account = data["account"]
            insured_data = {
                "name": account.get("name", ""),
                "tax_id": account.get("id"),
                "business_type_id": 1,  # Default to Corporation
                "dba": account.get("dba"),
                "address": account.get("street_1", ""),
                "city": account.get("city", ""),
                "state": account.get("state", ""),
                "zip": account.get("zip", "")
            }
        
        # Extract location info
        locations = []
        if "locations" in data and isinstance(data["locations"], list):
            locations = data["locations"]
        elif insured_data.get("address"):
            # Create location from insured data
            locations = [{
                "address": insured_data.get("address", ""),
                "city": insured_data.get("city", ""),
                "state": insured_data.get("state", ""),
                "zip": insured_data.get("zip", ""),
                "location_type": "primary"
            }]
        
        # Build result
        result = {
            "policy_data": {
                "policy_number": policy_number,
                "effective_date": effective_date,
                "expiration_date": expiration_date,
                "line_of_business": line_of_business,
                "line_guid": line_guid,
                "producer_guid": producer_guid
            },
            "insured_data": insured_data,
            "locations": locations,
            "coverages": data.get("coverages", []),
            "premium": data.get("premium")
        }
        
        logger.info(f"Transformed Triton binding data for policy: {policy_number}, LOB: {line_of_business}")
        return result
    
    def _transform_cancellation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform cancellation transaction data"""
        logger.info("Transforming cancellation transaction")
        
        # Extract control number from policy number
        policy_number = data.get("policy_number", "")
        control_number = self._extract_control_number(policy_number)
        
        # Build cancellation data
        cancellation_data = {
            "control_number": control_number,
            "cancellation_date": data.get("cancellation_date"),
            "cancellation_reason": data.get("cancellation_reason", ""),
            "cancellation_reason_id": self._map_cancellation_reason(data.get("cancellation_reason", "")),
            "comments": data.get("cancellation_reason", "Policy cancelled via Triton"),
            "flat_cancel": data.get("flat_cancel", False),
            "return_premium": data.get("return_premium_entries") is not None
        }
        
        # Add user info if available
        if "user" in data:
            cancellation_data["user_guid"] = data["user"].get("guid")
        
        result = {
            "cancellation_data": cancellation_data,
            "policy_number": policy_number,
            "original_premium": data.get("original_premium"),
            "return_premium_entries": data.get("return_premium_entries", [])
        }
        
        logger.info(f"Transformed cancellation for policy: {policy_number}")
        return result
    
    def _transform_endorsement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform endorsement transaction data"""
        logger.info("Transforming endorsement transaction")
        
        # Extract control number from policy number
        policy_number = data.get("policy_number", "")
        control_number = self._extract_control_number(policy_number)
        
        # Extract endorsement details
        endorsement = data.get("endorsement", {})
        if isinstance(data.get("endorsement"), dict):
            endorsement = data["endorsement"]
        
        # Build endorsement data
        endorsement_data = {
            "control_number": control_number,
            "endorsement_effective_date": endorsement.get("effective_from") or data.get("effective_date"),
            "endorsement_comment": endorsement.get("description", "Policy endorsement via Triton"),
            "endorsement_reason_id": self._map_endorsement_reason(endorsement.get("endorsement_code", "")),
            "calculation_type": "P",  # Default to pro-rata
            "endorsement_number": endorsement.get("endorsement_number"),
            "premium_change": endorsement.get("premium", 0)
        }
        
        # Add user info if available
        if "user" in data:
            endorsement_data["user_guid"] = data["user"].get("guid")
        
        result = {
            "endorsement_data": endorsement_data,
            "policy_number": policy_number,
            "endorsement_details": endorsement,
            "account": data.get("account"),
            "producer": data.get("producer")
        }
        
        logger.info(f"Transformed endorsement for policy: {policy_number}")
        return result
    
    def _transform_reinstatement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform reinstatement transaction data"""
        logger.info("Transforming reinstatement transaction")
        
        # Extract control number from policy number
        policy_number = data.get("policy_number", "")
        control_number = self._extract_control_number(policy_number)
        
        # Build reinstatement data
        reinstatement_data = {
            "control_number": control_number,
            "reinstatement_date": data.get("reinstatement_date") or data.get("effective_date"),
            "reinstatement_reason_id": self._map_reinstatement_reason(data.get("reason", "")),
            "comments": data.get("comments", "Policy reinstated via Triton"),
            "payment_received": data.get("payment_amount"),
            "check_number": data.get("check_number"),
            "generate_invoice": data.get("generate_invoice", True)
        }
        
        # Add user info if available
        if "user" in data:
            reinstatement_data["user_guid"] = data["user"].get("guid")
        
        result = {
            "reinstatement_data": reinstatement_data,
            "policy_number": policy_number,
            "payment_details": data.get("payment_details")
        }
        
        logger.info(f"Transformed reinstatement for policy: {policy_number}")
        return result
    
    def _extract_control_number(self, policy_number: str) -> Optional[int]:
        """Extract control number from policy number or lookup in IMS"""
        # For now, we'll need to implement a lookup service
        # This is a placeholder that assumes the control number is embedded in the policy number
        # In reality, this would query IMS to get the control number
        logger.warning(f"Control number extraction not implemented, using placeholder for policy: {policy_number}")
        # TODO: Implement actual control number lookup
        return 12345  # Placeholder
    
    def _map_cancellation_reason(self, reason: str) -> int:
        """Map Triton cancellation reason to IMS reason ID"""
        reason_mapping = {
            "non-payment": 1,
            "request": 2,
            "underwriting": 3,
            "fraud": 4,
            "other": 99
        }
        return reason_mapping.get(reason.lower(), 99)
    
    def _map_endorsement_reason(self, code: str) -> int:
        """Map Triton endorsement code to IMS reason ID"""
        reason_mapping = {
            "add_coverage": 1,
            "remove_coverage": 2,
            "change_limit": 3,
            "add_location": 4,
            "remove_location": 5,
            "other": 99
        }
        return reason_mapping.get(code.lower(), 99)
    
    def _map_reinstatement_reason(self, reason: str) -> int:
        """Map reinstatement reason to IMS reason ID"""
        reason_mapping = {
            "payment_received": 1,
            "error": 2,
            "appeal": 3,
            "other": 99
        }
        return reason_mapping.get(reason.lower(), 99)
        
    def get_excel_rater_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get Excel rater information based on the transformed data
        """
        # Check if this is a flat structure
        if self._is_flat_structure(data):
            logger.info("Using flat transformer for Excel rater info")
            from app.integrations.triton.flat_transformer import TritonFlatTransformer
            flat_transformer = TritonFlatTransformer(self.config)
            return flat_transformer.get_excel_rater_info(data)
            
        # Determine line of business
        line_of_business, _ = self.determine_line_of_business(data)
        
        # Get state
        state = ""
        if "insured" in data and isinstance(data["insured"], dict) and "locations" in data and len(data["locations"]) > 0:
            state = data["locations"][0].get("state", "")
        
        # Look up rater info based on LOB and state
        rater_info = self.config.get("raters", {}).get(line_of_business, {})
        
        # If state-specific rater exists, use that
        state_specific_key = f"{line_of_business}_{state}"
        state_specific_rater = self.config.get("raters", {}).get(state_specific_key, {})
        if state_specific_rater:
            rater_info = state_specific_rater
        
        if not rater_info:
            logger.warning(f"No rater configuration found for LOB: {line_of_business}, State: {state}")
        
        return {
            "rater_id": rater_info.get("rater_id"),
            "factor_set_guid": rater_info.get("factor_set_guid"),
            "template": rater_info.get("template"),
            "lob": line_of_business,
            "state": state
        }