#!/usr/bin/env python3
"""
Test IMS producer contact lookup
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ims_soap_client import IMSSoapClient
import logging

logging.basicConfig(level=logging.INFO)

def test_producer_lookup():
    """Test producer contact lookup"""
    
    # Initialize IMS client
    client = IMSSoapClient("IMS_ONE.config")
    
    try:
        # Login first
        print("1. Logging in to IMS...")
        username = "david.korff"
        password = "kCeTLc2bxqOmG72ZBvMFkA=="
        
        client.login(username, password)
        print("   ✓ Login successful")
        
        # Test producer lookup
        print("\n2. Looking up producer contact...")
        producer_guid = "895E9291-CFB6-4299-8799-9AF77DF937D6"
        
        try:
            # First, let's check if we can get producer info
            print(f"   Getting producer info for: {producer_guid}")
            
            # Direct SOAP call to GetProducerInfo
            body_content = f"""
            <GetProducerInfo xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
                <producerGuid>{producer_guid}</producerGuid>
            </GetProducerInfo>
            """
            
            response = client._make_soap_request(
                client.producer_functions_url,
                "http://tempuri.org/IMSWebServices/ProducerFunctions/GetProducerInfo",
                body_content
            )
            
            if response and 'soap:Body' in response:
                producer_info = response['soap:Body'].get('GetProducerInfoResponse', {})
                result = producer_info.get('GetProducerInfoResult', {})
                print(f"   Producer found: {result}")
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
            
        # Now test the stored procedure
        print("\n3. Testing DK_GetDefaultProducerContact stored procedure...")
        try:
            contact = client.get_default_producer_contact(producer_guid)
            if contact:
                print(f"   ✓ Found contact: {contact}")
            else:
                print("   ✗ No contact found")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            
    except Exception as e:
        print(f"\nERROR: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(test_producer_lookup())