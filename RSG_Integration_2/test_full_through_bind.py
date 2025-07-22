#!/usr/bin/env python3
"""
Test script that runs the complete workflow through binding.
Processes a payload from start to finish: insured -> quote -> store data -> bind.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Try to import dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import all services
from app.services.ims.auth_service import get_auth_service
from app.services.ims.insured_service import get_insured_service
from app.services.ims.data_access_service import get_data_access_service
from app.services.ims.underwriter_service import get_underwriter_service
from app.services.ims.quote_service import get_quote_service
from app.services.ims.quote_options_service import get_quote_options_service
from app.services.ims.payload_processor_service import get_payload_processor_service
from app.services.ims.bind_service import get_bind_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_full_workflow(json_file):
    """Process the complete workflow from insured through binding."""
    print("\n" + "="*60)
    print(f"Full Workflow Processing: {json_file}")
    print("="*60)
    
    # Load payload
    try:
        with open(json_file, 'r') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"\n✗ Failed to load {json_file}: {e}")
        return False
    
    print(f"\nPayload Details:")
    print(f"  Policy: {payload.get('policy_number')}")
    print(f"  Insured: {payload.get('insured_name')}")
    print(f"  Premium: ${payload.get('net_premium', 0):,.2f}")
    print(f"  Transaction Type: {payload.get('transaction_type')}")
    
    results = {}
    
    # 1. Authenticate
    print("\n1. Authenticating...", end='', flush=True)
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(" ✗ FAILED")
        print(f"\nRequest: LoginIMSUser")
        print(f"Response: {auth_message}")
        return False
    print(" ✓")
    
    # 2. Find/Create Insured
    print("2. Finding/Creating Insured...", end='', flush=True)
    insured_service = get_insured_service()
    success, insured_guid, message = insured_service.find_or_create_insured(payload)
    
    if not success:
        print(" ✗ FAILED")
        request_data = {
            "function": "find_or_create_insured",
            "insured_name": payload.get('insured_name'),
            "address": payload.get('address_1'),
            "city": payload.get('city'),
            "state": payload.get('state'),
            "zip": payload.get('zip')
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    results['insured_guid'] = insured_guid
    print(f" ✓ {insured_guid}")
    
    # 3. Find Producer
    print("3. Finding Producer...", end='', flush=True)
    data_service = get_data_access_service()
    success, producer_info, message = data_service.process_producer_from_payload(payload)
    
    if not success:
        print(" ✗ FAILED")
        request_data = {
            "function": "process_producer_from_payload",
            "producer_name": payload.get('producer_name')
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    results['producer_contact_guid'] = producer_info.get('ProducerContactGUID')
    results['producer_location_guid'] = producer_info.get('ProducerLocationGUID')
    print(f" ✓")
    
    # 4. Find Underwriter
    print("4. Finding Underwriter...", end='', flush=True)
    underwriter_service = get_underwriter_service()
    success, underwriter_guid, message = underwriter_service.process_underwriter_from_payload(payload)
    
    if not success:
        print(" ✗ FAILED")
        request_data = {
            "function": "process_underwriter_from_payload",
            "underwriter_name": payload.get('underwriter_name')
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    results['underwriter_guid'] = underwriter_guid
    print(f" ✓")
    
    # 5. Create Quote (AddQuoteWithSubmission)
    print("5. Creating Quote with Submission...", end='', flush=True)
    quote_service = get_quote_service()
    success, quote_guid, message = quote_service.create_quote_from_payload(
        payload=payload,
        insured_guid=results['insured_guid'],
        producer_contact_guid=results['producer_contact_guid'],
        producer_location_guid=results['producer_location_guid'],
        underwriter_guid=results['underwriter_guid']
    )
    
    if not success:
        print(" ✗ FAILED")
        request_data = {
            "function": "create_quote_from_payload",
            "insured_guid": results['insured_guid'],
            "producer_contact_guid": results['producer_contact_guid'],
            "producer_location_guid": results['producer_location_guid'],
            "underwriter_guid": results['underwriter_guid'],
            "effective_date": payload.get('effective_date'),
            "expiration_date": payload.get('expiration_date'),
            "state": payload.get('insured_state')
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    results['quote_guid'] = quote_guid
    print(f" ✓")
    
    # 6. Add Quote Options
    print("6. Adding Quote Options...", end='', flush=True)
    quote_options_service = get_quote_options_service()
    success, option_info, message = quote_options_service.auto_add_quote_options(quote_guid)
    
    if not success:
        print(" ✗ FAILED")
        request_data = {
            "function": "auto_add_quote_options",
            "quote_guid": quote_guid
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    results['quote_option_guid'] = option_info.get('QuoteOptionGuid')
    print(f" ✓")
    
    # 7. Process Payload Data (Store in tblTritonQuoteData)
    print("7. Processing Payload Data...", end='', flush=True)
    payload_processor = get_payload_processor_service()
    
    success, result_data, message = payload_processor.process_payload(
        payload=payload,
        quote_guid=results['quote_guid'],
        quote_option_guid=results['quote_option_guid']
    )
    
    if not success:
        print(" ✗ FAILED")
        request_data = {
            "function": "process_payload",
            "quote_guid": results['quote_guid'],
            "quote_option_guid": results['quote_option_guid'],
            "policy_number": payload.get('policy_number'),
            "net_premium": payload.get('net_premium')
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        if result_data:
            print(f"Error details: {result_data}")
        return False
    print(" ✓")
    
    # 8. Bind Quote
    print("8. Binding Quote...", end='', flush=True)
    bind_service = get_bind_service()
    success, bound_policy_number, message = bind_service.bind_quote(results['quote_guid'])
    
    if not success:
        print(" ✗ FAILED")
        request_data = {
            "function": "BindQuote",
            "quote_guid": results['quote_guid']
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    results['bound_policy_number'] = bound_policy_number
    print(f" ✓")
    
    # Summary - show only extracted values on success
    print("\n" + "="*60)
    print("✓ WORKFLOW COMPLETE - QUOTE BOUND!")
    print("="*60)
    print(f"\nTransaction ID: {payload.get('transaction_id')}")
    print(f"Transaction Type: {payload.get('transaction_type')}")
    print(f"Insured Name: {payload.get('insured_name')}")
    print(f"Insured GUID: {results.get('insured_guid')}")
    print(f"Producer Contact GUID: {results.get('producer_contact_guid')}")
    print(f"Producer Location GUID: {results.get('producer_location_guid')}")
    print(f"Underwriter GUID: {results.get('underwriter_guid')}")
    print(f"Quote GUID: {results.get('quote_guid')}")
    print(f"Quote Option GUID: {results.get('quote_option_guid')}")
    print(f"Premium Registered: ${payload.get('net_premium', 0):,.2f}")
    print(f"\nOriginal Policy Number: {payload.get('policy_number')}")
    print(f"Bound Policy Number: {bound_policy_number}")
    print(f"Status: BOUND")
    
    return True


def main():
    """Run the test."""
    if len(sys.argv) != 2:
        print("Usage: python3 test_full_through_bind.py <json_file>")
        print("Example: python3 test_full_through_bind.py TEST.json")
        return 1
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"Error: File '{json_file}' not found")
        return 1
    
    print("\nIMS Full Workflow Test (Through Bind)")
    print("=====================================")
    print(f"Testing with payload file: {json_file}")
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please ensure .env file exists with:")
        print("  IMS_ONE_USERNAME=your_username")
        print("  IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Process the full workflow
    success = process_full_workflow(json_file)
    
    if success:
        print("\n✓ All steps completed successfully!")
        print("  Quote created, data stored, and policy bound.")
        return 0
    else:
        print("\n✗ Workflow failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())