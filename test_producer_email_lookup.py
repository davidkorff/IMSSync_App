#!/usr/bin/env python3
"""
Test script for the new producer email lookup functionality.
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.services.ims.auth_service import get_auth_service
from app.services.ims.data_access_service import get_data_access_service


def test_producer_email_lookup():
    """Test the new producer email lookup."""
    print("\nTesting Producer Email Lookup")
    print("=" * 60)
    
    # Load test payload
    with open('test_new_business.json', 'r') as f:
        payload = json.load(f)
    
    # Authenticate
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"✗ Authentication failed: {auth_message}")
        return False
    
    print(f"✓ Authenticated successfully")
    
    # Test the new email lookup
    data_service = get_data_access_service()
    
    producer_email = payload.get('producer_email')
    if not producer_email:
        print("✗ No producer_email field in test payload")
        return False
    
    print(f"\nLooking up producer with email: {producer_email}")
    
    # Use the new method
    success, producer_info, message = data_service.get_producer_by_email(producer_email)
    
    if success and producer_info:
        print(f"\n✓ Producer found!")
        print(f"  ProducerContactGUID: {producer_info.get('ProducerContactGUID')}")
        print(f"  ProducerLocationGUID: {producer_info.get('ProducerLocationGUID')}")
        return True
    else:
        print(f"\n✗ Producer lookup failed: {message}")
        return False


def test_process_payload():
    """Test the process_producer_from_payload method."""
    print("\n\nTesting Process Producer From Payload")
    print("=" * 60)
    
    # Load test payload
    with open('test_new_business.json', 'r') as f:
        payload = json.load(f)
    
    # Authenticate
    auth_service = get_auth_service()
    auth_success, auth_message = auth_service.login()
    
    if not auth_success:
        print(f"✗ Authentication failed: {auth_message}")
        return False
    
    # Test the payload processor
    data_service = get_data_access_service()
    
    success, producer_info, message = data_service.process_producer_from_payload(payload)
    
    if success and producer_info:
        print(f"\n✓ Producer found via payload processor!")
        print(f"  ProducerContactGUID: {producer_info.get('ProducerContactGUID')}")
        print(f"  ProducerLocationGUID: {producer_info.get('ProducerLocationGUID')}")
        return True
    else:
        print(f"\n✗ Producer lookup failed: {message}")
        return False


def main():
    """Run tests."""
    print("\n" + "="*60)
    print("Producer Email Lookup Test")
    print("="*60)
    
    # Check credentials
    if not os.getenv("IMS_ONE_USERNAME") or not os.getenv("IMS_ONE_PASSWORD"):
        print("\nERROR: IMS credentials not set!")
        print("Please set environment variables:")
        print("  export IMS_ONE_USERNAME=your_username")
        print("  export IMS_ONE_PASSWORD=your_encrypted_password")
        return 1
    
    # Run both tests
    test1 = test_producer_email_lookup()
    test2 = test_process_payload()
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Direct email lookup: {'✓ PASSED' if test1 else '✗ FAILED'}")
    print(f"Payload processor: {'✓ PASSED' if test2 else '✗ FAILED'}")
    
    return 0 if (test1 and test2) else 1


if __name__ == "__main__":
    sys.exit(main())