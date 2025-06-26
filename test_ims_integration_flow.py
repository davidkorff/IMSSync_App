#!/usr/bin/env python3
"""
Test IMS integration flow with transformed TEST.json payload
"""

import json
import requests
import os
from datetime import datetime
import time

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8020")
API_KEY = os.getenv("API_KEY", "test-api-key")

def load_transformed_payload():
    """Load the transformed payload with required defaults"""
    
    # First check if transformed file exists
    if os.path.exists("TEST_transformed.json"):
        with open("TEST_transformed.json", 'r') as f:
            data = json.load(f)
    else:
        # Create it from TEST.json
        with open("TEST.json", 'r') as f:
            flat_data = json.load(f)
        
        # Transform with defaults for missing fields
        eff_date = flat_data.get('effective_date', '')
        if '/' in eff_date:
            parts = eff_date.split('/')
            eff_date = f"{parts[2]}-{parts[0]:0>2}-{parts[1]:0>2}"
        
        exp_date = flat_data.get('expiration_date', '')
        if '/' in exp_date:
            parts = exp_date.split('/')
            exp_date = f"{parts[2]}-{parts[0]:0>2}-{parts[1]:0>2}"
        
        data = {
            "transaction_type": "binding",
            "transaction_id": flat_data.get('transaction_id'),
            "transaction_date": flat_data.get('transaction_date'),
            "policy_number": flat_data.get('policy_number'),
            "effective_date": eff_date,
            "expiration_date": exp_date,
            "is_renewal": flat_data.get('business_type', '').lower() == 'renewal',
            "account": {
                "name": flat_data.get('insured_name'),
                "street_1": "123 Main Street",  # Default value
                "city": "Miami",  # Default based on FL zip
                "state": flat_data.get('insured_state'),
                "zip": flat_data.get('insured_zip')
            },
            "producer": {
                "name": flat_data.get('producer_name')
            },
            "program": {
                "name": flat_data.get('program_name', 'Allied Health'),
                "id": "allied-health-001"  # Default program ID
            },
            "premium": {
                "annual_premium": float(flat_data.get('gross_premium', 0)),
                "policy_fee": float(flat_data.get('policy_fee', 0)),
                "commission_rate": float(flat_data.get('commission_rate', 0))
            },
            "exposures": []
        }
    
    return data

def test_transaction_endpoint(payload, sync_mode=True):
    """Test the transaction endpoint"""
    
    url = f"{API_BASE_URL}/api/triton/transaction/new"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    params = {"sync_mode": str(sync_mode).lower()}
    
    print(f"\\nTesting endpoint: {url}")
    print(f"Sync mode: {sync_mode}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        return response
    except Exception as e:
        print(f"Request failed: {str(e)}")
        return None

def analyze_ims_response(response_data):
    """Analyze the IMS integration response"""
    
    print("\\nIMS Integration Analysis:")
    print("-" * 50)
    
    if not response_data:
        print("No response data to analyze")
        return
    
    # Check overall status
    status = response_data.get('status')
    message = response_data.get('message', '')
    
    print(f"Transaction Status: {status}")
    print(f"Message: {message}")
    
    # Check IMS details
    ims_details = response_data.get('ims_details', {})
    if ims_details:
        print("\\nIMS Processing Details:")
        print(f"  Processing Status: {ims_details.get('processing_status')}")
        print(f"  Insured GUID: {ims_details.get('insured_guid')}")
        print(f"  Submission GUID: {ims_details.get('submission_guid')}")
        print(f"  Quote GUID: {ims_details.get('quote_guid')}")
        print(f"  Policy Number: {ims_details.get('policy_number')}")
        
        if ims_details.get('error'):
            print(f"\\n  ERROR: {ims_details.get('error')}")
    
    return ims_details

def test_transaction_status(transaction_id):
    """Check the status of a transaction"""
    
    url = f"{API_BASE_URL}/api/transaction/{transaction_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get transaction status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error checking transaction status: {str(e)}")
        return None

def main():
    """Main test flow"""
    
    print("=== IMS Integration Test Flow ===\\n")
    
    # Step 1: Load and prepare payload
    print("1. Loading transformed payload...")
    payload = load_transformed_payload()
    print(f"   Policy: {payload['policy_number']}")
    print(f"   Insured: {payload['account']['name']}")
    print(f"   Premium: ${payload['premium']['annual_premium']}")
    
    # Save complete payload for inspection
    with open("TEST_complete_payload.json", 'w') as f:
        json.dump(payload, f, indent=2)
    print("   Saved complete payload to TEST_complete_payload.json")
    
    # Step 2: Test synchronous processing
    print("\\n2. Testing SYNCHRONOUS processing...")
    response = test_transaction_endpoint(payload, sync_mode=True)
    
    if response and response.status_code == 200:
        print("   ✓ Request successful!")
        result = response.json()
        transaction_id = result.get('transaction_id')
        print(f"   Transaction ID: {transaction_id}")
        
        # Analyze IMS response
        ims_details = analyze_ims_response(result)
        
        # Save response
        with open("TEST_ims_response.json", 'w') as f:
            json.dump(result, f, indent=2)
        print("\\n   Response saved to TEST_ims_response.json")
        
    else:
        print(f"   ✗ Request failed!")
        if response:
            print(f"   Status Code: {response.status_code}")
            print(f"   Error: {response.text}")
            
            # Save error response
            with open("TEST_error_response.json", 'w') as f:
                json.dump({
                    "status_code": response.status_code,
                    "error": response.text,
                    "headers": dict(response.headers)
                }, f, indent=2)
    
    # Step 3: Test asynchronous processing (if sync failed or for comparison)
    print("\\n3. Testing ASYNCHRONOUS processing...")
    
    # Modify transaction ID to avoid duplicates
    payload['transaction_id'] = f"{payload['transaction_id']}-async"
    
    response = test_transaction_endpoint(payload, sync_mode=False)
    
    if response and response.status_code == 200:
        print("   ✓ Request accepted!")
        result = response.json()
        async_transaction_id = result.get('transaction_id')
        print(f"   Transaction ID: {async_transaction_id}")
        
        # Poll for status
        print("\\n   Polling for completion...")
        for i in range(10):  # Poll for up to 30 seconds
            time.sleep(3)
            status_result = test_transaction_status(async_transaction_id)
            if status_result:
                status = status_result.get('status')
                print(f"   [{i+1}] Status: {status}")
                if status in ['completed', 'failed']:
                    print("\\n   Final result:")
                    analyze_ims_response(status_result)
                    break
    
    print("\\n=== Test Complete ===")
    print("\\nCheck these files for details:")
    print("  - TEST_complete_payload.json - The full payload sent")
    print("  - TEST_ims_response.json - The IMS response (if successful)")
    print("  - TEST_error_response.json - Error details (if failed)")

if __name__ == "__main__":
    main()