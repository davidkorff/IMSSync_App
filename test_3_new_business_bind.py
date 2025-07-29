"""
Test 3: New Business Bind Workflow
Tests the complete workflow for binding a new business policy
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_bind_workflow_base import *
from app.services.transaction_handler import get_transaction_handler
import json

def test_new_business_bind():
    """Test complete new business bind workflow"""
    test_result = TestResult("new_business_bind")
    handler = get_transaction_handler()
    
    try:
        # Step 1: Create new business payload
        log_test_step("Create new business bind payload")
        payload = create_test_payload(
            transaction_type="bind",
            opportunity_id=999002,  # New unique opportunity_id
            policy_number="TST999002",
            opportunity_type="new"  # Explicitly set as new business
        )
        
        # Add any additional fields needed
        payload.update({
            "umr": "TEST/UMR/999002",
            "agreement_number": "TEST-AGREE-001",
            "section_number": "001",
            "policy_fee": 250.00,
            "invoice_date": datetime.now().strftime("%m/%d/%Y")
        })
        
        test_result.add_step("Create payload", True, {
            "transaction_id": payload["transaction_id"],
            "opportunity_id": payload["opportunity_id"],
            "opportunity_type": payload["opportunity_type"]
        })
        
        logger.info(f"Testing new business bind with:")
        logger.info(f"  Transaction ID: {payload['transaction_id']}")
        logger.info(f"  Opportunity ID: {payload['opportunity_id']}")
        logger.info(f"  Policy Number: {payload['policy_number']}")
        
        # Step 2: Process the transaction
        log_test_step("Process new business bind transaction", {
            "handler": "TransactionHandler.process_transaction"
        })
        
        # Log the full payload being sent
        logger.debug(f"Full payload:\n{json.dumps(payload, indent=2)}")
        
        # Process the transaction
        success, results, message = handler.process_transaction(payload)
        
        # Log complete results
        log_test_step("Transaction results", {
            "success": success,
            "message": message,
            "results": results
        })
        
        test_result.add_step("Process transaction", success, {
            "message": message,
            "results": results
        }, None if success else message)
        
        # Step 3: Validate results
        if success:
            # Check that all required GUIDs were created
            required_results = [
                ("insured_guid", "Insured GUID"),
                ("producer_contact_guid", "Producer Contact GUID"),
                ("producer_location_guid", "Producer Location GUID"),
                ("underwriter_guid", "Underwriter GUID"),
                ("quote_guid", "Quote GUID"),
                ("quote_option_guid", "Quote Option GUID")
            ]
            
            for field, name in required_results:
                if field in results and results[field]:
                    test_result.add_step(f"Validate {name}", True, {field: results[field]})
                    logger.info(f"✓ {name}: {results[field]}")
                else:
                    test_result.add_step(f"Validate {name}", False, results, f"{name} not found in results")
                    logger.error(f"✗ {name} missing from results")
            
            # Check bind-specific results
            if results.get("bind_status") == "completed":
                bound_policy = results.get("bound_policy_number")
                if bound_policy:
                    test_result.add_step("Validate bind", True, {"bound_policy_number": bound_policy})
                    logger.info(f"✓ Policy bound successfully: {bound_policy}")
                else:
                    test_result.add_step("Validate bind", False, results, "No bound policy number returned")
            else:
                test_result.add_step("Validate bind", False, results, 
                                   f"Bind status: {results.get('bind_status', 'unknown')}")
        
        # Step 4: Verify data was stored correctly
        if success and results.get("quote_guid"):
            log_test_step("Verify data storage")
            
            # Check if quote was stored in tblTritonQuoteData
            from app.services.ims.data_access_service import get_data_access_service
            data_service = get_data_access_service()
            
            # Get quote by opportunity_id to verify storage
            verify_success, verify_xml, verify_msg = data_service.execute_dataset(
                "spGetQuoteByOpportunityID",
                ["OpportunityID", str(payload["opportunity_id"])]
            )
            
            if verify_success and verify_xml:
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(verify_xml)
                    table = root.find('.//Table')
                    if table:
                        stored_data = {elem.tag: elem.text for elem in table}
                        test_result.add_step("Verify storage", True, stored_data)
                        logger.info("✓ Quote data successfully stored in tblTritonQuoteData")
                        logger.info(f"  Stored Quote GUID: {stored_data.get('QuoteGuid')}")
                        logger.info(f"  Stored Policy Number: {stored_data.get('policy_number')}")
                    else:
                        test_result.add_step("Verify storage", False, None, "Quote not found in database")
                except Exception as e:
                    test_result.add_step("Verify storage", False, None, f"Parse error: {str(e)}")
            else:
                test_result.add_step("Verify storage", False, None, verify_msg)
        
        # Step 5: Test error handling - duplicate bind attempt
        if success:
            log_test_step("Test duplicate bind prevention")
            
            # Try to bind the same opportunity_id again
            success2, results2, message2 = handler.process_transaction(payload)
            
            if not success2 and "already bound" in message2.lower():
                test_result.add_step("Duplicate bind prevention", True, {
                    "message": message2,
                    "prevented": True
                })
                logger.info("✓ Duplicate bind correctly prevented")
            else:
                test_result.add_step("Duplicate bind prevention", False, 
                                   {"success": success2, "message": message2},
                                   "Duplicate bind was not prevented")
        
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
        test_result.add_step("Exception", False, None, str(e))
    
    # Save results
    summary = test_result.get_summary()
    save_test_results("new_business_bind", summary)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY: {test_result.test_name}")
    print(f"{'='*60}")
    print(f"Success: {test_result.success}")
    print(f"Total Steps: {summary['total_steps']}")
    print(f"Failed Steps: {summary['failed_steps']}")
    if test_result.errors:
        print("\nErrors:")
        for error in test_result.errors:
            print(f"  - {error}")
    print(f"{'='*60}\n")
    
    return test_result

if __name__ == "__main__":
    test_new_business_bind()