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
        # Default values
        default_lob = "AHC Primary"
        default_guid = self.config.get("default_line_guid", "00000000-0000-0000-0000-000000000000")
        
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
        
        # Extract location info
        locations = []
        if "locations" in data and isinstance(data["locations"], list):
            locations = data["locations"]
        
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
        
        logger.info(f"Transformed Triton data for policy: {policy_number}, LOB: {line_of_business}")
        return result
        
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