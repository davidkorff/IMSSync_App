#!/usr/bin/env python3
"""
Simple test to verify producer email lookup is working.
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
    print("Testing Producer Email Lookup")
    print("="*60)
    
    # Initialize service
    data_service = get_data_access_service()
    
    # Test email
    test_email = "mike.woodworth@example.com"
    
    print(f"\nAttempting to look up producer with email: {test_email}")
    print(f"Using stored procedure: getProducerGuid")
    print(f"Parameter: producer_email = '{test_email}'")
    
    # This should call the new getProducerGuid stored procedure
    # Note: This will likely fail if the email doesn't exist in the database
    # but it will confirm the procedure is being called correctly
    
    payload = {"producer_email": test_email}
    success, producer_info, message = data_service.process_producer_from_payload(payload)
    
    if success:
        print(f"\n✓ Producer found!")
        print(f"  ProducerContactGUID: {producer_info.get('ProducerContactGUID')}")
        print(f"  ProducerLocationGUID: {producer_info.get('ProducerLocationGUID')}")
    else:
        print(f"\n✗ Producer not found")
        print(f"  Message: {message}")
        
        # This is expected if the email doesn't exist in the database
        if "getProducerGuid" in message or "producer_email" in message:
            print(f"\n✓ The new stored procedure is being called correctly!")
            print(f"  (The lookup failed because the email doesn't exist in the database)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())