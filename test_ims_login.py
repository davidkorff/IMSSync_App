#!/usr/bin/env python3
"""
Test script to verify IMS login
"""

import logging
import os
import sys
from app.services.ims_soap_client import IMSSoapClient
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

def test_ims_login(environment="ims_one"):
    """Test IMS login with the specified environment"""
    try:
        # Get environment settings
        env_config = settings.IMS_ENVIRONMENTS.get(environment)
        if not env_config:
            print(f"Error: Unknown environment '{environment}'")
            print(f"Available environments: {list(settings.IMS_ENVIRONMENTS.keys())}")
            return False
        
        config_file = env_config["config_file"]
        username = env_config["username"]
        password = env_config["password"]
        
        print(f"Testing IMS login for environment: {environment}")
        print(f"Config file: {config_file}")
        print(f"Username: {username}")
        
        # Initialize SOAP client
        client = IMSSoapClient(config_file)
        
        # Test login
        print("Attempting login...")
        token = client.login(username, password)
        
        if token:
            print(f"Login successful! Token: {token}")
            
            # Test parsing configuration
            print("\nURL Configuration:")
            print(f"Logon URL: {client.logon_url}")
            print(f"QuoteFunctions URL: {client.quote_functions_url}")
            print(f"InsuredFunctions URL: {client.insured_functions_url}")
            print(f"DataAccess URL: {client.data_access_url}")
            
            return True
        else:
            print("Login failed: No token returned")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Use command line argument for environment if provided
    environment = "ims_one"
    if len(sys.argv) > 1:
        environment = sys.argv[1]
    
    success = test_ims_login(environment)
    sys.exit(0 if success else 1)