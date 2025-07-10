"""
Test policy reinstatement flow through IMS integration
"""

import requests
import json
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-123"

# Create a reinstatement transaction
def test_reinstatement_flow():
    """Test reinstating a cancelled policy through the Triton endpoint"""
    
    # Sample reinstatement data from Triton
    reinstatement_data = {
        "transaction_type": "reinstatement",
        "policy_number": "TST-2024-00001",  # Must be a cancelled policy
        "reinstatement_date": datetime.now().strftime("%Y-%m-%d"),
        "effective_date": datetime.now().strftime("%Y-%m-%d"),
        "reason": "payment_received",
        "comments": "Policy reinstated - payment received",
        "payment_amount": 2500.00,
        "check_number": "CHK-12345",
        "generate_invoice": True,
        "payment_details": {
            "method": "check",
            "check_number": "CHK-12345",
            "amount": 2500.00,
            "received_date": datetime.now().strftime("%Y-%m-%d"),
            "deposited": True
        },
        "user": {
            "guid": "12345678-1234-1234-1234-123456789012",
            "name": "Test User"
        },
        "account": {
            "id": "ACC001",
            "name": "Test Account"
        }
    }
    
    # Send to Triton reinstatement endpoint
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/sources/triton/transaction/reinstatement",
        json=reinstatement_data,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nReinstatement processed successfully!")
        print(f"Transaction ID: {result.get('transaction_id')}")
        print(f"Status: {result.get('status')}")
        if result.get('ims_details'):
            print(f"IMS Processing Status: {result['ims_details'].get('processing_status')}")
    else:
        print(f"\nError processing reinstatement: {response.text}")

def test_reinstatement_without_payment():
    """Test reinstating due to error correction"""
    
    reinstatement_data = {
        "transaction_type": "reinstatement",
        "policy_number": "TST-2024-00002",
        "reinstatement_date": datetime.now().strftime("%Y-%m-%d"),
        "reason": "error",
        "comments": "Policy cancelled in error - reinstating",
        "generate_invoice": False,  # No invoice needed for error correction
        "user": {
            "guid": "12345678-1234-1234-1234-123456789012",
            "name": "Test User"
        }
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
    
    print(f"\nReinstatement (Error Correction) Test:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("Testing Policy Reinstatement Flow")
    print("=" * 50)
    test_reinstatement_flow()
    
    print("\n" + "=" * 50)
    test_reinstatement_without_payment()