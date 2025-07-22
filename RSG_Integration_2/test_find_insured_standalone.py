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

# Mock the dotenv module
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
    print("\n1. Loading TEST.json payload...")
    try:
        with open('TEST.json', 'r') as f:
            payload = json.load(f)
        print("   ✓ Payload loaded successfully")
    except Exception as e:
        print(f"   ✗ Failed to load payload: {e}")
        return 1
    
    # Display payload info
    print(f"\n   Insured Name: {payload.get('insured_name', 'N/A')}")
    print(f"   City: {payload.get('city', 'N/A')}")
    print(f"   State: {payload.get('state', 'N/A')}")
    print(f"   ZIP: {payload.get('zip', 'N/A')}")
    
    # Authenticate
    print("\n2. Authenticating with IMS...")
    auth_service = get_auth_service()
    success, message = auth_service.login()
    
    if not success:
        print(f"   ✗ Authentication failed: {message}")
        return 1
    
    print(f"   ✓ Authentication successful")
    print(f"   Token: {auth_service.token[:20]}...")
    
    # Search for insured
    print("\n3. Searching for insured...")
    insured_service = get_insured_service()
    
    found, insured_guid, message = insured_service.process_triton_payload(payload)
    
    print(f"\n   Result: {'FOUND' if found else 'NOT FOUND'}")
    print(f"   Message: {message}")
    
    if found:
        print(f"\n   ✓ SUCCESS: Insured exists in IMS")
        print(f"   Insured GUID: {insured_guid}")
        print("\n   Next step: Use this GUID for further operations")
    else:
        print(f"\n   → INFO: Insured not found in IMS")
        print("   Next step: Create new insured record")
    
    # Test direct search as well
    print("\n4. Testing direct search (without payload)...")
    test_found, test_guid, test_message = insured_service.find_insured_by_name(
        "BLC Industries, LLC",
        "Kalamazoo",
        "MI",
        "49048"
    )
    
    print(f"   Test search result: {'FOUND' if test_found else 'NOT FOUND'}")
    if test_found:
        print(f"   Test GUID: {test_guid}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())