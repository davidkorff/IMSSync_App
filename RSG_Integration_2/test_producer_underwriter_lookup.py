#!/usr/bin/env python3
"""
Test script for looking up both producer and underwriter information using IMS DataAccess service.
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
from app.services.ims.data_access_service import get_data_access_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_complete_lookup_with_payload():
    """Test both producer and underwriter lookup using the payload data."""
    print("\n" + "="*60)
    print("Testing Complete Lookup with Payload")
    print("="*60)
    
    # Load test payload
    try:
        with open('TEST.json', 'r') as f:
            payload = json.load(f)
        print("\n✓ Payload loaded successfully")
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # Display information from payload
    print(f"\nPayload Information:")
    print(f"  Producer Name: {payload.get('producer_name', 'N/A')}")
    print(f"  Underwriter Name: {payload.get('underwriter_name', 'N/A')}")
    
    # Authenticate
    print("\n1. Authenticating with IMS...")
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"   ✗ Authentication failed: {auth_message}")
        return False
    
    print(f"   ✓ Authentication successful")
    print(f"   Token: {auth_service.token[:20]}...")
    
    data_service = get_data_access_service()
    
    # Look up producer
    print("\n2. Looking up producer...")
    producer_success, producer_info, producer_message = data_service.process_producer_from_payload(payload)
    
    print(f"   Result: {'FOUND' if producer_success else 'NOT FOUND'}")
    print(f"   Message: {producer_message}")
    
    if producer_success and producer_info:
        print(f"   ProducerContactGUID: {producer_info.get('ProducerContactGUID', 'N/A')}")
        print(f"   ProducerLocationGUID: {producer_info.get('ProducerLocationGUID', 'N/A')}")
        
        # Store for future use
        payload['producer_contact_guid'] = producer_info.get('ProducerContactGUID')
        payload['producer_location_guid'] = producer_info.get('ProducerLocationGUID')
    
    # Look up underwriter
    print("\n3. Looking up underwriter...")
    underwriter_success, underwriter_guid, underwriter_message = data_service.process_underwriter_from_payload(payload)
    
    print(f"   Result: {'FOUND' if underwriter_success else 'NOT FOUND'}")
    print(f"   Message: {underwriter_message}")
    
    if underwriter_success and underwriter_guid:
        print(f"   UnderwriterGUID: {underwriter_guid}")
        
        # Store for future use
        payload['underwriter_guid'] = underwriter_guid
    
    # Summary
    if producer_success and underwriter_success:
        print(f"\n✓ All lookups successful - ready for quote creation")
        print(f"\nExtracted GUIDs:")
        print(f"  Producer Contact: {payload.get('producer_contact_guid', 'N/A')}")
        print(f"  Producer Location: {payload.get('producer_location_guid', 'N/A')}")
        print(f"  Underwriter: {payload.get('underwriter_guid', 'N/A')}")
        return True
    else:
        print(f"\n✗ Some lookups failed")
        return False


def test_specific_lookups():
    """Test looking up specific producers and underwriters."""
    print("\n" + "="*60)
    print("Testing Specific Lookups")
    print("="*60)
    
    # Test cases
    test_cases = [
        {
            "type": "Producer",
            "names": ["Mike Woodworth", "Dan Mulligan", "John Doe"]
        },
        {
            "type": "Underwriter", 
            "names": ["Christina Rentas", "Haley Crocombe", "Jane Smith"]
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
    
    data_service = get_data_access_service()
    
    # Test producers
    print("\nProducer Lookups:")
    print("-" * 40)
    for name in test_cases[0]["names"]:
        success, producer_info, message = data_service.get_producer_by_name(name)
        
        if success and producer_info:
            print(f"{name}:")
            print(f"  ✓ Contact GUID: {producer_info.get('ProducerContactGUID', 'N/A')}")
            print(f"  ✓ Location GUID: {producer_info.get('ProducerLocationGUID', 'N/A')}")
        else:
            print(f"{name}: ✗ Not found")
    
    # Test underwriters
    print("\n\nUnderwriter Lookups:")
    print("-" * 40)
    for name in test_cases[1]["names"]:
        success, underwriter_guid, message = data_service.get_underwriter_by_name(name)
        
        if success and underwriter_guid:
            print(f"{name}:")
            print(f"  ✓ User GUID: {underwriter_guid}")
        else:
            print(f"{name}: ✗ Not found")
    
    return True


def test_stored_procedures():
    """Test the stored procedures directly."""
    print("\n" + "="*60)
    print("Testing Stored Procedures")
    print("="*60)
    
    # Authenticate
    print("\nAuthenticating...")
    auth_service = get_auth_service()
    auth_success, _ = auth_service.login()
    
    if not auth_success:
        print("Authentication failed")
        return False
    
    print("✓ Authenticated successfully\n")
    
    data_service = get_data_access_service()
    
    # Test getProducerbyName_WS
    print("1. Testing getProducerbyName stored procedure...")
    success, result_xml, message = data_service.execute_dataset(
        "getProducerbyName",
        ["fullname", "Mike Woodworth"]
    )
    
    if success and result_xml:
        print("   ✓ Success")
        print(f"   XML Result Preview: {result_xml[:150]}...")
    else:
        print(f"   ✗ Failed: {message}")
    
    # Test getUserbyName_WS
    print("\n2. Testing getUserbyName stored procedure...")
    success, result_xml, message = data_service.execute_dataset(
        "getUserbyName",
        ["fullname", "Christina Rentas"]
    )
    
    if success and result_xml:
        print("   ✓ Success")
        print(f"   XML Result Preview: {result_xml[:150]}...")
    else:
        print(f"   ✗ Failed: {message}")
    
    return True


def main():
    """Run all tests."""
    print("\nIMS Producer & Underwriter Lookup Test Suite")
    print("===========================================")
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please ensure .env file exists with:")
        print("  IMS_ONE_USERNAME=your_username")
        print("  IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Run tests
    tests = [
        ("Complete Lookup with Payload", test_complete_lookup_with_payload),
        ("Specific Lookups", test_specific_lookups),
        ("Stored Procedures", test_stored_procedures)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if test_name == "Stored Procedures":
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