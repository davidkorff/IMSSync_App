#!/usr/bin/env python3
"""
Clean output test for IMS integration - easy to copy/paste
"""

import json
import requests
import os
from datetime import datetime
import sys

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "triton_test_key")

def test_ims_integration():
    """Test IMS integration with clean output"""
    
    print("TEST START:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    # Load TEST.json
    try:
        with open("TEST.json", 'r') as f:
            test_data = json.load(f)
        print("LOADED: TEST.json")
        print(f"  Policy: {test_data.get('policy_number')}")
        print(f"  Insured: {test_data.get('insured_name')}")
    except Exception as e:
        print(f"ERROR loading TEST.json: {str(e)}")
        return
    
    # Prepare transformed payload
    from app.integrations.triton.flat_transformer import TritonFlatTransformer
    transformer = TritonFlatTransformer({})
    
    try:
        payload = transformer.transform_to_ims_format(test_data)
        print("TRANSFORMED: Success")
    except Exception as e:
        print(f"ERROR transforming: {str(e)}")
        return
    
    # Test API call
    url = f"{API_BASE_URL}/api/triton/transaction/new"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"\nAPI CALL: POST {url}")
    print(f"HEADERS: {headers}")
    
    try:
        response = requests.post(
            url,
            json=test_data,  # Send original flat structure
            headers=headers,
            params={"sync_mode": "true"},
            timeout=30
        )
        
        print(f"\nRESPONSE STATUS: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Transaction processed")
            print(f"  Transaction ID: {result.get('transaction_id')}")
            print(f"  Status: {result.get('status')}")
            
            ims = result.get('ims_details', {})
            if ims:
                print("\nIMS RESULTS:")
                print(f"  Processing Status: {ims.get('processing_status')}")
                print(f"  Insured GUID: {ims.get('insured_guid')}")
                print(f"  Quote GUID: {ims.get('quote_guid')}")
                print(f"  Policy Number: {ims.get('policy_number')}")
                if ims.get('error'):
                    print(f"  ERROR: {ims.get('error')}")
        else:
            print(f"ERROR {response.status_code}: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Connection refused - is the service running?")
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("TEST END:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    # Add app to path
    sys.path.insert(0, os.path.abspath('.'))
    
    # Run test
    test_ims_integration()