"""
Enhanced Triton transformer that handles flat structure from TEST.json
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class TritonFlatTransformer:
    """
    Transformer for Triton's flat JSON structure (as seen in TEST.json)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def transform_to_ims_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform flat Triton structure to IMS format
        """
        logger.info("Transforming flat Triton data to IMS format")
        
        # Handle date conversions
        effective_date = self._convert_date(data.get('effective_date'))
        expiration_date = self._convert_date(data.get('expiration_date'))
        bound_date = self._convert_date(data.get('bound_date'))
        
        # Parse limit string (e.g., "$1,000,000/$3,000,000")
        limit_info = self._parse_limit_string(data.get('limit_amount', ''))
        
        # Parse deductible (e.g., "$2,500")
        deductible = self._parse_currency(data.get('deductible_amount', '0'))
        
        # Build transformed data
        transformed = {
            "policy_data": {
                "policy_number": data.get('policy_number'),
                "effective_date": effective_date,
                "expiration_date": expiration_date,
                "bound_date": bound_date,
                "line_of_business": self._determine_lob(data),
                "line_guid": self.config.get("default_line_guid", "00000000-0000-0000-0000-000000000000"),
                "producer_guid": self.config.get("default_producer_guid", "00000000-0000-0000-0000-000000000000"),
                "producer_location_guid": self.config.get("default_producer_location_guid"),
                "commission_rate": float(data.get('commission_rate', 0)),
                "is_renewal": data.get('business_type', '').lower() == 'renewal',
                "status": data.get('status', 'bound'),
                "program_name": data.get('program_name'),
                "class_of_business": data.get('class_of_business'),
                "opportunity_id": data.get('opportunity_id'),
                "transaction_type": data.get('transaction_type', 'NEW BUSINESS')
            },
            "insured_data": {
                "name": data.get('insured_name'),
                "dba": None,  # Not provided in flat structure
                "tax_id": None,  # Not provided
                "business_type_id": self._get_business_type_id(data.get('business_type', '')),
                "contact_first_name": None,
                "contact_last_name": None,
                "contact_phone": None,
                "contact_email": None,
                "state": data.get('insured_state'),
                "zip": data.get('insured_zip'),
                # Use provided address or default
                "address_1": data.get('insured_address1', "Address Line 1"),
                "city": self._get_city_from_zip(data.get('insured_zip', '')),
                "country": "USA"
            },
            "producer_data": {
                "name": data.get('producer_name'),
                "underwriter_name": data.get('underwriter_name')
            },
            "premium_data": {
                "gross_premium": float(data.get('gross_premium', 0)),
                "base_premium": float(data.get('base_premium', 0)),
                "net_premium": float(data.get('net_premium', 0)),
                "policy_fee": float(data.get('policy_fee', 0)),
                "surplus_lines_tax": self._parse_currency(data.get('surplus_lines_tax', '0')),
                "stamping_fee": self._parse_currency(data.get('stamping_fee', '0')),
                "other_fee": self._parse_currency(data.get('other_fee', '0')),
                "commission_amount": float(data.get('commission_amount', 0)),
                "commission_percent": float(data.get('commission_percent', 0))
            },
            "locations": [
                {
                    "address_1": "Primary Location",
                    "city": self._get_city_from_zip(data.get('insured_zip', '')),
                    "state": data.get('insured_state'),
                    "zip": data.get('insured_zip'),
                    "country": "USA",
                    "is_primary": True
                }
            ],
            "coverages": [
                {
                    "coverage_type": self._determine_coverage_type(data),
                    "limit_occurrence": limit_info.get('occurrence', 0),
                    "limit_aggregate": limit_info.get('aggregate', 0),
                    "deductible": deductible,
                    "premium": float(data.get('gross_premium', 0))
                }
            ],
            "additional_data": {
                "umr": data.get('umr'),
                "agreement_number": data.get('agreement_number'),
                "section_number": data.get('section_number'),
                "invoice_date": data.get('invoice_date'),
                "opportunity_type": data.get('opportunity_type'),
                "limit_prior": data.get('limit_prior'),
                "midterm_endt_id": data.get('midterm_endt_id'),
                "midterm_endt_description": data.get('midterm_endt_description'),
                "midterm_endt_effective_from": data.get('midterm_endt_effective_from'),
                "midterm_endt_endorsement_number": data.get('midterm_endt_endorsement_number'),
                "additional_insured": data.get('additional_insured', []),
                "opportunity_id": data.get('opportunity_id'),  # Store Triton opportunity ID
                "bound_date_original": data.get('bound_date'),  # Store original if different from today
                "business_type": data.get('business_type')  # NEW BUSINESS vs RENEWAL
            },
            # Prepare AdditionalInformation array for IMS
            "additional_information": self._build_additional_information(data)
        }
        
        return transformed
    
    def get_excel_rater_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get Excel rater information based on flat data
        """
        # Determine LOB based on program/class
        lob = self._determine_lob(data)
        state = data.get('insured_state', '')
        
        # Map to Excel rater configuration
        rater_config = self.config.get("excel_raters", {})
        
        # Try to find matching rater by LOB and state
        for rater_id, rater_info in rater_config.items():
            if (rater_info.get("lob") == lob and 
                state in rater_info.get("states", [])):
                return {
                    "rater_id": int(rater_id),
                    "factor_set_guid": rater_info.get("factor_set_guid"),
                    "lob": lob,
                    "state": state
                }
        
        # Return default if no match
        return {
            "rater_id": self.config.get("default_excel_rater_id", 1),
            "factor_set_guid": self.config.get("default_factor_set_guid"),
            "lob": lob,
            "state": state
        }
    
    def _convert_date(self, date_str: Optional[str]) -> Optional[str]:
        """Convert MM/DD/YYYY to YYYY-MM-DD format"""
        if not date_str:
            return None
            
        # Handle ISO format (already correct)
        if 'T' in str(date_str) or '-' in str(date_str):
            return date_str.split('T')[0] if 'T' in date_str else date_str
            
        # Handle MM/DD/YYYY format
        if '/' in date_str:
            try:
                parts = date_str.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    # Handle 2-digit year
                    if len(year) == 2:
                        year = f"20{year}"
                    return f"{year}-{month:0>2}-{day:0>2}"
            except:
                logger.warning(f"Could not parse date: {date_str}")
                
        return date_str
    
    def _parse_limit_string(self, limit_str: str) -> Dict[str, float]:
        """Parse limit string like '$1,000,000/$3,000,000' """
        result = {'occurrence': 0, 'aggregate': 0}
        
        if not limit_str:
            return result
            
        # Remove $ and commas
        clean_str = limit_str.replace('$', '').replace(',', '')
        
        # Split by /
        parts = clean_str.split('/')
        
        try:
            if len(parts) >= 1 and parts[0]:
                result['occurrence'] = float(parts[0])
            if len(parts) >= 2 and parts[1]:
                result['aggregate'] = float(parts[1])
        except ValueError:
            logger.warning(f"Could not parse limit string: {limit_str}")
            
        return result
    
    def _parse_currency(self, value: Any) -> float:
        """Parse currency string to float"""
        if not value or value == "":
            return 0.0
            
        if isinstance(value, (int, float)):
            return float(value)
            
        # Remove currency symbols and commas
        clean_str = str(value).replace('$', '').replace(',', '').strip()
        
        try:
            return float(clean_str) if clean_str else 0.0
        except ValueError:
            logger.warning(f"Could not parse currency value: {value}")
            return 0.0
    
    def _determine_lob(self, data: Dict[str, Any]) -> str:
        """Determine line of business from flat data"""
        program = data.get('program_name', '').lower()
        class_of_business = data.get('class_of_business', '').lower()
        
        # Logic based on program/class
        if 'allied' in program or 'ahc' in program:
            # Check if it's excess based on limit or other indicators
            limit_str = data.get('limit_amount', '')
            if 'excess' in class_of_business or '5000000' in limit_str:
                return "AHC Excess"
            return "AHC Primary"
            
        # Default
        return "GL"
    
    def _determine_coverage_type(self, data: Dict[str, Any]) -> str:
        """Determine coverage type from flat data"""
        lob = self._determine_lob(data)
        
        if lob == "AHC Primary":
            return "Professional Liability"
        elif lob == "AHC Excess":
            return "Excess Liability"
        else:
            return "General Liability"
    
    def _get_city_from_zip(self, zip_code: str) -> str:
        """Get city name from zip code - placeholder implementation"""
        # In a real implementation, this would use a zip code database
        # For now, return a default based on state
        if zip_code and zip_code.startswith('333'):
            return "Miami"  # Florida 333xx
        elif zip_code and zip_code.startswith('100'):
            return "New York"  # NY 100xx
        else:
            return "Unknown City"
    
    def _get_business_type_id(self, business_type: str) -> int:
        """Map business type string to IMS BusinessTypeID"""
        # IMS Business Types mapping - verified against IMS database
        # Order matters - check longer strings first
        business_type_map = {
            'limited liability partnership': 3,  # Check this before 'partnership'
            'limited liability company': 5,      # Check this before 'company'
            'limited liability corporation': 5,  # Check this before 'corporation'
            'sole proprietor': 4,               # Check this before 'sole prop'
            'corporation': 1,
            'incorporated': 1,
            'partnership': 2,
            'individual': 3,
            'sole prop': 4,
            'person': 3,
            'corp': 1,
            'inc': 1,
            'llp': 3,
            'llc': 5,
            'other': 5  # Map 'other' to LLC as a safe default
        }
        
        # Clean and normalize the business type
        normalized = business_type.lower().strip()
        
        # Skip transaction types (these are not business entity types)
        transaction_types = ['renewal', 'new business', 'endorsement', 'cancellation']
        if normalized in transaction_types:
            logger.warning(f"'{business_type}' is a transaction type, not a business entity type. Defaulting to Corporation (1)")
            return 1
        
        # First try exact match
        if normalized in business_type_map:
            return business_type_map[normalized]
        
        # Then try partial match (longer strings first due to dict ordering)
        for key, value in business_type_map.items():
            if key in normalized:
                return value
        
        # Default to Corporation if not found
        logger.warning(f"Unknown business type '{business_type}', defaulting to Corporation (1)")
        return 1  # Corporation
    
    def _build_additional_information(self, data: Dict[str, Any]) -> List[str]:
        """Build AdditionalInformation array for IMS AddQuote"""
        additional_info = []
        
        # Add Triton opportunity ID
        if data.get('opportunity_id'):
            additional_info.append(f"TritonOpportunityId:{data['opportunity_id']}")
        
        # Add original bound date if different from today
        if data.get('bound_date'):
            additional_info.append(f"OriginalBoundDate:{data['bound_date']}")
        
        # Add limit prior for comparison
        if data.get('limit_prior'):
            additional_info.append(f"PriorLimits:{data['limit_prior']}")
        
        # Add UMR if present
        if data.get('umr'):
            additional_info.append(f"UMR:{data['umr']}")
        
        # Add agreement/section numbers if present
        if data.get('agreement_number'):
            additional_info.append(f"AgreementNumber:{data['agreement_number']}")
        
        if data.get('section_number'):
            additional_info.append(f"SectionNumber:{data['section_number']}")
        
        # For endorsements, add endorsement details
        if data.get('midterm_endt_id'):
            additional_info.append(f"EndorsementId:{data['midterm_endt_id']}")
            if data.get('midterm_endt_description'):
                additional_info.append(f"EndorsementDesc:{data['midterm_endt_description']}")
        
        # Add additional insureds as JSON string (for future use)
        if data.get('additional_insured'):
            import json
            ai_json = json.dumps(data['additional_insured'])
            additional_info.append(f"AdditionalInsureds:{ai_json}")
        
        return additional_info