#!/usr/bin/env python3
"""
Test script for producer validation during midterm endorsements.

This script tests the new producer validation logic that:
1. Creates an endorsement quote
2. Checks the producer from tblQuotes
3. Compares with the producer from the payload
4. Changes producer if needed using spChangeProducer_Triton
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from app.services.transaction_handler import get_transaction_handler
from app.services.ims.data_access_service import get_data_access_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_endorsement_payload(
    opportunity_id: int,
    policy_number: str,
    producer_email: str = None,
    producer_name: str = None,
    endorsement_premium: float = 100.0
) -> Dict[str, Any]:
    """Create a test midterm endorsement payload with specific producer info."""
    
    effective_date = datetime.now()
    expiration_date = effective_date + timedelta(days=365)
    endorsement_date = effective_date + timedelta(days=90)  # 90 days into policy
    
    payload = {
        "transaction_id": f"TEST_ENDT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "transaction_type": "midterm_endorsement",
        "transaction_date": endorsement_date.isoformat(),
        "opportunity_id": opportunity_id,
        "option_id": opportunity_id,  # Same as opportunity_id in this context
        "policy_number": policy_number,
        
        # Endorsement specific fields
        "midterm_endt_id": f"ENDT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "midterm_endt_premium": endorsement_premium,
        "midterm_endt_effective_from": endorsement_date.isoformat(),
        "midterm_endt_description": "Test Producer Validation Endorsement",
        
        # Producer information - this is what will be validated
        "producer_email": producer_email or "test.producer@example.com",
        "producer_name": producer_name or "Test Producer",
        
        # Other required fields
        "insured_name": "Test Insured Company",
        "gross_premium": endorsement_premium,
        "net_premium": endorsement_premium * 0.9,
        "effective_date": effective_date.isoformat(),
        "expiration_date": expiration_date.isoformat(),
        "market_segment_code": "RT",
        "policy_status": "Active"
    }
    
    return payload


def test_producer_validation():
    """Test the producer validation during midterm endorsement."""
    
    logger.info("=" * 80)
    logger.info("Testing Producer Validation for Midterm Endorsements")
    logger.info("=" * 80)
    
    # Initialize services
    handler = get_transaction_handler()
    data_service = get_data_access_service()
    
    # Test Case 1: Endorsement with SAME producer
    logger.info("\n" + "=" * 60)
    logger.info("TEST CASE 1: Endorsement with SAME producer")
    logger.info("=" * 60)
    
    # You'll need to update these with actual values from your test environment
    opportunity_id_1 = 12345  # Replace with actual opportunity_id
    policy_number_1 = "TEST-POL-001"  # Replace with actual policy number
    existing_producer_email = "existing.producer@example.com"  # Replace with actual producer email
    
    payload_1 = create_test_endorsement_payload(
        opportunity_id=opportunity_id_1,
        policy_number=policy_number_1,
        producer_email=existing_producer_email,
        endorsement_premium=500.0
    )
    
    logger.info(f"Testing with opportunity_id: {opportunity_id_1}")
    logger.info(f"Producer email: {existing_producer_email}")
    
    # Process the transaction
    success, results, message = handler.process_transaction(payload_1)
    
    if success:
        logger.info(f"✓ Test Case 1 PASSED: {message}")
        if results.get("producer_validated"):
            logger.info("  - Producer matched, no change was needed")
        logger.info(f"  - Endorsement Quote: {results.get('endorsement_quote_guid')}")
        logger.info(f"  - Endorsement Number: {results.get('endorsement_number')}")
    else:
        logger.error(f"✗ Test Case 1 FAILED: {message}")
    
    # Test Case 2: Endorsement with DIFFERENT producer
    logger.info("\n" + "=" * 60)
    logger.info("TEST CASE 2: Endorsement with DIFFERENT producer")
    logger.info("=" * 60)
    
    opportunity_id_2 = 12346  # Replace with actual opportunity_id
    policy_number_2 = "TEST-POL-002"  # Replace with actual policy number
    new_producer_email = "new.producer@example.com"  # Replace with different producer email
    
    payload_2 = create_test_endorsement_payload(
        opportunity_id=opportunity_id_2,
        policy_number=policy_number_2,
        producer_email=new_producer_email,
        endorsement_premium=750.0
    )
    
    logger.info(f"Testing with opportunity_id: {opportunity_id_2}")
    logger.info(f"New producer email: {new_producer_email}")
    
    # Process the transaction
    success, results, message = handler.process_transaction(payload_2)
    
    if success:
        logger.info(f"✓ Test Case 2 PASSED: {message}")
        if results.get("producer_changed"):
            logger.info("  - Producer was changed successfully")
            logger.info(f"    Old Producer: {results.get('old_producer_guid')}")
            logger.info(f"    New Producer: {results.get('new_producer_guid')}")
        logger.info(f"  - Endorsement Quote: {results.get('endorsement_quote_guid')}")
        logger.info(f"  - Endorsement Number: {results.get('endorsement_number')}")
    else:
        logger.error(f"✗ Test Case 2 FAILED: {message}")
    
    # Test Case 3: Test direct producer lookup and change
    logger.info("\n" + "=" * 60)
    logger.info("TEST CASE 3: Direct Producer Validation Test")
    logger.info("=" * 60)
    
    test_quote_guid = "00000000-0000-0000-0000-000000000000"  # Replace with actual test quote
    
    # Test getting producer from quote
    logger.info(f"Testing get_quote_producer_contact_guid for quote: {test_quote_guid}")
    success, producer_guid, message = data_service.get_quote_producer_contact_guid(test_quote_guid)
    
    if success and producer_guid:
        logger.info(f"✓ Retrieved producer: {producer_guid}")
        
        # Test changing producer (if you have a different producer GUID to test with)
        new_test_producer = "00000000-0000-0000-0000-000000000001"  # Replace with actual producer GUID
        if new_test_producer != producer_guid:
            logger.info(f"Testing change_producer to: {new_test_producer}")
            success, message = data_service.change_producer(test_quote_guid, new_test_producer)
            if success:
                logger.info(f"✓ Producer changed successfully")
            else:
                logger.error(f"✗ Failed to change producer: {message}")
    else:
        logger.warning(f"Could not retrieve producer: {message}")
    
    logger.info("\n" + "=" * 80)
    logger.info("Producer Validation Testing Complete")
    logger.info("=" * 80)


if __name__ == "__main__":
    test_producer_validation()