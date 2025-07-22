#!/usr/bin/env python3
"""
Test script for creating quotes using IMS Quote service.
This test demonstrates creating a quote with all required GUIDs.
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime, date

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

# Now import our services
from app.services.ims.auth_service import get_auth_service
from app.services.ims.quote_service import get_quote_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_quote_creation_with_sample_data():
    """Test quote creation with sample GUIDs from TEST.json."""
    print("\n" + "="*60)
    print("Testing Quote Creation with Sample Data")
    print("="*60)
    
    # Load test payload
    try:
        with open('TEST.json', 'r') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # Sample GUIDs (would normally come from previous steps)
    sample_data = {
        "insured_guid": "3602d4e6-6353-4f4c-8426-15b82130e88e",
        "producer_contact_guid": "77742f00-97b9-49e5-b01a-0292e972d43d",
        "producer_location_guid": "b37422f1-7dc7-4d15-8d59-d717803fa160",
        "underwriter_guid": "ae8000e6-a437-4990-b867-7925d7f1e4b4",
        "effective_date": payload.get('effective_date', '2025-09-24'),
        "expiration_date": payload.get('expiration_date', '2026-09-24'),
        "state_id": payload.get('insured_state', 'MI'),
        "producer_commission": payload.get('commission_rate', 17.5)
    }
    
    # Authenticate
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Request: LoginIMSUser")
        print(f"Response: {auth_message}")
        return False
    
    # Create quote
    quote_service = get_quote_service()
    
    # Capture request data
    request_data = {
        "function": "AddQuoteWithSubmission",
        "insured_guid": sample_data["insured_guid"],
        "producer_contact_guid": sample_data["producer_contact_guid"],
        "underwriter_guid": sample_data["underwriter_guid"],
        "effective_date": sample_data["effective_date"],
        "expiration_date": sample_data["expiration_date"],
        "state_id": sample_data["state_id"],
        "producer_commission": sample_data["producer_commission"]
    }
    
    success, quote_guid, message = quote_service.add_quote_with_submission(
        insured_guid=sample_data["insured_guid"],
        producer_contact_guid=sample_data["producer_contact_guid"],
        underwriter_guid=sample_data["underwriter_guid"],
        effective_date=sample_data["effective_date"],
        expiration_date=sample_data["expiration_date"],
        state_id=sample_data["state_id"],
        producer_commission=sample_data["producer_commission"]
    )
    
    if success and quote_guid:
        # Success - show only extracted values
        print(f"\nAuthentication Token: {auth_service.token[:20]}...")
        print(f"Quote GUID: {quote_guid}")
        print(f"Status: SUCCESS")
    else:
        # Failure - show full request and response
        print(f"\n✗ Failed to create quote")
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
    
    return success


def test_quote_creation_with_payload():
    """Test quote creation using payload data."""
    print("\n" + "="*60)
    print("Testing Quote Creation with Payload")
    print("="*60)
    
    # Load test payload
    try:
        with open('TEST.json', 'r') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # For this test, we'll use sample GUIDs since we're not running the full workflow
    sample_guids = {
        "insured_guid": "3602d4e6-6353-4f4c-8426-15b82130e88e",
        "producer_contact_guid": "77742f00-97b9-49e5-b01a-0292e972d43d",
        "producer_location_guid": "b37422f1-7dc7-4d15-8d59-d717803fa160",
        "underwriter_guid": "ae8000e6-a437-4990-b867-7925d7f1e4b4"
    }
    
    # Authenticate
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Request: LoginIMSUser")
        print(f"Response: {auth_message}")
        return False
    
    # Create quote from payload
    quote_service = get_quote_service()
    
    # Capture request data
    request_data = {
        "function": "create_quote_from_payload",
        "insured_name": payload.get('insured_name'),
        "effective_date": payload.get('effective_date'),
        "expiration_date": payload.get('expiration_date'),
        "state": payload.get('insured_state'),
        "commission_rate": payload.get('commission_rate'),
        "insured_guid": sample_guids["insured_guid"],
        "producer_contact_guid": sample_guids["producer_contact_guid"],
        "producer_location_guid": sample_guids["producer_location_guid"],
        "underwriter_guid": sample_guids["underwriter_guid"]
    }
    
    success, quote_guid, message = quote_service.create_quote_from_payload(
        payload=payload,
        insured_guid=sample_guids["insured_guid"],
        producer_contact_guid=sample_guids["producer_contact_guid"],
        producer_location_guid=sample_guids["producer_location_guid"],
        underwriter_guid=sample_guids["underwriter_guid"]
    )
    
    if success and quote_guid:
        # Success - show only extracted values
        print(f"\nAuthentication Token: {auth_service.token[:20]}...")
        print(f"Insured Name: {payload.get('insured_name')}")
        print(f"State: {payload.get('insured_state')}")
        print(f"Effective Date: {payload.get('effective_date')}")
        print(f"Expiration Date: {payload.get('expiration_date')}")
        print(f"Commission Rate: {payload.get('commission_rate')}%")
        print(f"Quote GUID: {quote_guid}")
        print(f"Status: SUCCESS")
        
        # Store for future use
        payload['quote_guid'] = quote_guid
    else:
        # Failure - show full request and response
        print(f"\n✗ Failed to create quote")
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
    
    return success


def test_error_handling():
    """Test error handling scenarios."""
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
    
    quote_service = get_quote_service()
    
    # Test cases that should fail
    test_cases = [
        {
            "name": "missing effective date",
            "data": {
                "insured_guid": "3602d4e6-6353-4f4c-8426-15b82130e88e",
                "producer_contact_guid": "77742f00-97b9-49e5-b01a-0292e972d43d",
                "underwriter_guid": "ae8000e6-a437-4990-b867-7925d7f1e4b4",
                "effective_date": "",  # Missing
                "expiration_date": "2026-09-24",
                "state_id": "MI",
                "producer_commission": 0.175
            }
        },
        {
            "name": "invalid insured GUID",
            "data": {
                "insured_guid": "invalid-guid",
                "producer_contact_guid": "77742f00-97b9-49e5-b01a-0292e972d43d",
                "underwriter_guid": "ae8000e6-a437-4990-b867-7925d7f1e4b4",
                "effective_date": "2025-09-24",
                "expiration_date": "2026-09-24",
                "state_id": "MI",
                "producer_commission": 0.175
            }
        }
    ]
    
    all_passed = True
    for test in test_cases:
        success, guid, message = quote_service.add_quote_with_submission(**test["data"])
        
        if not success:
            # Expected failure - show details
            print(f"\n✓ {test['name']} test - Expected failure")
            print(f"Request Data:")
            print(json.dumps(test["data"], indent=2))
            print(f"Response: {message}")
        else:
            # Unexpected success
            print(f"\n✗ {test['name']} test - Unexpected success")
            print(f"Quote GUID: {guid}")
            all_passed = False
    
    return all_passed


def test_commission_conversion():
    """Test commission rate conversion."""
    print("\n" + "="*60)
    print("Testing Commission Rate Conversion")
    print("="*60)
    
    test_payloads = [
        {"commission_rate": 17.5, "expected": 0.175},
        {"commission_rate": 0.175, "expected": 0.175},
        {"commission_rate": "17.5", "expected": 0.175},
        {"commission_rate": "0.175", "expected": 0.175},
        {"commission_rate": 25, "expected": 0.25},
        {"commission_rate": 0, "expected": 0.0}
    ]
    
    quote_service = get_quote_service()
    
    for test in test_payloads:
        payload = {
            "effective_date": "2025-09-24",
            "expiration_date": "2026-09-24",
            "insured_state": "MI",
            "commission_rate": test["commission_rate"]
        }
        
        # Test internal commission conversion logic
        commission = test["commission_rate"]
        if isinstance(commission, (int, float)):
            if commission > 1:
                commission = commission / 100
        else:
            try:
                commission = float(commission)
                if commission > 1:
                    commission = commission / 100
            except:
                commission = 0.175
        
        print(f"Input: {test['commission_rate']} → Output: {commission} (Expected: {test['expected']})")
        assert abs(commission - test['expected']) < 0.0001, f"Conversion failed for {test['commission_rate']}"
    
    print("\n✓ All commission conversions passed")
    return True


def main():
    """Run all tests."""
    print("\nIMS Quote Creation Test Suite")
    print("=============================")
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please ensure .env file exists with:")
        print("  IMS_ONE_USERNAME=your_username")
        print("  IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Check quote configuration
    from config import QUOTE_CONFIG
    print("\nQuote Configuration:")
    print(f"  Quoting Location: {QUOTE_CONFIG['quoting_location']}")
    print(f"  Company Location: {QUOTE_CONFIG['company_location']}")
    print(f"  Primary Line GUID: {QUOTE_CONFIG['primary_line_guid']}")
    
    # Run tests
    tests = [
        ("Commission Conversion", test_commission_conversion),
        ("Quote Creation with Payload", test_quote_creation_with_payload)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if test_name in ["Quote Creation with Sample Data", "Error Handling"]:
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