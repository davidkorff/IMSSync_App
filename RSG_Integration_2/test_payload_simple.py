#!/usr/bin/env python3
"""
Simple test script for payload processing.
Just processes the JSON file you give it - no confusing extra tests.
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
from app.services.ims.issue_service import get_issue_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_transaction(json_file):
    """Process the transaction from start to finish."""
    print("\n" + "="*60)
    print(f"Processing Transaction: {json_file}")
    print("="*60)
    
    # Load payload
    try:
        with open(json_file, 'r') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"\n✗ Failed to load {json_file}: {e}")
        return False
    
    print(f"\nTransaction Details:")
    print(f"  Type: {payload.get('transaction_type')}")
    print(f"  Policy: {payload.get('policy_number')}")
    print(f"  Insured: {payload.get('insured_name')}")
    print(f"  Premium: ${payload.get('net_premium', 0):,.2f}")
    
    results = {}
    
    # 1. Authenticate
    print("\n1. Authenticating...", end='', flush=True)
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(" ✗ FAILED")
        print(f"   Error: {auth_message}")
        return False
    print(" ✓")
    
    # 2. Find/Create Insured
    print("2. Finding/Creating Insured...", end='', flush=True)
    insured_service = get_insured_service()
    success, insured_guid, message = insured_service.find_or_create_insured(payload)
    
    if not success:
        print(" ✗ FAILED")
        print(f"   Error: {message}")
        return False
    results['insured_guid'] = insured_guid
    print(f" ✓ {insured_guid}")
    
    # 3. Find Producer
    print("3. Finding Producer...", end='', flush=True)
    data_service = get_data_access_service()
    success, producer_info, message = data_service.process_producer_from_payload(payload)
    
    if not success:
        print(" ✗ FAILED")
        print(f"   Error: {message}")
        return False
    results['producer_contact_guid'] = producer_info.get('ProducerContactGUID')
    results['producer_location_guid'] = producer_info.get('ProducerLocationGUID')
    print(f" ✓ {results['producer_contact_guid']}")
    
    # 4. Find Underwriter
    print("4. Finding Underwriter...", end='', flush=True)
    underwriter_service = get_underwriter_service()
    success, underwriter_guid, message = underwriter_service.process_underwriter_from_payload(payload)
    
    if not success:
        print(" ✗ FAILED")
        print(f"   Error: {message}")
        return False
    results['underwriter_guid'] = underwriter_guid
    print(f" ✓ {underwriter_guid}")
    
    # 5. Create Quote
    print("5. Creating Quote...", end='', flush=True)
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
        print(f"   Error: {message}")
        return False
    results['quote_guid'] = quote_guid
    print(f" ✓ {quote_guid}")
    
    # 6. Add Quote Options
    print("6. Adding Quote Options...", end='', flush=True)
    quote_options_service = get_quote_options_service()
    success, option_info, message = quote_options_service.auto_add_quote_options(quote_guid)
    
    if not success:
        print(" ✗ FAILED")
        print(f"   Error: {message}")
        return False
    results['quote_option_guid'] = option_info.get('QuoteOptionGuid')
    print(f" ✓ {results['quote_option_guid']}")
    
    # 7. Process Payload (Store in tblTritonQuoteData)
    print("7. Storing Payload Data...", end='', flush=True)
    payload_processor = get_payload_processor_service()
    
    success, result_data, message = payload_processor.process_payload(
        payload=payload,
        quote_guid=results['quote_guid'],
        quote_option_guid=results['quote_option_guid']
    )
    
    if not success:
        print(" ✗ FAILED")
        print(f"   Error: {message}")
        return False
    print(" ✓ Data stored in tblTritonQuoteData")
    
    # 8. Handle transaction type
    transaction_type = payload.get('transaction_type', '').lower()
    
    if transaction_type == 'bind':
        print("8. Binding Quote...", end='', flush=True)
        bind_service = get_bind_service()
        success, policy_number, message = bind_service.bind_quote(results['quote_guid'])
        
        if not success:
            print(" ✗ FAILED")
            print(f"   Error: {message}")
            return False
        results['bound_policy_number'] = policy_number
        print(f" ✓ Policy: {policy_number}")
        
    elif transaction_type == 'issue':
        # First bind
        print("8a. Binding Quote...", end='', flush=True)
        bind_service = get_bind_service()
        success, policy_number, message = bind_service.bind_quote(results['quote_guid'])
        
        if not success:
            print(" ✗ FAILED")
            print(f"   Error: {message}")
            return False
        results['bound_policy_number'] = policy_number
        print(f" ✓ Policy: {policy_number}")
        
        # Then issue
        print("8b. Issuing Policy...", end='', flush=True)
        issue_service = get_issue_service()
        success, issue_date, message = issue_service.issue_policy(results['quote_guid'])
        
        if not success:
            print(" ✗ FAILED")
            print(f"   Error: {message}")
            return False
        results['issue_date'] = issue_date
        print(f" ✓ Issued: {issue_date}")
    
    # Summary
    print("\n" + "="*60)
    print("✓ TRANSACTION COMPLETE")
    print("="*60)
    print(f"\nQuote GUID: {results.get('quote_guid')}")
    print(f"Quote Option GUID: {results.get('quote_option_guid')}")
    if results.get('bound_policy_number'):
        print(f"Policy Number: {results.get('bound_policy_number')}")
    if results.get('issue_date'):
        print(f"Issue Date: {results.get('issue_date')}")
    
    return True


def main():
    """Run the test."""
    if len(sys.argv) != 2:
        print("Usage: python3 test_payload_simple.py <json_file>")
        print("Example: python3 test_payload_simple.py TEST.json")
        return 1
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"Error: File '{json_file}' not found")
        return 1
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please ensure .env file exists with:")
        print("  IMS_ONE_USERNAME=your_username")
        print("  IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Process the transaction
    success = process_transaction(json_file)
    
    if success:
        print("\n✓ All steps completed successfully!")
        return 0
    else:
        print("\n✗ Transaction failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())