"""
Test Data Configuration for IMS Integration API

This file contains default values, known GUIDs for the 'ims_one' test environment,
and helper functions for generating test data based on the CSV format.
"""

# --- IMS Line of Business GUIDs (for 'ims_one' environment) ---
# Provided by user:
LINE_GUID_AHC_PRIMARY = "07564291-CBFE-4BBE-88D1-0548C88ACED4" # AHC Primary
LINE_GUID_AHC_EXCESS = "08798559-321C-4FC0-98ED-A61B92215F31" # AHC Excess

# --- Default IMS Entities & IDs for 'ims_one' (Placeholders - NEED ACTUAL VALUES) ---
# These should be actual, valid GUIDs/IDs from your 'ims_one' IMS environment.
# If lookups by name are implemented and preferred for testing, these names should exist in IMS.

# Producer (Example - replace with actuals or use names for lookup)
DEFAULT_PRODUCER_NAME_FOR_LOOKUP = "Everisk Insurance Programs, Inc." # From CSV example
# If using direct GUIDs for testing:
DEFAULT_PRODUCER_CONTACT_GUID = "895E9291-CFB6-4299-8799-9AF77DF937D6" # From user
# The ProducerLocationGUID for "H&H Insurance Services" (ProducerLocationID 19817 from sample)
# can be looked up using GetProducerInfoByContact(DEFAULT_PRODUCER_CONTACT_GUID)
# or ProducerSearch("H&H Insurance Services").
# For initial testing, if you know this GUID, you can set it directly:
DEFAULT_PRODUCER_LOCATION_GUID = "YOUR_HH_INSURANCE_SERVICES_LOCATION_GUID" # Placeholder - PLEASE PROVIDE if known
DEFAULT_PRODUCER_LOCATION_NAME_FOR_LOOKUP = "H&H Insurance Services" # From sample data

# Underwriter (Example - replace with actuals or use names for lookup)
DEFAULT_UNDERWRITER_NAME_FOR_LOOKUP = "Christina Rentas" # From CSV example - can be overridden by direct GUID
# If using direct GUIDs for testing:
DEFAULT_UNDERWRITER_GUID = "E4391D2A-58FB-4E2D-8B7D-3447D9E18C88" # From user

# Company/Branch Locations (Required for Quote creation)
# NEED ACTUAL GUIDS for Quoting, Issuing, and Company locations in 'ims_one'
# From sample quote for 'ims_one'
DEFAULT_QUOTING_LOCATION_GUID = "C5C006BB-6437-42F3-95D4-C090ADD3B37D"
DEFAULT_ISSUING_LOCATION_GUID = "C5C006BB-6437-42F3-95D4-C090ADD3B37D" # Often same as Quoting
DEFAULT_COMPANY_LOCATION_GUID = "DF35D4C7-C663-4974-A886-A1E18D3C9618"

# IMS Program (Associated with Line of Business)
# The sample quote has CompanyLineGuid = 09A5F49F-71FD-47FF-BBAE-77A5C298B435.
# This is noted as a combination of State, Line, and Company.
# We will use individual StateID, LineGUID, CompanyLocationGuid.
# The mapping of CSV "Program" (e.g., "Allied Health") to an IMS ProgramCode/ProgramID for 'ims_one' is still needed.
DEFAULT_PROGRAM_CODE_AHC = "AHC_STD_PROG" # Placeholder - NEEDS ACTUAL IMS_ONE Program Code for AHC Line
# DEFAULT_PROGRAM_ID_AHC = 12345 # Or ProgramID

# Other Default IDs (Values from 'ims_one' sample quote where available)
DEFAULT_QUOTE_STATUS_ID = 3       # From sample quote (e.g., 3 might be "Bound" or "Issued")
DEFAULT_BILLING_TYPE_ID = 3       # From sample quote
DEFAULT_INSURED_BUSINESS_TYPE_ID_STR = "Corporation" # API expects string. This maps to an ID.
                                                     # Sample quote had 21 for "Amit Test".
DEFAULT_TERMS_OF_PAYMENT_ID = 0   # Placeholder - NEED ACTUAL VALID ID from 'ims_one' or confirm if optional/defaulted by IMS
DEFAULT_RATER_ID = 0              # Placeholder - RaterID use (e.g. 100 for NetRate, custom for Excel) is for Part 2 of intake.
                                  # For initial submission, this might be 0 or not applicable.
DEFAULT_POLICY_TYPE_ID = 1        # From sample quote

# Optional: Technical Assistant/Customer Service Rep
# DEFAULT_TACSR_GUID = "YOUR_IMS_ONE_TACSR_GUID" # Sample quote has NULL for TACSRUserGuid

# --- Mappings and Default Logic ---

# Insured Business Type Mapping (for 'ims_one' environment)
# Maps string values (expected in API) to IMS BusinessTypeID
INSURED_BUSINESS_TYPE_MAPPING = {
    "Corporation": 13,
    "Partnership": 2,
    "Limited Liability Partnership": 3,
    "Individual": 4, # Note: there's also BusinessTypeID 4 for Individual. Sample quote had 21 for a test name. Clarify which ID "Individual" string should map to.
    "Other": 5,
    "Limited Liability Corporation": 9, # Often LLC
    "Joint Venture": 10,
    "Trust": 11,
    # From sample quote, "Amit Test" had InsuredBusinessTypeID = 21. What string does 21 represent?
    # Add more as needed
}

# Mapping from CSV "Program" field to our API's Line of Business and Program
LOB_PROGRAM_MAPPING = {
    "Allied Health": {
        "api_line_of_business_name": "AHC Primary", # To be sent in PolicySubmission.line_of_business
        "ims_line_guid": LINE_GUID_AHC_PRIMARY, # This is 'LineGUID' from sample quote
        "api_program_name": DEFAULT_PROGRAM_CODE_AHC, # To be sent in PolicySubmission.program. NEEDS CONFIRMATION
        "coverage_type_default": "Allied Health Professional Liability"
    },
    "Middle Market": { # Example, adjust as needed
        "api_line_of_business_name": "AHC Primary", # Or AHC Excess, TBD. Needs mapping confirmation.
        "ims_line_guid": LINE_GUID_AHC_PRIMARY,     # Or LINE_GUID_AHC_EXCESS
        "api_program_name": "MM_General_Program", # A specific program name for Middle Market. NEEDS CONFIRMATION
        "coverage_type_default": "Commercial General Liability"
    }
    # Add more mappings based on distinct values in CSV "Program" column
}

# --- Helper Functions for Data Transformation ---
def parse_date_mdy_to_ymd(date_str):
    """Converts M/D/YYYY or MM/DD/YYYY to YYYY-MM-DD"""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        from datetime import datetime
        # Attempt to parse common variations
        dt_obj = None
        for fmt in ("%m/%d/%Y", "%m/%d/%y", "%-m/%-d/%Y", "%-m/%-d/%y"):
            try:
                dt_obj = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        if dt_obj:
            return dt_obj.strftime("%Y-%m-%d")
    except Exception:
        pass # Log error appropriately in real use
    return None

def clean_numeric_string(value_str):
    """Removes $, commas, and converts to float. Handles percentages if '%' is present."""
    if isinstance(value_str, (int, float)):
        return float(value_str)
    if not value_str or not isinstance(value_str, str):
        return 0.0
    
    cleaned = str(value_str).strip()
    is_percentage = '%' in cleaned
    
    # Remove currency symbols and commas
    for char_to_remove in ['$', ',']:
        cleaned = cleaned.replace(char_to_remove, '')
    
    # Handle potential spaces if they represent thousands, e.g., "2 500" -> "2500"
    # This is a basic attempt; more robust parsing might be needed if formats vary wildly.
    # For now, focusing on removing common currency/comma noise.
    # If " " is used as a thousand separator, it needs more specific handling.
    # The current logic expects "2,500" or "2500".
    
    cleaned = cleaned.replace('%', '') # Remove percentage sign after checking its presence

    try:
        num = float(cleaned)
        if is_percentage:
            return num / 100.0 # Convert percentage to decimal (e.g., 17.5% -> 0.175)
        return num
    except ValueError:
        return 0.0 # Or raise error, or return None

def extract_insured_dba(insured_name_field):
    """Extracts DBA if present in 'Name dba DBA Name' format"""
    name_parts = insured_name_field.split(" dba ", 1)
    if len(name_parts) == 2:
        return name_parts[0].strip(), name_parts[1].strip()
    return insured_name_field.strip(), None

# --- Default Values for API Payload Construction ---
DEFAULT_COUNTRY = "USA"
DEFAULT_INSURED_CONTACT_PERSON_NAME_FALLBACK = "Primary Contact" # If specific contact not available
DEFAULT_LOCATION_STREET_ADDRESS = "N/A - See Insured Details" # Fallback if not in source

# --- Default Insured Address Details (can be overridden by more specific source data) ---
# From sample quote (Amit Test) - used if CSV doesn't provide full street/city
DEFAULT_INSURED_ADDRESS1 = "4732 N. Talman Avenue"
DEFAULT_INSURED_CITY = "Chicago"
DEFAULT_INSURED_STATE = "IL" # Sample quote uses IL
DEFAULT_INSURED_ZIP = "60606" # Sample quote uses 60606 