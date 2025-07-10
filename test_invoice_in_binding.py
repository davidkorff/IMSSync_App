"""
Test invoice number retrieval during policy binding
This demonstrates that invoice numbers are now returned in the response
"""

import requests
import json
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-123"

def test_binding_with_invoice():
    """Test binding a new policy and receiving invoice number in response"""
    
    print("Testing Policy Binding with Invoice Retrieval")
    print("=" * 60)
    
    # Sample binding data from Triton
    binding_data = {
        "transaction_type": "binding",
        "policy_number": f"INV-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "effective_date": datetime.now().strftime("%Y-%m-%d"),
        "expiration_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
        "account": {
            "id": "ACC-INV-001",
            "name": "Invoice Test Company",
            "street_1": "789 Invoice Street",
            "city": "Test City",
            "state": "CA",
            "zip": "90001"
        },
        "producer": {
            "id": "PROD001",
            "name": "Test Producer"
        },
        "coverages": [{
            "type": "General Liability",
            "limit": 1000000,
            "deductible": 5000,
            "premium": 5000.00
        }],
        "premium": {
            "total": 5000.00,
            "term": "annual"
        }
    }
    
    # Send to Triton binding endpoint (synchronous mode)
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"\nSending binding request for policy: {binding_data['policy_number']}")
    print("Request will process synchronously and wait for IMS to complete...")
    
    response = requests.post(
        f"{BASE_URL}/api/sources/triton/transaction/new",
        json=binding_data,
        headers=headers,
        params={"sync_mode": "true"}  # Ensure synchronous processing
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse: {json.dumps(result, indent=2)}")
        
        # Check for invoice number
        if result.get('ims_details'):
            ims_details = result['ims_details']
            policy_number = ims_details.get('policy_number')
            invoice_number = ims_details.get('invoice_number')
            
            print("\n" + "=" * 60)
            print("RESULTS:")
            print(f"✓ Policy Number: {policy_number}")
            
            if invoice_number:
                print(f"✓ Invoice Number: {invoice_number}")
                print("\nSUCCESS: Invoice number was retrieved and included in the response!")
            else:
                print("⚠ Invoice Number: Not available")
                print("\nNOTE: Invoice may not be immediately available after binding.")
                print("IMS may generate invoices asynchronously.")
                
                # Demonstrate manual retrieval
                if policy_number:
                    print("\nAttempting manual invoice retrieval...")
                    invoice_response = requests.get(
                        f"{BASE_URL}/api/v1/invoice/policy/{policy_number}/latest",
                        headers=headers
                    )
                    
                    if invoice_response.status_code == 200:
                        invoice_data = invoice_response.json()
                        if invoice_data.get('invoice_number'):
                            print(f"✓ Invoice retrieved manually: {invoice_data['invoice_number']}")
                        else:
                            print("Invoice still not available")
    else:
        print(f"\nError: {response.text}")

def test_async_binding():
    """Test async binding - invoice won't be in initial response"""
    
    print("\n\nTesting Async Policy Binding")
    print("=" * 60)
    
    binding_data = {
        "transaction_type": "binding",
        "policy_number": f"ASYNC-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "effective_date": datetime.now().strftime("%Y-%m-%d"),
        "expiration_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
        "account": {
            "id": "ACC-ASYNC-001",
            "name": "Async Test Company",
            "street_1": "123 Async Avenue",
            "city": "Test City",
            "state": "CA",
            "zip": "90001"
        },
        "premium": {
            "total": 3000.00
        }
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"\nSending async binding request...")
    
    response = requests.post(
        f"{BASE_URL}/api/sources/triton/transaction/new",
        json=binding_data,
        headers=headers,
        params={"sync_mode": "false"}  # Async processing
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nAsync Response: {json.dumps(result, indent=2)}")
        print("\nNOTE: In async mode, the transaction is queued for processing.")
        print("Invoice details won't be available in the initial response.")
        print("Use the transaction ID to check status later.")
    else:
        print(f"\nError: {response.text}")

if __name__ == "__main__":
    print("Invoice Retrieval in Binding Response Test")
    print("=" * 60)
    print("This test demonstrates the new invoice retrieval feature:")
    print("- When a policy is bound in IMS, we attempt to retrieve the invoice")
    print("- The invoice number is included in the response to Triton")
    print("- If invoice isn't immediately available, it returns null")
    
    input("\nPress Enter to start the test...")
    
    # Run synchronous test
    test_binding_with_invoice()
    
    # Run async test for comparison
    test_async_binding()
    
    print("\n" + "=" * 60)
    print("Test completed!")