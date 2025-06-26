#!/usr/bin/env python3
"""
Comprehensive test to validate TEST.json payload and test IMS integration
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Add app directory to path
sys.path.insert(0, os.path.abspath('.'))

from app.models.triton_models import TritonBindingTransaction
from app.integrations.triton.transformer import TritonTransformer
from app.services.transaction_service import TransactionService
from app.models.transaction_models import TransactionType
from pydantic import ValidationError

def load_test_data(file_path: str) -> Dict[str, Any]:
    """Load the TEST.json file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def validate_flat_structure(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate the flat structure has minimum required fields"""
    errors = []
    required_fields = [
        'policy_number', 'insured_name', 'insured_state', 'insured_zip',
        'effective_date', 'expiration_date', 'gross_premium', 'producer_name'
    ]
    
    for field in required_fields:
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: {field}")
    
    return len(errors) == 0, errors

def create_minimal_triton_payload(flat_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a minimal valid Triton payload from flat data"""
    
    # Parse dates to ensure proper format
    effective_date = flat_data.get('effective_date', '09/20/2025')
    expiration_date = flat_data.get('expiration_date', '09/20/2026')
    
    # Convert MM/DD/YYYY to YYYY-MM-DD
    if '/' in effective_date:
        parts = effective_date.split('/')
        effective_date = f"20{parts[2]}-{parts[0]:0>2}-{parts[1]:0>2}" if len(parts[2]) == 2 else f"{parts[2]}-{parts[0]:0>2}-{parts[1]:0>2}"
    
    if '/' in expiration_date:
        parts = expiration_date.split('/')
        expiration_date = f"20{parts[2]}-{parts[0]:0>2}-{parts[1]:0>2}" if len(parts[2]) == 2 else f"{parts[2]}-{parts[0]:0>2}-{parts[1]:0>2}"
    
    return {
        "transaction_type": "binding",
        "transaction_id": flat_data.get('transaction_id', str(datetime.now().timestamp())),
        "transaction_date": flat_data.get('transaction_date', datetime.now().isoformat()),
        "policy_number": flat_data.get('policy_number'),
        "effective_date": effective_date,
        "expiration_date": expiration_date,
        "is_renewal": flat_data.get('business_type', '').lower() == 'renewal',
        
        "account": {
            "name": flat_data.get('insured_name'),
            "street_1": "123 Main St",  # Default values for missing fields
            "city": "Unknown City",
            "state": flat_data.get('insured_state'),
            "zip": flat_data.get('insured_zip')
        },
        
        "producer": {
            "name": flat_data.get('producer_name')
        },
        
        "program": {
            "name": flat_data.get('program_name', 'Unknown Program'),
            "id": "default-program-id"
        },
        
        "premium": {
            "annual_premium": float(flat_data.get('gross_premium', 0))
        },
        
        "exposures": []  # Empty list is valid
    }

def test_payload_validation():
    """Test payload validation without making API calls"""
    
    print("=== Triton Payload Validation Test ===\\n")
    
    # Load test data
    print("1. Loading TEST.json...")
    flat_data = load_test_data("TEST.json")
    print(f"   Policy Number: {flat_data.get('policy_number')}")
    print(f"   Insured: {flat_data.get('insured_name')}")
    print(f"   Premium: ${flat_data.get('gross_premium')}")
    
    # Validate flat structure
    print("\\n2. Validating flat structure...")
    is_valid, errors = validate_flat_structure(flat_data)
    if is_valid:
        print("   ✓ All required fields present")
    else:
        print("   ✗ Validation errors:")
        for error in errors:
            print(f"     - {error}")
    
    # Create minimal Triton payload
    print("\\n3. Creating minimal Triton payload...")
    triton_payload = create_minimal_triton_payload(flat_data)
    
    # Save for inspection
    with open("TEST_minimal_triton.json", 'w') as f:
        json.dump(triton_payload, f, indent=2)
    print("   Saved to TEST_minimal_triton.json")
    
    # Validate against Triton model
    print("\\n4. Validating against Triton model...")
    try:
        transaction = TritonBindingTransaction(**triton_payload)
        print("   ✓ Payload validates successfully!")
        print(f"   Transaction Type: {transaction.transaction_type}")
        print(f"   Policy Number: {transaction.policy_number}")
        print(f"   Account Name: {transaction.account.name}")
    except ValidationError as e:
        print("   ✗ Validation failed:")
        for error in e.errors():
            print(f"     - {error['loc']}: {error['msg']}")
    
    # Test with TransactionService
    print("\\n5. Testing with TransactionService...")
    try:
        service = TransactionService()
        transaction = service.create_transaction(
            TransactionType.NEW,
            "triton",
            triton_payload,
            external_id=flat_data.get('transaction_id')
        )
        print(f"   ✓ Transaction created: {transaction.transaction_id}")
        print(f"   Status: {transaction.status}")
        
        # Clean up - remove the test transaction
        import shutil
        transaction_dir = f"data/transactions/{transaction.transaction_id}"
        if os.path.exists(transaction_dir):
            shutil.rmtree(transaction_dir)
            print("   Cleaned up test transaction")
            
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
    
    print("\\n=== Validation Test Complete ===")

def test_ims_field_mapping():
    """Test how fields will be mapped to IMS"""
    
    print("\\n=== IMS Field Mapping Test ===\\n")
    
    flat_data = load_test_data("TEST.json")
    
    print("Flat Structure -> IMS Mapping:")
    print(f"  insured_name: '{flat_data.get('insured_name')}' -> Insured.Name")
    print(f"  insured_state: '{flat_data.get('insured_state')}' -> Insured.State")
    print(f"  insured_zip: '{flat_data.get('insured_zip')}' -> Insured.ZipCode")
    print(f"  producer_name: '{flat_data.get('producer_name')}' -> Producer.Name (needs lookup)")
    print(f"  policy_number: '{flat_data.get('policy_number')}' -> Quote.ControlNumber")
    print(f"  effective_date: '{flat_data.get('effective_date')}' -> Quote.EffectiveDate")
    print(f"  gross_premium: {flat_data.get('gross_premium')} -> Premium.TotalAmount")
    print(f"  policy_fee: {flat_data.get('policy_fee')} -> Premium.PolicyFee")
    print(f"  commission_rate: {flat_data.get('commission_rate')}% -> Premium.CommissionRate")
    
    # Show what's missing
    print("\\nMissing data that IMS requires:")
    print("  - Insured street address")
    print("  - Insured city")
    print("  - Producer location/office code")
    print("  - Underwriter details")
    print("  - Coverage/limit details")
    print("  - Business type ID (currently text)")

if __name__ == "__main__":
    # Run validation test
    test_payload_validation()
    
    # Run field mapping analysis
    test_ims_field_mapping()