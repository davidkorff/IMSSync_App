#!/usr/bin/env python3
"""
Test script for invoice data retrieval endpoint
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"  # Replace with actual API key

def test_get_invoice_by_policy(policy_number):
    """Test retrieving invoice by policy number"""
    
    url = f"{BASE_URL}/api/v1/invoice/policy/{policy_number}/latest"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    params = {
        "include_payment_info": True,
        "format_currency": True
    }
    
    print(f"\n=== Testing GET Invoice by Policy Number ===")
    print(f"URL: {url}")
    print(f"Policy Number: {policy_number}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nSuccess! Invoice data retrieved:")
            print(json.dumps(data, indent=2))
            
            # Validate response structure
            if "invoice_data" in data:
                invoice = data["invoice_data"]
                print(f"\nInvoice Summary:")
                print(f"  Invoice Number: {invoice.get('invoice_number')}")
                print(f"  Invoice Date: {invoice.get('invoice_date')}")
                print(f"  Due Date: {invoice.get('due_date')}")
                print(f"  Total Amount: {invoice.get('totals', {}).get('formatted_total')}")
                print(f"  Policy Number: {invoice.get('policy_info', {}).get('policy_number')}")
                print(f"  Insured: {invoice.get('insured', {}).get('name')}")
        else:
            print(f"\nError Response:")
            print(json.dumps(response.json(), indent=2))
            
    except Exception as e:
        print(f"\nError making request: {str(e)}")
        return False
    
    return response.status_code == 200

def test_get_invoice_by_quote(quote_id):
    """Test retrieving invoice by quote ID"""
    
    url = f"{BASE_URL}/api/v1/invoice/quote/{quote_id}/latest"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    params = {
        "include_payment_info": True,
        "format_currency": True
    }
    
    print(f"\n=== Testing GET Invoice by Quote ID ===")
    print(f"URL: {url}")
    print(f"Quote ID: {quote_id}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nSuccess! Invoice data retrieved:")
            print(json.dumps(data, indent=2))
        else:
            print(f"\nError Response:")
            print(json.dumps(response.json(), indent=2))
            
    except Exception as e:
        print(f"\nError making request: {str(e)}")
        return False
    
    return response.status_code == 200

def test_error_cases():
    """Test error cases"""
    
    print(f"\n=== Testing Error Cases ===")
    
    # Test 1: Invalid policy number
    print(f"\n1. Testing with invalid policy number:")
    test_get_invoice_by_policy("INVALID-POLICY-123")
    
    # Test 2: Missing API key
    print(f"\n2. Testing without API key:")
    url = f"{BASE_URL}/api/v1/invoice/policy/POL-2024-001234/latest"
    response = requests.get(url)
    print(f"Status Code: {response.status_code} (Expected: 403)")
    
    # Test 3: Without optional parameters
    print(f"\n3. Testing without optional parameters:")
    url = f"{BASE_URL}/api/v1/invoice/policy/POL-2024-001234/latest"
    headers = {"X-API-Key": API_KEY}
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success - optional parameters have defaults")

def main():
    """Main test function"""
    
    print("=" * 60)
    print("Invoice Data Retrieval Endpoint Test")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Use command line argument as policy number
        policy_number = sys.argv[1]
    else:
        # Use default test policy number
        policy_number = "POL-2024-001234"
    
    # Test with policy number
    success = test_get_invoice_by_policy(policy_number)
    
    if success:
        print("\n✅ Policy number test passed!")
    else:
        print("\n❌ Policy number test failed!")
    
    # Test with quote ID (if you have a test quote ID)
    # test_get_invoice_by_quote("Q-2024-001234")
    
    # Test error cases
    test_error_cases()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()