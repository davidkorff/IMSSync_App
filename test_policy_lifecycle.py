"""
Test complete policy lifecycle flow through IMS integration
This demonstrates: New Policy -> Endorsement -> Cancellation -> Reinstatement
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-123"

def create_new_policy():
    """Step 1: Create a new policy"""
    print("\n1. Creating New Policy")
    print("-" * 30)
    
    policy_data = {
        "transaction_type": "binding",
        "policy_number": "LIFE-2024-00001",
        "effective_date": datetime.now().strftime("%Y-%m-%d"),
        "expiration_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
        "account": {
            "id": "ACC-LIFE-001",
            "name": "Lifecycle Test Company",
            "street_1": "123 Test Street",
            "city": "Test City",
            "state": "CA",
            "zip": "90001"
        },
        "producer": {
            "id": "PROD001",
            "name": "Test Producer"
        },
        "coverages": [{
            "type": "General Liability",
            "limit": 1000000,
            "deductible": 5000,
            "premium": 5000.00
        }],
        "premium": {
            "total": 5000.00,
            "term": "annual"
        }
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/sources/triton/transaction/new",
        json=policy_data,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Transaction ID: {result.get('transaction_id')}")
        print(f"Policy created successfully!")
        return result.get('transaction_id')
    else:
        print(f"Error: {response.text}")
        return None

def endorse_policy():
    """Step 2: Endorse the policy"""
    print("\n2. Endorsing Policy")
    print("-" * 30)
    time.sleep(2)  # Wait for previous transaction to complete
    
    endorsement_data = {
        "transaction_type": "endorsement",
        "policy_number": "LIFE-2024-00001",
        "effective_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "endorsement": {
            "endorsement_number": "END-001",
            "effective_from": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "description": "Add Property coverage",
            "endorsement_code": "add_coverage",
            "premium": 2000.00,
            "changes": [{
                "type": "add_coverage",
                "coverage": "Property",
                "limit": 500000,
                "premium": 2000.00
            }]
        }
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/sources/triton/transaction/endorsement",
        json=endorsement_data,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Transaction ID: {result.get('transaction_id')}")
        print(f"Endorsement created successfully!")
        return result.get('transaction_id')
    else:
        print(f"Error: {response.text}")
        return None

def cancel_policy():
    """Step 3: Cancel the policy"""
    print("\n3. Cancelling Policy")
    print("-" * 30)
    time.sleep(2)  # Wait for previous transaction to complete
    
    cancellation_data = {
        "transaction_type": "cancellation",
        "policy_number": "LIFE-2024-00001",
        "cancellation_date": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
        "cancellation_reason": "request",
        "comments": "Customer requested cancellation",
        "flat_cancel": False,
        "return_premium_entries": [{
            "coverage": "General Liability",
            "premium": -4166.67  # Pro-rata return for 10 months
        }, {
            "coverage": "Property",
            "premium": -1666.67  # Pro-rata return for 10 months
        }]
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/sources/triton/transaction/cancellation",
        json=cancellation_data,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Transaction ID: {result.get('transaction_id')}")
        print(f"Policy cancelled successfully!")
        return result.get('transaction_id')
    else:
        print(f"Error: {response.text}")
        return None

def reinstate_policy():
    """Step 4: Reinstate the policy"""
    print("\n4. Reinstating Policy")
    print("-" * 30)
    time.sleep(2)  # Wait for previous transaction to complete
    
    reinstatement_data = {
        "transaction_type": "reinstatement",
        "policy_number": "LIFE-2024-00001",
        "reinstatement_date": (datetime.now() + timedelta(days=65)).strftime("%Y-%m-%d"),
        "reason": "payment_received",
        "comments": "Customer paid outstanding balance",
        "payment_amount": 5833.34,  # Amount owed for reinstatement
        "check_number": "CHK-98765",
        "generate_invoice": True
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/sources/triton/transaction/reinstatement",
        json=reinstatement_data,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Transaction ID: {result.get('transaction_id')}")
        print(f"Policy reinstated successfully!")
        return result.get('transaction_id')
    else:
        print(f"Error: {response.text}")
        return None

def check_transaction_status(transaction_id):
    """Check the status of a transaction"""
    headers = {
        "X-API-Key": API_KEY
    }
    
    response = requests.get(
        f"{BASE_URL}/api/transactions/{transaction_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        return result.get('status'), result.get('ims_processing', {}).get('status')
    return None, None

if __name__ == "__main__":
    print("Testing Complete Policy Lifecycle")
    print("=" * 50)
    
    # Run the complete lifecycle
    transaction_ids = []
    
    # Create new policy
    tx_id = create_new_policy()
    if tx_id:
        transaction_ids.append(("New Policy", tx_id))
    
    # Endorse policy
    tx_id = endorse_policy()
    if tx_id:
        transaction_ids.append(("Endorsement", tx_id))
    
    # Cancel policy
    tx_id = cancel_policy()
    if tx_id:
        transaction_ids.append(("Cancellation", tx_id))
    
    # Reinstate policy
    tx_id = reinstate_policy()
    if tx_id:
        transaction_ids.append(("Reinstatement", tx_id))
    
    # Check final status of all transactions
    print("\n" + "=" * 50)
    print("Final Transaction Status Summary:")
    print("-" * 50)
    
    for name, tx_id in transaction_ids:
        status, ims_status = check_transaction_status(tx_id)
        print(f"{name}: {status} (IMS: {ims_status})")