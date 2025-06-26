#!/usr/bin/env python3
"""
Analyze TEST.json payload and show what changes are needed
"""

import json
from datetime import datetime

def analyze_test_payload():
    """Analyze the TEST.json file and show required changes"""
    
    print("=== TEST.json Payload Analysis ===\n")
    
    # Load the TEST.json file
    with open("TEST.json", 'r') as f:
        data = json.load(f)
    
    print("Current Payload Structure:")
    print("-" * 50)
    print(f"Transaction ID: {data.get('transaction_id')}")
    print(f"Policy Number: {data.get('policy_number')}")
    print(f"Insured Name: {data.get('insured_name')}")
    print(f"Transaction Type: {data.get('transaction_type')}")
    print(f"Source System: {data.get('source_system')}")
    
    print("\n\nIssues with Current Payload:")
    print("-" * 50)
    
    # Issue 1: Flat structure
    print("\n1. STRUCTURE ISSUE:")
    print("   Current: Flat JSON structure")
    print("   Required: Nested objects for account, producer, premium, exposures")
    
    # Issue 2: Missing required fields
    print("\n2. MISSING REQUIRED FIELDS:")
    print("   - account.street_1 (insured street address)")
    print("   - account.city (insured city)")
    print("   - program object with ID and name")
    print("   - exposures array (can be empty but must exist)")
    
    # Issue 3: Date format
    print("\n3. DATE FORMAT ISSUES:")
    print(f"   Current effective_date: {data.get('effective_date')} (MM/DD/YYYY)")
    print("   Required: YYYY-MM-DD or ISO format")
    
    # Issue 4: Empty values
    print("\n4. EMPTY STRING VALUES:")
    empty_fields = [k for k, v in data.items() if v == ""]
    if empty_fields:
        print(f"   Fields with empty strings: {', '.join(empty_fields)}")
        print("   These should be null or have default values")
    
    print("\n\nRequired Transformation:")
    print("-" * 50)
    
    # Show the transformation
    print("\nFROM (current flat structure):")
    print(json.dumps({
        "insured_name": data.get("insured_name"),
        "insured_state": data.get("insured_state"),
        "insured_zip": data.get("insured_zip"),
        "producer_name": data.get("producer_name"),
        "gross_premium": data.get("gross_premium")
    }, indent=2))
    
    print("\nTO (required Triton structure):")
    
    # Convert dates
    eff_date = data.get('effective_date', '')
    if '/' in eff_date:
        parts = eff_date.split('/')
        eff_date = f"{parts[2]}-{parts[0]:0>2}-{parts[1]:0>2}"
    
    exp_date = data.get('expiration_date', '')
    if '/' in exp_date:
        parts = exp_date.split('/')
        exp_date = f"{parts[2]}-{parts[0]:0>2}-{parts[1]:0>2}"
    
    transformed = {
        "transaction_type": "binding",
        "transaction_id": data.get('transaction_id'),
        "transaction_date": data.get('transaction_date'),
        "policy_number": data.get('policy_number'),
        "effective_date": eff_date,
        "expiration_date": exp_date,
        "is_renewal": data.get('business_type', '').lower() == 'renewal',
        "account": {
            "name": data.get('insured_name'),
            "street_1": "REQUIRED - Not provided",
            "city": "REQUIRED - Not provided",
            "state": data.get('insured_state'),
            "zip": data.get('insured_zip')
        },
        "producer": {
            "name": data.get('producer_name')
        },
        "program": {
            "name": data.get('program_name', 'REQUIRED'),
            "id": "REQUIRED - Not provided"
        },
        "premium": {
            "annual_premium": data.get('gross_premium'),
            "policy_fee": data.get('policy_fee'),
            "commission_rate": data.get('commission_rate')
        },
        "exposures": []
    }
    
    print(json.dumps(transformed, indent=2))
    
    # Save the transformed version
    with open("TEST_transformed.json", 'w') as f:
        json.dump(transformed, f, indent=2)
    
    print("\n\nSummary:")
    print("-" * 50)
    print("✗ The TEST.json payload will NOT work as-is")
    print("✓ A transformation is required to convert to Triton format")
    print("✓ Saved transformed version to TEST_transformed.json")
    print("\nNext steps:")
    print("1. Add missing required fields (address, city, program ID)")
    print("2. Use the transformation script to convert payloads")
    print("3. Test with the /api/triton/transaction/new endpoint")

if __name__ == "__main__":
    analyze_test_payload()