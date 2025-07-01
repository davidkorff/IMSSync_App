#!/usr/bin/env python3
"""
Test script to get valid business types from IMS using the GetInsuredBusinessTypes API
"""

import os
import sys
import requests
import xml.etree.ElementTree as ET

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_business_types_direct():
    """Query business types directly from IMS"""
    
    # IMS endpoints
    logon_url = "http://dc02imsws01.rsgcorp.local/ims_one/logon.asmx"
    insured_url = "http://dc02imsws01.rsgcorp.local/ims_one/InsuredFunctions.asmx"
    
    # First, login to get a token
    print("Logging in to IMS...")
    login_body = """<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <LoginIMSUser xmlns="http://tempuri.org/IMSWebServices/Logon">
                <userName>david.korff</userName>
                <password>P@ssw0rd123!</password>
            </LoginIMSUser>
        </soap:Body>
    </soap:Envelope>"""
    
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'http://tempuri.org/IMSWebServices/Logon/LoginIMSUser'
    }
    
    try:
        response = requests.post(logon_url, data=login_body, headers=headers)
        response.raise_for_status()
        
        # Parse the response to get the token
        root = ET.fromstring(response.text)
        token_elem = root.find('.//{http://tempuri.org/IMSWebServices/Logon}LoginIMSUserResult')
        
        if token_elem is None:
            print("Failed to get login token")
            return
            
        token = token_elem.text
        print(f"Got token: {token[:20]}...")
        
        # Now get business types
        print("\nQuerying business types...")
        business_types_body = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <GetInsuredBusinessTypes xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
                    <token>{token}</token>
                </GetInsuredBusinessTypes>
            </soap:Body>
        </soap:Envelope>"""
        
        headers['SOAPAction'] = 'http://tempuri.org/IMSWebServices/InsuredFunctions/GetInsuredBusinessTypes'
        
        response = requests.post(insured_url, data=business_types_body, headers=headers)
        response.raise_for_status()
        
        print("\nResponse:")
        print(response.text)
        
        # Try to parse the business types
        root = ET.fromstring(response.text)
        
        # Look for BusinessType elements in the response
        print("\nParsed Business Types:")
        print("ID | Description")
        print("-" * 40)
        
        # The response structure might vary, so let's try different paths
        for elem in root.iter():
            if 'BusinessType' in elem.tag and elem.text:
                print(f"Found element: {elem.tag} = {elem.text}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_business_types_direct()