#!/usr/bin/env python3
"""Simple test to check JSON loading without dependencies"""
import json
import sys

print("Python version:", sys.version)
print("Script starting...")

# Test 1: Basic JSON loading
try:
    with open('test.json', 'r') as f:
        data = json.load(f)
    print("✓ JSON loaded successfully")
    print(f"  Number of keys: {len(data)}")
except Exception as e:
    print(f"✗ Failed to load JSON: {e}")
    sys.exit(1)

# Test 2: Check for empty values that might cause issues
print("\nChecking for potential issues:")
for key, value in data.items():
    if value is None:
        print(f"  - {key}: null")
    elif value == "":
        print(f"  - {key}: empty string")
    elif isinstance(value, list) and len(value) == 0:
        print(f"  - {key}: empty list")

# Test 3: Verify it's a valid bind payload
required_for_bind = [
    'transaction_id', 'transaction_type', 'opportunity_id', 
    'policy_number', 'insured_name', 'underwriter_name', 
    'producer_name'
]

print("\nChecking required fields for bind:")
missing = []
for field in required_for_bind:
    if field in data:
        print(f"  ✓ {field}: {data[field]}")
    else:
        print(f"  ✗ Missing: {field}")
        missing.append(field)

if missing:
    print(f"\nMissing {len(missing)} required field(s)")
else:
    print("\n✓ All required fields present")
    
# Test 4: Check data types
print("\nChecking data types:")
if 'opportunity_id' in data:
    print(f"  opportunity_id type: {type(data['opportunity_id'])}")
if 'gross_premium' in data:
    print(f"  gross_premium type: {type(data['gross_premium'])}")
    
print("\nTest complete!")