#!/usr/bin/env python3
"""
Test 9: Reinstatement Workflow
Tests the reinstatement of a cancelled policy when transaction_type = reinstatement
"""
import sys
import os
import argparse
import json
import traceback
from datetime import datetime

# Debug: Print Python version and path
print(f"Python: {sys.version}")
print(f"Script: {__file__}")
print(f"Working dir: {os.getcwd()}")

# Add current directory to path FIRST
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    print(f"Added to path: {current_dir}")

# Try imports with error handling
try:
    import logging
    # Set up logging BEFORE other imports
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    print("[OK] Logging configured")
except Exception as e:
    print(f"[FAIL] Failed to setup logging: {e}")
    logger = None

# Import test base with error handling
try:
    from test_bind_workflow_base import (
        TestResult, log_test_step, save_test_results, 
        create_test_payload
    )
    print("[OK] Imported test_bind_workflow_base")
except Exception as e:
    print(f"[FAIL] Failed to import test_bind_workflow_base: {e}")
    traceback.print_exc()
    sys.exit(1)

# Import transaction handler
try:
    from app.services.transaction_handler import get_transaction_handler
    print("[OK] Imported transaction_handler")
except Exception as e:
    print(f"[FAIL] Failed to import transaction_handler: {e}")
    print("  This might be due to missing dotenv or other dependencies")
    traceback.print_exc()
    sys.exit(1)

def test_reinstatement(json_file=None):
    """Test complete reinstatement workflow with enhanced error handling"""
    print("\n" + "="*60)
    print("Starting Reinstatement Test")
    print("="*60)
    
    test_result = TestResult("reinstatement")
    
    try:
        # Get handler first to ensure services are available
        print("\nInitializing transaction handler...")
        handler = get_transaction_handler()
        print("[OK] Transaction handler ready")
    except Exception as e:
        print(f"[FAIL] Failed to initialize handler: {e}")
        test_result.add_step("Initialize handler", False, None, str(e))
        return test_result
    
    try:
        # Step 1: Create reinstatement payload
        log_test_step("Create reinstatement payload")
        
        # Try to load from JSON file first
        json_loaded = False
        if json_file:
            if os.path.exists(json_file):
                # Load payload from JSON file
                print(f"\nAttempting to load JSON from: {json_file}")
                log_test_step(f"Loading payload from {json_file}")
                
                try:
                    # Load JSON with explicit encoding
                    with open(json_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"  File size: {len(content)} bytes")
                        payload = json.loads(content)
                    
                    print(f"[OK] Successfully loaded JSON with {len(payload)} fields")
                    if logger:
                        logger.info(f"[OK] Loaded payload from {json_file}")
                    
                    # Ensure transaction_type is set to "reinstatement"
                    if payload.get('transaction_type', '').lower() != 'reinstatement':
                        print(f"  Updating transaction_type from '{payload.get('transaction_type')}' to 'reinstatement'")
                        payload['transaction_type'] = 'reinstatement'
                    
                    # Validate required fields for reinstatement transaction
                    required = ['transaction_id', 'transaction_type', 'opportunity_id']
                    
                    for field in required:
                        if field not in payload:
                            print(f"  Warning: Missing required field '{field}'")
                        else:
                            print(f"  [OK] {field}: {payload[field]}")
                    
                    # Check that we have opportunity_id (required for reinstatement)
                    if not payload.get('opportunity_id'):
                        print(f"  Error: Reinstatement transaction requires 'opportunity_id'")
                        test_result.add_step("Validate payload", False, None, 
                                           "Missing required field: opportunity_id")
                        return test_result
                    
                    json_loaded = True
                            
                except json.JSONDecodeError as e:
                    print(f"[FAIL] Invalid JSON: {e}")
                    test_result.add_step("Load JSON file", False, None, f"JSON decode error: {e}")
                    return test_result
                except Exception as e:
                    print(f"[FAIL] Unexpected error loading JSON: {e}")
                    traceback.print_exc()
                    test_result.add_step("Load JSON file", False, None, str(e))
                    return test_result
            else:
                print(f"\nJSON file '{json_file}' not found, using default test payload instead")
        
        if not json_loaded:
            # Use default test payload based on test4reinstate.json
            print("\nGenerating default test payload...")
            payload = create_test_payload(
                transaction_type="reinstatement",
                opportunity_id=106205,
                policy_number="SPG0000089-251",
                opportunity_type="Renewal"
            )
            
            # Add additional fields specific to reinstatement
            payload.update({
                "gross_premium": 1500,
                "net_premium": 1050,
                "commission_amount": 450,
                "commission_percent": 30,
                "commission_rate": 20,
                "policy_fee": 250,
                "status": "cancelled",
                "prior_transaction_id": "c2833221-d3c1-4218-b1ff-ecd16356972b",
                "transaction_date": datetime.now().isoformat() + "+00:00",
                "insured_name": "Vida Hospice Services Inc",
                "underwriter_name": "Christina Rentas",
                "producer_name": "Mike Woodworth",
                "producer_email": "mike.woodworth@amwins.com",
                "effective_date": "11/11/2025",
                "expiration_date": "11/11/2026",
                "invoice_date": "11/11/2025",
                "bound_date": "08/15/2025",
                "reinstatement_reason": "Policy reinstated per insured request"
            })
            print("[OK] Generated default payload")
        
        # Log payload creation success
        test_result.add_step("Create payload", True, {
            "transaction_id": payload.get("transaction_id", "N/A"),
            "transaction_type": payload.get("transaction_type", "N/A"),
            "opportunity_id": payload.get("opportunity_id", "N/A"),
            "policy_number": payload.get("policy_number", "N/A")
        })
        
        print(f"\nTesting reinstatement with:")
        print(f"  Transaction ID: {payload.get('transaction_id', 'N/A')}")
        print(f"  Transaction Type: {payload.get('transaction_type', 'N/A')}")
        print(f"  Opportunity ID: {payload.get('opportunity_id', 'N/A')}")
        print(f"  Policy Number: {payload.get('policy_number', 'N/A')}")
        print(f"  Status: {payload.get('status', 'N/A')}")
        print(f"  Premium: ${payload.get('gross_premium', 0):,.2f}")
        print(f"  Underwriter: {payload.get('underwriter_name', 'N/A')}")
        
        if logger:
            logger.info(f"Testing reinstatement with:")
            logger.info(f"  Transaction ID: {payload['transaction_id']}")
            logger.info(f"  Transaction Type: {payload['transaction_type']}")
            logger.info(f"  Opportunity ID: {payload['opportunity_id']}")
            logger.info(f"  Policy Number: {payload['policy_number']}")
        
        # Step 2: Process the transaction
        log_test_step("Process reinstatement transaction", {
            "handler": "TransactionHandler.process_transaction"
        })
        
        # Log the full payload being sent
        if logger:
            logger.debug(f"Full payload:\n{json.dumps(payload, indent=2)}")
        
        print("\nProcessing transaction...")
        success, results, message = handler.process_transaction(payload)
        
        print(f"\nTransaction result: {'SUCCESS' if success else 'FAILED'}")
        print(f"Message: {message}")
        
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
            print("\nValidating results...")
            
            # Check for reinstatement-specific fields
            reinstatement_fields = [
                ("reinstatement_quote_guid", "Reinstatement Quote GUID"),
                ("reinstatement_quote_option_guid", "Reinstatement Quote Option GUID"),
                ("original_quote_guid", "Original Quote GUID"),
                ("cancellation_quote_guid", "Cancellation Quote GUID"),
                ("reinstatement_number", "Reinstatement Number"),
                ("reinstatement_premium", "Reinstatement Premium"),
                ("reinstatement_effective_date", "Reinstatement Effective Date")
            ]
            
            for field, name in reinstatement_fields:
                if field in results and results[field]:
                    test_result.add_step(f"Validate {name}", True, {field: results[field]})
                    print(f"  [OK] {name}: {results[field]}")
                    if logger:
                        logger.info(f"[OK] {name}: {results[field]}")
                else:
                    test_result.add_step(f"Validate {name}", False, results, f"{name} not found in results")
                    print(f"  [FAIL] {name} missing from results")
                    if logger:
                        logger.error(f"[FAIL] {name} missing from results")
            
            # Check reinstatement-specific results
            if results.get("reinstatement_status") == "completed":
                reinstated_policy = results.get("reinstatement_policy_number")
                if reinstated_policy:
                    test_result.add_step("Validate reinstatement", True, {
                        "reinstatement_policy_number": reinstated_policy,
                        "net_premium_change": results.get("net_premium_change")
                    })
                    print(f"\n[OK] Policy reinstated successfully: {reinstated_policy}")
                    if results.get("net_premium_change"):
                        print(f"  Net Premium Change: ${results.get('net_premium_change'):,.2f}")
                    if logger:
                        logger.info(f"[OK] Policy reinstated successfully: {reinstated_policy}")
                else:
                    test_result.add_step("Validate reinstatement", False, results, "No reinstated policy number returned")
            else:
                test_result.add_step("Validate reinstatement", False, results, 
                                   f"Reinstatement status: {results.get('reinstatement_status', 'unknown')}")
                print(f"  [FAIL] Reinstatement status: {results.get('reinstatement_status', 'unknown')}")
            
            # Check for invoice data
            if results.get("invoice_data"):
                test_result.add_step("Validate invoice data", True, {"has_invoice": True})
                print(f"  [OK] Invoice data retrieved")
                if logger:
                    logger.info(f"[OK] Invoice data retrieved")
            else:
                print(f"  [WARN] No invoice data in results")
        
    except Exception as e:
        print(f"\n[FAIL] Test failed with exception: {str(e)}")
        traceback.print_exc()
        if logger:
            logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
        test_result.add_step("Exception", False, None, str(e))
    
    # Save results
    summary = test_result.get_summary()
    save_test_results("reinstatement", summary)
    
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

def main():
    """Main entry point with enhanced error handling"""
    print("\n" + "="*80)
    print("REINSTATEMENT TEST")
    print("="*80)
    
    parser = argparse.ArgumentParser(description='Test reinstatement workflow')
    parser.add_argument('--json', '-j', type=str, default='test4reinstate.json', 
                       help='Path to JSON file containing test payload (default: test4reinstate.json)')
    
    try:
        args = parser.parse_args()
        print(f"\nArguments: json={args.json}")
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        return 1
    
    try:
        result = test_reinstatement(json_file=args.json)
        return 0 if result.success else 1
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())