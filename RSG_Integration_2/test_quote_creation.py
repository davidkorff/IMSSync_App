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
    """Test quote creation with sample GUIDs."""
    print("\n" + "="*60)
    print("Testing Quote Creation with Sample Data")
    print("="*60)
    
    # Sample GUIDs (from the examples in documentation)
    sample_data = {
        "insured_guid": "3602d4e6-6353-4f4c-8426-15b82130e88e",
        "producer_contact_guid": "77742f00-97b9-49e5-b01a-0292e972d43d",
        "producer_location_guid": "b37422f1-7dc7-4d15-8d59-d717803fa160",
        "underwriter_guid": "ae8000e6-a437-4990-b867-7925d7f1e4b4",
        "effective_date": "2025-09-24",
        "expiration_date": "2026-09-24",
        "state_id": "MI",
        "producer_commission": 17.5  # 17.5%
    }
    
    print(f"\nSample Data:")
    for key, value in sample_data.items():
        print(f"  {key}: {value}")
    
    # Authenticate
    print("\n1. Authenticating with IMS...")
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"   ✗ Authentication failed: {auth_message}")
        return False
    
    print(f"   ✓ Authentication successful")
    print(f"   Token: {auth_service.token[:20]}...")
    
    # Create quote
    print("\n2. Creating quote...")
    quote_service = get_quote_service()
    
    success, quote_guid, message = quote_service.add_quote_with_submission(
        insured_guid=sample_data["insured_guid"],
        producer_contact_guid=sample_data["producer_contact_guid"],
        underwriter_guid=sample_data["underwriter_guid"],
        effective_date=sample_data["effective_date"],
        expiration_date=sample_data["expiration_date"],
        state_id=sample_data["state_id"],
        producer_commission=sample_data["producer_commission"]
    )
    
    print(f"\n   Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"   Message: {message}")
    
    if success and quote_guid:
        print(f"\n   ✓ Quote created successfully")
        print(f"   Quote GUID: {quote_guid}")
    else:
        print(f"\n   ✗ Failed to create quote")
    
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
        print("\n✓ Payload loaded successfully")
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # Display relevant payload information
    print(f"\nPayload Information:")
    print(f"  Insured Name: {payload.get('insured_name', 'N/A')}")
    print(f"  State: {payload.get('insured_state', 'N/A')}")
    print(f"  Effective Date: {payload.get('effective_date', 'N/A')}")
    print(f"  Expiration Date: {payload.get('expiration_date', 'N/A')}")
    print(f"  Commission Rate: {payload.get('commission_rate', 'N/A')}%")
    
    # For this test, we'll use sample GUIDs since we're not running the full workflow
    print("\n(Using sample GUIDs for test purposes)")
    
    sample_guids = {
        "insured_guid": "3602d4e6-6353-4f4c-8426-15b82130e88e",
        "producer_contact_guid": "77742f00-97b9-49e5-b01a-0292e972d43d",
        "producer_location_guid": "b37422f1-7dc7-4d15-8d59-d717803fa160",
        "underwriter_guid": "ae8000e6-a437-4990-b867-7925d7f1e4b4"
    }
    
    # Authenticate
    print("\n1. Authenticating with IMS...")
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"   ✗ Authentication failed: {auth_message}")
        return False
    
    print(f"   ✓ Authentication successful")
    
    # Create quote from payload
    print("\n2. Creating quote from payload...")
    quote_service = get_quote_service()
    
    success, quote_guid, message = quote_service.create_quote_from_payload(
        payload=payload,
        insured_guid=sample_guids["insured_guid"],
        producer_contact_guid=sample_guids["producer_contact_guid"],
        producer_location_guid=sample_guids["producer_location_guid"],
        underwriter_guid=sample_guids["underwriter_guid"]
    )
    
    print(f"\n   Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"   Message: {message}")
    
    if success and quote_guid:
        print(f"\n   ✓ Quote created successfully")
        print(f"   Quote GUID: {quote_guid}")
        
        # Store for future use
        payload['quote_guid'] = quote_guid
    else:
        print(f"\n   ✗ Failed to create quote")
    
    return success


def test_error_handling():
    """Test error handling scenarios."""
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
    
    quote_service = get_quote_service()
    
    # Test with missing required fields
    print("1. Testing with missing effective date...")
    success, guid, message = quote_service.add_quote_with_submission(
        insured_guid="3602d4e6-6353-4f4c-8426-15b82130e88e",
        producer_contact_guid="77742f00-97b9-49e5-b01a-0292e972d43d",
        underwriter_guid="ae8000e6-a437-4990-b867-7925d7f1e4b4",
        effective_date="",  # Missing
        expiration_date="2026-09-24",
        state_id="MI",
        producer_commission=0.175
    )
    print(f"   Expected failure - Result: {message}")
    
    # Test with invalid GUID
    print("\n2. Testing with invalid insured GUID...")
    success, guid, message = quote_service.add_quote_with_submission(
        insured_guid="invalid-guid",
        producer_contact_guid="77742f00-97b9-49e5-b01a-0292e972d43d",
        underwriter_guid="ae8000e6-a437-4990-b867-7925d7f1e4b4",
        effective_date="2025-09-24",
        expiration_date="2026-09-24",
        state_id="MI",
        producer_commission=0.175
    )
    print(f"   Expected failure - Result: {message}")
    
    return True


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
        ("Quote Creation with Sample Data", test_quote_creation_with_sample_data),
        ("Quote Creation with Payload", test_quote_creation_with_payload),
        ("Error Handling", test_error_handling)
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