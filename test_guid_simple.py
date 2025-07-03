#!/usr/bin/env python3
"""
Simple test to verify GUID configuration
"""

import re

def check_file_for_guids(filepath, description):
    """Check a file for GUID usage"""
    print(f"\n{description}:")
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find all GUIDs (pattern: 8-4-4-4-12 hex characters)
    guid_pattern = r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
    guids = re.findall(guid_pattern, content)
    
    # Find specific valid GUIDs we configured
    valid_guids = {
        "07564291-CBFE-4BBE-88D1-0548C88ACED4": "AHC Primary LineGUID",
        "C5C006BB-6437-42F3-95D4-C090ADD3B37D": "Quoting/Issuing Location",
        "DF35D4C7-C663-4974-A886-A1E18D3C9618": "Company Location"
    }
    
    # Check for all-zeros GUID
    all_zeros = "00000000-0000-0000-0000-000000000000"
    
    found_valid = False
    for guid in set(guids):
        if guid in valid_guids:
            print(f"  ✓ Found valid GUID: {guid} ({valid_guids[guid]})")
            found_valid = True
        elif guid == all_zeros:
            # Find context where it's used
            for line_num, line in enumerate(content.split('\n'), 1):
                if guid in line and 'default' in line.lower():
                    print(f"  ⚠ All-zeros GUID still used at line {line_num}")
                    print(f"    Context: {line.strip()[:80]}...")
    
    if not found_valid:
        print("  ✗ No valid GUIDs found!")
    
    return found_valid

def main():
    """Check all updated files"""
    print("="*60)
    print("Checking GUID Configuration Updates")
    print("="*60)
    
    files_to_check = [
        ("app/services/ims_workflow_service.py", "IMS Workflow Service"),
        ("app/integrations/triton/transformer.py", "Triton Transformer"),
        ("app/integrations/triton/flat_transformer.py", "Triton Flat Transformer")
    ]
    
    all_good = True
    for filepath, desc in files_to_check:
        if not check_file_for_guids(filepath, desc):
            all_good = False
    
    print("\n" + "="*60)
    if all_good:
        print("✓ All files have been updated with valid IMS GUIDs!")
    else:
        print("✗ Some files may still need updates")
    print("="*60)

if __name__ == "__main__":
    main()