#!/usr/bin/env python3
"""Test the InsuredFunctions lookup directly"""

import os
import sys
import logging
import requests

# Set up debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ims_soap_client import IMSSoapClient

def test_find_insured():
    """Test finding an insured directly"""
    print("Testing InsuredFunctions.FindInsuredByName")
    print("=" * 50)
    
    # Create SOAP client and login
    client = IMSSoapClient("IMS_ONE.config")
    
    try:
        # Login first
        print("Logging in...")
        token = client.login("david.korff", "kCeTLc2bxqOmG72ZBvMFkA==")
        print(f"Login successful, token: {token[:20]}...")
        
        # Now test FindInsuredByName
        print("\nTesting FindInsuredByName...")
        print("Looking for: The Nanny Joynt LLC")
        
        # This will show us the exact SOAP request in debug logs
        result = client.find_insured_by_name(
            "The Nanny Joynt LLC",
            tax_id=None,
            city="",
            state="",
            zip_code=""
        )
        
        print(f"\nResult: {result}")
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {str(e)}")
        
        # If it's a 500 error, let's see the response
        if "500" in str(e):
            print("\nTrying raw SOAP request to see error details...")
            
            # Make raw request to see SOAP fault
            soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Header>
        <TokenHeader xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
            <Token>{client.token}</Token>
        </TokenHeader>
    </soap:Header>
    <soap:Body>
        <FindInsuredByName xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
            <insuredName>The Nanny Joynt LLC</insuredName>
            <city></city>
            <state></state>
            <zip></zip>
            <zipPlus></zipPlus>
        </FindInsuredByName>
    </soap:Body>
</soap:Envelope>"""
            
            headers = {
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": "http://tempuri.org/IMSWebServices/InsuredFunctions/FindInsuredByName"
            }
            
            response = requests.post(client.insured_functions_url, data=soap_envelope, headers=headers)
            print(f"\nRAW Response Status: {response.status_code}")
            print(f"RAW Response:\n{response.text}")

if __name__ == "__main__":
    test_find_insured()