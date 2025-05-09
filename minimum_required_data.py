"""
Minimum Required Data for IMS Integration

This file outlines the absolute minimum data fields required from Tritan
to successfully create a policy card and bind an account in IMS.
"""

# MINIMUM REQUIRED DATA FROM TRITAN
MINIMUM_REQUIRED_DATA = {
    # Policy Identification
    "policy_number": "String - Unique identifier for the policy from Tritan",
    "effective_date": "Date (YYYY-MM-DD) - Policy effective date",
    "expiration_date": "Date (YYYY-MM-DD) - Policy expiration date",
    "bound_date": "Date (YYYY-MM-DD) - Date the policy was bound",
    
    # Classification
    "program": "String - Insurance program name (e.g., 'Allied Health', 'Middle Market')",
    "line_of_business": "String - Line of business (e.g., 'AHC Primary', 'AHC Excess')",
    "state": "String - 2-letter state code where policy is written",
    
    # Insured Details
    "insured_name": "String - Full legal name of the insured",
    "insured_address": "String - Street address of the insured",
    "insured_city": "String - City of the insured",
    "insured_state": "String - 2-letter state code of the insured",
    "insured_zip": "String - Zip code of the insured",
    
    # Producer Information (for lookup)
    "producer_name": "String - Name of the producing agency/broker for lookup",
    "producer_commission": "Float - Producer's commission rate (e.g., 0.15 for 15%)",
    
    # Underwriter Information (for lookup)
    "underwriter_name": "String - Name of the underwriter for lookup",
    
    # Coverage & Premium
    "limit": "String/Float - Primary liability limit (e.g., 1000000)",
    "deductible": "String/Float - Deductible amount (e.g., 2500)",
    "premium": "Float - Total policy premium"
}

# BUSINESS TYPE MAPPING
# For mapping string values from Tritan to IMS BusinessTypeID
BUSINESS_TYPE_MAPPING = {
    "Partnership": 2,
    "Limited Liability Partnership": 3,
    "Individual": 4,
    "Other": 5,
    "Limited Liability Corporation": 9,
    "LLC": 9,  # Common abbreviation
    "Joint Venture": 10,
    "Trust": 11,
    "Corporation": 13,
    "Corp": 13,  # Common abbreviation
    "Inc": 13,   # Common abbreviation
}

# PRODUCER LOOKUP STRATEGY
"""
Since Tritan and IMS have separate producer databases with different GUIDs,
we need a lookup strategy:

1. Primary Lookup Method:
   - Use ProducerSearch(producer_name) from ProducerFunctions.asmx
   - Find best match by name comparison
   - Extract ProducerLocationGuid from results

2. Fallback Options:
   - If multiple matches, use additional data (state, zip) to narrow down
   - If no exact match, use fuzzy matching with a threshold
   - Consider maintaining a mapping table for frequently used producers

3. Data Quality Requirements:
   - Producer name should be standardized in Tritan (e.g., "ABC Insurance" not "ABC Ins.")
   - Consistent naming conventions help improve match accuracy
"""

# UNDERWRITER LOOKUP STRATEGY
"""
Similar to producers, underwriter lookup may be needed:

1. Primary Lookup Method:
   - Use appropriate IMS web service to search underwriters by name
   - Find best match and extract UnderwriterGuid

2. Fallback Options:
   - If no exact match, use fuzzy matching with a threshold
   - Consider maintaining a mapping table for frequently used underwriters
""" 