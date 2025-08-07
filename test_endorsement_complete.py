#!/usr/bin/env python3
"""
Test script to verify the complete midterm endorsement flow.

This tests that endorsements now:
1. Create the endorsement quote via stored procedure
2. Create/verify quote option exists
3. Process the payload to register data
4. Actually bind the endorsement through IMS
5. Retrieve invoice data
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


def test_complete_endorsement_flow():
    """Test the complete endorsement flow with all steps."""
    
    # Sample endorsement payload
    endorsement_payload = {
        "transaction_id": f"TEST-ENDT-COMPLETE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "transaction_type": "midterm_endorsement",
        "opportunity_id": "OPP-123456",  # Replace with actual opportunity ID
        "policy_number": "POL-2025-001",  # Replace with actual policy number
        "insured_name": "Test Company LLC",
        "gross_premium": 750.00,  # Endorsement premium
        "net_premium": 675.00,
        "transaction_date": datetime.now().isoformat(),
        "midterm_endt_description": "Add additional insured and increase limits",
        "producer_name": "Test Producer",
        "underwriter_name": "Test Underwriter"
    }
    
    logger.info("="*70)
    logger.info("Testing Complete Midterm Endorsement Flow")
    logger.info("="*70)
    logger.info(f"Transaction ID: {endorsement_payload['transaction_id']}")
    logger.info(f"Policy Number: {endorsement_payload['policy_number']}")
    logger.info(f"Endorsement Premium: ${endorsement_payload['gross_premium']:,.2f}")
    
    try:
        # Send the endorsement request
        logger.info("\nSending endorsement request...")
        response = requests.post(
            TRANSACTION_ENDPOINT,
            json=endorsement_payload,
            headers={"Content-Type": "application/json"}
        )
        
        logger.info(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            data = result.get("data", {})
            
            logger.info("\n" + "="*70)
            logger.info("ENDORSEMENT PROCESSING RESULTS")
            logger.info("="*70)
            
            # Check each step of the process
            steps_verified = []
            
            # 1. Endorsement Quote Created
            if data.get("endorsement_quote_guid"):
                logger.info("✅ Step 1: Endorsement quote created")
                logger.info(f"   Quote GUID: {data['endorsement_quote_guid']}")
                steps_verified.append("quote_created")
            else:
                logger.error("❌ Step 1: No endorsement quote GUID")
            
            # 2. Quote Option Created/Verified
            if data.get("endorsement_quote_option_guid"):
                logger.info("✅ Step 2: Quote option created/verified")
                logger.info(f"   Option GUID: {data['endorsement_quote_option_guid']}")
                steps_verified.append("option_created")
            else:
                logger.error("❌ Step 2: No quote option GUID")
            
            # 3. Endorsement Number Assigned
            if data.get("endorsement_number"):
                logger.info("✅ Step 3: Endorsement number assigned")
                logger.info(f"   Endorsement #: {data['endorsement_number']}")
                steps_verified.append("number_assigned")
            else:
                logger.warning("⚠️  Step 3: No endorsement number")
            
            # 4. Endorsement Bound
            if data.get("endorsement_status") == "completed":
                logger.info("✅ Step 4: Endorsement successfully bound")
                if data.get("endorsement_policy_number"):
                    logger.info(f"   Policy Number: {data['endorsement_policy_number']}")
                steps_verified.append("bound")
            else:
                logger.error(f"❌ Step 4: Endorsement not bound - Status: {data.get('endorsement_status')}")
            
            # 5. Invoice Data Retrieved
            if data.get("invoice_data"):
                invoice = data["invoice_data"]
                logger.info("✅ Step 5: Invoice data retrieved")
                logger.info(f"   Invoice Number: {invoice.get('invoice_number')}")
                logger.info(f"   Total Amount: ${invoice.get('total_amount', 0):,.2f}")
                steps_verified.append("invoice_retrieved")
                
                # Display invoice details
                logger.info("\n" + "="*70)
                logger.info("INVOICE DETAILS")
                logger.info("="*70)
                logger.info(json.dumps(invoice, indent=2))
            else:
                logger.warning("⚠️  Step 5: No invoice data in response")
            
            # Summary
            logger.info("\n" + "="*70)
            logger.info("FLOW VERIFICATION SUMMARY")
            logger.info("="*70)
            
            expected_steps = ["quote_created", "option_created", "number_assigned", "bound", "invoice_retrieved"]
            all_steps_passed = all(step in steps_verified for step in expected_steps)
            
            if all_steps_passed:
                logger.info("✅ ALL STEPS COMPLETED SUCCESSFULLY!")
                logger.info("The endorsement flow is working correctly:")
                logger.info("  1. Created endorsement quote")
                logger.info("  2. Created/verified quote option")
                logger.info("  3. Assigned endorsement number")
                logger.info("  4. Bound the endorsement")
                logger.info("  5. Retrieved invoice data")
            else:
                missing_steps = [s for s in expected_steps if s not in steps_verified]
                logger.warning(f"⚠️  Some steps were not completed: {missing_steps}")
            
            # Display full response for debugging
            logger.info("\n" + "="*70)
            logger.info("FULL RESPONSE DATA")
            logger.info("="*70)
            logger.info(json.dumps(data, indent=2))
            
            return all_steps_passed
            
        else:
            logger.error(f"Request failed with status {response.status_code}")
            logger.error(f"Error: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        return False


def main():
    """Run the complete endorsement flow test."""
    
    print("\n" + "="*70)
    print("MIDTERM ENDORSEMENT COMPLETE FLOW TEST")
    print("="*70)
    print("\nThis test verifies that endorsements now:")
    print("1. Create the endorsement quote")
    print("2. Create/verify quote option")
    print("3. Process payload data")
    print("4. Actually bind through IMS")
    print("5. Retrieve invoice data")
    print("="*70)
    
    success = test_complete_endorsement_flow()
    
    if success:
        print("\n" + "="*70)
        print("TEST PASSED ✅")
        print("="*70)
        print("The midterm endorsement flow is now complete and matches the bind flow!")
    else:
        print("\n" + "="*70)
        print("TEST FAILED ❌")
        print("="*70)
        print("Please check the logs above for details.")
        print("\nMake sure to use valid test data:")
        print("- A valid opportunity_id or policy_number for an existing bound policy")
        print("- The API server is running")


if __name__ == "__main__":
    main()