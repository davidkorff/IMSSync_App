#!/usr/bin/env python3
"""
Test script to verify Line GUID selection logic and ProgramID setting.
"""

import logging
from app.services.ims.quote_service import get_quote_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_line_guid_determination():
    """Test the Line GUID determination logic."""
    quote_service = get_quote_service()
    
    test_cases = [
        {
            "description": "Primary line - Home Health",
            "payload": {
                "class_of_business": "Home Health and Hospice Services",
                "program_name": "Everest AH Small Business",
                "market_segment_code": "WL"
            },
            "expected_line": "primary"
        },
        {
            "description": "Excess line - Excess program",
            "payload": {
                "class_of_business": "General Liability",
                "program_name": "Excess Liability Program",
                "market_segment_code": "RT"
            },
            "expected_line": "excess"
        },
        {
            "description": "Excess line - Umbrella class",
            "payload": {
                "class_of_business": "Umbrella Coverage",
                "program_name": "Standard Program",
                "market_segment_code": "WL"
            },
            "expected_line": "excess"
        },
        {
            "description": "Primary line - Default case",
            "payload": {
                "class_of_business": "Professional Liability",
                "program_name": "Standard Professional",
                "market_segment_code": "RT"
            },
            "expected_line": "primary"
        }
    ]
    
    print("\n" + "="*80)
    print("Testing Line GUID Determination Logic")
    print("="*80)
    
    import os
    primary_line_guid = os.getenv("TRITON_PRIMARY_LINE_GUID", "07564291-CBFE-4BBE-88D1-0548C88ACED4")
    excess_line_guid = os.getenv("TRITON_EXCESS_LINE_GUID", "08798559-321C-4FC0-98ED-A61B92215F31")
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['description']}")
        print(f"  Payload: class_of_business='{test_case['payload']['class_of_business']}'")
        print(f"           program_name='{test_case['payload']['program_name']}'")
        print(f"           market_segment_code='{test_case['payload']['market_segment_code']}'")
        
        # Call the method
        line_guid = quote_service._determine_line_guid(test_case['payload'])
        
        # Check result
        if test_case['expected_line'] == 'primary':
            expected_guid = primary_line_guid
            line_type = "Primary"
        else:
            expected_guid = excess_line_guid
            line_type = "Excess"
        
        if line_guid == expected_guid:
            print(f"  ✓ Result: {line_type} Line GUID ({line_guid})")
        else:
            print(f"  ✗ Result: Unexpected GUID ({line_guid})")
            print(f"    Expected: {expected_guid}")
    
    # Show ProgramID mapping
    print("\n" + "="*80)
    print("ProgramID Mapping (from stored procedure logic)")
    print("="*80)
    print("\nMarket Segment + Line GUID → ProgramID:")
    print("  RT + Primary Line (07564291-...) → ProgramID = 11615")
    print("  WL + Primary Line (07564291-...) → ProgramID = 11613")
    print("  RT + Excess Line  (08798559-...) → ProgramID = 11612")
    print("  WL + Excess Line  (08798559-...) → ProgramID = 11614")
    
    print("\nExamples based on test cases:")
    for test_case in test_cases:
        market_segment = test_case['payload']['market_segment_code']
        line_guid = quote_service._determine_line_guid(test_case['payload'])
        
        if line_guid == primary_line_guid:
            if market_segment == 'RT':
                program_id = 11615
            else:  # WL
                program_id = 11613
        else:  # Excess line
            if market_segment == 'RT':
                program_id = 11612
            else:  # WL
                program_id = 11614
        
        print(f"  {test_case['description'][:30]:30s} → ProgramID = {program_id}")

if __name__ == "__main__":
    test_line_guid_determination()