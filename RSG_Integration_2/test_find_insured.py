#!/usr/bin/env python3
"""
Test script for finding insured using IMS web service.
Reads payload from TEST.json and searches for the insured.
"""

import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ims.auth_service import get_auth_service
from app.services.ims.insured_service import get_insured_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_payload():
    """Load the test payload from TEST.json."""
    try:
        with open('TEST.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("TEST.json not found")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse TEST.json: {e}")
        return None


def test_find_insured_with_payload():
    """Test finding an insured using the payload data."""
    print("\n" + "="*60)
    print("Testing Find Insured by Name with Payload")
    print("="*60)
    
    # Load payload
    payload = load_test_payload()
    if not payload:
        print("Failed to load TEST.json")
        return False
    
    # Display payload information
    print(f"\nPayload Information:")
    print(f"  Transaction ID: {payload.get('transaction_id', 'N/A')}")
    print(f"  Transaction Type: {payload.get('transaction_type', 'N/A')}")
    print(f"  Insured Name: {payload.get('insured_name', 'N/A')}")
    print(f"  City: {payload.get('city', 'N/A')}")
    print(f"  State: {payload.get('state', 'N/A')}")
    print(f"  ZIP: {payload.get('zip', 'N/A')}")
    
    # Authenticate first
    print("\n1. Authenticating with IMS...")
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"   ✗ Authentication failed: {auth_message}")
        return False
    
    print(f"   ✓ Authentication successful")
    print(f"   Token: {auth_service.token[:20]}...")
    
    # Search for insured
    print("\n2. Searching for insured...")
    insured_service = get_insured_service()
    
    found, insured_guid, message = insured_service.process_triton_payload(payload)
    
    print(f"\n   Result: {'FOUND' if found else 'NOT FOUND'}")
    print(f"   Message: {message}")
    
    if found:
        print(f"   Insured GUID: {insured_guid}")
        print("\n   ✓ Insured exists in IMS - no need to create")
    else:
        print("\n   → Insured not found - will need to create new insured")
    
    return found


def test_find_insured_direct():
    """Test finding an insured with direct parameters."""
    print("\n" + "="*60)
    print("Testing Find Insured by Name (Direct)")
    print("="*60)
    
    # Test data
    test_cases = [
        {
            "name": "Thrive Network LLC",
            "city": "Beaverton",
            "state": "OR",
            "zip": "97078"
        },
        {
            "name": "BLC Industries, LLC",
            "city": "Kalamazoo",
            "state": "MI",
            "zip": "49048"
        },
        {
            "name": "Non-Existent Company XYZ",
            "city": "",
            "state": "",
            "zip": ""
        }
    ]
    
    # Authenticate
    print("\nAuthenticating...")
    auth_service = get_auth_service()
    auth_success, _ = auth_service.login()
    
    if not auth_success:
        print("Authentication failed")
        return False
    
    print("✓ Authenticated successfully\n")
    
    # Test each case
    insured_service = get_insured_service()
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['name']}")
        print(f"  Location: {test_case['city']}, {test_case['state']} {test_case['zip']}")
        
        found, guid, message = insured_service.find_insured_by_name(
            test_case['name'],
            test_case['city'],
            test_case['state'],
            test_case['zip']
        )
        
        print(f"  Result: {'FOUND' if found else 'NOT FOUND'}")
        if found:
            print(f"  GUID: {guid}")
        print()
        
        results.append((test_case['name'], found))
    
    # Summary
    print("Summary:")
    for name, found in results:
        print(f"  {name}: {'✓ Found' if found else '✗ Not Found'}")
    
    return True


def main():
    """Run all tests."""
    print("\nIMS Find Insured Test Suite")
    print("===========================")
    
    # Check credentials
    auth_service = get_auth_service()
    if not auth_service.username or not auth_service.password:
        print("\nERROR: IMS credentials not configured!")
        print("Please set IMS_ONE_USERNAME and IMS_ONE_PASSWORD environment variables")
        return 1
    
    # Run tests
    tests = [
        ("Find Insured with Payload", test_find_insured_with_payload),
        ("Find Insured Direct", test_find_insured_direct)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
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
    
    return 0 if all(r[1] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())