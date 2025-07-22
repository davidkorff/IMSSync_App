#!/usr/bin/env python3
"""
Test script for looking up producer information using IMS DataAccess service.
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


def test_producer_lookup_with_payload():
    """Test producer lookup using the payload data."""
    print("\n" + "="*60)
    print("Testing Producer Lookup with Payload")
    print("="*60)
    
    # Load test payload
    try:
        with open('TEST.json', 'r') as f:
            payload = json.load(f)
        print("\n✓ Payload loaded successfully")
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # Display producer information from payload
    producer_name = payload.get('producer_name', 'N/A')
    print(f"\nPayload Information:")
    print(f"  Producer Name: {producer_name}")
    
    # Authenticate
    print("\n1. Authenticating with IMS...")
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"   ✗ Authentication failed: {auth_message}")
        return False
    
    print(f"   ✓ Authentication successful")
    print(f"   Token: {auth_service.token[:20]}...")
    
    # Look up producer
    print("\n2. Looking up producer...")
    data_service = get_data_access_service()
    
    success, producer_info, message = data_service.process_producer_from_payload(payload)
    
    print(f"\n   Result: {'FOUND' if success else 'NOT FOUND'}")
    print(f"   Message: {message}")
    
    if success and producer_info:
        print(f"\n   Producer Details:")
        print(f"   ProducerContactGUID: {producer_info.get('ProducerContactGUID', 'N/A')}")
        print(f"   ProducerLocationGUID: {producer_info.get('ProducerLocationGUID', 'N/A')}")
        
        # Store for future use
        payload['producer_contact_guid'] = producer_info.get('ProducerContactGUID')
        payload['producer_location_guid'] = producer_info.get('ProducerLocationGUID')
        
        print(f"\n   ✓ Producer GUIDs ready for quote creation")
    else:
        print(f"\n   ✗ Producer not found in IMS")
    
    return success


def test_specific_producers():
    """Test looking up specific producers."""
    print("\n" + "="*60)
    print("Testing Specific Producer Lookups")
    print("="*60)
    
    # Test cases
    test_producers = [
        "Mike Woodworth",
        "Dan Mulligan",
        "John Doe",  # Likely not found
    ]
    
    # Authenticate once
    print("\nAuthenticating...")
    auth_service = get_auth_service()
    auth_success, _ = auth_service.login()
    
    if not auth_success:
        print("Authentication failed")
        return False
    
    print("✓ Authenticated successfully\n")
    
    # Test each producer
    data_service = get_data_access_service()
    results = []
    
    for producer_name in test_producers:
        print(f"\nLooking up: {producer_name}")
        
        success, producer_info, message = data_service.get_producer_by_name(producer_name)
        
        if success and producer_info:
            print(f"  ✓ Found")
            print(f"  Contact GUID: {producer_info.get('ProducerContactGUID', 'N/A')}")
            print(f"  Location GUID: {producer_info.get('ProducerLocationGUID', 'N/A')}")
        else:
            print(f"  ✗ Not found: {message}")
        
        results.append((producer_name, success))
    
    # Summary
    print("\n" + "-"*60)
    print("Producer Lookup Summary:")
    for name, success in results:
        print(f"  {name}: {'✓ Found' if success else '✗ Not Found'}")
    
    return True


def test_execute_dataset_direct():
    """Test ExecuteDataSet method directly."""
    print("\n" + "="*60)
    print("Testing ExecuteDataSet Direct")
    print("="*60)
    
    # Authenticate
    print("\nAuthenticating...")
    auth_service = get_auth_service()
    auth_success, _ = auth_service.login()
    
    if not auth_success:
        print("Authentication failed")
        return False
    
    print("✓ Authenticated successfully\n")
    
    # Execute stored procedure
    data_service = get_data_access_service()
    
    print("Executing getProducerbyName stored procedure...")
    print("  Parameters: fullname = 'Mike Woodworth'")
    
    success, result_xml, message = data_service.execute_dataset(
        "getProducerbyName",
        ["fullname", "Mike Woodworth"]
    )
    
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
    print(f"Message: {message}")
    
    if success and result_xml:
        print(f"\nRaw XML Result:")
        print("-" * 40)
        print(result_xml)
        print("-" * 40)
    
    return success


def main():
    """Run all tests."""
    print("\nIMS Producer Lookup Test Suite")
    print("==============================")
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please set environment variables:")
        print("  export IMS_ONE_USERNAME=your_username")
        print("  export IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Run tests
    tests = [
        ("Producer Lookup with Payload", test_producer_lookup_with_payload),
        ("Specific Producer Lookups", test_specific_producers),
        ("ExecuteDataSet Direct", test_execute_dataset_direct)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if test_name == "ExecuteDataSet Direct":
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