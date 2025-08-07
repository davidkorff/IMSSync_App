#!/usr/bin/env python3
"""
Test script for midterm cancellation functionality.
Tests the cancellation transaction routing and processing.
"""

import asyncio
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from app.services.transaction_handler import get_transaction_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_payload(json_file: str = None) -> Dict[str, Any]:
    """Load test payload from JSON file or create default."""
    if json_file and Path(json_file).exists():
        logger.info(f"Loading test payload from {json_file}")
        with open(json_file, 'r') as f:
            payload = json.load(f)
    else:
        # Default test payload for cancellation
        payload = {
            "transaction_id": f"CANC_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "transaction_type": "cancellation",
            "transaction_date": datetime.now().isoformat(),
            "opportunity_id": 12346,  # Use an existing bound policy's opportunity_id
            "policy_number": "RSG-2025-001",
            
            # Cancellation specific fields
            "cancellation_type": "flat",  # "flat" for full refund or "earned" for pro-rata
            "cancellation_reason_code": 30,  # Insured Request
            "cancellation_reason": "Test cancellation - insured request",
            "refund_amount": 5000.00,
            
            # Basic insured info (for logging/tracking)
            "insured_name": "Test Company LLC",
            "insured_state": "CA",
            "insured_zip": "90210",
            
            # Producer info
            "producer_name": "Test Producer",
            
            # Underwriter info
            "underwriter_name": "Test Underwriter",
            
            # Program info
            "program_name": "Test Program",
            "class_of_business": "General Liability",
            
            # Premium info (for tracking/audit)
            "gross_premium": -5000.00,  # Negative for refund
            "net_premium": -4500.00,
            "agency_commission": -500.00
        }
        
        logger.info("Using default test cancellation payload")
    
    return payload


async def test_cancellation(json_file: str = None):
    """Test the cancellation functionality."""
    try:
        # Load test payload
        payload = load_test_payload(json_file)
        
        logger.info("="*80)
        logger.info("CANCELLATION TEST")
        logger.info("="*80)
        logger.info(f"Transaction ID: {payload['transaction_id']}")
        logger.info(f"Opportunity ID: {payload.get('opportunity_id')}")
        logger.info(f"Policy Number: {payload.get('policy_number')}")
        logger.info(f"Cancellation Type: {payload.get('cancellation_type')}")
        logger.info(f"Refund Amount: ${payload.get('refund_amount', 0):,.2f}")
        
        # Initialize transaction handler
        transaction_handler = get_transaction_handler()
        
        # Process the cancellation transaction
        logger.info("\nProcessing cancellation transaction...")
        success, results, message = transaction_handler.process_transaction(payload)
        
        # Display results
        logger.info("="*80)
        if success:
            logger.info("✓ CANCELLATION SUCCESSFUL")
            logger.info(f"Message: {message}")
            
            if results.get("cancellation_quote_guid"):
                logger.info(f"Cancellation Quote GUID: {results['cancellation_quote_guid']}")
            if results.get("cancellation_type"):
                logger.info(f"Cancellation Type: {results['cancellation_type']}")
            if results.get("cancellation_effective_date"):
                logger.info(f"Effective Date: {results['cancellation_effective_date']}")
            if results.get("refund_amount"):
                logger.info(f"Refund Amount: ${abs(float(results['refund_amount'])):,.2f}")
            if results.get("policy_number"):
                logger.info(f"Policy Number: {results['policy_number']}")
            
            # Display full results for debugging
            logger.info("\nFull Results:")
            logger.info(json.dumps(results, indent=2, default=str))
        else:
            logger.error("✗ CANCELLATION FAILED")
            logger.error(f"Error: {message}")
            if results:
                logger.error(f"Results: {json.dumps(results, indent=2, default=str)}")
        
        logger.info("="*80)
        
        return success, results, message
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        return False, {}, str(e)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Test midterm cancellation functionality')
    parser.add_argument(
        '--json',
        type=str,
        help='Path to JSON file containing test payload',
        default=None
    )
    
    args = parser.parse_args()
    
    # Run the test
    success, results, message = asyncio.run(test_cancellation(args.json))
    
    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()