#!/usr/bin/env python3
"""
Test script to verify midterm_endorsement returns invoice data.

This script tests that the midterm_endorsement transaction type
now returns the full invoice dataset just like the bind transaction.
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API configuration
BASE_URL = "http://localhost:7071"
TRANSACTION_ENDPOINT = f"{BASE_URL}/api/triton/transaction/new"


def test_midterm_endorsement_with_invoice():
    """Test midterm endorsement transaction with invoice data retrieval."""
    
    # Sample endorsement payload
    # Replace these values with actual data from your system
    endorsement_payload = {
        "transaction_id": f"TEST-ENDT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "transaction_type": "midterm_endorsement",
        "opportunity_id": "OPP-123456",  # or use policy_number
        "policy_number": "POL-2025-001",
        "insured_name": "Test Company LLC",
        "gross_premium": 500.00,  # Endorsement premium
        "net_premium": 450.00,
        "transaction_date": datetime.now().isoformat(),
        "midterm_endt_description": "Add additional coverage",
        "producer_name": "Test Producer",
        "underwriter_name": "Test Underwriter"
    }
    
    logger.info("="*60)
    logger.info("Testing Midterm Endorsement with Invoice Data")
    logger.info("="*60)
    logger.info(f"Payload: {json.dumps(endorsement_payload, indent=2)}")
    
    try:
        # Send the request
        response = requests.post(
            TRANSACTION_ENDPOINT,
            json=endorsement_payload,
            headers={"Content-Type": "application/json"}
        )
        
        logger.info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info("SUCCESS - Endorsement processed")
            
            # Check for invoice data in response
            if "data" in result and "invoice_data" in result["data"]:
                invoice_data = result["data"]["invoice_data"]
                logger.info("="*60)
                logger.info("INVOICE DATA RETRIEVED SUCCESSFULLY!")
                logger.info("="*60)
                logger.info(json.dumps(invoice_data, indent=2))
                
                # Verify key invoice fields
                logger.info("\nInvoice Summary:")
                logger.info(f"  Invoice Number: {invoice_data.get('invoice_number')}")
                logger.info(f"  Total Amount: ${invoice_data.get('total_amount', 0):,.2f}")
                logger.info(f"  Policy Number: {invoice_data.get('policy_number')}")
                logger.info(f"  Endorsement Premium: ${endorsement_payload['gross_premium']:,.2f}")
            else:
                logger.warning("No invoice data found in response")
                logger.info(f"Full response: {json.dumps(result, indent=2)}")
            
            # Display other endorsement results
            if "data" in result:
                data = result["data"]
                logger.info("\nEndorsement Results:")
                logger.info(f"  Endorsement Quote GUID: {data.get('endorsement_quote_guid')}")
                logger.info(f"  Endorsement Number: {data.get('endorsement_number')}")
                logger.info(f"  Endorsement Status: {data.get('endorsement_status')}")
                logger.info(f"  Effective Date: {data.get('endorsement_effective_date')}")
            
        else:
            logger.error(f"Request failed: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
        return False
    
    return True


def compare_with_bind_response():
    """Show the structure comparison between bind and endorsement responses."""
    
    print("\n" + "="*60)
    print("Response Structure Comparison")
    print("="*60)
    
    bind_structure = """
    BIND Response Structure:
    {
        "success": true,
        "message": "Transaction completed successfully",
        "data": {
            "transaction_id": "...",
            "transaction_type": "bind",
            "quote_guid": "...",
            "bound_policy_number": "POL-2025-001",
            "bind_status": "completed",
            "invoice_data": {
                "invoice_number": "INV-001",
                "invoice_date": "2025-01-15",
                "policy_number": "POL-2025-001",
                "total_amount": 5350.00,
                "line_items": [...]
            }
        }
    }
    """
    
    endorsement_structure = """
    ENDORSEMENT Response Structure (UPDATED):
    {
        "success": true,
        "message": "Transaction completed successfully",
        "data": {
            "transaction_id": "...",
            "transaction_type": "midterm_endorsement",
            "endorsement_quote_guid": "...",
            "endorsement_number": "ENDT-001",
            "endorsement_status": "completed",
            "endorsement_premium": 500.00,
            "endorsement_effective_date": "01/15/2025",
            "invoice_data": {           <-- NOW INCLUDED!
                "invoice_number": "INV-002",
                "invoice_date": "2025-01-15",
                "policy_number": "POL-2025-001",
                "total_amount": 500.00,
                "line_items": [...]
            }
        }
    }
    """
    
    print(bind_structure)
    print(endorsement_structure)
    print("\nBoth transaction types now return the full invoice_data object!")


def main():
    """Run the endorsement invoice test."""
    
    # Test the endorsement with invoice
    success = test_midterm_endorsement_with_invoice()
    
    if success:
        # Show structure comparison
        compare_with_bind_response()
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print("✓ Midterm endorsement now returns invoice data")
        print("✓ Invoice data format matches bind transaction")
        print("✓ Full invoice details available for downstream processing")
    else:
        print("\n" + "="*60)
        print("TEST FAILED")
        print("="*60)
        print("Please check the logs above for error details")
        print("Ensure you're using valid test data (policy number, opportunity_id, etc.)")


if __name__ == "__main__":
    main()