#!/usr/bin/env python3
"""
Test script for payload processing service.
This test orchestrates the complete workflow and processes the payload.
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

# Import all services
from app.services.ims.auth_service import get_auth_service
from app.services.ims.insured_service import get_insured_service
from app.services.ims.data_access_service import get_data_access_service
from app.services.ims.underwriter_service import get_underwriter_service
from app.services.ims.quote_service import get_quote_service
from app.services.ims.quote_options_service import get_quote_options_service
from app.services.ims.payload_processor_service import get_payload_processor_service
from app.services.ims.bind_service import get_bind_service
from app.services.ims.issue_service import get_issue_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_complete_payload_processing(json_file):
    """Test the complete workflow as if the JSON file was sent to the API."""
    print("\n" + "="*60)
    print("Testing Complete Transaction Processing")
    print("="*60)
    print(f"Simulating: POST /api/triton/transaction/new with {json_file}")
    
    # Load test payload
    try:
        with open(json_file, 'r') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"\n✗ Failed to load {json_file}: {e}")
        return False
    
    # Store results throughout the workflow
    results = {}
    
    # 1. Authenticate
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Request: LoginIMSUser")
        print(f"Response: {auth_message}")
        return False
    
    # 2. Find/Create Insured
    insured_service = get_insured_service()
    success, insured_guid, message = insured_service.find_or_create_insured(payload)
    
    if not success:
        print(f"\n✗ Failed to find/create insured")
        request_data = {
            "function": "find_or_create_insured",
            "insured_name": payload.get('insured_name'),
            "address": payload.get('address_1'),
            "city": payload.get('city'),
            "state": payload.get('state'),
            "zip": payload.get('zip')
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    
    results['insured_guid'] = insured_guid
    
    # 3. Find Producer
    data_service = get_data_access_service()
    success, producer_info, message = data_service.process_producer_from_payload(payload)
    
    if not success:
        print(f"\n✗ Failed to find producer")
        request_data = {
            "function": "process_producer_from_payload",
            "producer_name": payload.get('producer_name')
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    
    results['producer_contact_guid'] = producer_info.get('ProducerContactGUID')
    results['producer_location_guid'] = producer_info.get('ProducerLocationGUID')
    
    # 4. Find Underwriter
    underwriter_service = get_underwriter_service()
    success, underwriter_guid, message = underwriter_service.process_underwriter_from_payload(payload)
    
    if not success:
        print(f"\n✗ Failed to find underwriter")
        request_data = {
            "function": "process_underwriter_from_payload",
            "underwriter_name": payload.get('underwriter_name')
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    
    results['underwriter_guid'] = underwriter_guid
    
    # 5. Create Quote
    quote_service = get_quote_service()
    success, quote_guid, message = quote_service.create_quote_from_payload(
        payload=payload,
        insured_guid=results['insured_guid'],
        producer_contact_guid=results['producer_contact_guid'],
        producer_location_guid=results['producer_location_guid'],
        underwriter_guid=results['underwriter_guid']
    )
    
    if not success:
        print(f"\n✗ Failed to create quote")
        request_data = {
            "function": "create_quote_from_payload",
            "insured_guid": results['insured_guid'],
            "producer_contact_guid": results['producer_contact_guid'],
            "producer_location_guid": results['producer_location_guid'],
            "underwriter_guid": results['underwriter_guid'],
            "effective_date": payload.get('effective_date'),
            "expiration_date": payload.get('expiration_date'),
            "state": payload.get('insured_state')
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    
    results['quote_guid'] = quote_guid
    
    # 6. Add Quote Options
    quote_options_service = get_quote_options_service()
    success, option_info, message = quote_options_service.auto_add_quote_options(quote_guid)
    
    if not success:
        print(f"\n✗ Failed to add quote options")
        request_data = {
            "function": "auto_add_quote_options",
            "quote_guid": quote_guid
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        return False
    
    results['quote_option_guid'] = option_info.get('QuoteOptionGuid')
    
    # 7. Process Payload (Store data, update policy number, register premium)
    payload_processor = get_payload_processor_service()
    
    # Validate payload first
    is_valid, validation_error = payload_processor.validate_payload(payload)
    if not is_valid:
        print(f"\n✗ Payload validation failed")
        print(f"Validation Error: {validation_error}")
        return False
    
    # Process the payload
    success, result_data, message = payload_processor.process_payload(
        payload=payload,
        quote_guid=results['quote_guid'],
        quote_option_guid=results['quote_option_guid']
    )
    
    if not success:
        print(f"\n✗ Failed to process payload")
        request_data = {
            "function": "process_payload",
            "quote_guid": results['quote_guid'],
            "quote_option_guid": results['quote_option_guid'],
            "policy_number": payload.get('policy_number'),
            "net_premium": payload.get('net_premium')
        }
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
        if result_data:
            print(f"Error details: {result_data}")
        return False
    
    # 8. NOTE: Not binding/issuing - just storing data
    print(f"\nNOTE: Transaction type is '{payload.get('transaction_type')}' but NOT executing bind/issue")
    print("      This test only stores data and assigns policy number to quote")
    print("      Use test_bind_service.py to test binding")
    
    # Summary - show only extracted values on success
    print("\n" + "="*60)
    print("Workflow Complete!")
    print("="*60)
    print(f"\nTransaction ID: {payload.get('transaction_id')}")
    print(f"Transaction Type: {payload.get('transaction_type')}")
    print(f"Policy Number: {payload.get('policy_number')}")
    print(f"Insured Name: {payload.get('insured_name')}")
    print(f"Insured GUID: {results.get('insured_guid')}")
    print(f"Producer Contact GUID: {results.get('producer_contact_guid')}")
    print(f"Producer Location GUID: {results.get('producer_location_guid')}")
    print(f"Underwriter GUID: {results.get('underwriter_guid')}")
    print(f"Quote GUID: {results.get('quote_guid')}")
    print(f"Quote Option GUID: {results.get('quote_option_guid')}")
    print(f"Premium Registered: ${payload.get('net_premium', 0):,.2f}")
    
    print(f"\nPolicy Number Assigned to Quote: {payload.get('policy_number')}")
    print(f"Quote Status: Quote (NOT Bound)")
    print(f"\nStatus: SUCCESS")
    
    return True


def test_payload_validation():
    """Test payload validation logic."""
    print("\n" + "="*60)
    print("Testing Payload Validation")
    print("="*60)
    
    payload_processor = get_payload_processor_service()
    
    # Test valid payload
    valid_payload = {
        "transaction_type": "bind",
        "transaction_id": "test-123",
        "policy_number": "TEST-001",
        "insured_name": "Test Company",
        "net_premium": 1000
    }
    
    print("\n1. Testing valid payload...")
    is_valid, error = payload_processor.validate_payload(valid_payload)
    print(f"   Result: {'VALID' if is_valid else 'INVALID'}")
    if error:
        print(f"   Error: {error}")
    
    # Test missing required field
    invalid_payload = valid_payload.copy()
    del invalid_payload["policy_number"]
    
    print("\n2. Testing payload with missing policy number...")
    is_valid, error = payload_processor.validate_payload(invalid_payload)
    print(f"   Result: {'VALID' if is_valid else 'INVALID'}")
    if error:
        print(f"   Error: {error}")
    
    # Test invalid transaction type
    invalid_type_payload = valid_payload.copy()
    invalid_type_payload["transaction_type"] = "INVALID_TYPE"
    
    print("\n3. Testing payload with invalid transaction type...")
    is_valid, error = payload_processor.validate_payload(invalid_type_payload)
    print(f"   Result: {'VALID' if is_valid else 'INVALID'}")
    if error:
        print(f"   Error: {error}")
    
    return True


def test_transaction_types():
    """Test different transaction types."""
    print("\n" + "="*60)
    print("Testing Transaction Types")
    print("="*60)
    
    payload_processor = get_payload_processor_service()
    
    print("\nSupported Transaction Types:")
    for trans_type, description in payload_processor.TRANSACTION_TYPES.items():
        print(f"  - {trans_type}: {description}")
    
    # Test getting transaction info
    test_types = ["bind", "cancellation", "INVALID_TYPE"]
    
    print("\nTransaction Type Information:")
    for trans_type in test_types:
        info = payload_processor.get_transaction_info(trans_type)
        print(f"  {trans_type}: {info}")
    
    return True


def test_payload_processing_only(json_file):
    """Test payload processing with existing GUIDs."""
    print("\n" + "="*60)
    print("Testing Payload Processing Only")
    print("="*60)
    
    # Get GUIDs from user
    quote_guid = input("\nEnter Quote GUID (or press Enter to skip): ").strip()
    if not quote_guid:
        print("Skipping test - no Quote GUID provided")
        return True
    
    quote_option_guid = input("Enter Quote Option GUID: ").strip()
    if not quote_option_guid:
        print("Skipping test - no Quote Option GUID provided")
        return True
    
    # Load test payload
    try:
        with open(json_file, 'r') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"Failed to load {json_file}: {e}")
        return False
    
    # Authenticate
    print("\nAuthenticating...")
    auth_service = get_auth_service()
    auth_success, _ = auth_service.login()
    
    if not auth_success:
        print("Authentication failed")
        return False
    
    print("✓ Authenticated successfully")
    
    # Process payload
    print("\nProcessing payload...")
    payload_processor = get_payload_processor_service()
    
    success, result_data, message = payload_processor.process_payload(
        payload=payload,
        quote_guid=quote_guid,
        quote_option_guid=quote_option_guid
    )
    
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
    print(f"Message: {message}")
    
    if result_data:
        print("\nResult Details:")
        for key, value in result_data.items():
            print(f"  {key}: {value}")
    
    return success


def main():
    """Run all tests."""
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python3 test_payload_processing.py <json_file>")
        print("Example: python3 test_payload_processing.py TEST.json")
        return 1
    
    json_file = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(json_file):
        print(f"Error: File '{json_file}' not found")
        return 1
    
    print("\nIMS Payload Processing Test Suite")
    print("=================================")
    print(f"Testing with payload file: {json_file}")
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please ensure .env file exists with:")
        print("  IMS_ONE_USERNAME=your_username")
        print("  IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Run tests
    tests = [
        ("Payload Validation", test_payload_validation),
        ("Transaction Types", test_transaction_types),
        ("Complete Payload Processing", lambda: test_complete_payload_processing(json_file)),
        ("Payload Processing Only", lambda: test_payload_processing_only(json_file))
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if test_name == "Payload Processing Only":
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