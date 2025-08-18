#!/usr/bin/env python3
"""
Standalone test for IMS authentication - no external dependencies.
Set environment variables before running:
  export IMS_ONE_USERNAME=your_username
  export IMS_ONE_PASSWORD=your_encrypted_password
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the auth service
from app.services.ims.auth_service import IMSAuthService

def main():
    print("\nIMS Authentication Standalone Test")
    print("==================================")
    
    # Create auth service
    auth_service = IMSAuthService()
    
    # Check configuration
    print(f"\nConfiguration:")
    print(f"  Base URL: {auth_service.base_url}")
    print(f"  Endpoint: {auth_service.logon_endpoint}")
    print(f"  Username: {auth_service.username or 'NOT SET'}")
    print(f"  Password: {'SET' if auth_service.password else 'NOT SET'}")
    
    if not auth_service.username or not auth_service.password:
        print("\nERROR: Credentials not configured!")
        print("\nPlease set environment variables:")
        print("  export IMS_ONE_USERNAME=your_username")
        print("  export IMS_ONE_PASSWORD=your_encrypted_password")
        print("\nOr create a .env file with these values.")
        return 1
    
    # Test login
    print("\nTesting login...")
    print("-" * 40)
    
    try:
        success, message = auth_service.login()
        
        print(f"\nResult: {'✓ SUCCESS' if success else '✗ FAILED'}")
        print(f"Message: {message}")
        
        if success:
            print(f"\nAuthentication successful!")
            print(f"  User GUID: {auth_service._user_guid}")
            print(f"  Token: {auth_service._token[:20]}..." if auth_service._token else "  Token: None")
            
            # Test that token property works
            token = auth_service.token
            print(f"\nToken retrieval test: {'✓ PASS' if token else '✗ FAIL'}")
            
            # Test auth headers
            headers = auth_service.get_auth_headers()
            print(f"\nGenerated headers:")
            for key, value in headers.items():
                if key == 'Authorization' and value:
                    print(f"  {key}: Bearer {token[:20]}...")
                else:
                    print(f"  {key}: {value}")
            
            return 0
        else:
            print("\nAuthentication failed!")
            print("Please check:")
            print("  1. Credentials are correct")
            print("  2. IMS server is accessible")
            print("  3. Password is properly encrypted (Triple DES)")
            return 1
            
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        
        # More detailed error info
        import traceback
        print("\nDetailed error:")
        traceback.print_exc()
        
        return 1

if __name__ == "__main__":
    sys.exit(main())