#!/usr/bin/env python3
"""
Test client for the IMS Integration API
"""

import requests
import json
import argparse
import sys
import time
from datetime import date

# Default configuration
DEFAULT_URL = "http://localhost:8000"
DEFAULT_API_KEY = "test_api_key"

def create_new_transaction(base_url, api_key):
    """Create a new transaction with sample data"""
    
    # Sample policy data in JSON format
    sample_policy = {
        "policy_number": "TRI-12345",
        "effective_date": str(date.today()),
        "expiration_date": str(date(date.today().year + 1, date.today().month, date.today().day)),
        "bound_date": str(date.today()),
        "program": "Test Program",
        "line_of_business": "General Liability",
        "state": "TX",
        "insured": {
            "name": "Test Company LLC",
            "dba": "Test Co",
            "contact": {
                "name": "John Smith",
                "email": "john@example.com",
                "phone": "555-123-4567",
                "address": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701"
            },
            "tax_id": "12-3456789",
            "business_type": "LLC"
        },
        "locations": [
            {
                "address": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701",
                "country": "USA",
                "description": "Main Office"
            }
        ],
        "producer": {
            "name": "ABC Insurance Agency",
            "contact": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "555-987-6543"
            },
            "commission": 15.0
        },
        "underwriter": "Bob Johnson",
        "coverages": [
            {
                "type": "General Liability",
                "limit": 1000000.0,
                "deductible": 5000.0,
                "premium": 10000.0
            }
        ],
        "premium": 10000.0,
        "billing_type": "Agency Bill",
        "additional_data": {
            "source_system": "triton",
            "source_id": "TRI-12345-1"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    endpoint = f"{base_url}/api/transaction/new"
    
    print(f"Creating new transaction at {endpoint}...")
    
    response = requests.post(endpoint, json=sample_policy, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    return response.json().get("transaction_id")

def create_update_transaction(base_url, api_key, policy_number="TRI-12345"):
    """Create an update transaction with sample data"""
    
    # Sample update data in JSON format
    sample_update = {
        "policy_number": policy_number,
        "updates": {
            "premium": 12000.0,
            "coverages": [
                {
                    "type": "General Liability",
                    "limit": 1000000.0,
                    "deductible": 5000.0,
                    "premium": 12000.0
                }
            ]
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    endpoint = f"{base_url}/api/transaction/update"
    
    print(f"Creating update transaction at {endpoint}...")
    
    response = requests.post(endpoint, json=sample_update, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    return response.json().get("transaction_id")

def check_transaction_status(base_url, api_key, transaction_id):
    """Check the status of a transaction"""
    
    headers = {
        "X-API-Key": api_key
    }
    
    endpoint = f"{base_url}/api/transaction/{transaction_id}"
    
    print(f"Checking transaction status at {endpoint}...")
    
    response = requests.get(endpoint, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def main():
    parser = argparse.ArgumentParser(description="Test client for IMS Integration API")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Base URL for the API (default: {DEFAULT_URL})")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help=f"API key (default: {DEFAULT_API_KEY})")
    parser.add_argument("--action", choices=["new", "update", "status"], required=True, 
                        help="Action to perform (new, update, status)")
    parser.add_argument("--transaction-id", help="Transaction ID for status check")
    parser.add_argument("--policy-number", default="TRI-12345", help="Policy number for update")
    
    args = parser.parse_args()
    
    # Perform the requested action
    if args.action == "new":
        transaction_id = create_new_transaction(args.url, args.api_key)
        print(f"\nCreated transaction: {transaction_id}")
        
        # Check status a few times
        if transaction_id:
            for _ in range(3):
                time.sleep(2)
                check_transaction_status(args.url, args.api_key, transaction_id)
                
    elif args.action == "update":
        transaction_id = create_update_transaction(args.url, args.api_key, args.policy_number)
        print(f"\nCreated update transaction: {transaction_id}")
        
        # Check status a few times
        if transaction_id:
            for _ in range(3):
                time.sleep(2)
                check_transaction_status(args.url, args.api_key, transaction_id)
                
    elif args.action == "status":
        if not args.transaction_id:
            print("Error: --transaction-id is required for status check")
            sys.exit(1)
            
        check_transaction_status(args.url, args.api_key, args.transaction_id)
    
if __name__ == "__main__":
    main()