#!/usr/bin/env python3
"""
Standalone test for finding insured - no external dependencies.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Try to import dotenv, mock if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Mock the dotenv module if not installed
    class MockDotenv:
        def load_dotenv(self):
            pass
    sys.modules['dotenv'] = MockDotenv()

# Now import our services
from app.services.ims.auth_service import get_auth_service
from app.services.ims.insured_service import get_insured_service


def main():
    print("\nIMS Find Insured Standalone Test")
    print("=================================")
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please set environment variables:")
        print("  export IMS_ONE_USERNAME=your_username")
        print("  export IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Load test payload
    try:
        with open('TEST.json', 'r') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return 1
    
    # Authenticate
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Request: LoginIMSUser")
        print(f"Response: {auth_message}")
        return 1
    
    # Search for insured
    insured_service = get_insured_service()
    
    # Capture request data
    request_data = {
        "insured_name": payload.get('insured_name'),
        "city": payload.get('city'),
        "state": payload.get('state'),
        "zip": payload.get('zip')
    }
    
    found, insured_guid, message = insured_service.process_triton_payload(payload)
    
    if found:
        # Success - show only extracted values
        print(f"\nAuthentication Token: {auth_service.token[:20]}...")
        print(f"Insured Name: {payload.get('insured_name')}")
        print(f"Insured GUID: {insured_guid}")
        print(f"Status: FOUND")
    else:
        # Not found - show request/response for debugging
        print(f"\nInsured not found")
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())