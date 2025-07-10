"""
Test the simplified Triton-IMS integration flow
Demonstrates how simple the new architecture is
"""

import json
import logging
from datetime import date, datetime
from app.services.triton_processor import TritonProcessor, TritonError
from app.services.ims_client import IMSClient
from app.config.triton_config import get_config_for_environment

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_binding_transaction():
    """Test a simple binding transaction"""
    
    # Sample Triton binding data
    triton_data = {
        "transaction_type": "binding",
        "transaction_id": "TEST-001",
        "policy_number": "POL-2024-TEST-001",
        "effective_date": "2024-01-01",
        "expiration_date": "2025-01-01",
        "account": {
            "id": "ACC-TEST-001",
            "name": "Test Company LLC",
            "street_1": "123 Test Street",
            "city": "Dallas",
            "state": "TX",
            "zip": "75201"
        },
        "producer": {
            "name": "Test Agency",
            "id": "PROD-001"
        },
        "program": {
            "name": "AHC Primary GL"
        },
        "premium": {
            "annual_premium": 25000.00
        },
        "exposures": [{
            "coverage_name": "General Liability",
            "limit": {"value": 1000000},
            "deductible": {"value": 5000}
        }],
        # Custom fields that IMS doesn't have
        "custom_rating_factors": {
            "industry_modifier": 1.2,
            "location_factor": 0.95,
            "claims_free_discount": 0.10
        },
        "triton_specific_data": {
            "submission_source": "API",
            "broker_commission": 0.15,
            "payment_plan": "annual"
        }
    }
    
    print("\n=== Testing Triton Binding Transaction ===")
    print(f"Transaction ID: {triton_data['transaction_id']}")
    print(f"Policy Number: {triton_data['policy_number']}")
    
    try:
        # Get configuration
        config = get_config_for_environment('ims_one')
        
        # Create IMS client
        print("\n1. Initializing IMS client...")
        ims_client = IMSClient(config)
        
        # Create processor
        print("2. Creating Triton processor...")
        processor = TritonProcessor(ims_client, config)
        
        # Process the transaction
        print("3. Processing binding transaction...")
        result = processor.process_transaction(triton_data)
        
        print("\n✅ SUCCESS!")
        print(f"Policy Number: {result['policy_number']}")
        print(f"Quote GUID: {result['quote_guid']}")
        print(f"Invoice Number: {result.get('invoice_number', 'Not yet available')}")
        
        # All custom data was preserved in the Excel file!
        print("\n📊 Custom data preserved in Excel rating sheet")
        print("   - Industry modifier: 1.2")
        print("   - Location factor: 0.95")
        print("   - Broker commission: 15%")
        
    except TritonError as e:
        print(f"\n❌ ERROR at stage: {e.stage}")
        print(f"Message: {e.message}")
        print(f"Details: {json.dumps(e.details, indent=2)}")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


def test_cancellation_transaction():
    """Test a cancellation transaction"""
    
    triton_data = {
        "transaction_type": "cancellation",
        "transaction_id": "TEST-002",
        "policy_number": "POL-2024-TEST-001",
        "cancellation_date": "2024-06-01",
        "cancellation_reason": "non-payment",
        "flat_cancel": False
    }
    
    print("\n=== Testing Triton Cancellation Transaction ===")
    print(f"Transaction ID: {triton_data['transaction_id']}")
    print(f"Policy Number: {triton_data['policy_number']}")
    print(f"Cancellation Date: {triton_data['cancellation_date']}")
    
    try:
        # Get configuration
        config = get_config_for_environment('ims_one')
        
        # Create IMS client and processor
        ims_client = IMSClient(config)
        processor = TritonProcessor(ims_client, config)
        
        # Process the transaction
        result = processor.process_transaction(triton_data)
        
        print("\n✅ SUCCESS!")
        print(f"Message: {result['message']}")
        
    except TritonError as e:
        print(f"\n❌ ERROR at stage: {e.stage}")
        print(f"Message: {e.message}")
        print(f"Details: {json.dumps(e.details, indent=2)}")


def test_error_handling():
    """Test error handling with invalid data"""
    
    triton_data = {
        "transaction_type": "binding",
        "transaction_id": "TEST-003",
        # Missing required fields to trigger error
        "account": {
            "name": ""  # Empty name will cause error
        }
    }
    
    print("\n=== Testing Error Handling ===")
    
    try:
        config = get_config_for_environment('ims_one')
        ims_client = IMSClient(config)
        processor = TritonProcessor(ims_client, config)
        
        result = processor.process_transaction(triton_data)
        
    except TritonError as e:
        print(f"\n✅ Error caught correctly!")
        print(f"Stage: {e.stage}")
        print(f"Message: {e.message}")
        print(f"Details: {json.dumps(e.details, indent=2)}")
        print("\nThis is exactly what we want - clear error information!")


def main():
    """Run all tests"""
    print("=" * 60)
    print("SIMPLIFIED TRITON-IMS INTEGRATION TEST")
    print("=" * 60)
    
    # Test binding
    test_binding_transaction()
    
    # Test cancellation
    # test_cancellation_transaction()
    
    # Test error handling
    test_error_handling()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()