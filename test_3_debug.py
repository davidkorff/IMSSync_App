"""Debug version of test_3_new_business_bind.py"""
import sys
import os
import argparse
import json
import traceback

# Add path before imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Starting test script...")

try:
    from test_bind_workflow_base import *
    from app.services.transaction_handler import get_transaction_handler
    print("Imports successful")
except Exception as e:
    print(f"Import error: {e}")
    traceback.print_exc()
    sys.exit(1)

def test_new_business_bind_debug(json_file=None):
    """Test with extra debugging"""
    print(f"Starting test_new_business_bind_debug, json_file={json_file}")
    
    test_result = TestResult("new_business_bind")
    
    try:
        # Step 1: Create new business payload
        print("Step 1: Creating payload...")
        log_test_step("Create new business bind payload")
        
        if json_file:
            # Load payload from JSON file
            print(f"Loading from JSON file: {json_file}")
            log_test_step(f"Loading payload from {json_file}")
            
            try:
                with open(json_file, 'r') as f:
                    payload = json.load(f)
                print(f"JSON loaded successfully, keys: {list(payload.keys())[:5]}...")
                logger.info(f"✓ Loaded payload from {json_file}")
            except Exception as e:
                print(f"ERROR loading JSON: {e}")
                test_result.add_step("Load JSON file", False, None, str(e))
                return test_result
        else:
            print("Using default payload")
            payload = create_test_payload(
                transaction_type="bind",
                opportunity_id=999002,
                policy_number="TST999002",
                opportunity_type="new"
            )
            
            payload.update({
                "umr": "TEST/UMR/999002",
                "agreement_number": "TEST-AGREE-001",
                "section_number": "001",
                "policy_fee": 250.00,
                "invoice_date": datetime.now().strftime("%m/%d/%Y")
            })
        
        print("About to add step to test_result...")
        print(f"Payload has transaction_id: {'transaction_id' in payload}")
        print(f"Payload has opportunity_id: {'opportunity_id' in payload}")
        print(f"Payload has opportunity_type: {'opportunity_type' in payload}")
        
        # This is where it might be failing
        test_result.add_step("Create payload", True, {
            "transaction_id": payload.get("transaction_id", "NOT_FOUND"),
            "opportunity_id": payload.get("opportunity_id", "NOT_FOUND"),
            "opportunity_type": payload.get("opportunity_type", "NOT_FOUND")
        })
        
        print("Successfully added step to test_result")
        
        logger.info(f"Testing new business bind with:")
        logger.info(f"  Transaction ID: {payload.get('transaction_id', 'N/A')}")
        logger.info(f"  Opportunity ID: {payload.get('opportunity_id', 'N/A')}")
        logger.info(f"  Policy Number: {payload.get('policy_number', 'N/A')}")
        
        print("Completed initial logging")
        
        # Try to get handler
        print("Getting transaction handler...")
        handler = get_transaction_handler()
        print("Got transaction handler")
        
        # Step 2: Process the transaction
        log_test_step("Process new business bind transaction", {
            "handler": "TransactionHandler.process_transaction"
        })
        
        print("About to process transaction...")
        success, results, message = handler.process_transaction(payload)
        print(f"Transaction processed: success={success}, message={message}")
        
        # Continue with rest of test...
        print("Test completed")
        
    except Exception as e:
        print(f"EXCEPTION in test: {str(e)}")
        traceback.print_exc()
        test_result.add_step("Exception", False, None, str(e))
    
    return test_result

if __name__ == "__main__":
    print("Main starting...")
    parser = argparse.ArgumentParser(description='Debug test')
    parser.add_argument('--json', '-j', type=str, help='Path to JSON file')
    args = parser.parse_args()
    
    print(f"Args parsed: json={args.json}")
    
    result = test_new_business_bind_debug(json_file=args.json)
    print(f"Test completed, success: {result.success}")