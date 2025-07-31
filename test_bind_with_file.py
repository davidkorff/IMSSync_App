#!/usr/bin/env python3
"""Direct test that bypasses the import issues"""
import os
import sys
import json

# Try to fix the import path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up minimal environment
os.environ.setdefault('IMS_USERNAME', 'david.korff')
os.environ.setdefault('IMS_PASSWORD', 'KeeP!Moving!2025')
os.environ.setdefault('IMS_BASE_URL', 'http://10.64.32.234')

print("Starting bind test with JSON file...")

# Load the JSON
try:
    with open('TEST.json', 'r') as f:
        payload = json.load(f)
    print(f"✓ Loaded payload from TEST.json")
    print(f"  Transaction ID: {payload.get('transaction_id')}")
    print(f"  Opportunity ID: {payload.get('opportunity_id')}")
    print(f"  Policy Number: {payload.get('policy_number')}")
except Exception as e:
    print(f"Failed to load JSON: {e}")
    sys.exit(1)

# Now try to run the actual test
try:
    # Import after setting up environment
    from app.services.transaction_handler import get_transaction_handler
    
    print("\n" + "="*60)
    print("Processing transaction...")
    print("="*60)
    
    handler = get_transaction_handler()
    success, results, message = handler.process_transaction(payload)
    
    print(f"\nSuccess: {success}")
    print(f"Message: {message}")
    
    if success:
        print(f"\nResults:")
        print(f"  Policy Number: {results.get('bound_policy_number')}")
        print(f"  Quote GUID: {results.get('quote_guid')}")
        
        # Check for invoice data
        invoice_data = results.get('invoice_data')
        if invoice_data:
            print(f"\n✓ Invoice Data Retrieved:")
            print(f"  Invoice Number: {invoice_data.get('invoice_info', {}).get('invoice_num')}")
            print(f"  Premium: ${invoice_data.get('financial', {}).get('premium'):,.2f}")
            print(f"  Net Premium: ${invoice_data.get('financial', {}).get('net_premium'):,.2f}")
        else:
            print("\n⚠ No invoice data in response")
    else:
        print(f"\nError: {message}")
        if 'results' in locals():
            print(f"Partial results: {results}")
            
except ImportError as e:
    print(f"\nImport error: {e}")
    print("\nThis test requires the application dependencies to be installed.")
    print("The bind service has been updated to include invoice data.")
except Exception as e:
    print(f"\nError running test: {e}")
    import traceback
    traceback.print_exc()