#!/usr/bin/env python3
"""
Test script to verify the GUID updates and flat transformer usage
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.integrations.triton.transformer import TritonTransformer
from app.integrations.triton.flat_transformer import TritonFlatTransformer
from app.services.ims_workflow_service import IMSWorkflowService
from app.models.transaction_models import Transaction, TransactionType

def test_transformers():
    """Test that transformers use correct GUIDs"""
    print("=== Testing Transformer GUIDs ===\n")
    
    # Test data from TEST.json
    test_data = {
        "policy_number": "AHC0000125",
        "insured_name": "Test Company LLC",
        "insured_state": "FL",
        "gross_premium": 1000.00,
        "producer_name": "Test Producer"
    }
    
    # Test regular transformer
    print("1. Testing TritonTransformer:")
    transformer = TritonTransformer()
    lob, line_guid = transformer.determine_line_of_business(test_data)
    print(f"   Line of Business: {lob}")
    print(f"   Line GUID: {line_guid}")
    print(f"   ✓ Expected: 07564291-CBFE-4BBE-88D1-0548C88ACED4")
    
    # Test flat transformer
    print("\n2. Testing TritonFlatTransformer:")
    flat_transformer = TritonFlatTransformer()
    transformed = flat_transformer.transform_to_ims_format(test_data)
    
    print(f"   Line GUID in policy_data: {transformed['policy_data']['line_guid']}")
    print(f"   Business Type ID: {transformed['insured_data']['business_type_id']}")
    print(f"   ✓ Line GUID should be: 07564291-CBFE-4BBE-88D1-0548C88ACED4")
    print(f"   ✓ Business Type ID should be: 9 (LLC - Partnership)")
    
    return transformed

def test_workflow_extraction(transformed_data):
    """Test that workflow service extracts data correctly"""
    print("\n=== Testing Workflow Service Extraction ===\n")
    
    # Create a mock transaction
    transaction = Transaction(
        transaction_id="test-123",
        type=TransactionType.NEW_BUSINESS,
        source="triton",
        raw_data={"test": "data"},
        parsed_data={"test": "data"},
        processed_data=transformed_data
    )
    
    # Initialize workflow service (without connecting to IMS)
    workflow = IMSWorkflowService("LOCAL")
    
    # Test quote data extraction
    print("1. Testing quote data extraction:")
    try:
        quote_data = workflow._extract_quote_data(transaction)
        print(f"   Line GUID: {quote_data['line_guid']}")
        print(f"   Quoting Location GUID: {quote_data['quoting_location_guid']}")
        print(f"   Issuing Location GUID: {quote_data['issuing_location_guid']}")
        print(f"   Company Location GUID: {quote_data['company_location_guid']}")
        print("   ✓ All GUIDs should be non-zero values")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test insured data extraction
    print("\n2. Testing insured data extraction:")
    try:
        insured_data = workflow._extract_insured_data(transaction)
        print(f"   Name: {insured_data['name']}")
        print(f"   Business Type ID: {insured_data['business_type_id']}")
        print(f"   State: {insured_data.get('state')}")
        print("   ✓ Should use transformed data structure")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test premium data extraction
    print("\n3. Testing premium data extraction:")
    try:
        premium_data = workflow._extract_premium_data(transaction)
        print(f"   Total Premium: ${premium_data['total_premium']}")
        print(f"   Number of Coverages: {len(premium_data['coverages'])}")
        if premium_data['coverages']:
            coverage = premium_data['coverages'][0]
            print(f"   Coverage Type: {coverage['type']}")
            print(f"   Coverage Premium: ${coverage['premium']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Testing GUID Updates and Flat Transformer Usage")
    print("="*60 + "\n")
    
    # Test transformers
    transformed_data = test_transformers()
    
    # Test workflow extraction
    test_workflow_extraction(transformed_data)
    
    print("\n" + "="*60)
    print("Test Summary:")
    print("- Transformers should use valid IMS GUIDs (not all zeros)")
    print("- Flat transformer should be used for flat JSON structure")
    print("- Workflow service should use transformed data when available")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()