#!/usr/bin/env python3
"""
Simple test that demonstrates the complete Triton workflow.
Loads TEST.json and processes it through the entire system.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Try to import dotenv, mock if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Mock the dotenv module if not installed
    class MockDotenv:
        def load_dotenv(self):
            pass
    sys.modules['dotenv'] = MockDotenv()

# Import the transaction handler
from app.services.transaction_handler import get_transaction_handler


def main():
    """Process JSON file through the complete workflow."""
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python3 test_triton_workflow.py <json_file>")
        print("Example: python3 test_triton_workflow.py TEST.json")
        return 1
    
    json_file = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(json_file):
        print(f"Error: File '{json_file}' not found")
        return 1
    
    print("\nTriton Transaction Workflow Test")
    print("================================")
    print(f"Testing with payload file: {json_file}")
    print("This simulates Triton sending the payload to /api/triton/transaction/new")
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please ensure .env file exists with:")
        print("  IMS_ONE_USERNAME=your_username")
        print("  IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Load JSON file
    try:
        with open(json_file, 'r') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"\nFailed to load {json_file}: {e}")
        return 1
    
    print(f"\nProcessing transaction:")
    print(f"  ID: {payload.get('transaction_id')}")
    print(f"  Type: {payload.get('transaction_type')}")
    print(f"  Insured: {payload.get('insured_name')}")
    print(f"  Premium: ${payload.get('net_premium', 0):,.2f}")
    
    # Process the transaction
    print("\nProcessing...")
    handler = get_transaction_handler()
    success, results, message = handler.process_transaction(payload)
    
    # Display results
    print(f"\n{'='*60}")
    print("Results:")
    print(f"{'='*60}")
    print(f"Success: {success}")
    print(f"Message: {message}")
    
    if success and results:
        print(f"\nCreated Resources:")
        print(f"  Insured GUID: {results.get('insured_guid')}")
        print(f"  Quote GUID: {results.get('quote_guid')}")
        print(f"  Quote Option GUID: {results.get('quote_option_guid')}")
        
        if results.get('bound_policy_number'):
            print(f"  Policy Number: {results.get('bound_policy_number')}")
        if results.get('issue_date'):
            print(f"  Issue Date: {results.get('issue_date')}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())