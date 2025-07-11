#!/usr/bin/env python3
"""
Helper function to detect business entity type from insured name
"""

import re
from typing import Optional

def detect_business_type_from_name(insured_name: str) -> Optional[str]:
    """
    Detect business entity type from the insured name
    Returns the detected type or None if not found
    """
    if not insured_name:
        return None
    
    name_upper = insured_name.upper()
    
    # Check for common business entity suffixes
    # Order matters - check more specific ones first
    patterns = [
        (r'\bLLC\b|L\.L\.C\.|LIMITED LIABILITY COMPANY', 'LLC'),
        (r'\bLLP\b|L\.L\.P\.|LIMITED LIABILITY PARTNERSHIP', 'LLP'),
        (r'\bINC\b|INC\.|INCORPORATED|CORPORATION|CORP\b|CORP\.', 'CORPORATION'),
        (r'\bLTD\b|LTD\.|LIMITED\b', 'CORPORATION'),  # Often corporations
        (r'\bPC\b|P\.C\.|PROFESSIONAL CORPORATION', 'CORPORATION'),
        (r'\bPA\b|P\.A\.|PROFESSIONAL ASSOCIATION', 'CORPORATION'),
        (r'\bPLLC\b|P\.L\.L\.C\.|PROFESSIONAL LIMITED LIABILITY', 'LLC'),
        (r'\bPARTNERSHIP\b|PARTNERS\b', 'PARTNERSHIP'),
        (r'\bLP\b|L\.P\.|LIMITED PARTNERSHIP', 'PARTNERSHIP'),
        (r'\bTRUST\b', 'TRUST'),  # May need special handling
        (r'\bESTATE\b', 'ESTATE'),  # May need special handling
        (r'DBA\b|D/B/A|D\.B\.A\.', None),  # Skip DBA, look at rest of name
    ]
    
    for pattern, entity_type in patterns:
        if re.search(pattern, name_upper):
            if entity_type:  # Skip None (like DBA)
                return entity_type
    
    # If no pattern matches and it looks like a person's name, might be sole prop
    # This is a simple heuristic - checking for common name patterns
    if not any(word in name_upper for word in ['COMPANY', 'GROUP', 'SERVICES', 'ENTERPRISES']):
        # Could be an individual/sole proprietor
        parts = insured_name.split()
        if len(parts) == 2 and all(part.isalpha() for part in parts):
            return 'INDIVIDUAL'
    
    return None


# Test the function
if __name__ == "__main__":
    test_names = [
        "Ruby's Nursing Care LLC",
        "Smith Corporation", 
        "Johnson & Sons Partnership",
        "ABC Inc.",
        "John Doe",
        "XYZ Limited",
        "Professional Services LLP",
        "The Smith Family Trust",
        "Estate of John Smith",
        "ABC Company dba XYZ Services",
        "First National Bank, N.A.",
        "Medical Associates, P.C."
    ]
    
    print("Business Entity Type Detection Tests:")
    print("=" * 60)
    
    for name in test_names:
        detected = detect_business_type_from_name(name)
        print(f"{name:<40} → {detected or 'Not detected'}")