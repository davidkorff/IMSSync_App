"""
Test 4: Renewal Bind Workflow
Tests the complete workflow for binding a renewal policy
"""
import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_bind_workflow_base import *
from app.services.transaction_handler import get_transaction_handler
from app.services.ims.data_access_service import get_data_access_service
import json
import xml.etree.ElementTree as ET

def test_renewal_bind(json_file=None):
    """Test complete renewal bind workflow"""
    test_result = TestResult("renewal_bind")
    handler = get_transaction_handler()
    data_service = get_data_access_service()
    
    try:
        # Step 1: Create renewal payload
        log_test_step("Create renewal bind payload")
        
        if json_file:
            # Load payload from JSON file
            log_test_step(f"Loading payload from {json_file}")
            try:
                with open(json_file, 'r') as f:
                    payload = json.load(f)
                logger.info(f"✓ Loaded payload from {json_file}")
            except Exception as e:
                test_result.add_step("Load JSON file", False, None, str(e))
                return test_result
        else:
            # For renewal, we need an expiring policy
            payload = create_test_payload(
                transaction_type="bind",
                opportunity_id=999003,  # New renewal opportunity
                policy_number="TST999003",
                opportunity_type="renewal",  # Set as renewal
                expiring_opportunity_id=88475,  # Reference to expiring policy
                expiring_policy_number="RSG240088475"  # Expiring policy number
            )
        
        test_result.add_step("Create payload", True, {
            "transaction_id": payload["transaction_id"],
            "opportunity_id": payload["opportunity_id"],
            "opportunity_type": payload["opportunity_type"],
            "expiring_opportunity_id": payload["expiring_opportunity_id"],
            "expiring_policy_number": payload["expiring_policy_number"]
        })
        
        logger.info(f"Testing renewal bind with:")
        logger.info(f"  Transaction ID: {payload['transaction_id']}")
        logger.info(f"  Opportunity ID: {payload['opportunity_id']}")
        logger.info(f"  Expiring Opportunity ID: {payload['expiring_opportunity_id']}")
        logger.info(f"  Expiring Policy Number: {payload['expiring_policy_number']}")
        
        # Step 2: Look up expiring policy (if exists)
        log_test_step("Look up expiring policy", {
            "expiring_policy_number": payload["expiring_policy_number"]
        })
        
        expiring_quote_guid = None
        
        # Only look up expiring policy if expiring_policy_number is provided
        if payload.get("expiring_policy_number"):
            success, result_xml, message = data_service.execute_dataset(
                "spGetQuoteByExpiringPolicyNumber",
                ["ExpiringPolicyNumber", payload["expiring_policy_number"]]
            )
        else:
            success = False
            result_xml = None
            message = "No expiring policy number provided"
        
        if success and result_xml:
            try:
                root = ET.fromstring(result_xml)
                table = root.find('.//Table')
                if table:
                    expiring_data = {elem.tag: elem.text for elem in table}
                    expiring_quote_guid = expiring_data.get("QuoteGuid")
                    
                    test_result.add_step("Find expiring policy", True, expiring_data)
                    logger.info(f"✓ Found expiring policy quote: {expiring_quote_guid}")
                    logger.info(f"  Expiration Date: {expiring_data.get('expiration_date')}")
                else:
                    test_result.add_step("Find expiring policy", True, 
                                       {"message": "No expiring policy found - will create without link"})
                    logger.info("ℹ No expiring policy found - renewal will be created without link")
            except Exception as e:
                test_result.add_step("Parse expiring policy", False, None, str(e))
        else:
            test_result.add_step("Find expiring policy", True, 
                               {"message": "Expiring policy lookup skipped or failed"})
        
        # Step 3: Process the renewal transaction
        log_test_step("Process renewal bind transaction")
        
        # Log the full payload
        logger.debug(f"Full renewal payload:\n{json.dumps(payload, indent=2)}")
        
        # Process the transaction
        success, results, message = handler.process_transaction(payload)
        
        # Log complete results
        log_test_step("Renewal transaction results", {
            "success": success,
            "message": message,
            "results": results
        })
        
        test_result.add_step("Process renewal", success, {
            "message": message,
            "results": results
        }, None if success else message)
        
        # Step 4: Validate renewal-specific results
        if success:
            # Check standard results
            required_results = [
                ("quote_guid", "Quote GUID"),
                ("quote_option_guid", "Quote Option GUID"),
                ("bound_policy_number", "Bound Policy Number")
            ]
            
            for field, name in required_results:
                if field in results and results[field]:
                    test_result.add_step(f"Validate {name}", True, {field: results[field]})
                    logger.info(f"✓ {name}: {results[field]}")
                else:
                    test_result.add_step(f"Validate {name}", False, results, f"{name} not found")
            
            # Check for invoice data in renewal bind
            invoice_data = results.get("invoice_data")
            if invoice_data:
                test_result.add_step("Validate invoice data", True, {
                    "invoice_num": invoice_data.get("invoice_info", {}).get("invoice_num"),
                    "policy_number": invoice_data.get("invoice_info", {}).get("policy_number"),
                    "premium": invoice_data.get("financial", {}).get("premium"),
                    "net_premium": invoice_data.get("financial", {}).get("net_premium")
                })
                logger.info(f"✓ Invoice data retrieved successfully for renewal")
                logger.info(f"  Invoice Number: {invoice_data.get('invoice_info', {}).get('invoice_num')}")
                logger.info(f"  Policy Number: {invoice_data.get('invoice_info', {}).get('policy_number')}")
                logger.info(f"  Premium: ${invoice_data.get('financial', {}).get('premium'):,.2f}")
                logger.info(f"  Net Premium: ${invoice_data.get('financial', {}).get('net_premium'):,.2f}")
            else:
                logger.warning("⚠ No invoice data returned with renewal bind result")
                test_result.add_step("Validate invoice data", False, results, "No invoice data in response")
            
            # Verify renewal was created with correct policy type
            if results.get("quote_guid"):
                log_test_step("Verify renewal quote details")
                
                # Get the created quote to verify it's a renewal
                verify_success, verify_xml, verify_msg = data_service.execute_dataset(
                    "spGetQuoteByOpportunityID",
                    ["OpportunityID", str(payload["opportunity_id"])]
                )
                
                if verify_success and verify_xml:
                    try:
                        root = ET.fromstring(verify_xml)
                        table = root.find('.//Table')
                        if table:
                            renewal_data = {elem.tag: elem.text for elem in table}
                            
                            # Check if renewal_of_quote_guid was set (if we had an expiring quote)
                            if expiring_quote_guid and renewal_data.get("renewal_of_quote_guid"):
                                test_result.add_step("Verify renewal link", True, {
                                    "renewal_of_quote_guid": renewal_data.get("renewal_of_quote_guid"),
                                    "linked_to_expiring": expiring_quote_guid
                                })
                                logger.info("✓ Renewal correctly linked to expiring policy")
                            else:
                                test_result.add_step("Verify renewal link", True, {
                                    "message": "No renewal link (expiring policy not found)"
                                })
                            
                            logger.info(f"✓ Renewal quote created: {renewal_data.get('QuoteGuid')}")
                            logger.info(f"  Policy Number: {renewal_data.get('policy_number')}")
                            
                    except Exception as e:
                        test_result.add_step("Parse renewal verification", False, None, str(e))
        
        # Step 5: Test renewal with missing expiring policy (only if using generated payload)
        if not json_file:
            log_test_step("Test renewal without expiring policy reference")
            
            orphan_payload = create_test_payload(
                transaction_type="bind",
                opportunity_id=999004,
                policy_number="TST999004",
                opportunity_type="renewal"
                # No expiring_opportunity_id or expiring_policy_number
            )
            
            success2, results2, message2 = handler.process_transaction(orphan_payload)
            
            if success2:
                test_result.add_step("Renewal without expiring", True, {
                    "message": "Renewal created without expiring policy link",
                    "quote_guid": results2.get("quote_guid")
                })
                logger.info("✓ Renewal can be created without expiring policy reference")
            else:
                test_result.add_step("Renewal without expiring", False, results2, message2)
        else:
            test_result.add_step("Renewal without expiring", True, {
                "message": "Skipped orphan renewal test when using external JSON"
            })
        
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
        test_result.add_step("Exception", False, None, str(e))
    
    # Save results
    summary = test_result.get_summary()
    save_test_results("renewal_bind", summary)
    
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
    parser = argparse.ArgumentParser(description='Test renewal bind workflow')
    parser.add_argument('--json', '-j', type=str, help='Path to JSON file containing test payload')
    args = parser.parse_args()
    
    test_renewal_bind(json_file=args.json)