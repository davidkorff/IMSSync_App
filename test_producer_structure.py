#!/usr/bin/env python3
"""
Test script to understand IMS producer structure
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ims_soap_client import IMSSoapClient
import logging

logging.basicConfig(level=logging.INFO)

def test_producer_structure():
    """Test producer structure and find contact"""
    
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
        
        # Get producer info using the GUID as location GUID
        body_content = f"""
        <GetProducerInfo xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
            <producerLocationGuid>{producer_location_guid}</producerLocationGuid>
        </GetProducerInfo>
        """
        
        response = client._make_soap_request(
            client.producer_functions_url,
            "http://tempuri.org/IMSWebServices/ProducerFunctions/GetProducerInfo",
            body_content
        )
        
        if response and 'soap:Body' in response:
            get_response = response['soap:Body'].get('GetProducerInfoResponse', {})
            producer_info = get_response.get('GetProducerInfoResult', {})
            
            print("\n   Producer Info:")
            print(f"   - Producer Name: {producer_info.get('ProducerName')}")
            print(f"   - Producer Code: {producer_info.get('ProducerCode')}")
            print(f"   - Location Name: {producer_info.get('LocationName')}")
            print(f"   - Location Code: {producer_info.get('LocationCode')}")
            print(f"   - Location GUID: {producer_info.get('ProducerLocationGuid')}")
            
            location_code = producer_info.get('LocationCode')
            
            if location_code:
                print(f"\n3. Getting producer contact for location code: {location_code}")
                
                # Get producer contact by location code
                body_content = f"""
                <GetProducerContactByLocationCode xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
                    <locationCode>{location_code}</locationCode>
                </GetProducerContactByLocationCode>
                """
                
                response = client._make_soap_request(
                    client.producer_functions_url,
                    "http://tempuri.org/IMSWebServices/ProducerFunctions/GetProducerContactByLocationCode",
                    body_content
                )
                
                if response and 'soap:Body' in response:
                    contact_response = response['soap:Body'].get('GetProducerContactByLocationCodeResponse', {})
                    contact_guid = contact_response.get('GetProducerContactByLocationCodeResult')
                    
                    if contact_guid:
                        print(f"\n   ✓ Found Producer Contact GUID: {contact_guid}")
                        
                        # Get contact details
                        print("\n4. Getting producer contact details...")
                        body_content = f"""
                        <GetProducerContactInfo xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
                            <producerContactGuid>{contact_guid}</producerContactGuid>
                        </GetProducerContactInfo>
                        """
                        
                        response = client._make_soap_request(
                            client.producer_functions_url,
                            "http://tempuri.org/IMSWebServices/ProducerFunctions/GetProducerContactInfo",
                            body_content
                        )
                        
                        if response and 'soap:Body' in response:
                            contact_info_response = response['soap:Body'].get('GetProducerContactInfoResponse', {})
                            contact_info = contact_info_response.get('GetProducerContactInfoResult', {})
                            
                            print("\n   Contact Info:")
                            print(f"   - Name: {contact_info.get('FName')} {contact_info.get('LName')}")
                            print(f"   - Title: {contact_info.get('Title')}")
                            print(f"   - Email: {contact_info.get('Email')}")
                            print(f"   - Phone: {contact_info.get('Phone')}")
                    else:
                        print("   ✗ No contact GUID returned")
                else:
                    print("   ✗ No response from GetProducerContactByLocationCode")
            else:
                print("   ✗ No location code found in producer info")
        else:
            print("   ✗ Failed to get producer info")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(test_producer_structure())