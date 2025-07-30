#!/usr/bin/env python3
"""
Test script for quote options service.
This test orchestrates all services to create a quote and add options.
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Try to import dotenv, mock if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Mock the dotenv module if not installed
    class MockDotenv:
        def load_dotenv(self):
            pass
    sys.modules['dotenv'] = MockDotenv()

# Import all services
from app.services.ims.auth_service import get_auth_service
from app.services.ims.insured_service import get_insured_service
from app.services.ims.data_access_service import get_data_access_service
from app.services.ims.underwriter_service import get_underwriter_service
from app.services.ims.quote_service import get_quote_service
from app.services.ims.quote_options_service import get_quote_options_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_complete_workflow():
    """Test the complete workflow from payload to quote with options."""
    print("\n" + "="*60)
    print("Testing Complete Workflow: Payload → Quote → Quote Options")
    print("="*60)
    
    # Load test payload
    try:
        with open('TEST.json', 'r') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # Store results
    results = {}
    
    # 1. Authenticate
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Request: LoginIMSUser")
        print(f"Response: {auth_message}")
        return False
    
    # 2. Find/Create Insured
    insured_service = get_insured_service()
    success, insured_guid, message = insured_service.find_or_create_insured(payload)
    
    if not success:
        print(f"\n✗ Failed to find/create insured")
        request_data = {
            "function": "find_or_create_insured",
            "insured_name": payload.get('insured_name')
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    
    results['insured_guid'] = insured_guid
    
    # 3. Find Producer
    data_service = get_data_access_service()
    success, producer_info, message = data_service.process_producer_from_payload(payload)
    
    if not success:
        print(f"\n✗ Failed to find producer")
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
    
    # 4. Find Underwriter
    underwriter_service = get_underwriter_service()
    success, underwriter_guid, message = underwriter_service.process_underwriter_from_payload(payload)
    
    if not success:
        print(f"\n✗ Failed to find underwriter")
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
    
    # 5. Create Quote
    quote_service = get_quote_service()
    success, quote_guid, message = quote_service.create_quote_from_payload(
        payload=payload,
        insured_guid=results['insured_guid'],
        producer_contact_guid=results['producer_contact_guid'],
        producer_location_guid=results['producer_location_guid'],
        underwriter_guid=results['underwriter_guid']
    )
    
    if not success:
        print(f"\n✗ Failed to create quote")
        request_data = {
            "function": "create_quote_from_payload",
            "effective_date": payload.get('effective_date'),
            "expiration_date": payload.get('expiration_date'),
            "state": payload.get('insured_state'),
            "commission_rate": payload.get('commission_rate')
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    
    results['quote_guid'] = quote_guid
    
    # 6. Add Quote Options
    quote_options_service = get_quote_options_service()
    success, option_info, message = quote_options_service.auto_add_quote_options(quote_guid)
    
    if not success:
        print(f"\n✗ Failed to add quote options")
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
    
    # Summary - show only extracted values on success
    print("\n" + "="*60)
    print("Workflow Complete!")
    print("="*60)
    print(f"\nAuthentication Token: {auth_service.token[:20]}...")
    print(f"Transaction ID: {payload.get('transaction_id')}")
    print(f"Insured Name: {payload.get('insured_name')}")
    print(f"Insured GUID: {results.get('insured_guid')}")
    print(f"Producer Contact GUID: {results.get('producer_contact_guid')}")
    print(f"Producer Location GUID: {results.get('producer_location_guid')}")
    print(f"Underwriter GUID: {results.get('underwriter_guid')}")
    print(f"Quote GUID: {results.get('quote_guid')}")
    print(f"Quote Option GUID: {results.get('quote_option_guid')}")
    print(f"Line GUID: {option_info.get('LineGuid')}")
    print(f"Line Name: {option_info.get('LineName')}")
    print(f"Company Location: {option_info.get('CompanyLocation')}")
    print(f"Status: SUCCESS")
    
    return True


def test_quote_options_only():
    """Test quote options with an existing quote GUID."""
    print("\n" + "="*60)
    print("Testing Quote Options Only")
    print("="*60)
    
    # Get quote GUID from user
    quote_guid = input("\nEnter an existing Quote GUID (or press Enter to skip): ").strip()
    
    if not quote_guid:
        print("Skipping test - no Quote GUID provided")
        return True
    
    # Authenticate
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Request: LoginIMSUser")
        print(f"Response: {auth_message}")
        return False
    
    # Add quote options
    quote_options_service = get_quote_options_service()
    
    request_data = {
        "function": "auto_add_quote_options",
        "quote_guid": quote_guid
    }
    
    success, option_info, message = quote_options_service.auto_add_quote_options(quote_guid)
    
    if success and option_info:
        # Success - show only extracted values
        print(f"\nAuthentication Token: {auth_service.token[:20]}...")
        print(f"Quote GUID: {quote_guid}")
        print(f"Quote Option GUID: {option_info.get('QuoteOptionGuid')}")
        print(f"Line GUID: {option_info.get('LineGuid')}")
        print(f"Line Name: {option_info.get('LineName')}")
        print(f"Company Location: {option_info.get('CompanyLocation')}")
        print(f"Status: SUCCESS")
    else:
        # Failure - show full request and response
        print(f"\n✗ Failed to add quote options")
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
    
    return success


def test_error_handling():
    """Test error handling for quote options."""
    print("\n" + "="*60)
    print("Testing Error Handling")
    print("="*60)
    
    # Authenticate
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Response: {auth_message}")
        return False
    
    quote_options_service = get_quote_options_service()
    
    # Test cases that should fail
    test_cases = [
        {"name": "invalid quote GUID", "guid": "invalid-guid"},
        {"name": "null quote GUID", "guid": "00000000-0000-0000-0000-000000000000"}
    ]
    
    all_passed = True
    for test in test_cases:
        request_data = {
            "function": "auto_add_quote_options",
            "quote_guid": test["guid"]
        }
        
        success, option_info, message = quote_options_service.auto_add_quote_options(test["guid"])
        
        if not success:
            # Expected failure - show details
            print(f"\n✓ {test['name']} test - Expected failure")
            print(f"Request Data:")
            print(json.dumps(request_data, indent=2))
            print(f"Response: {message}")
        else:
            # Unexpected success
            print(f"\n✗ {test['name']} test - Unexpected success")
            print(f"Quote Option GUID: {option_info.get('QuoteOptionGuid')}")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print("\nIMS Quote Options Test Suite")
    print("============================")
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please ensure .env file exists with:")
        print("  IMS_ONE_USERNAME=your_username")
        print("  IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Run tests
    tests = [
        ("Complete Workflow", test_complete_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if test_name in ["Quote Options Only", "Error Handling"]:
                # Optional tests
                response = input(f"\nRun {test_name} test? (y/n): ")
                if response.lower() != 'y':
                    results.append((test_name, True, "Skipped"))
                    continue
            
            print(f"\nRunning: {test_name}")
            success = test_func()
            results.append((test_name, success, "Passed" if success else "Failed"))
        except Exception as e:
            logger.exception(f"Test {test_name} failed with exception")
            results.append((test_name, False, f"Exception: {str(e)}"))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, success, status in results:
        print(f"{test_name}: {status}")
    
    # Overall result
    failed = sum(1 for _, success, status in results if not success and status != "Skipped")
    if failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())