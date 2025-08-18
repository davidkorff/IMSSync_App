#!/usr/bin/env python3
"""
Test script to debug invoice XML parsing issue
"""
import sys
import os
import logging
import json

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Set up debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.services.transaction_handler import get_transaction_handler

def test_invoice_extraction():
    """Test invoice extraction with enhanced debugging"""
    print("\n" + "="*60)
    print("INVOICE XML DEBUG TEST")
    print("="*60)
    
    # Load the test payload
    with open('TEST.json', 'r') as f:
        payload = json.load(f)
    
    print(f"\nProcessing transaction: {payload['transaction_id']}")
    print(f"Policy Number: {payload['policy_number']}")
    
    # Get handler and process
    handler = get_transaction_handler()
    success, results, message = handler.process_transaction(payload)
    
    print(f"\nTransaction result: {'SUCCESS' if success else 'FAILED'}")
    print(f"Message: {message}")
    
    # Check for invoice data
    if success and 'invoice_data' in results:
        print("\n✓ Invoice data successfully extracted!")
        print(f"Invoice data keys: {list(results['invoice_data'].keys())}")
    else:
        print("\n✗ No invoice data in results")
        
    # Check if debug XML was saved
    debug_dir = "debug_xml"
    if os.path.exists(debug_dir):
        xml_files = [f for f in os.listdir(debug_dir) if f.endswith('.xml')]
        if xml_files:
            print(f"\nDebug XML files saved: {xml_files}")
            latest_file = sorted(xml_files)[-1]
            print(f"Latest debug file: {os.path.join(debug_dir, latest_file)}")
    
    return success, results

if __name__ == "__main__":
    test_invoice_extraction()