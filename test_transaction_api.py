#!/usr/bin/env python3
"""Test a single transaction through the API"""

import requests
import json

def test_single_transaction():
    """Test a single transaction"""
    print("Testing single transaction through API")
    print("=" * 50)
    
    # Transaction data
    transaction_data = {
        "transaction_id": "TEST_SINGLE_001",
        "transaction_date": "2025-06-23",
        "transaction_type": "NEW_BUSINESS",
        "source_system": "triton",
        "policy": {
            "policy_number": "TEST-001",
            "insured_name": "Test Company LLC",
            "insured_city": "Chicago",
            "insured_state": "IL",
            "insured_zip": "60601",
            "producer_name": "Test Producer",
            "underwriter_name": "Test Underwriter",
            "effective_date": "2025-01-01",
            "expiration_date": "2026-01-01",
            "gross_premium": 1000.00
        }
    }
    
    # API details
    url = "http://localhost:8000/api/transaction/new"
    headers = {
        "X-API-Key": "test_api_key",
        "Content-Type": "application/json"
    }
    params = {
        "source": "triton",
        "sync_mode": "true"
    }
    
    print(f"Sending to: {url}")
    print(f"Headers: {headers}")
    print(f"Params: {params}")
    print(f"Data: {json.dumps(transaction_data, indent=2)}")
    
    try:
        response = requests.post(url, json=transaction_data, headers=headers, params=params)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_single_transaction()