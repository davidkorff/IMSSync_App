#!/usr/bin/env python3
"""
Test script that simulates the complete API endpoint workflow.
This test loads TEST.json and processes it as if it was sent to /api/triton/transaction/new
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the dotenv module
class MockDotenv:
    def load_dotenv(self):
        pass

sys.modules['dotenv'] = MockDotenv()

# Import the API processor
from app.api.process_transaction import process_triton_transaction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_api_endpoint(json_file):
    """Test the complete API endpoint workflow with specified JSON file."""
    print("\n" + "="*60)
    print("Testing API Endpoint: /api/triton/transaction/new")
    print("="*60)
    
    # Load JSON file
    try:
        with open(json_file, 'r') as f:
            payload = json.load(f)
        print(f"\n✓ Loaded {json_file} successfully")
    except Exception as e:
        print(f"\n✗ Failed to load {json_file}: {e}")
        return False
    
    # Display payload information
    print(f"\nPayload Details:")
    print(f"  Transaction ID: {payload.get('transaction_id')}")
    print(f"  Transaction Type: {payload.get('transaction_type')}")
    print(f"  Insured: {payload.get('insured_name')}")
    print(f"  Policy Number: {payload.get('policy_number')}")
    print(f"  Premium: ${payload.get('net_premium', 0):,.2f}")
    
    # Simulate API call
    print(f"\n{'='*60}")
    print(f"Simulating POST to /api/triton/transaction/new")
    print(f"{'='*60}")
    
    start_time = datetime.utcnow()
    
    # Process the transaction (this is what the API endpoint calls)
    result = process_triton_transaction(payload)
    
    end_time = datetime.utcnow()
    processing_time = (end_time - start_time).total_seconds()
    
    # Display results
    print(f"\n{'='*60}")
    print("API Response:")
    print(f"{'='*60}")
    
    print(f"\nSuccess: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"Processing Time: {processing_time:.2f} seconds")
    
    if result.get('data'):
        print(f"\nResponse Data:")
        data = result['data']
        
        # Display key results
        print(f"  Status: {data.get('status')}")
        print(f"  Insured GUID: {data.get('insured_guid')}")
        print(f"  Quote GUID: {data.get('quote_guid')}")
        print(f"  Quote Option GUID: {data.get('quote_option_guid')}")
        
        # Transaction-specific results
        if data.get('transaction_type') == 'bind':
            print(f"  Bound Policy Number: {data.get('bound_policy_number')}")
        elif data.get('transaction_type') == 'issue':
            print(f"  Bound Policy Number: {data.get('bound_policy_number')}")
            print(f"  Issue Date: {data.get('issue_date')}")
        
        # Full data (optional)
        show_full = input("\nShow full response data? (y/n): ")
        if show_full.lower() == 'y':
            print("\nFull Response Data:")
            print(json.dumps(data, indent=2))
    
    if result.get('error'):
        print(f"\nError Details: {result['error']}")
    
    return result['success']


def test_different_transaction_types(json_file):
    """Test different transaction types."""
    print("\n" + "="*60)
    print("Testing Different Transaction Types")
    print("="*60)
    
    # Load base payload
    try:
        with open(json_file, 'r') as f:
            base_payload = json.load(f)
    except Exception as e:
        print(f"Failed to load {json_file}: {e}")
        return False
    
    # Test each transaction type
    transaction_types = ['bind', 'issue', 'unbind', 'cancellation']
    
    for trans_type in transaction_types:
        response = input(f"\nTest '{trans_type}' transaction? (y/n): ")
        if response.lower() != 'y':
            continue
        
        print(f"\n{'-'*40}")
        print(f"Testing: {trans_type}")
        print(f"{'-'*40}")
        
        # Update transaction type
        test_payload = base_payload.copy()
        test_payload['transaction_type'] = trans_type
        test_payload['transaction_id'] = f"test-{trans_type}-{datetime.utcnow().isoformat()}"
        
        # Process
        result = process_triton_transaction(test_payload)
        
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        
        if result['success'] and result.get('data'):
            data = result['data']
            if trans_type == 'bind' and data.get('bound_policy_number'):
                print(f"Policy Number: {data['bound_policy_number']}")
            elif trans_type == 'issue':
                if data.get('bound_policy_number'):
                    print(f"Policy Number: {data['bound_policy_number']}")
                if data.get('issue_date'):
                    print(f"Issue Date: {data['issue_date']}")
    
    return True


def test_api_error_handling():
    """Test API error handling."""
    print("\n" + "="*60)
    print("Testing API Error Handling")
    print("="*60)
    
    # Test with invalid payload
    print("\n1. Testing with invalid transaction type...")
    invalid_payload = {
        "transaction_type": "INVALID_TYPE",
        "transaction_id": "test-invalid",
        "policy_number": "TEST-001",
        "insured_name": "Test Company",
        "net_premium": 1000
    }
    
    result = process_triton_transaction(invalid_payload)
    print(f"   Success: {result['success']} (expected: False)")
    print(f"   Message: {result['message']}")
    
    # Test with missing required fields
    print("\n2. Testing with missing required fields...")
    incomplete_payload = {
        "transaction_type": "bind",
        "transaction_id": "test-incomplete"
        # Missing other required fields
    }
    
    result = process_triton_transaction(incomplete_payload)
    print(f"   Success: {result['success']} (expected: False)")
    print(f"   Message: {result['message']}")
    
    return True


def main():
    """Run all API endpoint tests."""
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python3 test_api_endpoint.py <json_file>")
        print("Example: python3 test_api_endpoint.py TEST.json")
        return 1
    
    json_file = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(json_file):
        print(f"Error: File '{json_file}' not found")
        return 1
    
    print("\nTriton API Endpoint Test Suite")
    print("==============================")
    print(f"Testing with payload file: {json_file}")
    print("\nThis test simulates sending payloads to /api/triton/transaction/new")
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please ensure .env file exists with:")
        print("  IMS_ONE_USERNAME=your_username")
        print("  IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Run tests
    tests = [
        ("API Endpoint Test", lambda: test_api_endpoint(json_file)),
        ("Different Transaction Types", lambda: test_different_transaction_types(json_file)),
        ("Error Handling", test_api_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            response = input(f"\nRun {test_name}? (y/n): ")
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