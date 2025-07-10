"""
Test policy endorsement flow through IMS integration
"""

import requests
import json
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-123"

# Create an endorsement transaction
def test_endorsement_flow():
    """Test endorsing a policy through the Triton endpoint"""
    
    # Sample endorsement data from Triton
    endorsement_data = {
        "transaction_type": "endorsement",
        "policy_number": "TST-2024-00001",  # Must be an existing policy
        "effective_date": datetime.now().strftime("%Y-%m-%d"),
        "endorsement": {
            "endorsement_number": "END-001",
            "effective_from": datetime.now().strftime("%Y-%m-%d"),
            "description": "Add additional coverage for new location",
            "endorsement_code": "add_coverage",
            "premium": 1500.00,  # Additional premium
            "changes": [
                {
                    "type": "add_location",
                    "location": {
                        "address": "456 New Street",
                        "city": "New City",
                        "state": "CA",
                        "zip": "90210"
                    }
                },
                {
                    "type": "modify_coverage",
                    "coverage": "General Liability",
                    "old_limit": 1000000,
                    "new_limit": 2000000
                }
            ]
        },
        "user": {
            "guid": "12345678-1234-1234-1234-123456789012",
            "name": "Test User"
        },
        "account": {
            "id": "ACC001",
            "name": "Test Account"
        },
        "producer": {
            "id": "PROD001",
            "name": "Test Producer"
        }
    }
    
    # Send to Triton endorsement endpoint
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/sources/triton/transaction/endorsement",
        json=endorsement_data,
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nEndorsement processed successfully!")
        print(f"Transaction ID: {result.get('transaction_id')}")
        print(f"Status: {result.get('status')}")
        if result.get('ims_details'):
            print(f"IMS Processing Status: {result['ims_details'].get('processing_status')}")
    else:
        print(f"\nError processing endorsement: {response.text}")

def test_midterm_endorsement_flow():
    """Test midterm endorsement through the Triton endpoint"""
    
    # Sample midterm endorsement data
    midterm_data = {
        "transaction_type": "midterm_endorsement",
        "policy_number": "TST-2024-00001",
        "effective_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "endorsement": {
            "endorsement_number": "MID-001",
            "effective_from": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "description": "Midterm adjustment - reduce coverage",
            "endorsement_code": "remove_coverage",
            "premium": -750.00,  # Return premium
            "changes": [
                {
                    "type": "remove_coverage",
                    "coverage": "Property",
                    "reason": "No longer needed"
                }
            ]
        },
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
        f"{BASE_URL}/api/sources/triton/transaction/midterm_endorsement",
        json=midterm_data,
        headers=headers
    )
    
    print(f"\nMidterm Endorsement Test:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("Testing Policy Endorsement Flow")
    print("=" * 50)
    test_endorsement_flow()
    
    print("\n" + "=" * 50)
    test_midterm_endorsement_flow()