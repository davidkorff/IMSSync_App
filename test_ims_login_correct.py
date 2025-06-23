#!/usr/bin/env python3
"""Test IMS login with correct namespace from WSDL"""

import requests
import xml.etree.ElementTree as ET

# IMS server details
LOGON_URL = "http://dc02imsws01.rsgcorp.local/ims_one/logon.asmx"

def test_login():
    """Test login with correct namespace from WSDL"""
    
    # The password from the config (already encrypted)
    username = "david.korff"
    password = "kCeTLc2bxqOmG72ZBvMFkA=="
    
    print("Testing IMS Login with WSDL-specified namespace")
    print("=" * 50)
    
    # Use the namespace from the WSDL
    soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Body>
    <LoginIMSUser xmlns="http://tempuri.org/IMSWebServices/Logon">
      <userName>{username}</userName>
      <tripleDESEncryptedPassword>{password}</tripleDESEncryptedPassword>
    </LoginIMSUser>
  </soap:Body>
</soap:Envelope>"""
    
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://tempuri.org/IMSWebServices/Logon/LoginIMSUser"  # No quotes
    }
    
    try:
        print(f"Sending login request to: {LOGON_URL}")
        print(f"Username: {username}")
        print(f"SOAPAction: {headers['SOAPAction']}")
        print(f"\nSOAP Request:")
        print(soap_envelope)
        
        response = requests.post(LOGON_URL, data=soap_envelope, headers=headers, timeout=10)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"\nResponse Body:")
        print(response.text[:1000])  # First 1000 chars
        
        if response.status_code == 200:
            # Parse response
            root = ET.fromstring(response.text)
            # Look for token in response
            for elem in root.iter():
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if 'Token' == tag_name and elem.text:
                    print(f"\nSUCCESS! Found Token: {elem.text[:20]}...")
                if 'UserGuid' == tag_name and elem.text:
                    print(f"User GUID: {elem.text}")
                if 'ErrorMessage' == tag_name and elem.text:
                    print(f"Error Message: {elem.text}")
        elif response.status_code == 500:
            # Parse fault
            root = ET.fromstring(response.text)
            fault_string = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault/faultstring')
            if fault_string is not None:
                print(f"\nSOAP Fault: {fault_string.text}")
                
            # Also check for login errors in response
            for elem in root.iter():
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if 'ErrorMessage' == tag_name and elem.text:
                    print(f"Login Error: {elem.text}")
                    
    except Exception as e:
        print(f"\nError: {type(e).__name__} - {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login()