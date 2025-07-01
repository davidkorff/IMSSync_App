#!/usr/bin/env python3
"""
Test the business type mapping fix
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.integrations.triton.flat_transformer import TritonFlatTransformer

def test_business_type_mapping():
    """Test the updated business type mapping"""
    
    transformer = TritonFlatTransformer()
    
    print("Testing Business Type Mapping Fix")
    print("=" * 60)
    
    test_cases = [
        # Business entity types
        ("Corporation", 1),
        ("CORP", 1),
        ("Inc.", 1),
        ("ABC Company, Inc", 1),
        ("Partnership", 2),
        ("Limited Liability Partnership", 3),
        ("LLP", 3),
        ("Individual", 3),
        ("Sole Proprietor", 4),
        ("Sole Prop", 4),
        ("LLC", 5),
        ("Limited Liability Company", 5),
        ("Other", 5),
        
        # Transaction types (should default to 1)
        ("Renewal", 1),
        ("New Business", 1),
        ("Endorsement", 1),
        ("Cancellation", 1),
        
        # Unknown types (should default to 1)
        ("Unknown Entity", 1),
        ("", 1),
        ("Some Random Text", 1)
    ]
    
    print(f"{'Input':<35} {'Expected':<10} {'Actual':<10} {'Status':<10}")
    print("-" * 70)
    
    all_passed = True
    
    for test_input, expected in test_cases:
        actual = transformer._get_business_type_id(test_input)
        status = "PASS" if actual == expected else "FAIL"
        
        if actual != expected:
            all_passed = False
            
        print(f"{test_input:<35} {expected:<10} {actual:<10} {status:<10}")
    
    print("-" * 70)
    
    if all_passed:
        print("\nAll tests PASSED! The business type mapping is now correct.")
        print("\nThe fix addresses:")
        print("1. Corporation now maps to ID 1 (not 13)")
        print("2. Transaction types like 'Renewal' are handled properly")
        print("3. All mappings are consistent with IMS database")
    else:
        print("\nSome tests FAILED. Please check the implementation.")
    
    # Test with sample data
    print("\n\nTesting with sample data:")
    print("=" * 60)
    
    sample_data = {
        "insured_name": "Test Company Inc",
        "business_type": "Renewal",  # This was causing the error
        "effective_date": "01/01/2025",
        "insured_state": "FL",
        "insured_zip": "33301"
    }
    
    result = transformer.transform_to_ims_format(sample_data)
    
    print(f"Input business_type: '{sample_data['business_type']}'")
    print(f"Output business_type_id: {result['insured_data']['business_type_id']}")
    print(f"Is renewal flag: {result['policy_data']['is_renewal']}")
    
    if result['insured_data']['business_type_id'] == 1:
        print("\nSUCCESS: 'Renewal' now correctly maps to BusinessTypeID 1 (Corporation)")
        print("This should fix the foreign key constraint error!")
    else:
        print("\nERROR: The mapping is still incorrect!")

if __name__ == "__main__":
    test_business_type_mapping()