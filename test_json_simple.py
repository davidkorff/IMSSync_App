#!/usr/bin/env python3
"""
Simple test script to send TEST.json to IMS via the integration service
"""

import json
import requests
import sys

# Configuration
API_URL = "http://localhost:8000/api/triton/transaction/new"
API_KEY = "triton_test_key"

def main():
    print("=== Testing TEST.json flow to IMS ===\n")
    
    # 1. Load TEST.json
    print("1. Loading TEST.json...")
    try:
        with open('TEST.json', 'r') as f:
            payload = json.load(f)
        print(f"   ✓ Loaded policy: {payload.get('policy_number')}")
        print(f"   ✓ Insured: {payload.get('insured_name')}")
    except Exception as e:
        print(f"   ✗ Error loading TEST.json: {e}")
        return 1
    
    # 2. Send to API
    print(f"\n2. Sending to {API_URL}...")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    params = {"sync_mode": "true"}
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, params=params)
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n3. SUCCESS! IMS Integration Results:")
            print(f"   Transaction ID: {result.get('transaction_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
            
            # Show IMS details if available
            ims_details = result.get('ims_details', {})
            if ims_details:
                print("\n4. IMS Details:")
                print(f"   Processing Status: {ims_details.get('processing_status')}")
                print(f"   Insured GUID: {ims_details.get('insured_guid')}")
                print(f"   Submission GUID: {ims_details.get('submission_guid')}")
                print(f"   Quote GUID: {ims_details.get('quote_guid')}")
                print(f"   Policy Number: {ims_details.get('policy_number')}")
                
                if ims_details.get('error'):
                    print(f"\n   ERROR: {ims_details.get('error')}")
        else:
            print(f"\n   ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            return 1
            
    except Exception as e:
        print(f"\n   ERROR: {e}")
        return 1
    
    print("\n✓ Test completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())