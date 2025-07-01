#!/usr/bin/env python3
"""Test direct connection to IMS server"""

import requests
import xml.etree.ElementTree as ET

# IMS server details from IMS_ONE.config
IMS_BASE_URL = "http://10.64.32.234/ims_one"
LOGON_URL = f"{IMS_BASE_URL}/logon.asmx"
INSURED_URL = f"{IMS_BASE_URL}/InsuredFunctions.asmx"

def test_wsdl_access():
    """Test if we can access the WSDL files"""
    print("Testing IMS Server Connectivity")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        (f"{LOGON_URL}?wsdl", "Logon WSDL"),
        (f"{INSURED_URL}?wsdl", "Insured Functions WSDL"),
        (f"{IMS_BASE_URL}/DocumentFunctions.asmx?wsdl", "Document Functions WSDL"),
    ]
    
    for url, name in endpoints:
        print(f"\nTesting {name}: {url}")
        try:
            response = requests.get(url, timeout=5)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                # Check if it's valid XML/WSDL
                try:
                    ET.fromstring(response.text)
                    print(f"  Result: Valid WSDL received")
                    print(f"  Size: {len(response.text)} bytes")
                except:
                    print(f"  Result: Response received but not valid XML")
                    print(f"  Content preview: {response.text[:200]}...")
            else:
                print(f"  Error: HTTP {response.status_code}")
                print(f"  Response: {response.text[:200]}...")
        except requests.exceptions.Timeout:
            print(f"  Error: Connection timeout")
        except requests.exceptions.ConnectionError as e:
            print(f"  Error: Cannot connect - {str(e)}")
        except Exception as e:
            print(f"  Error: {type(e).__name__} - {str(e)}")

def test_soap_call():
    """Test a simple SOAP call to logon"""
    print("\n\nTesting SOAP Call to Logon Service")
    print("=" * 50)
    
    # Simple SOAP envelope to test
    soap_envelope = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <LoginIMSUser xmlns="http://www.IMSPRO.com/WebServices/"></LoginIMSUser>
  </soap:Body>
</soap:Envelope>"""
    
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://www.IMSPRO.com/WebServices/LoginIMSUser"
    }
    
    try:
        print(f"Sending SOAP request to: {LOGON_URL}")
        response = requests.post(LOGON_URL, data=soap_envelope, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        if response.status_code == 500:
            print("Note: 500 error might be expected if no credentials provided")
        print(f"Response preview: {response.text[:500]}...")
    except Exception as e:
        print(f"Error: {type(e).__name__} - {str(e)}")

if __name__ == "__main__":
    test_wsdl_access()
    test_soap_call()