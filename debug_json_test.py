#!/usr/bin/env python3
"""Debug JSON loading issue"""
import json
import sys

try:
    with open('test.json', 'r') as f:
        payload = json.load(f)
    
    print("Successfully loaded JSON")
    print(f"Keys in payload: {list(payload.keys())}")
    
    # Check for required fields
    required_fields = ['transaction_id', 'opportunity_id', 'opportunity_type']
    for field in required_fields:
        if field in payload:
            print(f"✓ {field}: {payload[field]}")
        else:
            print(f"✗ Missing field: {field}")
            
except Exception as e:
    print(f"Error loading JSON: {str(e)}")
    import traceback
    traceback.print_exc()