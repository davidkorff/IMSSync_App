#!/usr/bin/env python3
"""Test IMS login with correct namespace"""

import requests
import xml.etree.ElementTree as ET

# IMS server details
LOGON_URL = "http://dc02imsws01.rsgcorp.local/ims_one/logon.asmx"

def test_login_namespace():
    """Test login with different namespaces"""
    
    # The password from the config (already encrypted)
    username = "david.korff"
    password = "kCeTLc2bxqOmG72ZBvMFkA=="
    
    print("Testing IMS Login with correct namespace")
    print("=" * 50)
    
    # Try with the namespace that IMS expects (from the error message)
    soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Body>
    <LoginIMSUser xmlns="http://www.IMSPRO.com/WebServices/">
      <userName>{username}</userName>
      <tripleDESEncryptedPassword>{password}</tripleDESEncryptedPassword>
    </LoginIMSUser>
  </soap:Body>
</soap:Envelope>"""
    
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": '"http://www.IMSPRO.com/WebServices/LoginIMSUser"'  # Note the quotes
    }
    
    try:
        print(f"Sending login request to: {LOGON_URL}")
        print(f"Username: {username}")
        print(f"Headers: {headers}")
        print(f"\nSOAP Request:")
        print(soap_envelope)
        
        response = requests.post(LOGON_URL, data=soap_envelope, headers=headers, timeout=10)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"\nResponse Body:")
        print(response.text)
        
        if response.status_code == 200:
            # Parse response
            root = ET.fromstring(response.text)
            # Look for token in response
            for elem in root.iter():
                if 'Token' in (elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag):
                    print(f"\nFound Token: {elem.text}")
                if 'UserGuid' in (elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag):
                    print(f"User GUID: {elem.text}")
                if 'ErrorMessage' in (elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag):
                    print(f"Error Message: {elem.text}")
                    
    except Exception as e:
        print(f"\nError: {type(e).__name__} - {str(e)}")

def check_wsdl_namespace():
    """Check what namespace the WSDL defines"""
    print("\n\nChecking WSDL for correct namespace")
    print("=" * 50)
    
    try:
        response = requests.get(f"{LOGON_URL}?wsdl")
        if response.status_code == 200:
            root = ET.fromstring(response.text)
            
            # Find targetNamespace
            for elem in root.iter():
                if elem.tag.endswith('definitions'):
                    target_ns = elem.get('targetNamespace')
                    print(f"Target Namespace: {target_ns}")
                    break
                    
            # Find operation info
            for elem in root.iter():
                if elem.tag.endswith('operation') and elem.get('name') == 'LoginIMSUser':
                    print("\nFound LoginIMSUser operation")
                    # Look for soapAction
                    for child in elem.iter():
                        if child.tag.endswith('operation') and child.get('soapAction'):
                            print(f"SOAPAction: {child.get('soapAction')}")
                            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_wsdl_namespace()
    test_login_namespace()