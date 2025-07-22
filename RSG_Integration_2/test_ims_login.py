#!/usr/bin/env python3
"""
Test script for IMS authentication service.
Tests login functionality and token management.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ims.auth_service import get_auth_service, IMSAuthService

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Show only important messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_login():
    """Test basic login functionality."""
    print("\n" + "="*60)
    print("Testing IMS Login")
    print("="*60)
    
    # Get auth service instance
    auth_service = get_auth_service()
    
    # Display configuration (without passwords)
    print(f"\nConfiguration:")
    print(f"  Base URL: {auth_service.base_url}")
    print(f"  Endpoint: {auth_service.logon_endpoint}")
    print(f"  Username: {auth_service.username}")
    print(f"  Password: {'*' * 10 if auth_service.password else 'NOT SET'}")
    
    # Test login
    print("\nAttempting login...")
    success, message = auth_service.login()
    
    if success:
        print(f"\n✓ LOGIN SUCCESSFUL")
        print(f"  User GUID: {auth_service._user_guid}")
        print(f"  Token: {auth_service._token}")
        return True
    else:
        print(f"\n✗ LOGIN FAILED")
        print(f"  Error: {message}")
        return False
    
    return success


def test_token_management():
    """Test token caching and refresh."""
    print("\n" + "="*60)
    print("Testing Token Management")
    print("="*60)
    
    auth_service = get_auth_service()
    
    # First access should trigger login
    print("\nGetting token (should trigger login)...")
    token1 = auth_service.token
    
    if token1:
        print(f"✓ TOKEN RETRIEVED: {token1}")
    else:
        print("✗ FAILED TO GET TOKEN")
        return False
    
    # Second access should use cached token
    print("\nGetting token again (should use cache)...")
    token2 = auth_service.token
    
    if token1 == token2:
        print(f"✓ CACHE WORKING - Same token returned")
    else:
        print(f"✗ CACHE FAILED - Different tokens")
        return False
    
    # Test logout
    auth_service.logout()
    print(f"\n✓ LOGGED OUT")


def test_error_handling():
    """Test error handling scenarios."""
    print("\n" + "="*60)
    print("Testing Error Handling")
    print("="*60)
    
    # Create a new instance with bad config
    bad_auth = IMSAuthService()
    
    # Test with invalid URL
    print("\nTesting with invalid URL...")
    original_url = bad_auth.base_url
    bad_auth.base_url = "http://invalid.url.test"
    
    success, message = bad_auth.login()
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"Message: {message}")
    
    # Restore URL
    bad_auth.base_url = original_url
    
    # Test with invalid credentials (if safe to do so)
    if input("\nTest with invalid credentials? (y/n): ").lower() == 'y':
        original_password = bad_auth.password
        bad_auth.password = "invalid_password"
        
        success, message = bad_auth.login()
        print(f"Result: {'SUCCESS' if success else 'FAILED'}")
        print(f"Message: {message}")
        
        # Restore password
        bad_auth.password = original_password


def main():
    """Run all tests."""
    print("\nIMS Authentication Service Test Suite")
    print("=====================================")
    
    # Check if credentials are configured
    auth_service = get_auth_service()
    if not auth_service.username or not auth_service.password:
        print("\nERROR: IMS credentials not configured!")
        print("Please set IMS_ONE_USERNAME and IMS_ONE_PASSWORD in your .env file")
        return 1
    
    # Run tests
    tests = [
        ("Basic Login", test_login),
        ("Token Management", test_token_management),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if test_name == "Token Management":
                # Skip if login failed
                if results and not results[0][1]:
                    print(f"\nSkipping {test_name} - login failed")
                    results.append((test_name, False, "Skipped"))
                    continue
            
            if test_name == "Error Handling":
                # Optional test
                if input(f"\nRun {test_name} test? (y/n): ").lower() != 'y':
                    results.append((test_name, False, "Skipped"))
                    continue
            
            test_func()
            results.append((test_name, True, "Passed"))
        except Exception as e:
            logger.exception(f"Test {test_name} failed with exception")
            results.append((test_name, False, f"Exception: {str(e)}"))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, passed, status in results:
        print(f"{test_name}: {status}")
    
    # Overall result
    failed = sum(1 for _, passed, status in results if not passed and status != "Skipped")
    if failed == 0:
        print("\nAll tests passed!")
        return 0
    else:
        print(f"\n{failed} test(s) failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())