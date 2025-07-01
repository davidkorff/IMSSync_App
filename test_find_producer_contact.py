#!/usr/bin/env python3
"""
Find producer contact GUID for IMS integration
"""

import requests
import xml.etree.ElementTree as ET

# Configuration
LOGON_URL = "http://10.64.32.234/ims_one/logon.asmx"
PRODUCER_URL = "http://10.64.32.234/ims_one/ProducerFunctions.asmx"

def login():
    """Login to IMS"""
    username = "david.korff"
    password = "kCeTLc2bxqOmG72ZBvMFkA=="
    
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
        "SOAPAction": "http://tempuri.org/IMSWebServices/Logon/LoginIMSUser"
    }
    
    response = requests.post(LOGON_URL, data=soap_envelope, headers=headers, timeout=10)
    
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        for elem in root.iter():
            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if 'Token' == tag_name and elem.text:
                return elem.text
    return None

def get_producer_info(token, producer_location_guid):
    """Get producer info"""
    soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <soap:Header>
        <TokenHeader xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
          <Token>{token}</Token>
        </TokenHeader>
      </soap:Header>
      <soap:Body>
        <GetProducerInfo xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
          <producerLocationGuid>{producer_location_guid}</producerLocationGuid>
        </GetProducerInfo>
      </soap:Body>
    </soap:Envelope>"""
    
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://tempuri.org/IMSWebServices/ProducerFunctions/GetProducerInfo"
    }
    
    response = requests.post(PRODUCER_URL, data=soap_envelope, headers=headers, timeout=10)
    
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        producer_info = {}
        for elem in root.iter():
            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if elem.text and tag_name in ['ProducerName', 'ProducerCode', 'LocationName', 'LocationCode']:
                producer_info[tag_name] = elem.text
        return producer_info
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    return None

def get_producer_contact_by_location_code(token, location_code):
    """Get producer contact by location code"""
    soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <soap:Header>
        <TokenHeader xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
          <Token>{token}</Token>
        </TokenHeader>
      </soap:Header>
      <soap:Body>
        <GetProducerContactByLocationCode xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
          <locationCode>{location_code}</locationCode>
        </GetProducerContactByLocationCode>
      </soap:Body>
    </soap:Envelope>"""
    
    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "http://tempuri.org/IMSWebServices/ProducerFunctions/GetProducerContactByLocationCode"
    }
    
    response = requests.post(PRODUCER_URL, data=soap_envelope, headers=headers, timeout=10)
    
    if response.status_code == 200:
        root = ET.fromstring(response.text)
        for elem in root.iter():
            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if 'GetProducerContactByLocationCodeResult' == tag_name and elem.text:
                return elem.text
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    return None

def main():
    print("=== Finding Producer Contact GUID ===\n")
    
    # Step 1: Login
    print("1. Logging in to IMS...")
    token = login()
    if not token:
        print("   ✗ Login failed")
        return 1
    print(f"   ✓ Login successful, token: {token[:20]}...")
    
    # Step 2: Get producer info
    producer_location_guid = "895E9291-CFB6-4299-8799-9AF77DF937D6"
    print(f"\n2. Getting producer info for GUID: {producer_location_guid}")
    
    producer_info = get_producer_info(token, producer_location_guid)
    if not producer_info:
        print("   ✗ Failed to get producer info")
        return 1
    
    print("   Producer Info:")
    for key, value in producer_info.items():
        print(f"   - {key}: {value}")
    
    location_code = producer_info.get('LocationCode')
    if not location_code:
        print("   ✗ No location code found")
        return 1
    
    # Step 3: Get producer contact
    print(f"\n3. Getting producer contact for location code: {location_code}")
    contact_guid = get_producer_contact_by_location_code(token, location_code)
    
    if contact_guid:
        print(f"\n   ✓ FOUND PRODUCER CONTACT GUID: {contact_guid}")
        print("\n   Add this to your .env file:")
        print(f"   TRITON_DEFAULT_PRODUCER_CONTACT_GUID={contact_guid}")
    else:
        print("   ✗ No contact GUID found")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())