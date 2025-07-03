#!/usr/bin/env python3
"""
Send TEST.json directly to the API without transformation
"""

import json
import requests
import os

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "triton_test_key")

def main():
    print("=== Sending TEST.json directly to API ===\n")
    
    # Load TEST.json as-is
    with open("TEST.json", 'r') as f:
        data = json.load(f)
    
    print(f"Policy Number: {data['policy_number']}")
    print(f"Insured Name: {data['insured_name']}")
    print(f"Producer Name: {data['producer_name']}")
    print(f"Premium: ${data['gross_premium']}")
    
    # Send to API
    url = f"{API_BASE_URL}/api/triton/transaction/new"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    params = {"sync_mode": "true"}
    
    print(f"\nSending to: {url}")
    
    try:
        response = requests.post(url, json=data, headers=headers, params=params)
        
        print(f"\nResponse Status: {response.status_code}")
        result = response.json()
        
        print(f"Transaction ID: {result.get('transaction_id')}")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        
        if result.get('ims_details'):
            print("\nIMS Details:")
            for key, value in result['ims_details'].items():
                if value:
                    print(f"  {key}: {value}")
                    
    except Exception as e:
        print(f"Error: {str(e)}")
        if response:
            print(f"Response: {response.text}")

if __name__ == "__main__":
    main()