#!/usr/bin/env python3
"""
Debug test for payload processing - shows SOAP request/response
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.services.ims.auth_service import get_auth_service
from app.services.ims.data_access_service import get_data_access_service

# Configure logging to DEBUG level to see SOAP requests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_stored_procedure():
    """Test the stored procedure directly with debug output."""
    
    # Load test payload
    with open('TEST.json', 'r') as f:
        payload = json.load(f)
    
    # Test GUIDs (use actual ones from a successful run)
    quote_guid = input("Enter Quote GUID: ").strip()
    quote_option_guid = input("Enter Quote Option GUID: ").strip()
    
    if not quote_guid or not quote_option_guid:
        print("GUIDs required!")
        return
    
    # Authenticate
    auth_service = get_auth_service()
    auth_success, _ = auth_service.login()
    
    if not auth_success:
        print("Authentication failed")
        return
    
    # Build parameters
    data_service = get_data_access_service()
    
    # Build parameters array
    parameters = [
        "QuoteGuid", quote_guid,
        "QuoteOptionGuid", quote_option_guid,
        "umr", str(payload.get("umr", "")),
        "agreement_number", str(payload.get("agreement_number", "")),
        "section_number", str(payload.get("section_number", "")),
        "class_of_business", str(payload.get("class_of_business", "")),
        "program_name", str(payload.get("program_name", "")),
        "policy_number", str(payload.get("policy_number", "")),
        "underwriter_name", str(payload.get("underwriter_name", "")),
        "producer_name", str(payload.get("producer_name", "")),
        "invoice_date", str(payload.get("invoice_date", "")),
        "policy_fee", str(payload.get("policy_fee", "")),
        "surplus_lines_tax", str(payload.get("surplus_lines_tax", "")),
        "stamping_fee", str(payload.get("stamping_fee", "")),
        "other_fee", str(payload.get("other_fee", "")),
        "insured_name", str(payload.get("insured_name", "")),
        "insured_state", str(payload.get("insured_state", "")),
        "insured_zip", str(payload.get("insured_zip", "")),
        "effective_date", str(payload.get("effective_date", "")),
        "expiration_date", str(payload.get("expiration_date", "")),
        "bound_date", str(payload.get("bound_date", "")),
        "opportunity_type", str(payload.get("opportunity_type", "")),
        "business_type", str(payload.get("business_type", "")),
        "status", str(payload.get("status", "")),
        "limit_amount", str(payload.get("limit_amount", "")),
        "limit_prior", str(payload.get("limit_prior", "")),
        "deductible_amount", str(payload.get("deductible_amount", "")),
        "gross_premium", str(payload.get("gross_premium", "")),
        "commission_rate", str(payload.get("commission_rate", "")),
        "commission_percent", str(payload.get("commission_percent", "")),
        "commission_amount", str(payload.get("commission_amount", "")),
        "net_premium", str(payload.get("net_premium", "")),
        "base_premium", str(payload.get("base_premium", "")),
        "opportunity_id", str(payload.get("opportunity_id", "")),
        "midterm_endt_id", str(payload.get("midterm_endt_id", "")),
        "midterm_endt_description", str(payload.get("midterm_endt_description", "")),
        "midterm_endt_effective_from", str(payload.get("midterm_endt_effective_from", "")),
        "midterm_endt_endorsement_number", str(payload.get("midterm_endt_endorsement_number", "")),
        "additional_insured", json.dumps(payload.get("additional_insured", [])),
        "address_1", str(payload.get("address_1", "")),
        "address_2", str(payload.get("address_2", "")),
        "city", str(payload.get("city", "")),
        "state", str(payload.get("state", "")),
        "zip", str(payload.get("zip", "")),
        "transaction_id", str(payload.get("transaction_id", "")),
        "transaction_type", str(payload.get("transaction_type", "")),
        "transaction_date", str(payload.get("transaction_date", "")),
        "source_system", str(payload.get("source_system", ""))
    ]
    
    print("\nCalling stored procedure with parameters...")
    success, result_xml, message = data_service.execute_dataset(
        "spProcessTritonPayload_WS",
        parameters
    )
    
    if success:
        print("\n✓ Success!")
        print(f"Result XML: {result_xml}")
    else:
        print("\n✗ Failed!")
        print(f"Error: {message}")

if __name__ == "__main__":
    test_stored_procedure()