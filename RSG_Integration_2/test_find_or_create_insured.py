#!/usr/bin/env python3
"""
Test script for finding or creating insured records in IMS.
This demonstrates the complete flow of processing a Triton payload.
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

# Now import our services
from app.services.ims.auth_service import get_auth_service
from app.services.ims.insured_service import get_insured_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_with_payload():
    """Test the find or create flow with the actual payload."""
    print("\n" + "="*60)
    print("Testing Find or Create Insured with Payload")
    print("="*60)
    
    # Load test payload
    try:
        with open('TEST.json', 'r') as f:
            payload = json.load(f)
        print("\n✓ Payload loaded successfully")
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # Display payload information
    print(f"\nPayload Information:")
    print(f"  Transaction ID: {payload.get('transaction_id', 'N/A')}")
    print(f"  Transaction Type: {payload.get('transaction_type', 'N/A')}")
    print(f"  Insured Name: {payload.get('insured_name', 'N/A')}")
    print(f"  Address: {payload.get('address_1', 'N/A')}")
    print(f"  City, State ZIP: {payload.get('city', 'N/A')}, {payload.get('state', 'N/A')} {payload.get('zip', 'N/A')}")
    
    # Authenticate
    print("\n1. Authenticating with IMS...")
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"   ✗ Authentication failed: {auth_message}")
        return False
    
    print(f"   ✓ Authentication successful")
    print(f"   Token: {auth_service.token[:20]}...")
    
    # Find or create insured
    print("\n2. Processing insured (find or create)...")
    insured_service = get_insured_service()
    
    success, insured_guid, message = insured_service.find_or_create_insured(payload)
    
    print(f"\n   Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"   Message: {message}")
    
    if success:
        print(f"   Insured GUID: {insured_guid}")
        
        # Store the GUID for future use
        payload['insured_guid'] = insured_guid
        print(f"\n   ✓ Insured ready for transaction processing")
        print(f"   GUID has been added to payload for next steps")
    else:
        print(f"\n   ✗ Failed to find or create insured")
    
    return success


def test_specific_scenarios():
    """Test specific scenarios for find or create."""
    print("\n" + "="*60)
    print("Testing Specific Scenarios")
    print("="*60)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Existing Insured Test",
            "payload": {
                "insured_name": "BLC Industries, LLC",
                "address_1": "2222 The Dells",
                "address_2": "",
                "city": "Kalamazoo",
                "state": "MI",
                "zip": "49048"
            }
        },
        {
            "name": "New Insured Test",
            "payload": {
                "insured_name": f"Test Company {datetime.now().strftime('%Y%m%d%H%M%S')}",
                "address_1": "123 Test Street",
                "address_2": "Suite 100",
                "city": "TestCity",
                "state": "CA",
                "zip": "90210"
            }
        },
        {
            "name": "Missing Address Test",
            "payload": {
                "insured_name": "Incomplete Company LLC",
                "city": "TestCity",
                "state": "CA"
                # Missing address_1 and zip - should fail creation
            }
        }
    ]
    
    # Authenticate once
    print("\nAuthenticating...")
    auth_service = get_auth_service()
    auth_success, _ = auth_service.login()
    
    if not auth_success:
        print("Authentication failed")
        return False
    
    print("✓ Authenticated successfully\n")
    
    # Test each scenario
    insured_service = get_insured_service()
    results = []
    
    for test_case in test_cases:
        print(f"\nScenario: {test_case['name']}")
        print(f"  Insured: {test_case['payload'].get('insured_name', 'N/A')}")
        
        success, guid, message = insured_service.find_or_create_insured(test_case['payload'])
        
        print(f"  Result: {'SUCCESS' if success else 'FAILED'}")
        print(f"  Message: {message}")
        if success:
            print(f"  GUID: {guid}")
        
        results.append((test_case['name'], success))
    
    # Summary
    print("\n" + "-"*60)
    print("Scenario Summary:")
    for name, success in results:
        print(f"  {name}: {'✓ Success' if success else '✗ Failed'}")
    
    return all(success for _, success in results[:2])  # First two should succeed


def test_direct_create():
    """Test creating an insured directly."""
    print("\n" + "="*60)
    print("Testing Direct Insured Creation")
    print("="*60)
    
    # Authenticate
    print("\nAuthenticating...")
    auth_service = get_auth_service()
    auth_success, _ = auth_service.login()
    
    if not auth_success:
        print("Authentication failed")
        return False
    
    print("✓ Authenticated successfully\n")
    
    # Create test insured
    insured_service = get_insured_service()
    test_name = f"Direct Test Company {datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    print(f"Creating insured: {test_name}")
    
    success, guid, message = insured_service.add_insured_with_location(
        insured_name=test_name,
        address1="456 Direct Street",
        city="DirectCity",
        state="TX",
        zip_code="75001",
        address2="Floor 2"
    )
    
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
    print(f"Message: {message}")
    if success:
        print(f"GUID: {guid}")
    
    return success


def main():
    """Run all tests."""
    print("\nIMS Find or Create Insured Test Suite")
    print("=====================================")
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please set environment variables:")
        print("  export IMS_ONE_USERNAME=your_username")
        print("  export IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Run tests
    tests = [
        ("Find or Create with Payload", test_with_payload),
        ("Specific Scenarios", test_specific_scenarios),
        ("Direct Create", test_direct_create)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if test_name == "Direct Create":
                # Optional test
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