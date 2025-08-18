#!/usr/bin/env python3
"""
Test script for the new midterm endorsement flow using ProcessFlatEndorsement.
This script tests the complete flow from finding the latest quote to binding the endorsement.
"""

import json
import logging
from datetime import datetime
from app.services.transaction_handler import get_transaction_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_endorsement_flow():
    """Test the new endorsement flow with a sample payload."""
    
    # Sample endorsement payload
    payload = {
        "transaction_id": f"TEST_ENDT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "transaction_type": "midterm_endorsement",
        "opportunity_id": 12345,  # This should match an existing bound policy
        "policy_number": "TEST-POL-001",
        "insured_name": "Test Insured LLC",
        
        # Endorsement specific fields
        "midterm_endt_premium": 1500.00,  # Additional premium for endorsement
        "midterm_endt_effective_from": "2025-02-01",  # ISO format date
        "midterm_endt_description": "Adding additional coverage",
        
        # Alternative field names (fallback)
        "gross_premium": 1500.00,
        "transaction_date": "2025-02-01T00:00:00Z",
        
        # Other required fields
        "source_system": "triton",
        "producer_name": "Test Producer",
        "underwriter_name": "Test Underwriter"
    }
    
    logger.info("=" * 80)
    logger.info("TESTING NEW ENDORSEMENT FLOW")
    logger.info("=" * 80)
    logger.info(f"Test payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Get the transaction handler
        handler = get_transaction_handler()
        
        # Process the endorsement transaction
        logger.info("\nProcessing endorsement transaction...")
        success, results, message = handler.process_transaction(payload)
        
        # Display results
        logger.info("\n" + "=" * 80)
        logger.info("ENDORSEMENT RESULTS")
        logger.info("=" * 80)
        logger.info(f"Success: {success}")
        logger.info(f"Message: {message}")
        
        if results:
            logger.info("\nDetailed Results:")
            for key, value in results.items():
                if key != "invoice_data":  # Skip large invoice data for display
                    logger.info(f"  {key}: {value}")
            
            # Display key endorsement information
            if success:
                logger.info("\n" + "-" * 40)
                logger.info("KEY ENDORSEMENT INFORMATION:")
                logger.info("-" * 40)
                logger.info(f"Original Quote GUID: {results.get('original_quote_guid')}")
                logger.info(f"New Endorsement Quote GUID: {results.get('endorsement_quote_guid')}")
                logger.info(f"Control Number: {results.get('control_no')}")
                logger.info(f"Endorsement Number: {results.get('endorsement_number')}")
                logger.info(f"Original Premium: ${results.get('original_premium', 0):,.2f}")
                logger.info(f"Premium Change: ${results.get('premium_change', 0):,.2f}")
                logger.info(f"New Total Premium: ${results.get('new_total_premium', 0):,.2f}")
                logger.info(f"Endorsement Status: {results.get('endorsement_status')}")
                logger.info(f"Policy Number: {results.get('endorsement_policy_number')}")
                
                if results.get('invoice_data'):
                    logger.info("\n✓ Invoice data generated successfully")
        
        return success, results
        
    except Exception as e:
        logger.error(f"Error during endorsement test: {str(e)}", exc_info=True)
        return False, None

def test_with_custom_opportunity_id(opportunity_id):
    """Test with a specific opportunity_id provided by the user."""
    
    payload = {
        "transaction_id": f"TEST_ENDT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "transaction_type": "midterm_endorsement",
        "opportunity_id": opportunity_id,
        "policy_number": "TEST-POL-CUSTOM",
        "insured_name": "Custom Test Insured",
        
        # Endorsement details
        "midterm_endt_premium": 2000.00,
        "midterm_endt_effective_from": "2025-03-01",
        "midterm_endt_description": "Custom endorsement test",
        
        "source_system": "triton",
        "producer_name": "Test Producer",
        "underwriter_name": "Test Underwriter"
    }
    
    logger.info(f"\nTesting with opportunity_id: {opportunity_id}")
    
    handler = get_transaction_handler()
    success, results, message = handler.process_transaction(payload)
    
    if success:
        logger.info(f"✓ Endorsement successful! New Quote: {results.get('endorsement_quote_guid')}")
    else:
        logger.error(f"✗ Endorsement failed: {message}")
    
    return success, results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Use provided opportunity_id
        try:
            opp_id = int(sys.argv[1])
            logger.info(f"Using provided opportunity_id: {opp_id}")
            test_with_custom_opportunity_id(opp_id)
        except ValueError:
            logger.error("Please provide a valid integer opportunity_id")
            sys.exit(1)
    else:
        # Run default test
        logger.info("Running default endorsement test...")
        logger.info("To test with a specific opportunity_id, run: python test_endorsement_new_flow.py <opportunity_id>")
        test_endorsement_flow()