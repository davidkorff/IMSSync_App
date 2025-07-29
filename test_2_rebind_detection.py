"""
Test 2: Rebind Detection
Tests the spGetQuoteByOpportunityID_WS and spCheckQuoteBoundStatus_WS procedures
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_bind_workflow_base import *
from app.services.ims.data_access_service import get_data_access_service
from app.services.ims.auth_service import get_auth_service
import xml.etree.ElementTree as ET

def test_rebind_detection():
    """Test rebind detection workflow"""
    test_result = TestResult("rebind_detection")
    data_service = get_data_access_service()
    auth_service = get_auth_service()
    
    try:
        # Step 1: Authenticate
        log_test_step("Authenticate with IMS")
        success, message = auth_service.login()
        test_result.add_step("Authentication", success, {"message": message}, None if success else message)
        
        if not success:
            return test_result
        
        # Step 2: Create test payload for rebind scenario
        log_test_step("Create test payload for rebind")
        payload = create_test_payload(
            transaction_type="bind",
            opportunity_id=88475,  # Use a known opportunity_id that might exist
            policy_number="RSG240088475"
        )
        test_result.add_step("Create payload", True, {"payload": payload})
        
        # Step 3: Check if quote exists for this opportunity_id
        log_test_step("Check for existing quote by opportunity_id", {
            "opportunity_id": payload["opportunity_id"]
        })
        
        success, result_xml, message = data_service.execute_dataset(
            "spGetQuoteByOpportunityID",
            ["OpportunityID", str(payload["opportunity_id"])]
        )
        
        # Log the raw response
        if data_service._last_soap_request:
            log_soap_request("DataAccess", "spGetQuoteByOpportunityID", data_service._last_soap_request)
        if data_service._last_soap_response:
            log_soap_response("DataAccess", "spGetQuoteByOpportunityID", data_service._last_soap_response, 200 if success else 500)
        
        test_result.add_step("Get quote by opportunity_id", success, {
            "message": message,
            "has_result": result_xml is not None
        }, None if success else message)
        
        quote_guid = None
        is_bound = False
        
        # Step 4: Parse results
        if success and result_xml:
            log_test_step("Parse quote lookup results")
            try:
                root = ET.fromstring(result_xml)
                table = root.find('.//Table')
                
                if table is not None:
                    result_data = {}
                    for element in table:
                        result_data[element.tag] = element.text
                    
                    quote_guid = result_data.get("QuoteGuid")
                    is_bound_str = result_data.get("IsBound", "0")
                    is_bound = is_bound_str == "1"
                    
                    log_test_step("Quote found", {
                        "quote_guid": quote_guid,
                        "policy_number": result_data.get("policy_number"),
                        "is_bound": is_bound,
                        "quote_status_id": result_data.get("QuoteStatusID"),
                        "date_bound": result_data.get("DateBound")
                    })
                    
                    test_result.add_step("Parse quote data", True, result_data)
                    
                    if quote_guid:
                        logger.info(f"✓ Found existing quote: {quote_guid}")
                        logger.info(f"  Is Bound: {is_bound}")
                        logger.info(f"  Policy Number: {result_data.get('policy_number')}")
                    else:
                        logger.info("ℹ No existing quote found for this opportunity_id")
                        test_result.add_step("Quote lookup", True, {"message": "No existing quote"})
                else:
                    logger.info("ℹ No quote found for this opportunity_id (no Table in response)")
                    test_result.add_step("Quote lookup", True, {"message": "No existing quote"})
                    
            except Exception as e:
                test_result.add_step("Parse quote results", False, None, str(e))
        
        # Step 5: If quote found, check bound status in detail
        if quote_guid:
            log_test_step("Check quote bound status", {"quote_guid": quote_guid})
            
            success, result_xml, message = data_service.execute_dataset(
                "spCheckQuoteBoundStatus",
                ["QuoteGuid", quote_guid]
            )
            
            # Log the raw response
            if data_service._last_soap_request:
                log_soap_request("DataAccess", "spCheckQuoteBoundStatus", data_service._last_soap_request)
            if data_service._last_soap_response:
                log_soap_response("DataAccess", "spCheckQuoteBoundStatus", data_service._last_soap_response, 200 if success else 500)
            
            if success and result_xml:
                try:
                    root = ET.fromstring(result_xml)
                    table = root.find('.//Table')
                    
                    if table:
                        bound_data = {}
                        for element in table:
                            bound_data[element.tag] = element.text
                        
                        log_test_step("Bound status details", bound_data)
                        test_result.add_step("Check bound status", True, bound_data)
                        
                        # Determine action based on bound status
                        if bound_data.get("IsBound") == "1":
                            logger.warning("⚠ REBIND BLOCKED: Policy is already bound")
                            logger.info(f"  Policy Number: {bound_data.get('PolicyNumber')}")
                            logger.info(f"  Date Bound: {bound_data.get('DateBound')}")
                            test_result.add_step("Rebind decision", True, {
                                "action": "BLOCK",
                                "reason": "Policy already bound"
                            })
                        else:
                            logger.info("✓ REBIND ALLOWED: Quote exists but is not bound")
                            test_result.add_step("Rebind decision", True, {
                                "action": "ALLOW",
                                "reason": "Quote not bound"
                            })
                            
                except Exception as e:
                    test_result.add_step("Parse bound status", False, None, str(e))
            else:
                test_result.add_step("Check bound status", False, None, message)
        else:
            # No existing quote - this would be a new bind, not a rebind
            logger.info("ℹ No existing quote - this would be a NEW BIND, not a rebind")
            test_result.add_step("Rebind decision", True, {
                "action": "NEW_BIND",
                "reason": "No existing quote found"
            })
        
        # Step 6: Test with a different opportunity_id that shouldn't exist
        log_test_step("Test with non-existent opportunity_id")
        success, result_xml, message = data_service.execute_dataset(
            "spGetQuoteByOpportunityID",
            ["OpportunityID", "999999"]
        )
        
        if success:
            if result_xml:
                try:
                    root = ET.fromstring(result_xml)
                    table = root.find('.//Table')
                    if table is None:
                        test_result.add_step("Test non-existent", True, {"result": "No quote found as expected"})
                        logger.info("✓ Correctly returned no results for non-existent opportunity_id")
                    else:
                        test_result.add_step("Test non-existent", False, None, "Unexpected quote found")
                except:
                    test_result.add_step("Test non-existent", True, {"result": "No valid XML table"})
            else:
                test_result.add_step("Test non-existent", True, {"result": "No results returned"})
        
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
        test_result.add_step("Exception", False, None, str(e))
    
    # Save results
    summary = test_result.get_summary()
    save_test_results("rebind_detection", summary)
    
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
    test_rebind_detection()