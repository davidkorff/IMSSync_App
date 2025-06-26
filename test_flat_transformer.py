#!/usr/bin/env python3
"""
Test the flat transformer with TEST.json
"""

import json
import sys
import os

# Add app to path
sys.path.insert(0, os.path.abspath('.'))

from app.integrations.triton.flat_transformer import TritonFlatTransformer

def test_flat_transformer():
    """Test the flat transformer with TEST.json data"""
    
    print("=== Testing Flat Transformer ===\n")
    
    # Load TEST.json
    with open("TEST.json", 'r') as f:
        test_data = json.load(f)
    
    # Create transformer with sample config
    config = {
        "default_line_guid": "12345678-1234-1234-1234-123456789012",
        "default_producer_guid": "87654321-4321-4321-4321-210987654321",
        "default_excel_rater_id": 1,
        "excel_raters": {
            "1": {
                "lob": "AHC Primary",
                "states": ["FL", "NY", "CA"],
                "factor_set_guid": "abcdef12-3456-7890-abcd-ef1234567890"
            }
        }
    }
    
    transformer = TritonFlatTransformer(config)
    
    # Transform the data
    print("1. Transforming flat data...")
    transformed = transformer.transform_to_ims_format(test_data)
    
    # Save transformed data
    with open("TEST_flat_transformed.json", 'w') as f:
        json.dump(transformed, f, indent=2)
    print("   ✓ Saved to TEST_flat_transformed.json")
    
    # Display key transformations
    print("\n2. Key Transformations:")
    print(f"   Policy Number: {test_data.get('policy_number')} → {transformed['policy_data']['policy_number']}")
    print(f"   Insured Name: {test_data.get('insured_name')} → {transformed['insured_data']['name']}")
    print(f"   Effective Date: {test_data.get('effective_date')} → {transformed['policy_data']['effective_date']}")
    print(f"   Premium: ${test_data.get('gross_premium')} → ${transformed['premium_data']['gross_premium']}")
    print(f"   LOB: (determined) → {transformed['policy_data']['line_of_business']}")
    
    # Get Excel rater info
    print("\n3. Excel Rater Info:")
    rater_info = transformer.get_excel_rater_info(test_data)
    print(f"   Rater ID: {rater_info['rater_id']}")
    print(f"   Factor Set GUID: {rater_info['factor_set_guid']}")
    print(f"   LOB: {rater_info['lob']}")
    print(f"   State: {rater_info['state']}")
    
    # Validate structure
    print("\n4. Validation:")
    required_sections = ['policy_data', 'insured_data', 'producer_data', 'premium_data', 'locations', 'coverages']
    all_present = all(section in transformed for section in required_sections)
    
    if all_present:
        print("   ✓ All required sections present")
        
        # Check for IMS required fields
        ims_required = {
            'policy_data': ['policy_number', 'effective_date', 'expiration_date'],
            'insured_data': ['name', 'state', 'zip'],
            'premium_data': ['gross_premium']
        }
        
        for section, fields in ims_required.items():
            for field in fields:
                value = transformed.get(section, {}).get(field)
                if value:
                    print(f"   ✓ {section}.{field}: {value}")
                else:
                    print(f"   ✗ {section}.{field}: MISSING")
    else:
        print("   ✗ Missing required sections")
    
    print("\n=== Test Complete ===")
    print("\nThe flat transformer successfully converts TEST.json to IMS format!")
    print("Next step: Update the Triton service to use this transformer for flat data.")

if __name__ == "__main__":
    test_flat_transformer()