#!/usr/bin/env python3
"""
Debug script to show exactly what BusinessTypeID is being sent to IMS
"""

import json

# Load the TEST.json file
with open('TEST.json', 'r') as f:
    test_data = json.load(f)

print("TEST.json data:")
print(f"  business_type field: '{test_data.get('business_type')}'")
print(f"  insured_name: '{test_data.get('insured_name')}'")
print(f"  transaction_type: '{test_data.get('transaction_type')}'")

# Simulate the transformer logic
business_type = test_data.get('business_type', '').lower().strip()
print(f"\nTransformer logic:")
print(f"  Normalized business_type: '{business_type}'")

# Check if it's a transaction type
transaction_types = ['renewal', 'new business', 'endorsement', 'cancellation']
if business_type in transaction_types:
    print(f"  ⚠️  '{business_type}' is a transaction type, not a business entity type")
    print(f"  Will default to Corporation (BusinessTypeID = 1)")
else:
    print(f"  Business type '{business_type}' will be mapped accordingly")

print("\nThe error suggests BusinessTypeID 1 might not exist in your IMS_DEV database.")
print("You need to check what BusinessTypeIDs are valid in your IMS environment.")