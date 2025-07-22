#!/usr/bin/env python3
"""
Test script for bind service.
Tests the BindQuote functionality.
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the dotenv module
class MockDotenv:
    def load_dotenv(self):
        pass

sys.modules['dotenv'] = MockDotenv()

# Import services
from app.services.ims.auth_service import get_auth_service
from app.services.ims.bind_service import get_bind_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_bind_quote():
    """Test binding a quote."""
    print("\n" + "="*60)
    print("Testing Bind Quote")
    print("="*60)
    
    # Get quote GUID from user
    quote_guid = input("\nEnter Quote GUID to bind: ").strip()
    if not quote_guid:
        print("No Quote GUID provided - skipping test")
        return False
    
    # Authenticate first
    print("\nAuthenticating...")
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"✗ Authentication failed: {auth_message}")
        return False
    
    print("✓ Authenticated successfully")
    
    # Bind the quote
    print(f"\nBinding quote: {quote_guid}")
    bind_service = get_bind_service()
    success, policy_number, message = bind_service.bind_quote(quote_guid)
    
    if success:
        print(f"\n✓ Quote bound successfully!")
        print(f"  Policy Number: {policy_number}")
        print(f"  Message: {message}")
        return True
    else:
        print(f"\n✗ Failed to bind quote")
        print(f"  Message: {message}")
        return False


def test_complete_workflow_with_bind():
    """Test complete workflow including binding."""
    print("\n" + "="*60)
    print("Testing Complete Workflow with Bind")
    print("="*60)
    
    # This would be similar to test_complete_payload_processing
    # but would add binding as the final step
    print("\nThis test would:")
    print("1. Create insured")
    print("2. Find producer and underwriter")
    print("3. Create quote")
    print("4. Add quote options")
    print("5. Process payload (store data, update policy number, register premium)")
    print("6. Bind the quote to get final policy number")
    
    print("\nTo run the complete workflow, use test_payload_processing.py")
    print("and then run this script to bind the resulting quote.")
    
    return True


def main():
    """Run bind tests."""
    # Check command line arguments (optional for this test)
    if len(sys.argv) > 2:
        print("Usage: python3 test_bind_service.py [json_file]")
        print("Example: python3 test_bind_service.py TEST.json")
        return 1
    
    json_file = sys.argv[1] if len(sys.argv) == 2 else None
    
    print("\nIMS Bind Service Test Suite")
    print("===========================")
    if json_file:
        print(f"Using payload file: {json_file}")
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please ensure .env file exists with:")
        print("  IMS_ONE_USERNAME=your_username")
        print("  IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Run tests
    tests = [
        ("Bind Quote", test_bind_quote),
        ("Complete Workflow Info", test_complete_workflow_with_bind)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if test_name == "Bind Quote":
                # Optional test
                response = input(f"\nRun {test_name} test? (y/n): ")
                if response.lower() != 'y':
                    results.append((test_name, True, "Skipped"))
                    continue
            
            print(f"\nRunning: {test_name}")
            success = test_func()
            results.append((test_name, success, "Passed" if success else "Failed"))
        except Exception as e:
            logger.exception(f"Test {test_name} failed with exception")
            results.append((test_name, False, f"Exception: {str(e)}"))
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, success, status in results:
        print(f"{test_name}: {status}")
    
    # Overall result
    failed = sum(1 for _, success, status in results if not success and status != "Skipped")
    if failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())