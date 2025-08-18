#!/usr/bin/env python3
"""
Test script to verify midterm endorsement with premium application.
This script tests the complete workflow to ensure premium is properly applied.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.transaction_handler import TransactionHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_midterm_endorsement_with_premium():
    """Test midterm endorsement with premium to ensure it's properly applied."""
    
    # Create the test payload with a non-zero premium
    test_payload = {
        "transaction_id": f"TEST_ENDT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "transaction_type": "midterm_endorsement",
        "transaction_date": datetime.now().isoformat(),
        "opportunity_id": "300001",  # Use a valid opportunity_id from your test data
        "policy_number": "TST-2025-001",  # Use a valid bound policy number
        "gross_premium": 1500.00,  # Non-zero premium for the endorsement
        "midterm_endt_description": "Test Endorsement with Premium",
        "midterm_endt_effective_from": datetime.now().strftime("%Y-%m-%d"),
        "insured_name": "Test Insured",
        "producer_name": "Test Producer",
        "underwriter_name": "Test Underwriter",
        "program_name": "Test Program",
        "class_of_business": "GL",
        "effective_date": "2025-08-01",
        "expiration_date": "2026-08-01",
        "insured_state": "CA",
        "insured_zip": "90210"
    }
    
    logger.info("=" * 80)
    logger.info("MIDTERM ENDORSEMENT WITH PREMIUM TEST")
    logger.info("=" * 80)
    logger.info(f"Test Payload: {json.dumps(test_payload, indent=2)}")
    
    # Initialize the transaction handler
    handler = TransactionHandler()
    
    # Process the transaction
    logger.info("\nProcessing midterm endorsement transaction...")
    success, results, message = handler.process_transaction(test_payload)
    
    # Output results
    logger.info("\n" + "=" * 80)
    logger.info("TEST RESULTS")
    logger.info("=" * 80)
    logger.info(f"Success: {success}")
    logger.info(f"Message: {message}")
    logger.info(f"Results: {json.dumps(results, indent=2, default=str)}")
    
    # Verify premium was applied
    if success:
        endorsement_premium = results.get("endorsement_premium")
        if endorsement_premium and endorsement_premium > 0:
            logger.info(f"\n✓ Premium successfully applied: ${endorsement_premium}")
        else:
            logger.error(f"\n✗ Premium NOT applied. Expected: ${test_payload['gross_premium']}, Got: ${endorsement_premium}")
            
        # Check for QuoteOptionGuid
        quote_option_guid = results.get("endorsement_quote_option_guid")
        if quote_option_guid:
            logger.info(f"✓ QuoteOptionGuid created: {quote_option_guid}")
        else:
            logger.error("✗ QuoteOptionGuid NOT created")
            
        # Check for invoice data
        invoice_data = results.get("invoice_data")
        if invoice_data:
            logger.info(f"✓ Invoice data retrieved")
            if "Premiums" in invoice_data:
                logger.info(f"  Total Premiums: ${invoice_data.get('Premiums', {}).get('TotalPremium', 0)}")
        else:
            logger.warning("⚠ No invoice data retrieved")
    
    return success, results


def verify_premium_in_database(quote_option_guid):
    """
    Optional: Directly query the database to verify premium was inserted.
    This requires database access configuration.
    """
    try:
        from app.services.ims.data_access_service import get_data_access_service
        
        data_service = get_data_access_service()
        
        # Query to check premium
        query = f"""
        SELECT 
            qop.QuoteOptionGuid,
            qop.ChargeCode,
            qop.Premium,
            qop.AnnualPremium,
            qop.Added
        FROM tblQuoteOptionPremiums qop
        WHERE qop.QuoteOptionGuid = '{quote_option_guid}'
        """
        
        success, result, message = data_service.execute_dataset(
            procedure_name="sp_executesql",
            parameters=["@statement", query]
        )
        
        if success:
            logger.info(f"\nDatabase Verification - Premium Records:")
            logger.info(result)
        else:
            logger.error(f"Failed to verify premium in database: {message}")
            
    except Exception as e:
        logger.error(f"Error verifying premium in database: {str(e)}")


if __name__ == "__main__":
    try:
        # Run the test
        success, results = test_midterm_endorsement_with_premium()
        
        # Optional: Verify in database
        if success and results.get("endorsement_quote_option_guid"):
            verify_premium_in_database(results["endorsement_quote_option_guid"])
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        sys.exit(1)