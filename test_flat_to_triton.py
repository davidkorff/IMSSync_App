#!/usr/bin/env python3
"""
Test script to transform flat TEST.json structure to Triton format and test IMS integration
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any

def load_test_data(file_path: str) -> Dict[str, Any]:
    """Load the TEST.json file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def transform_flat_to_triton(flat_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform flat structure to expected Triton format"""
    
    # Parse limit string to extract occurrence and aggregate
    limit_string = flat_data.get('limit_amount', '$1,000,000/$3,000,000')
    limit_parts = limit_string.replace('$', '').replace(',', '').split('/')
    occurrence_limit = int(limit_parts[0]) if len(limit_parts) > 0 else 1000000
    aggregate_limit = int(limit_parts[1]) if len(limit_parts) > 1 else 3000000
    
    # Parse deductible
    deductible_string = flat_data.get('deductible_amount', '$2,500')
    deductible_amount = int(deductible_string.replace('$', '').replace(',', ''))
    
    # Create Triton-formatted transaction
    triton_transaction = {
        "transaction_type": "binding",
        "transaction_id": flat_data.get('transaction_id'),
        "transaction_date": flat_data.get('transaction_date'),
        "sent_at": datetime.now().isoformat(),
        
        # Policy details
        "policy_number": flat_data.get('policy_number'),
        "effective_date": flat_data.get('effective_date'),
        "expiration_date": flat_data.get('expiration_date'),
        "is_renewal": flat_data.get('business_type', '').lower() == 'renewal',
        
        # Account (Insured) information
        "account": {
            "name": flat_data.get('insured_name'),
            "street_1": "Address Unknown",  # Not provided in flat structure
            "city": "City Unknown",  # Not provided
            "state": flat_data.get('insured_state'),
            "zip": flat_data.get('insured_zip')
        },
        
        # Producer information
        "producer": {
            "name": flat_data.get('producer_name'),
            "email": None,  # Not provided
            "phone": None   # Not provided
        },
        
        # Program information
        "program": {
            "name": flat_data.get('program_name'),
            "class_of_business": flat_data.get('class_of_business')
        },
        
        # Underwriter information
        "underwriter": {
            "name": flat_data.get('underwriter_name')
        },
        
        # Premium information
        "premium": {
            "annual_premium": flat_data.get('gross_premium', 0),
            "policy_fee": flat_data.get('policy_fee', 0),
            "commission_rate": flat_data.get('commission_rate', 0),
            "invoice_date": flat_data.get('invoice_date'),
            "invoice_number": flat_data.get('policy_number')  # Using policy number as invoice
        },
        
        # Exposures (Coverage) information
        "exposures": [
            {
                "program_class_name": flat_data.get('class_of_business'),
                "coverage_name": "General Liability",
                "limit": {
                    "occurrence": occurrence_limit,
                    "aggregate": aggregate_limit
                },
                "deductible": deductible_amount
            }
        ],
        
        # Additional metadata from flat structure
        "metadata": {
            "source_system": flat_data.get('source_system', 'triton'),
            "transaction_type_original": flat_data.get('transaction_type'),
            "opportunity_id": flat_data.get('opportunity_id'),
            "bound_date": flat_data.get('bound_date'),
            "status": flat_data.get('status')
        }
    }
    
    return triton_transaction

def test_api_endpoint(transformed_data: Dict[str, Any], api_key: str, base_url: str):
    """Test the Triton API endpoint with transformed data"""
    
    # Endpoint URL
    url = f"{base_url}/api/triton/transaction/new"
    
    # Headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-External-ID": transformed_data.get('transaction_id')
    }
    
    # Make request
    try:
        print(f"\\nSending request to: {url}")
        print(f"Headers: {headers}")
        print(f"\\nPayload preview:")
        print(json.dumps(transformed_data, indent=2)[:500] + "...\\n")
        
        response = requests.post(
            url,
            headers=headers,
            json=transformed_data,
            params={"sync_mode": "true"}  # Process synchronously
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\\nSuccess! Response:")
            print(json.dumps(result, indent=2))
            return result
        else:
            print(f"\\nError Response:")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"\\nRequest failed with error: {str(e)}")
        return None

def main():
    """Main test function"""
    
    # Configuration
    TEST_FILE = "TEST.json"
    API_KEY = "your-api-key-here"  # Replace with actual API key
    BASE_URL = "http://localhost:8020"  # Adjust as needed
    
    print("=== Flat to Triton Transformation Test ===\\n")
    
    # Load test data
    print(f"1. Loading test data from {TEST_FILE}...")
    flat_data = load_test_data(TEST_FILE)
    print(f"   Loaded data for policy: {flat_data.get('policy_number')}")
    
    # Transform data
    print("\\n2. Transforming flat structure to Triton format...")
    triton_data = transform_flat_to_triton(flat_data)
    print("   Transformation complete")
    
    # Save transformed data for inspection
    transformed_file = "TEST_triton_format.json"
    with open(transformed_file, 'w') as f:
        json.dump(triton_data, f, indent=2)
    print(f"   Saved transformed data to {transformed_file}")
    
    # Test API endpoint
    print("\\n3. Testing API endpoint...")
    result = test_api_endpoint(triton_data, API_KEY, BASE_URL)
    
    if result:
        print("\\n4. Analyzing IMS integration results...")
        if result.get('ims_details'):
            ims = result['ims_details']
            print(f"   IMS Processing Status: {ims.get('processing_status')}")
            print(f"   Insured GUID: {ims.get('insured_guid')}")
            print(f"   Quote GUID: {ims.get('quote_guid')}")
            print(f"   Policy Number: {ims.get('policy_number')}")
            if ims.get('error'):
                print(f"   Error: {ims.get('error')}")
    
    print("\\n=== Test Complete ===")

if __name__ == "__main__":
    main()