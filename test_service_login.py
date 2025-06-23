#!/usr/bin/env python3
"""Test the service's login mechanism directly"""

import os
import sys
import logging

# Set up debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ims_soap_client import IMSSoapClient

def test_service_login():
    """Test login using the service's SOAP client"""
    print("Testing service login mechanism")
    print("=" * 50)
    
    # Create SOAP client with IMS_ONE config
    client = IMSSoapClient("IMS_ONE.config")
    
    # Try to login with the same credentials
    username = "david.korff"
    password = "kCeTLc2bxqOmG72ZBvMFkA=="
    
    try:
        print(f"Attempting login with username: {username}")
        print(f"Using URL: {client.logon_url}")
        
        token = client.login(username, password)
        print(f"\nSUCCESS! Received token: {token}")
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_service_login()