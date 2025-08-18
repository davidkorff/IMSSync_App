#!/usr/bin/env python3
"""
Test the enhanced producer lookup with email and name fallback.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock dotenv if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.services.ims.data_access_service import get_data_access_service


def main():
    print("\n" + "="*60)
    print("Testing Producer Lookup with Email/Name Fallback")
    print("="*60)
    
    # Initialize service
    data_service = get_data_access_service()
    
    # Test cases
    test_cases = [
        {
            "producer_email": "CAFinver@Wholesure.com",
            "producer_name": "Mike Woodworth",
            "description": "Email doesn't exist, should fallback to name"
        },
        {
            "producer_email": "",
            "producer_name": "Mike Woodworth", 
            "description": "No email provided, should use name"
        },
        {
            "producer_email": "test@example.com",
            "producer_name": "",
            "description": "No name provided, should try email only"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['description']}")
        print("-" * 40)
        
        payload = {
            "producer_email": test_case["producer_email"],
            "producer_name": test_case["producer_name"]
        }
        
        print(f"Email: {test_case['producer_email'] or '(none)'}")
        print(f"Name: {test_case['producer_name'] or '(none)'}")
        
        success, producer_info, message = data_service.process_producer_from_payload(payload)
        
        if success:
            print(f"✓ Producer found!")
            print(f"  ProducerContactGUID: {producer_info.get('ProducerContactGUID')}")
            print(f"  ProducerLocationGUID: {producer_info.get('ProducerLocationGUID')}")
        else:
            print(f"✗ Producer not found")
            # Don't print full SOAP details, just the basic message
            if "No producer found" in message:
                print(f"  Message: {message.split('Request URL')[0].strip()}")
            else:
                print(f"  Message: {message[:200]}")
    
    print("\n" + "="*60)
    print("The fallback mechanism is now in place!")
    print("The stored procedure will:")
    print("1. First try to find producer by email (if provided)")
    print("2. If not found, fallback to name lookup (if provided)")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())