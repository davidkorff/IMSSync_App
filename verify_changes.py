#!/usr/bin/env python3
"""
Simple verification script to check the code changes
"""

import os
import re

def verify_business_type_change():
    """Verify the business type always returns 9"""
    print("\n=== Verifying Business Type Change ===")
    
    file_path = "app/integrations/triton/flat_transformer.py"
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Look for the _get_business_type_id method
    method_pattern = r'def _get_business_type_id\(self, business_type: str\) -> int:(.*?)(?=\n    def|\Z)'
    match = re.search(method_pattern, content, re.DOTALL)
    
    if match:
        method_content = match.group(1)
        if "return 9  # LLC - Partnership" in method_content:
            print("✓ _get_business_type_id() correctly returns 9 (LLC - Partnership)")
            print("  Found: 'return 9  # LLC - Partnership'")
            return True
        else:
            print("✗ _get_business_type_id() does not return 9")
            return False
    else:
        print("✗ Could not find _get_business_type_id method")
        return False

def verify_producer_search_method():
    """Verify the producer_search method exists"""
    print("\n=== Verifying Producer Search Method ===")
    
    file_path = "app/services/ims_soap_client.py"
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Look for the producer_search method
    if "def producer_search(self" in content:
        print("✓ producer_search() method exists in IMSSoapClient")
        
        # Check method signature
        pattern = r'def producer_search\(self([^)]*)\):'
        match = re.search(pattern, content)
        if match:
            print(f"  Method signature: producer_search(self{match.group(1)})")
        
        # Check if it uses ProducerSearch SOAP call
        if '<ProducerSearch xmlns=' in content:
            print("✓ Uses ProducerSearch SOAP call")
        
        return True
    else:
        print("✗ producer_search() method not found")
        return False

def verify_workflow_integration():
    """Verify the workflow uses the new producer search chain"""
    print("\n=== Verifying Workflow Integration ===")
    
    file_path = "app/services/ims_workflow_service.py"
    with open(file_path, 'r') as f:
        content = f.read()
    
    checks_passed = True
    
    # Check that old method is removed
    if "_lookup_producer_by_name" not in content:
        print("✓ Old _lookup_producer_by_name method has been removed")
    else:
        print("✗ Old _lookup_producer_by_name method still exists")
        checks_passed = False
    
    # Check that new producer search is used
    if "self.soap_client.producer_search(" in content:
        print("✓ Workflow uses new producer_search method")
    else:
        print("✗ Workflow does not use producer_search method")
        checks_passed = False
    
    # Check that location code lookup is used
    if "get_producer_contact_by_location_code(" in content:
        print("✓ Workflow uses get_producer_contact_by_location_code method")
    else:
        print("✗ Workflow does not use get_producer_contact_by_location_code method")
        checks_passed = False
    
    # Check the producer search chain comment
    if "Use the new producer search chain" in content:
        print("✓ Producer search chain implementation found")
    else:
        print("✗ Producer search chain implementation not found")
        checks_passed = False
    
    return checks_passed

def show_key_changes():
    """Show the key code changes"""
    print("\n=== Key Code Changes ===")
    
    print("\n1. Business Type Override (flat_transformer.py):")
    print("   - _get_business_type_id() now ALWAYS returns 9 (LLC - Partnership)")
    print("   - This is a temporary fix for testing")
    
    print("\n2. Producer Search Method (ims_soap_client.py):")
    print("   - Added producer_search(producer_name, city, state, zip_code)")
    print("   - Implements ProducerSearch SOAP call")
    print("   - Returns list of matching producers with location codes")
    
    print("\n3. Workflow Integration (ims_workflow_service.py):")
    print("   - Uses ProducerSearch → get LocationCode → GetProducerContactByLocationCode")
    print("   - Removed old _lookup_producer_by_name method")
    print("   - Producer search chain in _extract_submission_data()")

if __name__ == "__main__":
    print("Verifying IMS Integration Changes")
    print("=" * 50)
    
    all_passed = True
    
    if not verify_business_type_change():
        all_passed = False
        
    if not verify_producer_search_method():
        all_passed = False
        
    if not verify_workflow_integration():
        all_passed = False
    
    show_key_changes()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All changes verified successfully!")
        print("\nThe IMS integration is ready for testing with:")
        print("  - Business type always returns 9 (LLC - Partnership)")
        print("  - Producer search chain implemented")
    else:
        print("✗ Some verifications failed. Please check the implementation.")