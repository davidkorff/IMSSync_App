#!/usr/bin/env python3
"""
Simple test of XML parsing with ampersand fix
"""

import re
import xml.etree.ElementTree as ET

def parse_single_row_result(result_xml):
    """
    Parse XML result with ampersand fix.
    """
    try:
        if not result_xml:
            return None
        
        # Fix common XML issues - escape unescaped ampersands
        # Replace & that aren't part of existing entities
        result_xml = re.sub(r'&(?!(?:amp|lt|gt|apos|quot);)', '&amp;', result_xml)
            
        # Parse the XML
        root = ET.fromstring(result_xml)
        
        # Find the first Table element (single row result)
        table = root.find('.//Table')
        if table is None:
            return None
        
        # Convert all child elements to a dictionary
        result = {}
        for child in table:
            if child.text is not None:
                result[child.tag] = child.text
            else:
                result[child.tag] = None
                
        return result if result else None
        
    except ET.ParseError as e:
        print(f"XML Parse Error: {str(e)}")
        print(f"Problematic XML (first 500 chars): {result_xml[:500] if result_xml else 'None'}")
        return None
    except Exception as e:
        print(f"Error parsing single row result: {str(e)}")
        return None

# Test case 1: XML with unescaped ampersand (what we're getting from SQL)
test_xml_1 = """<?xml version="1.0" encoding="utf-8"?>
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

print("Test 1: XML with unescaped ampersand")
print("-" * 40)
result = parse_single_row_result(test_xml_1)
if result:
    print("✓ SUCCESS: Parsed XML successfully!")
    print(f"  Insured Name: {result.get('insured_name')}")
    print(f"  Quote GUID: {result.get('QuoteGuid')}")
else:
    print("✗ FAILED: Could not parse XML")

# Test case 2: Multiple ampersands
test_xml_2 = """<?xml version="1.0" encoding="utf-8"?>
<NewDataSet>
    <Table>
        <company>Smith & Jones & Associates</company>
        <address>123 Main St & Broadway</address>
    </Table>
</NewDataSet>"""

print("\n\nTest 2: Multiple unescaped ampersands")
print("-" * 40)
result = parse_single_row_result(test_xml_2)
if result:
    print("✓ SUCCESS: Parsed XML successfully!")
    print(f"  Company: {result.get('company')}")
    print(f"  Address: {result.get('address')}")
else:
    print("✗ FAILED: Could not parse XML")

# Test case 3: Mixed escaped and unescaped
test_xml_3 = """<?xml version="1.0" encoding="utf-8"?>
<NewDataSet>
    <Table>
        <field1>Already &amp; escaped</field1>
        <field2>Not & escaped</field2>
        <field3>Mix &amp; match & test</field3>
    </Table>
</NewDataSet>"""

print("\n\nTest 3: Mixed escaped and unescaped ampersands")
print("-" * 40)
result = parse_single_row_result(test_xml_3)
if result:
    print("✓ SUCCESS: Parsed XML successfully!")
    print(f"  Field1: {result.get('field1')}")
    print(f"  Field2: {result.get('field2')}")
    print(f"  Field3: {result.get('field3')}")
else:
    print("✗ FAILED: Could not parse XML")

# Test case 4: Already properly escaped (should not break)
test_xml_4 = """<?xml version="1.0" encoding="utf-8"?>
<NewDataSet>
    <Table>
        <company>Smith &amp; Jones</company>
        <special>&lt;tag&gt; &amp; &quot;quotes&quot;</special>
    </Table>
</NewDataSet>"""

print("\n\nTest 4: Already properly escaped XML")
print("-" * 40)
result = parse_single_row_result(test_xml_4)
if result:
    print("✓ SUCCESS: Parsed XML successfully!")
    print(f"  Company: {result.get('company')}")
    print(f"  Special: {result.get('special')}")
else:
    print("✗ FAILED: Could not parse XML")

print("\n" + "=" * 50)
print("All tests completed!")