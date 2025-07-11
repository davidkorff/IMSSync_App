#!/usr/bin/env python3
"""
Test script for Triton integration
This script tests the complete NEW BUSINESS flow with the actual IMS integration.

Usage:
    python test_triton_integration.py <json_file>
    python test_triton_integration.py TEST.json
    python test_triton_integration.py sample_data/another_test.json
"""

import json
import requests
import sys
import os
from datetime import datetime
import time
import argparse


def test_triton_new_business(json_file_path):
    """Test the Triton endpoint with provided JSON data"""
    
    # Configuration - adjust these for your environment
    BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    ENDPOINT = "/api/triton/transaction/new"
    API_KEY = os.getenv("API_KEY", "test-api-key")
    
    # Load JSON file
    print("=" * 60)
    print("TRITON INTEGRATION TEST")
    print("=" * 60)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Environment: {BASE_URL}")
    print(f"Test File: {json_file_path}")
    
    print(f"\n1. Loading {json_file_path}...")
    try:
        with open(json_file_path, 'r') as f:
            test_data = json.load(f)
        print(f"   ✓ {json_file_path} loaded successfully")
    except FileNotFoundError:
        print(f"   ✗ ERROR: File '{json_file_path}' not found")
        print(f"   Current directory: {os.getcwd()}")
        return False
    except json.JSONDecodeError as e:
        print(f"   ✗ ERROR: Invalid JSON in {json_file_path} - {e}")
        return False
    except Exception as e:
        print(f"   ✗ ERROR: Could not read file - {e}")
        return False
    
    # Determine transaction type
    transaction_type = test_data.get('transaction_type', 'Unknown')
    
    # Display test data
    print("\n2. Test Data Summary:")
    print(f"   - Transaction Type: {transaction_type}")
    print(f"   - Policy Number: {test_data.get('policy_number')}")
    print(f"   - Insured: {test_data.get('insured_name')}")
    print(f"   - State: {test_data.get('insured_state')}")
    
    # Display relevant fields based on transaction type
    if transaction_type.upper() in ['NEW BUSINESS', 'BINDING']:
        print(f"   - Address: {test_data.get('address_1')}, {test_data.get('city')}, {test_data.get('state')} {test_data.get('zip')}")
        print(f"   - Premium: ${test_data.get('gross_premium', test_data.get('premium', 0))}")
        print(f"   - Policy Fee: ${test_data.get('policy_fee', 0)}")
        print(f"   - Effective Date: {test_data.get('effective_date')}")
        print(f"   - Expiration Date: {test_data.get('expiration_date')}")
    elif transaction_type.upper() in ['CANCEL', 'CANCELLATION']:
        print(f"   - Cancellation Date: {test_data.get('cancellation_date')}")
        print(f"   - Cancellation Reason: {test_data.get('cancellation_reason_id')}")
        print(f"   - Flat Cancel: {test_data.get('flat_cancel', False)}")
    elif transaction_type.upper() in ['ENDORSEMENT', 'MIDTERM_ENDORSEMENT']:
        print(f"   - Endorsement Date: {test_data.get('endorsement_date')}")
        print(f"   - Premium Change: ${test_data.get('premium_change', 0)}")
        print(f"   - Comments: {test_data.get('comment', 'N/A')}")
    elif transaction_type.upper() == 'REINSTATEMENT':
        print(f"   - Reinstatement Date: {test_data.get('reinstatement_date')}")
        print(f"   - Payment Received: ${test_data.get('payment_received', 0)}")
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    # Make request
    print(f"\n3. Sending request to {BASE_URL}{ENDPOINT}")
    print("   Headers:")
    print(f"   - Content-Type: application/json")
    print(f"   - X-API-Key: {'*' * len(API_KEY)}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}{ENDPOINT}",
            json=test_data,
            headers=headers,
            timeout=60  # 60 second timeout for IMS processing
        )
        
        elapsed_time = time.time() - start_time
        print(f"\n4. Response received in {elapsed_time:.2f} seconds")
        print(f"   Status Code: {response.status_code}")
        
        # Parse response
        try:
            response_data = response.json()
        except:
            response_data = {"raw": response.text}
        
        # Check if successful
        if response.status_code == 200:
            print("   ✓ SUCCESS!")
            
            # Display response data
            print("\n5. Response Data:")
            
            # Handle different response structures
            if 'success' in response_data and response_data['success']:
                # New structure with success flag
                print(f"   Transaction ID: {response_data.get('transaction_id', 'N/A')}")
                
                if 'ims_response' in response_data:
                    print("\n   IMS Response:")
                    ims = response_data['ims_response']
                    for key, value in ims.items():
                        print(f"     - {key}: {value}")
                
                if 'invoice_details' in response_data:
                    print("\n   Invoice Details:")
                    invoice = response_data['invoice_details']
                    for key, value in invoice.items():
                        print(f"     - {key}: {value}")
                
                if 'errors' in response_data and response_data['errors']:
                    print("\n   Errors:")
                    for error in response_data['errors']:
                        print(f"     - {error}")
                
                if 'warnings' in response_data and response_data['warnings']:
                    print("\n   Warnings:")
                    for warning in response_data['warnings']:
                        print(f"     - {warning}")
            
            elif 'data' in response_data:
                # Old structure with data wrapper
                data = response_data['data']
                
                # IMS Response
                if 'ims_response' in data:
                    print("\n   IMS Response:")
                    ims = data['ims_response']
                    for key, value in ims.items():
                        print(f"     - {key}: {value}")
                
                # Invoice Details
                if 'invoice_details' in data:
                    print("\n   Invoice Details:")
                    invoice = data['invoice_details']
                    for key, value in invoice.items():
                        print(f"     - {key}: {value}")
                
                # Warnings
                if 'warnings' in data and data['warnings']:
                    print("\n   Warnings:")
                    for warning in data['warnings']:
                        print(f"     - {warning}")
            
            else:
                # Unknown structure - just print it
                print(json.dumps(response_data, indent=2))
            
            # Success summary
            print("\n" + "=" * 60)
            print(f"TEST COMPLETED SUCCESSFULLY! ({transaction_type})")
            print("=" * 60)
            
            return True
                
        else:
            print("   ✗ FAILED!")
            print("\n5. Error Response:")
            
            if isinstance(response_data, dict):
                # Handle structured error
                if 'error' in response_data:
                    error = response_data['error']
                    if isinstance(error, dict):
                        print(f"   Stage: {error.get('stage', 'Unknown')}")
                        print(f"   Message: {error.get('message', 'No message')}")
                        if 'details' in error and error['details']:
                            print("   Details:")
                            for key, value in error['details'].items():
                                print(f"     - {key}: {value}")
                    else:
                        print(f"   Error: {error}")
                elif 'errors' in response_data:
                    print("   Errors:")
                    for err in response_data['errors']:
                        print(f"     - {err}")
                else:
                    print(json.dumps(response_data, indent=2))
            else:
                print(f"   Raw Response: {response_data}")
            
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n   ✗ ERROR: Request timed out after 60 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print(f"\n   ✗ ERROR: Could not connect to {BASE_URL}")
        print("   Please ensure the service is running and accessible")
        return False
    except Exception as e:
        print(f"\n   ✗ ERROR: {type(e).__name__}: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def main():
    """Main test runner"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Test Triton integration with a JSON file',
        epilog='Environment variables: API_BASE_URL (default: http://localhost:8000), API_KEY (default: test-api-key)'
    )
    parser.add_argument('json_file', 
                       help='Path to JSON test file (e.g., TEST.json, cancellation_test.json)')
    parser.add_argument('--url', 
                       help='Override API base URL (can also use API_BASE_URL env var)')
    parser.add_argument('--key', 
                       help='Override API key (can also use API_KEY env var)')
    
    args = parser.parse_args()
    
    # Override environment variables if command line args provided
    if args.url:
        os.environ['API_BASE_URL'] = args.url
    if args.key:
        os.environ['API_KEY'] = args.key
    
    # Show configuration
    print("Environment Configuration:")
    print(f"  API_BASE_URL: {os.getenv('API_BASE_URL', 'http://localhost:8000')}")
    print(f"  API_KEY: {'Set' if os.getenv('API_KEY') else 'Not set (using default)'}")
    
    # Run the test
    success = test_triton_new_business(args.json_file)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()