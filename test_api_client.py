#!/usr/bin/env python3
"""
Simple API client to test the Triton transaction endpoint
This avoids complex import issues by making direct HTTP requests
"""
import json
import sys
import argparse
from datetime import datetime
import urllib.request
import urllib.error

def send_transaction(payload, api_url="http://localhost:8000/api/triton/transaction/new"):
    """Send a transaction to the API endpoint"""
    print(f"\nSending transaction to: {api_url}")
    print(f"Transaction ID: {payload.get('transaction_id', 'N/A')}")
    print(f"Transaction Type: {payload.get('transaction_type', 'N/A')}")
    print(f"Opportunity ID: {payload.get('opportunity_id', 'N/A')}")
    
    try:
        # Convert payload to JSON
        data = json.dumps(payload).encode('utf-8')
        
        # Create request
        req = urllib.request.Request(
            api_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Send request
        print("\nSending request...")
        response = urllib.request.urlopen(req)
        
        # Read response
        result = json.loads(response.read().decode('utf-8'))
        
        print(f"\nResponse Status: {response.status}")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        
        if result.get('data'):
            print("\nResponse Data:")
            print(json.dumps(result['data'], indent=2))
            
        return result
        
    except urllib.error.HTTPError as e:
        print(f"\nHTTP Error {e.code}: {e.reason}")
        try:
            error_body = json.loads(e.read().decode('utf-8'))
            print(f"Error Details: {error_body}")
        except:
            print("Could not parse error response")
        return None
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        return None

def create_default_payload():
    """Create a default test payload"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return {
        "transaction_id": f"API_TEST_{timestamp}",
        "transaction_type": "bind",
        "transaction_date": datetime.now().strftime("%m/%d/%Y"),
        "source_system": "API_TEST",
        
        # Business info
        "opportunity_id": 999003,
        "opportunity_type": "new",
        "policy_number": f"TST999003",
        
        # Insured info
        "insured_name": "API Test Company LLC",
        "insured_state": "MI",
        "insured_zip": "48226",
        "address_1": "456 API Test Ave",
        "city": "Detroit",
        "state": "MI",
        "zip": "48226",
        
        # Policy info
        "effective_date": "01/01/2025",
        "expiration_date": "01/01/2026",
        "bound_date": datetime.now().strftime("%m/%d/%Y"),
        
        # Business details
        "class_of_business": "General Liability",
        "program_name": "Test Program",
        "business_type": "Technology",
        "status": "Active",
        
        # Personnel - Use a valid underwriter name
        "underwriter_name": "David Korff",
        "producer_name": "Mike Woodworth",
        
        # Financial info
        "gross_premium": 15000.00,
        "commission_rate": 15.0,
        "net_premium": 12750.00,
        "base_premium": 14000.00,
        "limit_amount": "1000000/2000000",
        "deductible_amount": "5000",
        
        # Additional fields
        "invoice_date": datetime.now().strftime("%m/%d/%Y"),
        "umr": "TEST/UMR/999003",
        "agreement_number": "TEST-API-001",
        "section_number": "001",
        "policy_fee": 250.00
    }

def main():
    parser = argparse.ArgumentParser(description='Test Triton API endpoint')
    parser.add_argument('--json', '-j', type=str, help='Path to JSON file containing test payload')
    parser.add_argument('--url', '-u', type=str, default="http://localhost:8000/api/triton/transaction/new",
                       help='API endpoint URL (default: http://localhost:8000/api/triton/transaction/new)')
    parser.add_argument('--type', '-t', type=str, choices=['bind', 'unbind', 'issue'], default='bind',
                       help='Transaction type (default: bind)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("Triton API Test Client")
    print("="*60)
    
    # Load or create payload
    if args.json:
        print(f"\nLoading payload from: {args.json}")
        try:
            with open(args.json, 'r') as f:
                payload = json.load(f)
            print("✓ Successfully loaded JSON payload")
            
            # Ensure transaction_id is unique if not specified
            if not payload.get('transaction_id'):
                payload['transaction_id'] = f"API_TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                print(f"Generated transaction_id: {payload['transaction_id']}")
                
        except FileNotFoundError:
            print(f"✗ Error: File '{args.json}' not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"✗ Error: Invalid JSON in file: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"✗ Error loading file: {e}")
            sys.exit(1)
    else:
        print("\nUsing default test payload")
        payload = create_default_payload()
        payload['transaction_type'] = args.type
    
    # Send transaction
    result = send_transaction(payload, args.url)
    
    print("\n" + "="*60)
    if result and result.get('success'):
        print("✓ TEST PASSED")
    else:
        print("✗ TEST FAILED")
    print("="*60)
    
    return 0 if result and result.get('success') else 1

if __name__ == "__main__":
    sys.exit(main())