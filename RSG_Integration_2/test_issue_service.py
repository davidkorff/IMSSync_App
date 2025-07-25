#!/usr/bin/env python3
"""
Test script for issue service.
Tests the IssuePolicy functionality.
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

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

# Import services
from app.services.ims.auth_service import get_auth_service
from app.services.ims.issue_service import get_issue_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_issue_policy():
    """Test issuing a policy."""
    print("\n" + "="*60)
    print("Testing Issue Policy")
    print("="*60)
    
    # Get quote GUID from user
    quote_guid = input("\nEnter Quote GUID to issue: ").strip()
    if not quote_guid:
        print("No Quote GUID provided - skipping test")
        return False
    
    # Authenticate first
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"\n✗ Authentication failed")
        print(f"Request: LoginIMSUser")
        print(f"Response: {auth_message}")
        return False
    
    # Issue the policy
    issue_service = get_issue_service()
    
    # Capture request data
    request_data = {
        "function": "IssuePolicy",
        "quote_guid": quote_guid
    }
    
    success, issue_date, message = issue_service.issue_policy(quote_guid)
    
    if success:
        # Success - show only extracted values
        print(f"\nAuthentication Token: {auth_service.token[:20]}...")
        print(f"Quote GUID: {quote_guid}")
        print(f"Issue Date: {issue_date}")
        print(f"Status: ISSUED")
    else:
        # Failure - show full request and response
        print(f"\n✗ Failed to issue policy")
        print(f"\nRequest Data:")
        print(json.dumps(request_data, indent=2))
        print(f"\nFull Response:")
        print(f"{message}")
    
    return success


def test_issue_with_payload():
    """Test issuing using TEST.json data."""
    print("\n" + "="*60)
    print("Testing Issue with Payload")
    print("="*60)
    
    # Load test payload
    try:
        with open('TEST.json', 'r') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"\n✗ Failed to load payload: {e}")
        return False
    
    # Only proceed if transaction type is 'issue'
    if payload.get('transaction_type', '').lower() != 'issue':
        print(f"\nSkipping - transaction type is '{payload.get('transaction_type')}', not 'issue'")
        return True
    
    print(f"\nPayload Information:")
    print(f"  Transaction Type: {payload.get('transaction_type')}")
    print(f"  Policy Number: {payload.get('policy_number')}")
    print(f"  Insured Name: {payload.get('insured_name')}")
    
    print("\nNote: For 'issue' transaction type, the system will:")
    print("  1. BIND the quote first to get policy number")
    print("  2. ISSUE the policy to get issue date")
    
    return True


def main():
    """Run issue tests."""
    # Check command line arguments (optional for this test)
    if len(sys.argv) > 2:
        print("Usage: python3 test_issue_service.py [json_file]")
        print("Example: python3 test_issue_service.py TEST.json")
        return 1
    
    json_file = sys.argv[1] if len(sys.argv) == 2 else None
    
    print("\nIMS Issue Service Test Suite")
    print("============================")
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
        ("Issue Policy", test_issue_policy),
        ("Issue with Payload", test_issue_with_payload)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if test_name == "Issue Policy":
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