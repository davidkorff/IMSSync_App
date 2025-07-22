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
    
    # Authenticate first
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Request: LoginIMSUser")
        print(f"Response: {auth_message}")
        return False
    
    # Search for insured
    insured_service = get_insured_service()
    
    # Capture request data
    request_data = {
        "insured_name": payload.get('insured_name'),
        "city": payload.get('city'),
        "state": payload.get('state'),
        "zip": payload.get('zip')
    }
    
    found, insured_guid, message = insured_service.process_triton_payload(payload)
    
    if found:
        # Success - show only extracted values
        print(f"\nAuthentication Token: {auth_service.token[:20]}...")
        print(f"Transaction ID: {payload.get('transaction_id')}")
        print(f"Insured Name: {payload.get('insured_name')}")
        print(f"Insured GUID: {insured_guid}")
        print(f"Status: FOUND")
    else:
        # Not found - show full details
        print(f"\nInsured not found")
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
    
    return found


def test_find_insured_direct():
    """Test finding an insured directly using TEST.json data."""
    print("\n" + "="*60)
    print("Testing Find Insured by Name (Direct)")
    print("="*60)
    
    # Load test payload
    payload = load_test_payload()
    if not payload:
        print("Failed to load TEST.json")
        return False
    
    # Authenticate
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Response: {auth_message}")
        return False
    
    # Test with the actual payload data
    insured_service = get_insured_service()
    
    # Use the data from TEST.json
    test_case = {
        "name": payload.get('insured_name'),
        "city": payload.get('city'),
        "state": payload.get('state'),
        "zip": payload.get('zip')
    }
    
    found, guid, message = insured_service.find_insured_by_name(
        test_case['name'],
        test_case['city'],
        test_case['state'],
        test_case['zip']
    )
    
    if found:
        # Success - show only extracted values
        print(f"\nAuthentication Token: {auth_service.token[:20]}...")
        print(f"Insured Name: {test_case['name']}")
        print(f"Location: {test_case['city']}, {test_case['state']} {test_case['zip']}")
        print(f"GUID: {guid}")
        print(f"Status: FOUND")
    else:
        # Show failure details
        print(f"\n✗ Direct search failed")
        print(f"\nRequest Data:")
        print(json.dumps(test_case, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
    
    return found


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
        ("Find Insured with Payload", test_find_insured_with_payload)
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