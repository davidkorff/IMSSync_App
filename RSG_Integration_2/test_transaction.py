#!/usr/bin/env python3
"""
Test script for RSG Integration Service
Usage: python test_transaction.py [json_file]
Default: TEST.json
"""

import sys
import json
import os
import requests
from datetime import datetime
from pathlib import Path

def load_test_data(filename="TEST.json"):
    """Load test data from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{filename}': {e}")
        sys.exit(1)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_json(data, indent=2):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=indent, default=str))

def test_transaction(base_url="http://localhost:8000", json_file="TEST.json"):
    """Test transaction processing"""
    
    # Load test data
    print_section(f"Loading test data from: {json_file}")
    test_data = load_test_data(json_file)
    
    # Display transaction details
    print(f"Transaction Type: {test_data.get('transaction_type')}")
    print(f"Transaction ID: {test_data.get('transaction_id')}")
    print(f"Policy Number: {test_data.get('policy_number')}")
    print(f"Insured Name: {test_data.get('insured_name')}")
    
    # Test health endpoint first
    print_section("Testing Service Health")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status Code: {response.status_code}")
        print_json(response.json())
    except Exception as e:
        print(f"Error: Service not reachable at {base_url}")
        print(f"Details: {e}")
        sys.exit(1)
    
    # Send transaction
    print_section("Sending Transaction to Service")
    print(f"Endpoint: POST {base_url}/api/triton/transaction/new")
    print("\nRequest Payload:")
    print_json(test_data)
    
    try:
        start_time = datetime.now()
        response = requests.post(
            f"{base_url}/api/triton/transaction/new",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\nResponse Time: {duration:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        print("\nResponse Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        # Parse response
        print_section("Response Body")
        if response.status_code == 200:
            result = response.json()
            
            # Basic info
            print(f"Success: {result.get('success')}")
            print(f"Transaction ID: {result.get('transaction_id')}")
            print(f"Transaction Type: {result.get('transaction_type')}")
            
            # Service response
            if result.get('service_response'):
                print("\nService Response:")
                print_json(result['service_response'])
            
            # IMS responses
            if result.get('ims_responses'):
                print_section("IMS API Calls and Responses")
                for i, ims_response in enumerate(result['ims_responses'], 1):
                    print(f"\n{i}. Action: {ims_response.get('action')}")
                    print(f"   Result:")
                    print_json(ims_response.get('result', {}), indent=4)
            
            # Invoice details
            if result.get('invoice_details'):
                print_section("Invoice Details")
                print_json(result['invoice_details'])
            
            # Errors and warnings
            if result.get('errors'):
                print_section("Errors")
                for error in result['errors']:
                    print(f"  - {error}")
            
            if result.get('warnings'):
                print_section("Warnings")
                for warning in result['warnings']:
                    print(f"  - {warning}")
        
        else:
            # Error response
            print("ERROR Response:")
            try:
                error_data = response.json()
                print_json(error_data)
            except:
                print(response.text)
    
    except requests.exceptions.ConnectionError:
        print(f"\nError: Could not connect to service at {base_url}")
        print("Make sure the service is running (python main.py)")
    except Exception as e:
        print(f"\nUnexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def test_additional_endpoints(base_url="http://localhost:8000"):
    """Test additional IMS endpoints"""
    print_section("Testing Additional Endpoints")
    
    # Test insured search
    print("\n1. Testing Insured Search")
    params = {
        "name": "BLC Industries, LLC",
        "address": "2222 The Dells",
        "city": "Kalamazoo",
        "state": "MI",
        "zip_code": "49048"
    }
    
    try:
        response = requests.get(
            f"{base_url}/api/ims/insured/search",
            params=params
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    # Parse command line arguments
    json_file = "TEST.json"
    port = 8000
    
    # Simple argument parsing
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2  # Skip both --port and the port number
        elif not arg.startswith("--"):
            json_file = arg
            i += 1
        else:
            i += 1
    
    # Check if file exists
    if not Path(json_file).exists():
        print(f"Error: File '{json_file}' not found")
        print(f"\nUsage: python test_transaction.py [json_file] [--port PORT]")
        print(f"  json_file: JSON file with test data (default: TEST.json)")
        print(f"  --port: Service port (default: 8000)")
        print(f"\nExamples:")
        print(f"  python test_transaction.py")
        print(f"  python test_transaction.py TEST.json")
        print(f"  python test_transaction.py --port 8001")
        print(f"  python test_transaction.py TEST.json --port 8001")
        sys.exit(1)
    
    # Run tests
    print(f"RSG Integration Service Test")
    print(f"{'='*60}")
    print(f"Starting test at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using port: {port}")
    
    # Test with local service
    base_url = f"http://localhost:{port}"
    test_transaction(base_url, json_file)
    
    # Optionally test additional endpoints
    # test_additional_endpoints(base_url)
    
    print_section("Test Complete")