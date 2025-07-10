"""
Test the simplified Triton integration with TEST.json data
"""

import json
import requests
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def test_binding_with_test_json():
    """Test with the actual TEST.json file"""
    
    # Load TEST.json
    with open('TEST.json', 'r') as f:
        test_data = json.load(f)
    
    # Transform to match Triton webhook format
    triton_payload = {
        "transaction_type": "binding",  # or "new" based on transaction_type
        "transaction_id": test_data.get("transaction_id", f"TEST-{datetime.now().timestamp()}"),
        "policy_number": test_data["policy_number"],
        "effective_date": test_data["effective_date"],
        "expiration_date": test_data["expiration_date"],
        "bound_date": test_data["bound_date"],
        
        # Account/Insured info
        "account": {
            "name": test_data["insured_name"],
            "street_1": test_data["address_1"],
            "street_2": test_data.get("address_2", ""),
            "city": test_data["city"],
            "state": test_data["state"],
            "zip": test_data["zip"]
        },
        
        # Producer info
        "producer": {
            "name": test_data["producer_name"]
        },
        
        # Program info
        "program": {
            "name": test_data["program_name"],
            "class_of_business": test_data["class_of_business"]
        },
        
        # Underwriter
        "underwriter": {
            "name": test_data["underwriter_name"]
        },
        
        # Premium info
        "premium": {
            "annual_premium": test_data["gross_premium"],
            "base_premium": test_data["base_premium"],
            "policy_fee": test_data["policy_fee"],
            "commission_rate": test_data["commission_rate"]
        },
        
        # Coverage info (parsed from limit string)
        "exposures": [{
            "coverage_name": test_data["class_of_business"],
            "limit": {"value": test_data["limit_amount"]},
            "deductible": {"value": test_data["deductible_amount"]}
        }],
        
        # Additional insureds
        "additional_insureds": test_data.get("additional_insured", []),
        
        # All other fields preserved
        "original_data": {
            "opportunity_id": test_data["opportunity_id"],
            "business_type": test_data["business_type"],
            "status": test_data["status"],
            "commission_percent": test_data["commission_percent"],
            "net_premium": test_data["net_premium"]
        }
    }
    
    print("\n=== Testing with TEST.json data ===")
    print(f"Policy Number: {triton_payload['policy_number']}")
    print(f"Insured: {triton_payload['account']['name']}")
    print(f"Premium: ${triton_payload['premium']['annual_premium']}")
    
    # API endpoint - using the existing Triton endpoint
    url = "http://localhost:8000/api/triton/transaction/new"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "triton_test_key"  # Update with your API key
    }
    
    try:
        # Make the request
        print("\nSending to Triton transaction endpoint...")
        response = requests.post(url, json=triton_payload, headers=headers)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("\n✅ SUCCESS!")
                print(f"Policy Number: {result['data']['policy_number']}")
                print(f"Quote GUID: {result['data']['quote_guid']}")
                print(f"Invoice Number: {result['data'].get('invoice_number', 'Not yet available')}")
        else:
            print("\n❌ ERROR!")
            print(response.json())
            
    except Exception as e:
        print(f"\n❌ Request failed: {str(e)}")


def test_direct_processor():
    """Test the processor directly without HTTP"""
    from app.services.triton_processor import TritonProcessor
    from app.services.ims_client import IMSClient
    from app.config.triton_config import get_config_for_environment
    
    # Load TEST.json
    with open('TEST.json', 'r') as f:
        test_data = json.load(f)
    
    # Simple flat structure (similar to TEST.json)
    triton_data = {
        "transaction_type": "binding",
        "transaction_id": test_data["transaction_id"],
        "policy_number": test_data["policy_number"],
        "effective_date": test_data["effective_date"],
        "expiration_date": test_data["expiration_date"],
        "insured_name": test_data["insured_name"],
        "insured_state": test_data["state"],
        "insured_zip": test_data["zip"],
        "producer_name": test_data["producer_name"],
        "gross_premium": test_data["gross_premium"],
        "commission_rate": test_data["commission_rate"],
        "limit_amount": test_data["limit_amount"],
        "deductible_amount": test_data["deductible_amount"],
        "address_1": test_data["address_1"],
        "city": test_data["city"],
        "state": test_data["state"],
        "zip": test_data["zip"]
    }
    
    print("\n=== Testing Direct Processor (Flat Structure) ===")
    
    try:
        # Get configuration
        config = get_config_for_environment('ims_one')
        
        # Create IMS client and processor
        ims_client = IMSClient(config)
        processor = TritonProcessor(ims_client, config)
        
        # Process the transaction
        result = processor.process_transaction(triton_data)
        
        print("\n✅ SUCCESS!")
        print(f"Result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("TESTING WITH TEST.JSON DATA")
    print("=" * 60)
    
    # Test via HTTP
    test_binding_with_test_json()
    
    # Or test directly
    # test_direct_processor()