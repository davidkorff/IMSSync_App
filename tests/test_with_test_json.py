#!/usr/bin/env python3
"""
Simple test script for TEST.json
Run this to quickly test the Triton integration
"""

import json
import requests
import sys
from datetime import datetime


def test_triton_endpoint():
    """Test the Triton endpoint with TEST.json data"""
    
    # Configuration
    BASE_URL = "http://localhost:8000"
    ENDPOINT = "/api/triton/transaction/new"
    API_KEY = "triton_test_key"
    
    # Load TEST.json
    print("Loading TEST.json...")
    with open('../TEST.json', 'r') as f:
        test_data = json.load(f)
    
    # Show original data
    print("\nOriginal TEST.json data:")
    print(f"  Policy Number: {test_data['policy_number']}")
    print(f"  Insured: {test_data['insured_name']}")
    print(f"  State: {test_data['insured_state']}")
    print(f"  Premium: ${test_data['gross_premium']}")
    print(f"  Transaction Type: {test_data['transaction_type']}")
    
    # Prepare payload - only change transaction_type to standard value
    payload = test_data.copy()
    payload['transaction_type'] = 'binding'  # Normalize from "NEW BUSINESS" to "binding"
    
    print(f"\nSending to: {BASE_URL}{ENDPOINT}")
    print("Headers: X-API-Key: ***")
    
    try:
        # Make request
        response = requests.post(
            f"{BASE_URL}{ENDPOINT}",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        # Parse response
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Check success
        if response.status_code == 200 and result.get('status') == 'success':
            data = result['data']
            print("\n✅ SUCCESS!")
            print(f"  Transaction ID: {data.get('transaction_id')}")
            print(f"  Policy Number: {data.get('policy_number')}")
            print(f"  Quote GUID: {data.get('quote_guid')}")
            print(f"  Invoice Number: {data.get('invoice_number', 'Not yet available')}")
            return True
        else:
            print("\n❌ FAILED!")
            if 'error' in result:
                error = result['error']
                print(f"  Stage: {error.get('stage')}")
                print(f"  Message: {error.get('message')}")
                print(f"  Details: {json.dumps(error.get('details', {}), indent=2)}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server")
        print("  Make sure the server is running: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_async_mode():
    """Test async processing mode"""
    
    print("\n" + "=" * 60)
    print("Testing ASYNC mode")
    print("=" * 60)
    
    BASE_URL = "http://localhost:8000"
    ENDPOINT = "/api/triton/transaction/new?sync_mode=false"
    API_KEY = "triton_test_key"
    
    # Create simple test payload
    payload = {
        "transaction_type": "binding",
        "transaction_id": f"ASYNC-TEST-{datetime.now().timestamp()}",
        "policy_number": "TEST-ASYNC-001",
        "insured_name": "Async Test Company",
        "insured_state": "TX",
        "producer_name": "Test Producer",
        "gross_premium": 1000,
        "effective_date": "01/01/2025",
        "expiration_date": "01/01/2026"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{ENDPOINT}",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            }
        )
        
        print(f"Response Status: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 202:  # Accepted
            print("\n✅ Async request accepted!")
            print(f"  Transaction ID: {result['data']['transaction_id']}")
            print("  Status: Queued for processing")
            return True
        else:
            print("\n❌ Unexpected response for async mode")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("TRITON INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Main sync test with TEST.json
    success1 = test_triton_endpoint()
    
    # Test 2: Async mode
    success2 = test_async_mode()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Sync Mode Test:  {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Async Mode Test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    # Exit code
    sys.exit(0 if (success1 and success2) else 1)


if __name__ == "__main__":
    main()