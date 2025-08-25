#!/usr/bin/env python3
"""
Simple test to demonstrate Line GUID selection logic.
"""

def determine_line_guid(payload):
    """
    Determine the appropriate Line GUID based on payload data.
    """
    # Get potential determining fields
    class_of_business = payload.get("class_of_business", "").lower()
    program_name = payload.get("program_name", "").lower()
    
    # Line GUIDs
    primary_line_guid = "07564291-CBFE-4BBE-88D1-0548C88ACED4"
    excess_line_guid = "08798559-321C-4FC0-98ED-A61B92215F31"
    
    # Check for excess indicators in program name
    if "excess" in program_name or "umbrella" in program_name:
        print(f"  → Selected Excess Line based on program_name: {program_name}")
        return excess_line_guid
    
    # Check for excess indicators in class of business
    if "excess" in class_of_business or "umbrella" in class_of_business:
        print(f"  → Selected Excess Line based on class_of_business: {class_of_business}")
        return excess_line_guid
    
    # Default to primary line
    print(f"  → Selected Primary Line (default)")
    return primary_line_guid

def get_program_id(market_segment_code, line_guid):
    """
    Get ProgramID based on market segment and line GUID.
    """
    primary_line_guid = "07564291-CBFE-4BBE-88D1-0548C88ACED4"
    excess_line_guid = "08798559-321C-4FC0-98ED-A61B92215F31"
    
    if line_guid == primary_line_guid:
        if market_segment_code == 'RT':
            return 11615
        else:  # WL
            return 11613
    else:  # Excess line
        if market_segment_code == 'RT':
            return 11612
        else:  # WL
            return 11614

def main():
    """Test the Line GUID determination logic."""
    
    test_cases = [
        {
            "description": "Home Health - Primary line expected",
            "payload": {
                "class_of_business": "Home Health and Hospice Services",
                "program_name": "Everest AH Small Business",
                "market_segment_code": "WL"
            }
        },
        {
            "description": "Excess Program - Excess line expected",
            "payload": {
                "class_of_business": "General Liability",
                "program_name": "Excess Liability Program",
                "market_segment_code": "RT"
            }
        },
        {
            "description": "Umbrella Coverage - Excess line expected",
            "payload": {
                "class_of_business": "Umbrella Coverage",
                "program_name": "Standard Program",
                "market_segment_code": "WL"
            }
        },
        {
            "description": "Professional Liability - Primary line expected",
            "payload": {
                "class_of_business": "Professional Liability",
                "program_name": "Standard Professional",
                "market_segment_code": "RT"
            }
        }
    ]
    
    print("\n" + "="*80)
    print("Line GUID Determination and ProgramID Mapping Test")
    print("="*80)
    
    print("\nProgramID Mapping Rules:")
    print("  RT + Primary Line → ProgramID = 11615")
    print("  WL + Primary Line → ProgramID = 11613")
    print("  RT + Excess Line  → ProgramID = 11612")
    print("  WL + Excess Line  → ProgramID = 11614")
    
    print("\n" + "-"*80)
    print("Test Cases:")
    print("-"*80)
    
    for test_case in test_cases:
        print(f"\n{test_case['description']}")
        payload = test_case['payload']
        print(f"  Input: class_of_business='{payload['class_of_business']}'")
        print(f"         program_name='{payload['program_name']}'")
        print(f"         market_segment_code='{payload['market_segment_code']}'")
        
        # Determine Line GUID
        line_guid = determine_line_guid(payload)
        
        # Determine ProgramID
        program_id = get_program_id(payload['market_segment_code'], line_guid)
        
        # Display results
        line_type = "Primary" if line_guid == "07564291-CBFE-4BBE-88D1-0548C88ACED4" else "Excess"
        print(f"  Result: {line_type} Line → ProgramID = {program_id}")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("""
The logic now works as follows:
1. When a quote is created, the Line GUID is determined based on:
   - Program name containing 'excess' or 'umbrella' → Excess Line
   - Class of business containing 'excess' or 'umbrella' → Excess Line
   - Otherwise → Primary Line

2. When the quote is processed (during bind), the stored procedure sets ProgramID:
   - Reads market_segment_code from payload
   - Gets CompanyLineGuid from tblQuotes (set during quote creation)
   - Sets ProgramID in tblQuoteDetails based on the combination

This ensures the correct ProgramID is set BEFORE binding, based on both:
- The type of coverage (determining Line GUID)
- The market segment (RT/WL)
""")

if __name__ == "__main__":
    main()