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

# Mock the dotenv module
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
        print("\n✓ Payload loaded successfully")
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # Display underwriter information from payload
    underwriter_name = payload.get('underwriter_name', 'N/A')
    print(f"\nPayload Information:")
    print(f"  Transaction ID: {payload.get('transaction_id', 'N/A')}")
    print(f"  Underwriter Name: {underwriter_name}")
    
    # Authenticate
    print("\n1. Authenticating with IMS...")
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"   ✗ Authentication failed: {auth_message}")
        return False
    
    print(f"   ✓ Authentication successful")
    print(f"   Token: {auth_service.token[:20]}...")
    
    # Look up underwriter
    print("\n2. Looking up underwriter...")
    underwriter_service = get_underwriter_service()
    
    success, underwriter_guid, message = underwriter_service.process_underwriter_from_payload(payload)
    
    print(f"\n   Result: {'FOUND' if success else 'NOT FOUND'}")
    print(f"   Message: {message}")
    
    if success and underwriter_guid:
        print(f"\n   Underwriter Details:")
        print(f"   UserGUID (Underwriter): {underwriter_guid}")
        
        # Store for future use
        payload['underwriter_guid'] = underwriter_guid
        
        print(f"\n   ✓ Underwriter GUID ready for quote creation")
    else:
        print(f"\n   ✗ Underwriter not found in IMS")
    
    return success


def test_specific_underwriters():
    """Test looking up specific underwriters."""
    print("\n" + "="*60)
    print("Testing Specific Underwriter Lookups")
    print("="*60)
    
    # Test cases
    test_underwriters = [
        "Christina Rentas",
        "Haley Crocombe",
        "John Smith",  # Likely not found
    ]
    
    # Authenticate once
    print("\nAuthenticating...")
    auth_service = get_auth_service()
    auth_success, _ = auth_service.login()
    
    if not auth_success:
        print("Authentication failed")
        return False
    
    print("✓ Authenticated successfully\n")
    
    # Test each underwriter
    underwriter_service = get_underwriter_service()
    results = []
    
    for underwriter_name in test_underwriters:
        print(f"\nLooking up: {underwriter_name}")
        
        success, underwriter_guid, message = underwriter_service.get_underwriter_by_name(underwriter_name)
        
        if success and underwriter_guid:
            print(f"  ✓ Found")
            print(f"  UserGUID: {underwriter_guid}")
        else:
            print(f"  ✗ Not found: {message}")
        
        results.append((underwriter_name, success))
    
    # Summary
    print("\n" + "-"*60)
    print("Underwriter Lookup Summary:")
    for name, success in results:
        print(f"  {name}: {'✓ Found' if success else '✗ Not Found'}")
    
    return True


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
    
    underwriter_service = get_underwriter_service()
    
    # Test with empty name
    print("1. Testing with empty name...")
    success, guid, message = underwriter_service.get_underwriter_by_name("")
    print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"   Message: {message}")
    
    # Test with special characters
    print("\n2. Testing with special characters...")
    success, guid, message = underwriter_service.get_underwriter_by_name("Test & User <XML>")
    print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"   Message: {message}")
    
    # Test with very long name
    print("\n3. Testing with very long name...")
    long_name = "A" * 200
    success, guid, message = underwriter_service.get_underwriter_by_name(long_name)
    print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"   Message: {message}")
    
    return True


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
        ("Underwriter Lookup with Payload", test_underwriter_lookup_with_payload),
        ("Specific Underwriter Lookups", test_specific_underwriters),
        ("Error Handling", test_error_handling)
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