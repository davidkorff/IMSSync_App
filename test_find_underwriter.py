#!/usr/bin/env python3
"""
Find valid underwriter names in IMS
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ims.auth_service import get_auth_service
from app.services.ims.data_access_service import get_data_access_service
import xml.etree.ElementTree as ET

def find_underwriters():
    """Search for underwriters in the system"""
    # First authenticate
    auth_service = get_auth_service()
    success, auth_data, message = auth_service.login()
    
    if not success:
        print(f"Authentication failed: {message}")
        return
    
    print("Successfully authenticated to IMS")
    
    # Get data access service
    data_service = get_data_access_service()
    
    # Try some common names
    test_names = [
        "David Korff",
        "Admin",
        "Administrator", 
        "Test User",
        "System",
        "Default"
    ]
    
    print("\nSearching for underwriters...")
    found_users = []
    
    for name in test_names:
        success, xml_data, msg = data_service.execute_dataset(
            "getUserbyName",
            ["fullname", name]
        )
        
        if success and xml_data and xml_data.strip() != "<Results />":
            try:
                root = ET.fromstring(xml_data)
                table = root.find('.//Table')
                if table is not None:
                    user_guid = table.find('UserGUID')
                    if user_guid is not None and user_guid.text:
                        found_users.append({
                            'name': name,
                            'guid': user_guid.text
                        })
                        print(f"✓ Found: {name} (GUID: {user_guid.text})")
            except:
                pass
        else:
            print(f"✗ Not found: {name}")
    
    if found_users:
        print(f"\nFound {len(found_users)} valid underwriter(s)")
        print("\nYou can use any of these names in your test JSON:")
        for user in found_users:
            print(f'  "underwriter_name": "{user["name"]}"')
    else:
        print("\nNo underwriters found with the test names.")
        print("You may need to check with your IMS administrator for valid user names.")

if __name__ == "__main__":
    find_underwriters()