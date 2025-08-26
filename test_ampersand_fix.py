#!/usr/bin/env python3
"""
Test the ampersand fix in XML parsing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Test the XML parsing fix directly
from app.services.ims.data_access_service import IMSDataAccessService

def test_parse_single_row_with_ampersand():
    """Test parsing XML with unescaped ampersand"""
    
    # Create service instance
    service = IMSDataAccessService()
    
    # Test XML with unescaped ampersand (like from SQL Server)
    test_xml = """<?xml version="1.0" encoding="utf-8"?>
<NewDataSet>
    <Table>
        <QuoteGuid>d71e07ba-7a3a-49fa-9a91-b65f0eb6c691</QuoteGuid>
        <QuoteOptionGuid>8a7517b1-65dd-4113-a797-21b8935eae0a</QuoteOptionGuid>
        <policy_number>SPG0000104-251</policy_number>
        <insured_name>Wellness Core Adult Day Healthcare LLC & Wellness Core Transportation LLC</insured_name>
        <opportunity_id>105531</opportunity_id>
        <created_date>2025-08-25T18:56:10</created_date>
        <QuoteStatusID>5</QuoteStatusID>
        <IsBound>1</IsBound>
    </Table>
</NewDataSet>"""
    
    # Test the parsing
    print("Testing XML parsing with unescaped ampersand...")
    result = service._parse_single_row_result(test_xml)
    
    if result:
        print("✓ Successfully parsed XML with ampersand!")
        print(f"  Insured Name: {result.get('insured_name')}")
        print(f"  Quote GUID: {result.get('QuoteGuid')}")
        print(f"  Policy Number: {result.get('policy_number')}")
        return True
    else:
        print("✗ Failed to parse XML")
        return False

def test_parse_single_row_with_multiple_ampersands():
    """Test parsing XML with multiple unescaped ampersands"""
    
    # Create service instance
    service = IMSDataAccessService()
    
    # Test XML with multiple unescaped ampersands
    test_xml = """<?xml version="1.0" encoding="utf-8"?>
<NewDataSet>
    <Table>
        <QuoteGuid>test-guid-123</QuoteGuid>
        <insured_name>Smith & Jones & Associates LLC</insured_name>
        <producer_name>Johnson & Co Insurance</producer_name>
    </Table>
</NewDataSet>"""
    
    print("\nTesting XML parsing with multiple unescaped ampersands...")
    result = service._parse_single_row_result(test_xml)
    
    if result:
        print("✓ Successfully parsed XML with multiple ampersands!")
        print(f"  Insured Name: {result.get('insured_name')}")
        print(f"  Producer Name: {result.get('producer_name')}")
        return True
    else:
        print("✗ Failed to parse XML")
        return False

def test_parse_single_row_with_mixed_entities():
    """Test parsing XML with mixed escaped and unescaped entities"""
    
    # Create service instance  
    service = IMSDataAccessService()
    
    # Test XML with mixed entities
    test_xml = """<?xml version="1.0" encoding="utf-8"?>
<NewDataSet>
    <Table>
        <QuoteGuid>test-guid-456</QuoteGuid>
        <description>This &amp; that & the other < > things</description>
        <notes>Already escaped &amp; should stay, new & should be fixed</notes>
    </Table>
</NewDataSet>"""
    
    print("\nTesting XML parsing with mixed escaped/unescaped entities...")
    result = service._parse_single_row_result(test_xml)
    
    if result:
        print("✓ Successfully parsed XML with mixed entities!")
        print(f"  Description: {result.get('description')}")
        print(f"  Notes: {result.get('notes')}")
        return True
    else:
        print("✗ Failed to parse XML")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Ampersand Fix in XML Parsing")
    print("=" * 60)
    
    results = []
    results.append(test_parse_single_row_with_ampersand())
    results.append(test_parse_single_row_with_multiple_ampersands())
    results.append(test_parse_single_row_with_mixed_entities())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ ALL TESTS PASSED")
    else:
        print(f"✗ {sum(not r for r in results)} TEST(S) FAILED")
        sys.exit(1)