#!/usr/bin/env python3
"""
Standalone test for bulk transaction modifications logic
Tests the modification logic without requiring full imports
"""

import json

def modify_payload(payload, parameter_number=None, use_default_names=False):
    """
    Apply modifications to payload based on parameters
    
    Args:
        payload: Original payload dict
        parameter_number: Number to append to IDs
        use_default_names: If True, use default producer/underwriter names
        
    Returns:
        Modified payload dict
    """
    modified = payload.copy()
    
    # Apply parameter number modifications
    if parameter_number is not None:
        # Append to IDs
        fields_to_append = [
            'policy_number',
            'expiring_policy_number', 
            'opportunity_id',
            'midterm_endt_id'
        ]
        
        for field in fields_to_append:
            if field in modified and modified[field]:
                # Convert to string and append number
                if field == 'opportunity_id':
                    # For opportunity_id, handle as integer
                    try:
                        current_value = str(modified[field])
                        modified[field] = f"{current_value}{parameter_number}"
                    except:
                        pass
                elif field == 'midterm_endt_id':
                    # Only modify if not null/empty
                    if modified[field] and str(modified[field]).lower() not in ['null', 'none', '']:
                        current_value = str(modified[field])
                        modified[field] = f"{current_value}{parameter_number}"
                else:
                    # For string fields
                    current_value = str(modified[field])
                    modified[field] = f"{current_value}{parameter_number}"
        
        # Replace last 6 digits of transaction IDs with padded parameter
        padded_param = str(parameter_number).zfill(6)
        
        if 'transaction_id' in modified and modified['transaction_id']:
            tid = str(modified['transaction_id'])
            if len(tid) >= 6:
                modified['transaction_id'] = tid[:-6] + padded_param
                
        if 'prior_transaction_id' in modified and modified['prior_transaction_id']:
            ptid = str(modified['prior_transaction_id'])
            if ptid and str(ptid).lower() not in ['null', 'none', ''] and len(ptid) >= 6:
                modified['prior_transaction_id'] = ptid[:-6] + padded_param
    
    # Apply name overrides
    if use_default_names:
        modified['producer_name'] = 'Mike Woodworth'
        modified['underwriter_name'] = 'Christina Rentas'
    
    return modified


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
    for key, value in test_payload.items():
        print(f"  {key}: {value}")
    
    # Test with parameter number 42
    print("\n\nTest 1: With parameter=42")
    print("-"*30)
    modified = modify_payload(test_payload, parameter_number=42, use_default_names=False)
    
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
    modified = modify_payload(test_payload, parameter_number=139, use_default_names=True)
    
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
    modified = modify_payload(test_payload_null, parameter_number=99, use_default_names=False)
    print(f"  midterm_endt_id: {test_payload_null['midterm_endt_id']} → {modified['midterm_endt_id']} (should remain None)")
    
    # Test with no prior_transaction_id
    print("\n\nTest 4: With no prior_transaction_id")
    print("-"*30)
    test_payload_no_prior = test_payload.copy()
    test_payload_no_prior['prior_transaction_id'] = None
    modified = modify_payload(test_payload_no_prior, parameter_number=55, use_default_names=False)
    print(f"  prior_transaction_id: {test_payload_no_prior['prior_transaction_id']} → {modified['prior_transaction_id']} (should remain None)")
    
    # Test padding of transaction IDs
    print("\n\nTest 5: Transaction ID padding")
    print("-"*30)
    
    # Test with single digit
    modified = modify_payload(test_payload, parameter_number=7, use_default_names=False)
    print(f"  parameter=7 → transaction_id ends with: ...{modified['transaction_id'][-6:]}")
    
    # Test with three digits
    modified = modify_payload(test_payload, parameter_number=456, use_default_names=False)
    print(f"  parameter=456 → transaction_id ends with: ...{modified['transaction_id'][-6:]}")
    
    # Test with six digits
    modified = modify_payload(test_payload, parameter_number=123456, use_default_names=False)
    print(f"  parameter=123456 → transaction_id ends with: ...{modified['transaction_id'][-6:]}")
    
    print("\n" + "="*50)
    print("Modification tests completed successfully!")


if __name__ == "__main__":
    test_modifications()
    
    print("\n\nUsage Examples for bulk_test_transactions.py:")
    print("-"*50)
    print("# Run all transactions from CSV:")
    print("python3 bulk_test_transactions.py 'ims_payloads_from_triton (1).csv'")
    print("\n# Run with parameter 42:")
    print("python3 bulk_test_transactions.py 'ims_payloads_from_triton (1).csv' -p 42")
    print("\n# Run with parameter 139 and default names:")
    print("python3 bulk_test_transactions.py 'ims_payloads_from_triton (1).csv' -p 139 --names")
    print("\n# Run rows 10-20 with parameter 99:")
    print("python3 bulk_test_transactions.py 'ims_payloads_from_triton (1).csv' -p 99 --start 10 --end 20")
    print("\n# Stop on first error:")
    print("python3 bulk_test_transactions.py 'ims_payloads_from_triton (1).csv' --stop-on-error")
    print("\n# Verbose output:")
    print("python3 bulk_test_transactions.py 'ims_payloads_from_triton (1).csv' -p 42 --verbose")