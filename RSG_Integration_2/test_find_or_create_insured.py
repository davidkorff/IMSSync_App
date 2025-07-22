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
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # Authenticate
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Request: LoginIMSUser")
        print(f"Response: {auth_message}")
        return False
    
    # Find or create insured
    insured_service = get_insured_service()
    
    # Capture request details before making the call
    request_data = {
        "insured_name": payload.get('insured_name'),
        "address_1": payload.get('address_1'),
        "city": payload.get('city'),
        "state": payload.get('state'),
        "zip": payload.get('zip')
    }
    
    success, insured_guid, message = insured_service.find_or_create_insured(payload)
    
    if success:
        # Success - show only extracted values
        print(f"\nAuthentication Token: {auth_service.token[:20]}...")
        print(f"Insured GUID: {insured_guid}")
        print(f"Status: SUCCESS")
        
        # Store the GUID for future use
        payload['insured_guid'] = insured_guid
    else:
        # Failure - show full request and response
        print(f"\n✗ Failed to find or create insured")
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
    
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
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print("\n✗ Authentication failed")
        print(f"Response: {auth_message}")
        return False
    
    # Test each scenario
    insured_service = get_insured_service()
    results = []
    successful_results = []
    
    for test_case in test_cases:
        success, guid, message = insured_service.find_or_create_insured(test_case['payload'])
        
        if success:
            successful_results.append({
                "name": test_case['name'],
                "guid": guid,
                "insured_name": test_case['payload'].get('insured_name')
            })
        else:
            # Show failure details
            print(f"\n✗ {test_case['name']} FAILED")
            print(f"\nRequest Data:")
            print(json.dumps(test_case['payload'], indent=2))
            print(f"\nFull Response:")
            print(f"{message}")
        
        results.append((test_case['name'], success))
    
    # Show successful results
    if successful_results:
        print("\nSuccessful Results:")
        for result in successful_results:
            print(f"\n{result['name']}:")
            print(f"  Insured Name: {result['insured_name']}")
            print(f"  GUID: {result['guid']}")
    
    return all(success for _, success in results[:2])  # First two should succeed


def test_direct_create():
    """Test creating an insured directly."""
    print("\n" + "="*60)
    print("Testing Direct Insured Creation")
    print("="*60)
    
    # Authenticate
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print("\n✗ Authentication failed")
        print(f"Response: {auth_message}")
        return False
    
    # Create test insured
    insured_service = get_insured_service()
    test_name = f"Direct Test Company {datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Request data for potential failure logging
    request_data = {
        "insured_name": test_name,
        "address1": "456 Direct Street",
        "city": "DirectCity",
        "state": "TX",
        "zip_code": "75001",
        "address2": "Floor 2"
    }
    
    success, guid, message = insured_service.add_insured_with_location(
        insured_name=test_name,
        address1="456 Direct Street",
        city="DirectCity",
        state="TX",
        zip_code="75001",
        address2="Floor 2"
    )
    
    if success:
        # Success - show only extracted values
        print(f"\nInsured Name: {test_name}")
        print(f"GUID: {guid}")
        print(f"Status: SUCCESS")
    else:
        # Failure - show full request and response
        print(f"\n✗ Direct creation failed")
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
    
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