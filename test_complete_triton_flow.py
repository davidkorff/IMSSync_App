#!/usr/bin/env python3
"""
Complete test of Triton integration with TEST.json
"""

import json
import requests
import os
from datetime import datetime

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "test-api-key")

def test_triton_endpoint():
    """Test the complete Triton integration flow"""
    
    print("=== Complete Triton Integration Test ===\n")
    
    # Load TEST.json
    print("1. Loading TEST.json (flat structure)...")
    with open("TEST.json", 'r') as f:
        test_data = json.load(f)
    
    print(f"   Policy: {test_data['policy_number']}")
    print(f"   Insured: {test_data['insured_name']}")
    print(f"   State: {test_data['insured_state']}")
    print(f"   Premium: ${test_data['gross_premium']}")
    
    # Prepare request
    url = f"{API_BASE_URL}/api/triton/transaction/new"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    print(f"\n2. Sending to {url}...")
    print("   Using sync_mode=true for immediate IMS processing")
    
    try:
        # Make the request
        response = requests.post(
            url,
            json=test_data,
            headers=headers,
            params={"sync_mode": "true"}
        )
        
        print(f"\n3. Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n4. Success! Transaction Details:")
            print(f"   Transaction ID: {result.get('transaction_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
            
            # Check IMS details
            if result.get('ims_details'):
                print("\n5. IMS Processing Results:")
                ims = result['ims_details']
                print(f"   Processing Status: {ims.get('processing_status')}")
                print(f"   Insured GUID: {ims.get('insured_guid')}")
                print(f"   Submission GUID: {ims.get('submission_guid')}")
                print(f"   Quote GUID: {ims.get('quote_guid')}")
                print(f"   Policy Number: {ims.get('policy_number')}")
                
                if ims.get('error'):
                    print(f"\n   ⚠️  Error: {ims.get('error')}")
            
            # Save full response
            with open("TEST_complete_response.json", 'w') as f:
                json.dump(result, f, indent=2)
            print("\n   Full response saved to TEST_complete_response.json")
            
        else:
            print(f"\n   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n   ❌ Connection Error: Is the service running?")
        print("   Start the service with: python3 run_service.py")
    except Exception as e:
        print(f"\n   ❌ Error: {str(e)}")
    
    print("\n=== Test Complete ===")

def test_data_flow():
    """Show how the data flows through the system"""
    
    print("\n=== Data Flow Analysis ===\n")
    
    with open("TEST.json", 'r') as f:
        test_data = json.load(f)
    
    print("1. Input: Flat JSON structure (TEST.json)")
    print("   Fields: insured_name, insured_state, policy_number, etc.")
    
    print("\n2. Triton Service receives data")
    print("   → Detects flat structure using _is_flat_structure()")
    
    print("\n3. Flat Transformer converts to IMS format")
    print("   → Converts dates: 09/20/2025 → 2025-09-20")
    print("   → Parses limits: $1,000,000/$3,000,000 → {occurrence: 1000000, aggregate: 3000000}")
    print("   → Creates nested structure with policy_data, insured_data, etc.")
    
    print("\n4. IMS Workflow processes transformed data")
    print("   → Creates/finds insured")
    print("   → Creates submission")
    print("   → Creates quote with Excel rater")
    print("   → Binds policy (if requested)")
    
    print("\n5. Response includes IMS GUIDs and status")

if __name__ == "__main__":
    # Run the complete test
    test_triton_endpoint()
    
    # Show data flow
    test_data_flow()