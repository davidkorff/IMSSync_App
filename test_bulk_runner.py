#!/usr/bin/env python3
"""
Test runner for bulk transaction testing
Shows example usage and tests the modification logic
"""

import json
from bulk_test_transactions import BulkTransactionTester

def test_modifications():
    """Test the payload modification logic"""
    print("Testing Payload Modifications")
    print("="*50)
    
    # Create a test payload
    test_payload = {
        "transaction_id": "de493ca5-8be3-440d-a2e2-62fa1d191bac",
        "prior_transaction_id": "ca2e502d-97b6-49fb-a6bc-1026fcd659da",
        "opportunity_id": 67284,
        "policy_number": "GAH-67284-211101",
        "expiring_policy_number": "GAH-93395-240501",
        "midterm_endt_id": "ENDT-001",
        "producer_name": "Original Producer",
        "underwriter_name": "Original Underwriter"
    }
    
    print("\nOriginal Payload:")
    print(json.dumps(test_payload, indent=2))
    
    # Test with parameter number 42
    print("\n\nTest 1: With parameter=42")
    print("-"*30)
    tester = BulkTransactionTester("dummy.csv", parameter_number=42, use_default_names=False)
    modified = tester.modify_payload(test_payload)
    
    print("Modified fields:")
    print(f"  opportunity_id: {test_payload['opportunity_id']} → {modified['opportunity_id']}")
    print(f"  policy_number: {test_payload['policy_number']} → {modified['policy_number']}")
    print(f"  expiring_policy_number: {test_payload['expiring_policy_number']} → {modified['expiring_policy_number']}")
    print(f"  midterm_endt_id: {test_payload['midterm_endt_id']} → {modified['midterm_endt_id']}")
    print(f"  transaction_id: ...{test_payload['transaction_id'][-10:]} → ...{modified['transaction_id'][-10:]}")
    print(f"  prior_transaction_id: ...{test_payload['prior_transaction_id'][-10:]} → ...{modified['prior_transaction_id'][-10:]}")
    print(f"  producer_name: {modified['producer_name']}")
    print(f"  underwriter_name: {modified['underwriter_name']}")
    
    # Test with parameter number 139 and names
    print("\n\nTest 2: With parameter=139 and --names")
    print("-"*30)
    tester = BulkTransactionTester("dummy.csv", parameter_number=139, use_default_names=True)
    modified = tester.modify_payload(test_payload)
    
    print("Modified fields:")
    print(f"  opportunity_id: {test_payload['opportunity_id']} → {modified['opportunity_id']}")
    print(f"  policy_number: {test_payload['policy_number']} → {modified['policy_number']}")
    print(f"  transaction_id: ...{test_payload['transaction_id'][-10:]} → ...{modified['transaction_id'][-10:]}")
    print(f"  prior_transaction_id: ...{test_payload['prior_transaction_id'][-10:]} → ...{modified['prior_transaction_id'][-10:]}")
    print(f"  producer_name: {test_payload['producer_name']} → {modified['producer_name']}")
    print(f"  underwriter_name: {test_payload['underwriter_name']} → {modified['underwriter_name']}")
    
    # Test with null midterm_endt_id
    print("\n\nTest 3: With null midterm_endt_id")
    print("-"*30)
    test_payload_null = test_payload.copy()
    test_payload_null['midterm_endt_id'] = None
    tester = BulkTransactionTester("dummy.csv", parameter_number=99, use_default_names=False)
    modified = tester.modify_payload(test_payload_null)
    print(f"  midterm_endt_id: {test_payload_null['midterm_endt_id']} → {modified['midterm_endt_id']} (should remain None)")
    
    # Test with no prior_transaction_id
    print("\n\nTest 4: With no prior_transaction_id")
    print("-"*30)
    test_payload_no_prior = test_payload.copy()
    test_payload_no_prior['prior_transaction_id'] = None
    tester = BulkTransactionTester("dummy.csv", parameter_number=55, use_default_names=False)
    modified = tester.modify_payload(test_payload_no_prior)
    print(f"  prior_transaction_id: {test_payload_no_prior['prior_transaction_id']} → {modified['prior_transaction_id']} (should remain None)")
    
    print("\n" + "="*50)
    print("Modification tests completed!")

if __name__ == "__main__":
    test_modifications()
    
    print("\n\nUsage Examples:")
    print("-"*50)
    print("# Run all transactions from CSV:")
    print("python bulk_test_transactions.py 'ims_payloads_from_triton (1).csv'")
    print("\n# Run with parameter 42:")
    print("python bulk_test_transactions.py 'ims_payloads_from_triton (1).csv' -p 42")
    print("\n# Run with parameter 139 and default names:")
    print("python bulk_test_transactions.py 'ims_payloads_from_triton (1).csv' -p 139 --names")
    print("\n# Run rows 10-20 with parameter 99:")
    print("python bulk_test_transactions.py 'ims_payloads_from_triton (1).csv' -p 99 --start 10 --end 20")
    print("\n# Stop on first error:")
    print("python bulk_test_transactions.py 'ims_payloads_from_triton (1).csv' --stop-on-error")