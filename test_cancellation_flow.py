"""
Test policy cancellation flow through IMS integration
"""

import requests
import json
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-123"

# Create a cancellation transaction
def test_cancellation_flow():
    """Test cancelling a policy through the Triton endpoint"""
    
    # Sample cancellation data from Triton
    cancellation_data = {
        "transaction_type": "cancellation",
        "policy_number": "TST-2024-00001",  # Must be an existing policy
        "cancellation_date": datetime.now().strftime("%Y-%m-%d"),
        "cancellation_reason": "non-payment",
        "flat_cancel": False,  # Pro-rata cancellation
        "comments": "Policy cancelled due to non-payment",
        "return_premium_entries": [
            {
                "coverage": "General Liability",
                "premium": -1500.00  # Negative indicates return
            }
        ],
        "user": {
            "guid": "12345678-1234-1234-1234-123456789012",
            "name": "Test User"
        },
        "original_premium": 5000.00,
        "account": {
            "id": "ACC001",
            "name": "Test Account"
        }
    }
    
    # Send to Triton cancellation endpoint
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/sources/triton/transaction/cancellation",
        json=cancellation_data,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nCancellation processed successfully!")
        print(f"Transaction ID: {result.get('transaction_id')}")
        print(f"Status: {result.get('status')}")
        if result.get('ims_details'):
            print(f"IMS Processing Status: {result['ims_details'].get('processing_status')}")
    else:
        print(f"\nError processing cancellation: {response.text}")

if __name__ == "__main__":
    print("Testing Policy Cancellation Flow")
    print("=" * 50)
    test_cancellation_flow()