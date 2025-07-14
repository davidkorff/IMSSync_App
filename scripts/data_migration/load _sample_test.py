import requests
import json
from datetime import datetime

# API endpoint and authentication
API_URL = "http://localhost:8000/api/policy"
API_KEY = "test_api_key"

# Headers for the request
headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Sample policy data based on the CSV
sample_policy = {
  "policy_number": "GAH-102352-250402",
  "effective_date": "2025-04-02",
  "expiration_date": "2026-04-02",
  "bound_date": "2025-04-25",
  "program": "Allied Health",
  "line_of_business": "AHC Primary",
  "state": "FL",
  "insured": {
    "name": "Community Comfort Care Incorporated",
    "dba": "Comfort Care Nursing Professionals",
    "contact": {
      "name": "John Smith",
      "email": "john@comfortcare.com",
      "phone": "555-123-4567",
      "address": "123 Healthcare Ave",
      "city": "Miami",
      "state": "FL",
      "zip_code": "33351"
    },
    "tax_id": "12-3456789",
    "business_type": "Corporation"
  },
  "locations": [
    {
      "address": "123 Healthcare Ave",
      "city": "Miami",
      "state": "FL",
      "zip_code": "33351",
      "country": "USA",
      "description": "Main Office"
    }
  ],
  "producer": {
    "name": "Everisk Insurance Programs, Inc.",
    "commission": 0.175
  },
  "underwriter": "Christina Rentas",
  "coverages": [
    {
      "type": "Allied Health Professional Liability",
      "limit": 1000000,
      "deductible": 2500,
      "premium": 810.0
    }
  ],
  "premium": 2053.0,
  "billing_type": "Agency Bill"
}

def send_policy_to_api():
    """Send the sample policy to the API and print the response"""
    try:
        print(f"Sending policy {sample_policy['policy_number']} to {API_URL}...")
        
        # Make the POST request
        response = requests.post(
            API_URL, 
            headers=headers,
            data=json.dumps(sample_policy)
        )
        
        # Check if request was successful
        if response.status_code == 201:
            print("Success! Policy was created.")
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"Error: Received status code {response.status_code}")
            print("Response:")
            print(json.dumps(response.json(), indent=2) if response.text else "No response body")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {API_URL}")
        print("Make sure the server is running and accessible.")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("IMS Integration API - Test Policy Submission")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Send the policy
    send_policy_to_api()