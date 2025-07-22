#!/usr/bin/env python3
"""
Simple test script for IMS authentication - without external dependencies.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the dotenv module since it's not installed
class MockDotenv:
    def load_dotenv(self):
        pass

sys.modules['dotenv'] = MockDotenv()

# Now we can import
from app.services.ims.auth_service import IMSAuthService

def main():
    print("\nSimple IMS Authentication Test")
    print("==============================")
    
    # Manually set config for testing
    auth_service = IMSAuthService()
    
    # Override with test values if not in environment
    if not auth_service.username:
        print("\nWARNING: IMS_ONE_USERNAME not set in environment")
        auth_service.username = input("Enter IMS username: ")
    
    if not auth_service.password:
        print("WARNING: IMS_ONE_PASSWORD not set in environment")
        auth_service.password = input("Enter IMS password (encrypted): ")
    
    print(f"\nConfiguration:")
    print(f"  Base URL: {auth_service.base_url}")
    print(f"  Username: {auth_service.username}")
    print(f"  Password: {'*' * 10 if auth_service.password else 'NOT SET'}")
    
    print("\nAttempting login...")
    try:
        success, message = auth_service.login()
        print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
        print(f"Message: {message}")
        
        if success:
            print(f"\nToken obtained: {auth_service._token[:20]}...")
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()