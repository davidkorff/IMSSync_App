#!/usr/bin/env python3
"""
Test script for looking up underwriter information using IMS Underwriter service.
"""

import sys
import os
import json
import logging
from pathlib import Path

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
from app.services.ims.underwriter_service import get_underwriter_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_underwriter_lookup_with_payload():
    """Test underwriter lookup using the payload data."""
    print("\n" + "="*60)
    print("Testing Underwriter Lookup with Payload")
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
    
    # Look up underwriter
    underwriter_service = get_underwriter_service()
    
    # Capture request data
    underwriter_name = payload.get('underwriter_name', 'N/A')
    request_data = {
        "underwriter_name": underwriter_name,
        "stored_procedure": "getUserbyName"
    }
    
    success, underwriter_guid, message = underwriter_service.process_underwriter_from_payload(payload)
    
    if success and underwriter_guid:
        # Success - show only extracted values
        print(f"\nAuthentication Token: {auth_service.token[:20]}...")
        print(f"Transaction ID: {payload.get('transaction_id', 'N/A')}")
        print(f"Underwriter Name: {underwriter_name}")
        print(f"UserGUID (Underwriter): {underwriter_guid}")
        print(f"Status: FOUND")
        
        # Store for future use
        payload['underwriter_guid'] = underwriter_guid
    else:
        # Failure - show full request and response
        print(f"\n✗ Underwriter not found")
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
    
    return success


def test_specific_underwriters():
    """Test looking up specific underwriters from TEST.json."""
    print("\n" + "="*60)
    print("Testing Specific Underwriter Lookups")
    print("="*60)
    
    # Load test payload to get underwriter name
    try:
        with open('TEST.json', 'r') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # Use underwriter from TEST.json
    test_underwriters = [payload.get('underwriter_name', 'N/A')]
    
    # Authenticate once
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Response: {auth_message}")
        return False
    
    # Test each underwriter
    underwriter_service = get_underwriter_service()
    results = []
    successful_results = []
    
    for underwriter_name in test_underwriters:
        request_data = {
            "underwriter_name": underwriter_name,
            "stored_procedure": "getUserbyName"
        }
        
        success, underwriter_guid, message = underwriter_service.get_underwriter_by_name(underwriter_name)
        
        if success and underwriter_guid:
            successful_results.append({
                "name": underwriter_name,
                "guid": underwriter_guid
            })
        else:
            # Show failure details
            print(f"\n✗ Underwriter lookup failed")
            print(f"\nRequest Data:")
            print(json.dumps(request_data, indent=2))
            print(f"\nFull Response:")
            print(f"{message}")
        
        results.append((underwriter_name, success))
    
    # Show successful results
    if successful_results:
        print("\nSuccessful Results:")
        for result in successful_results:
            print(f"\nUnderwriter Name: {result['name']}")
            print(f"UserGUID: {result['guid']}")
            print(f"Status: FOUND")
    
    return all(success for _, success in results)


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
    
    underwriter_service = get_underwriter_service()
    
    # Test with empty name
    test_cases = [
        {"name": "empty name", "value": ""},
        {"name": "special characters", "value": "Test & User <XML>"},
        {"name": "very long name", "value": "A" * 200}
    ]
    
    all_passed = True
    for test in test_cases:
        request_data = {
            "underwriter_name": test["value"],
            "stored_procedure": "getUserbyName"
        }
        
        success, guid, message = underwriter_service.get_underwriter_by_name(test["value"])
        
        if not success:
            # Expected failure - show details
            print(f"\n✓ {test['name']} test - Expected failure")
            print(f"Request Data:")
            print(json.dumps(request_data, indent=2))
            print(f"Response: {message}")
        else:
            # Unexpected success
            print(f"\n✗ {test['name']} test - Unexpected success")
            print(f"GUID: {guid}")
            all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print("\nIMS Underwriter Lookup Test Suite")
    print("=================================")
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please ensure .env file exists with:")
        print("  IMS_ONE_USERNAME=your_username")
        print("  IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Run tests
    tests = [
        ("Underwriter Lookup with Payload", test_underwriter_lookup_with_payload)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if test_name == "Error Handling":
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