#!/usr/bin/env python3
"""
Simple test for producer lookup
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ims_soap_client import IMSSoapClient
import logging

logging.basicConfig(level=logging.DEBUG)

def main():
    """Test producer lookup"""
    
    # Initialize IMS client
    client = IMSSoapClient("IMS_ONE.config")
    
    try:
        # Login first
        print("1. Logging in to IMS...")
        username = "david.korff"
        password = "kCeTLc2bxqOmG72ZBvMFkA=="
        
        client.login(username, password)
        print("   ✓ Login successful")
        
        # Our producer location GUID from config
        producer_location_guid = "895E9291-CFB6-4299-8799-9AF77DF937D6"
        
        print(f"\n2. Getting producer info for location GUID: {producer_location_guid}")
        producer_info = client.get_producer_info(producer_location_guid)
        
        if producer_info:
            print("\n   Producer Info:")
            for key, value in producer_info.items():
                print(f"   - {key}: {value}")
            
            location_code = producer_info.get("location_code")
            
            if location_code:
                print(f"\n3. Getting producer contact for location code: {location_code}")
                contact_guid = client.get_producer_contact_by_location_code(location_code)
                
                if contact_guid:
                    print(f"\n   ✓ Found Producer Contact GUID: {contact_guid}")
                    print("\n   This GUID should be used in AddSubmission")
                    return contact_guid
                else:
                    print("   ✗ No contact GUID returned")
            else:
                print("   ✗ No location code found in producer info")
        else:
            print("   ✗ Failed to get producer info")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    return None

if __name__ == "__main__":
    contact_guid = main()
    if contact_guid:
        print(f"\n\nSUCCESS! Producer Contact GUID: {contact_guid}")
        print("\nNext steps:")
        print("1. Add this to your environment configuration")
        print("2. Update the code to use this contact GUID in AddSubmission")