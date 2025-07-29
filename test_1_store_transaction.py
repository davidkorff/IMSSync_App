"""
Test 1: Store Transaction Data
Tests the spStoreTritonTransaction_WS stored procedure
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_bind_workflow_base import *
from app.services.ims.data_access_service import get_data_access_service
from app.services.ims.auth_service import get_auth_service
import json

def test_store_transaction():
    """Test storing transaction data in tblTritonTransactionData"""
    test_result = TestResult("store_transaction")
    data_service = get_data_access_service()
    auth_service = get_auth_service()
    
    try:
        # Step 1: Authenticate
        log_test_step("Authenticate with IMS")
        success, message = auth_service.login()
        test_result.add_step("Authentication", success, {"message": message}, None if success else message)
        
        if not success:
            return test_result
        
        # Step 2: Create test payload
        log_test_step("Create test payload")
        payload = create_test_payload(
            transaction_type="bind",
            opportunity_id=999001,
            policy_number="TST999001"
        )
        test_result.add_step("Create payload", True, {"payload": payload})
        
        # Step 3: Store transaction
        log_test_step("Store transaction via spStoreTritonTransaction_WS", {
            "transaction_id": payload["transaction_id"],
            "opportunity_id": payload["opportunity_id"]
        })
        
        # Call the stored procedure
        success, result_xml, message = data_service.execute_dataset(
            "spStoreTritonTransaction",
            [
                "transaction_id", payload["transaction_id"],
                "full_payload_json", json.dumps(payload),
                "opportunity_id", str(payload["opportunity_id"]),
                "policy_number", payload["policy_number"],
                "insured_name", payload["insured_name"],
                "transaction_type", payload["transaction_type"],
                "transaction_date", payload["transaction_date"],
                "source_system", payload["source_system"]
            ]
        )
        
        # Log the raw response for debugging
        if data_service._last_soap_request:
            log_soap_request("DataAccess", "ExecuteDataSet", data_service._last_soap_request)
        if data_service._last_soap_response:
            log_soap_response("DataAccess", "ExecuteDataSet", data_service._last_soap_response, 200 if success else 500)
        
        test_result.add_step("Store transaction", success, {
            "result_xml": result_xml,
            "message": message
        }, None if success else message)
        
        # Step 4: Parse and validate results
        if success and result_xml:
            log_test_step("Parse stored procedure results")
            import xml.etree.ElementTree as ET
            
            try:
                root = ET.fromstring(result_xml)
                table = root.find('.//Table')
                
                if table is not None:
                    result_data = {}
                    for element in table:
                        result_data[element.tag] = element.text
                    
                    log_test_step("Stored procedure results", result_data)
                    
                    # Check if it was successful
                    if result_data.get("Status") == "Success":
                        test_result.add_step("Validate storage", True, result_data)
                        logger.info(f"✓ Transaction stored successfully: {result_data.get('transaction_id')}")
                        logger.info(f"  TritonTransactionDataID: {result_data.get('TritonTransactionDataID')}")
                    elif result_data.get("Status") == "Warning":
                        test_result.add_step("Validate storage", True, result_data)
                        logger.warning(f"⚠ Transaction already exists: {result_data.get('Message')}")
                    else:
                        test_result.add_step("Validate storage", False, result_data, 
                                           f"Unexpected status: {result_data.get('Status')}")
                else:
                    test_result.add_step("Parse results", False, None, "No Table element in XML response")
                    
            except Exception as e:
                test_result.add_step("Parse results", False, None, str(e))
        
        # Step 5: Verify by retrieving (optional - try to store again)
        log_test_step("Verify by attempting duplicate insert")
        success2, result_xml2, message2 = data_service.execute_dataset(
            "spStoreTritonTransaction",
            [
                "transaction_id", payload["transaction_id"],
                "full_payload_json", json.dumps(payload),
                "opportunity_id", str(payload["opportunity_id"]),
                "policy_number", payload["policy_number"],
                "insured_name", payload["insured_name"],
                "transaction_type", payload["transaction_type"],
                "transaction_date", payload["transaction_date"],
                "source_system", payload["source_system"]
            ]
        )
        
        if success2 and result_xml2:
            try:
                root = ET.fromstring(result_xml2)
                table = root.find('.//Table')
                if table:
                    result_data = {elem.tag: elem.text for elem in table}
                    if result_data.get("Status") == "Warning":
                        test_result.add_step("Verify duplicate prevention", True, result_data)
                        logger.info("✓ Duplicate prevention working correctly")
                    else:
                        test_result.add_step("Verify duplicate prevention", False, result_data,
                                           "Expected Warning status for duplicate")
            except Exception as e:
                test_result.add_step("Verify duplicate prevention", False, None, str(e))
        
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
        test_result.add_step("Exception", False, None, str(e))
    
    # Save results
    summary = test_result.get_summary()
    save_test_results("store_transaction", summary)
    
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
    test_store_transaction()