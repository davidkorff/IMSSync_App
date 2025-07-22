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

# Mock the dotenv module
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
        print("\n✓ Payload loaded successfully")
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # Display workflow overview
    print(f"\nWorkflow Overview:")
    print(f"  1. Authenticate with IMS")
    print(f"  2. Find/Create Insured")
    print(f"  3. Find Producer")
    print(f"  4. Find Underwriter")
    print(f"  5. Create Quote")
    print(f"  6. Add Quote Options")
    
    # Store results
    results = {}
    
    # 1. Authenticate
    print("\n" + "-"*60)
    print("Step 1: Authenticating with IMS...")
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"   ✗ Authentication failed: {auth_message}")
        return False
    
    print(f"   ✓ Authentication successful")
    print(f"   Token: {auth_service.token[:20]}...")
    
    # 2. Find/Create Insured
    print("\n" + "-"*60)
    print("Step 2: Finding/Creating Insured...")
    print(f"   Insured Name: {payload.get('insured_name', 'N/A')}")
    
    insured_service = get_insured_service()
    success, insured_guid, message = insured_service.find_or_create_insured(payload)
    
    if not success:
        print(f"   ✗ Failed: {message}")
        return False
    
    print(f"   ✓ Insured GUID: {insured_guid}")
    results['insured_guid'] = insured_guid
    
    # 3. Find Producer
    print("\n" + "-"*60)
    print("Step 3: Finding Producer...")
    print(f"   Producer Name: {payload.get('producer_name', 'N/A')}")
    
    data_service = get_data_access_service()
    success, producer_info, message = data_service.process_producer_from_payload(payload)
    
    if not success:
        print(f"   ✗ Failed: {message}")
        return False
    
    print(f"   ✓ Producer Contact GUID: {producer_info.get('ProducerContactGUID', 'N/A')}")
    print(f"   ✓ Producer Location GUID: {producer_info.get('ProducerLocationGUID', 'N/A')}")
    results['producer_contact_guid'] = producer_info.get('ProducerContactGUID')
    results['producer_location_guid'] = producer_info.get('ProducerLocationGUID')
    
    # 4. Find Underwriter
    print("\n" + "-"*60)
    print("Step 4: Finding Underwriter...")
    print(f"   Underwriter Name: {payload.get('underwriter_name', 'N/A')}")
    
    underwriter_service = get_underwriter_service()
    success, underwriter_guid, message = underwriter_service.process_underwriter_from_payload(payload)
    
    if not success:
        print(f"   ✗ Failed: {message}")
        return False
    
    print(f"   ✓ Underwriter GUID: {underwriter_guid}")
    results['underwriter_guid'] = underwriter_guid
    
    # 5. Create Quote
    print("\n" + "-"*60)
    print("Step 5: Creating Quote...")
    print(f"   Effective Date: {payload.get('effective_date', 'N/A')}")
    print(f"   Expiration Date: {payload.get('expiration_date', 'N/A')}")
    print(f"   State: {payload.get('insured_state', 'N/A')}")
    print(f"   Commission Rate: {payload.get('commission_rate', 'N/A')}%")
    
    quote_service = get_quote_service()
    success, quote_guid, message = quote_service.create_quote_from_payload(
        payload=payload,
        insured_guid=results['insured_guid'],
        producer_contact_guid=results['producer_contact_guid'],
        producer_location_guid=results['producer_location_guid'],
        underwriter_guid=results['underwriter_guid']
    )
    
    if not success:
        print(f"   ✗ Failed: {message}")
        return False
    
    print(f"   ✓ Quote GUID: {quote_guid}")
    results['quote_guid'] = quote_guid
    
    # 6. Add Quote Options
    print("\n" + "-"*60)
    print("Step 6: Adding Quote Options...")
    
    quote_options_service = get_quote_options_service()
    success, option_info, message = quote_options_service.auto_add_quote_options(quote_guid)
    
    if not success:
        print(f"   ✗ Failed: {message}")
        return False
    
    print(f"   ✓ Quote Option GUID: {option_info.get('QuoteOptionGuid', 'N/A')}")
    print(f"   Line GUID: {option_info.get('LineGuid', 'N/A')}")
    print(f"   Line Name: {option_info.get('LineName', 'N/A')}")
    print(f"   Company Location: {option_info.get('CompanyLocation', 'N/A')}")
    results['quote_option_guid'] = option_info.get('QuoteOptionGuid')
    
    # Summary
    print("\n" + "="*60)
    print("Workflow Complete!")
    print("="*60)
    print(f"\nFinal Results:")
    print(f"  Transaction ID: {payload.get('transaction_id', 'N/A')}")
    print(f"  Insured GUID: {results.get('insured_guid', 'N/A')}")
    print(f"  Quote GUID: {results.get('quote_guid', 'N/A')}")
    print(f"  Quote Option GUID: {results.get('quote_option_guid', 'N/A')}")
    
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
    print("\n1. Authenticating with IMS...")
    auth_service = get_auth_service()
    auth_success, _ = auth_service.login()
    
    if not auth_success:
        print("   ✗ Authentication failed")
        return False
    
    print("   ✓ Authentication successful")
    
    # Add quote options
    print("\n2. Adding quote options...")
    quote_options_service = get_quote_options_service()
    success, option_info, message = quote_options_service.auto_add_quote_options(quote_guid)
    
    print(f"\n   Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"   Message: {message}")
    
    if success and option_info:
        print(f"\n   Quote Option Details:")
        print(f"   Quote Option GUID: {option_info.get('QuoteOptionGuid', 'N/A')}")
        print(f"   Line GUID: {option_info.get('LineGuid', 'N/A')}")
        print(f"   Line Name: {option_info.get('LineName', 'N/A')}")
        print(f"   Company Location: {option_info.get('CompanyLocation', 'N/A')}")
    
    return success


def test_error_handling():
    """Test error handling for quote options."""
    print("\n" + "="*60)
    print("Testing Error Handling")
    print("="*60)
    
    # Authenticate
    print("\nAuthenticating...")
    auth_service = get_auth_service()
    auth_success, _ = auth_service.login()
    
    if not auth_success:
        print("Authentication failed")
        return False
    
    print("✓ Authenticated successfully\n")
    
    quote_options_service = get_quote_options_service()
    
    # Test with invalid GUID
    print("1. Testing with invalid quote GUID...")
    success, option_info, message = quote_options_service.auto_add_quote_options("invalid-guid")
    print(f"   Expected failure - Result: {message}")
    
    # Test with null GUID
    print("\n2. Testing with null quote GUID...")
    success, option_info, message = quote_options_service.auto_add_quote_options("00000000-0000-0000-0000-000000000000")
    print(f"   Expected failure - Result: {message}")
    
    return True


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
        ("Complete Workflow", test_complete_workflow),
        ("Quote Options Only", test_quote_options_only),
        ("Error Handling", test_error_handling)
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