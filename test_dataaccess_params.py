#!/usr/bin/env python3
"""
Test script to demonstrate the correct parameter format for DataAccess ExecuteDataSet
Based on the documentation, parameters must be passed as alternating name/value pairs
"""

def show_parameter_format():
    """Show how parameters should be formatted according to documentation"""
    
    # Example quote GUID
    quote_guid = "f4bbe818-2d6f-4b9d-91fb-e4916549c4c5"
    
    print("IMS DataAccess ExecuteDataSet Parameter Format Test")
    print("=" * 60)
    print()
    
    print("According to documentation:")
    print("- Parameters must be passed as an array of strings")
    print("- Format: [ParamName1, Value1, ParamName2, Value2, ...]")
    print("- The procedure name will have '_WS' appended automatically")
    print()
    
    print("For spGetQuoteOptions_WS with @QuoteGuid parameter:")
    print()
    
    # Different possible formats to try
    formats = [
        {
            "name": "Format 1: Parameter name without @",
            "params": ["QuoteGuid", quote_guid]
        },
        {
            "name": "Format 2: Parameter name with @",
            "params": ["@QuoteGuid", quote_guid]
        },
        {
            "name": "Format 3: Just the value (positional)",
            "params": [quote_guid]
        },
        {
            "name": "Format 4: Empty array (no parameters)",
            "params": []
        },
        {
            "name": "Format 5: Key=Value format",
            "params": ["QuoteGuid=" + quote_guid]
        }
    ]
    
    for fmt in formats:
        print(f"{fmt['name']}:")
        print(f"  parameters = {fmt['params']}")
        print()
    
    print("SOAP XML for Format 1 (most likely correct):")
    print("""
<ExecuteDataSet xmlns="http://tempuri.org/IMSWebServices/DataAccess">
  <procedureName>spGetQuoteOptions</procedureName>
  <parameters>
    <string>QuoteGuid</string>
    <string>f4bbe818-2d6f-4b9d-91fb-e4916549c4c5</string>
  </parameters>
</ExecuteDataSet>
""")
    
    print("SOAP XML for Format 2 (with @ prefix):")
    print("""
<ExecuteDataSet xmlns="http://tempuri.org/IMSWebServices/DataAccess">
  <procedureName>spGetQuoteOptions</procedureName>
  <parameters>
    <string>@QuoteGuid</string>
    <string>f4bbe818-2d6f-4b9d-91fb-e4916549c4c5</string>
  </parameters>
</ExecuteDataSet>
""")
    
    print("\nNOTE: The actual procedure called will be 'spGetQuoteOptions_WS'")
    print("      (IMS automatically appends '_WS' to the procedure name)")

if __name__ == "__main__":
    show_parameter_format()