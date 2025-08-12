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
    
    # Look up producer
    data_service = get_data_access_service()
    
    # Capture request data
    producer_email = payload.get('producer_email', 'N/A')
    
    success, producer_info, message = data_service.process_producer_from_payload(payload)
    
    if success and producer_info:
        # Success - show only extracted values
        print(f"\nAuthentication Token: {auth_service.token[:20]}...")
        print(f"Producer Email: {producer_email}")
        print(f"ProducerContactGUID: {producer_info.get('ProducerContactGUID', 'N/A')}")
        print(f"ProducerLocationGUID: {producer_info.get('ProducerLocationGUID', 'N/A')}")
        print(f"Status: FOUND")
        
        # Store for future use
        payload['producer_contact_guid'] = producer_info.get('ProducerContactGUID')
        payload['producer_location_guid'] = producer_info.get('ProducerLocationGUID')
    else:
        # Failure - show full request and response
        print(f"\n✗ Producer not found")
        print(f"\nFunction: ExecuteDataSet")
        print(f"Stored Procedure: getProducerGuid")
        print(f"Parameters: producer_email = '{producer_email}'")
        print(f"\nError Message:")
        print(f"{message}")
    
    return success


def test_specific_producers():
    """Test looking up specific producers from TEST.json."""
    print("\n" + "="*60)
    print("Testing Specific Producer Lookups")
    print("="*60)
    
    # Load test payload to get producer name
    try:
        with open('TEST.json', 'r') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # Use producer email from TEST.json
    test_producers = [payload.get('producer_email', 'N/A')]
    
    # Authenticate once
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Response: {auth_message}")
        return False
    
    # Test each producer
    data_service = get_data_access_service()
    results = []
    successful_results = []
    
    for producer_email in test_producers:
        request_data = {
            "producer_email": producer_email,
            "stored_procedure": "getProducerGuid"
        }
        
        success, producer_info, message = data_service.get_producer_by_email(producer_email)
        
        if success and producer_info:
            successful_results.append({
                "email": producer_email,
                "contact_guid": producer_info.get('ProducerContactGUID', 'N/A'),
                "location_guid": producer_info.get('ProducerLocationGUID', 'N/A')
            })
        else:
            # Show failure details
            print(f"\n✗ Producer lookup failed")
            print(f"\nRequest Data:")
            print(json.dumps(request_data, indent=2))
            print(f"\nFull Response:")
            print(f"{message}")
        
        results.append((producer_email, success))
    
    # Show successful results
    if successful_results:
        print("\nSuccessful Results:")
        for result in successful_results:
            print(f"\nProducer Email: {result['email']}")
            print(f"Contact GUID: {result['contact_guid']}")
            print(f"Location GUID: {result['location_guid']}")
            print(f"Status: FOUND")
    
    return all(success for _, success in results)


def test_execute_dataset_direct():
    """Test ExecuteDataSet method directly using TEST.json data."""
    print("\n" + "="*60)
    print("Testing ExecuteDataSet Direct")
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
        print(f"Response: {auth_message}")
        return False
    
    # Execute stored procedure
    data_service = get_data_access_service()
    producer_email = payload.get('producer_email', 'N/A')
    
    request_data = {
        "stored_procedure": "getProducerGuid",
        "parameters": ["producer_email", producer_email]
    }
    
    success, result_xml, message = data_service.execute_dataset(
        "getProducerGuid",
        ["producer_email", producer_email]
    )
    
    if success and result_xml:
        # Success - show only key info
        print(f"\nAuthentication Token: {auth_service.token[:20]}...")
        print(f"Stored Procedure: getProducerGuid")
        print(f"Producer Email: {producer_email}")
        print(f"Status: SUCCESS")
        print(f"Result Length: {len(result_xml)} characters")
    else:
        # Failure - show full request and response
        print(f"\n✗ ExecuteDataSet failed")
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
    
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
        ("Producer Lookup with Payload", test_producer_lookup_with_payload)
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