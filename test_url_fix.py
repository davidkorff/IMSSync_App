#!/usr/bin/env python3
"""Test the URL fix"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ims_soap_client import IMSSoapClient

def test_url_construction():
    """Test that URLs are constructed correctly"""
    print("Testing URL construction after fix")
    print("=" * 50)
    
    # Create SOAP client with IMS_ONE config
    client = IMSSoapClient("IMS_ONE.config")
    
    print(f"Logon URL: {client.logon_url}")
    print(f"Insured Functions URL: {client.insured_functions_url}")
    print(f"Quote Functions URL: {client.quote_functions_url}")
    print(f"Document Functions URL: {client.document_functions_url}")
    print(f"Producer Functions URL: {client.producer_functions_url}")
    
    # Check if URLs are valid
    print("\nValidation:")
    if client.insured_functions_url.startswith("http://"):
        print("✓ Insured Functions URL is valid")
    else:
        print("✗ Insured Functions URL is invalid")

if __name__ == "__main__":
    test_url_construction()