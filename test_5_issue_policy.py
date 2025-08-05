#!/usr/bin/env python3
"""
Test 5: Issue Policy Workflow
Tests the issuance of a policy when transaction_type = issue
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
    print("✓ Logging configured")
except Exception as e:
    print(f"✗ Failed to setup logging: {e}")
    logger = None

# Import test base with error handling
try:
    from test_bind_workflow_base import (
        TestResult, log_test_step, save_test_results, 
        create_test_payload
    )
    print("✓ Imported test_bind_workflow_base")
except Exception as e:
    print(f"✗ Failed to import test_bind_workflow_base: {e}")
    traceback.print_exc()
    sys.exit(1)

# Import transaction handler
try:
    from app.services.transaction_handler import get_transaction_handler
    print("✓ Imported transaction_handler")
except Exception as e:
    print(f"✗ Failed to import transaction_handler: {e}")
    print("  This might be due to missing dotenv or other dependencies")
    traceback.print_exc()
    sys.exit(1)

def test_issue_policy(json_file=None):
    """Test complete issue policy workflow with enhanced error handling"""
    print("\n" + "="*60)
    print("Starting Issue Policy Test")
    print("="*60)
    
    test_result = TestResult("issue_policy")
    
    try:
        # Get handler first to ensure services are available
        print("\nInitializing transaction handler...")
        handler = get_transaction_handler()
        print("✓ Transaction handler ready")
    except Exception as e:
        print(f"✗ Failed to initialize handler: {e}")
        test_result.add_step("Initialize handler", False, None, str(e))
        return test_result
    
    try:
        # Step 1: Create issue payload
        log_test_step("Create issue policy payload")
        
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
                    
                    print(f"✓ Successfully loaded JSON with {len(payload)} fields")
                    if logger:
                        logger.info(f"✓ Loaded payload from {json_file}")
                    
                    # Ensure transaction_type is set to "issue"
                    if payload.get('transaction_type', '').lower() != 'issue':
                        print(f"  Updating transaction_type from '{payload.get('transaction_type')}' to 'issue'")
                        payload['transaction_type'] = 'issue'
                    
                    # Validate required fields for issue transaction
                    required = ['transaction_id', 'transaction_type']
                    required_lookup = ['opportunity_id', 'policy_number']  # Need at least one
                    
                    for field in required:
                        if field not in payload:
                            print(f"  Warning: Missing required field '{field}'")
                        else:
                            print(f"  ✓ {field}: {payload[field]}")
                    
                    # Check that we have at least one lookup field
                    has_lookup = False
                    for field in required_lookup:
                        if field in payload and payload[field]:
                            print(f"  ✓ {field}: {payload[field]}")
                            has_lookup = True
                    
                    if not has_lookup:
                        print(f"  Error: Issue transaction requires either 'opportunity_id' or 'policy_number'")
                        test_result.add_step("Validate payload", False, None, 
                                           "Missing required lookup field (opportunity_id or policy_number)")
                        return test_result
                    
                    json_loaded = True
                            
                except json.JSONDecodeError as e:
                    print(f"✗ Invalid JSON: {e}")
                    test_result.add_step("Load JSON file", False, None, f"JSON decode error: {e}")
                    return test_result
                except Exception as e:
                    print(f"✗ Unexpected error loading JSON: {e}")
                    traceback.print_exc()
                    test_result.add_step("Load JSON file", False, None, str(e))
                    return test_result
            else:
                print(f"\nJSON file '{json_file}' not found, using default test payload instead")
        
        if not json_loaded:
            # Use default test payload
            print("\nGenerating default test payload...")
            payload = create_test_payload(
                transaction_type="issue",
                opportunity_id=88475,
                policy_number="TST-88475-240705",
                opportunity_type="new"
            )
            
            # Add additional fields specific to issue
            payload.update({
                "invoice_date": datetime.now().strftime("%m/%d/%Y")
            })
            print("✓ Generated default payload")
        
        # Log payload creation success
        test_result.add_step("Create payload", True, {
            "transaction_id": payload.get("transaction_id", "N/A"),
            "transaction_type": payload.get("transaction_type", "N/A"),
            "opportunity_id": payload.get("opportunity_id", "N/A"),
            "policy_number": payload.get("policy_number", "N/A")
        })
        
        print(f"\nTesting issue policy with:")
        print(f"  Transaction ID: {payload.get('transaction_id', 'N/A')}")
        print(f"  Transaction Type: {payload.get('transaction_type', 'N/A')}")
        print(f"  Opportunity ID: {payload.get('opportunity_id', 'N/A')}")
        print(f"  Policy Number: {payload.get('policy_number', 'N/A')}")
        print(f"  Underwriter: {payload.get('underwriter_name', 'N/A')}")
        
        if logger:
            logger.info(f"Testing issue policy with:")
            logger.info(f"  Transaction ID: {payload['transaction_id']}")
            logger.info(f"  Transaction Type: {payload['transaction_type']}")
            if payload.get('opportunity_id'):
                logger.info(f"  Opportunity ID: {payload['opportunity_id']}")
            if payload.get('policy_number'):
                logger.info(f"  Policy Number: {payload['policy_number']}")
        
        # Step 2: Process the transaction
        log_test_step("Process issue policy transaction", {
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
            
            # Check for quote_guid (should be found from lookup)
            if "quote_guid" in results and results["quote_guid"]:
                test_result.add_step("Validate Quote GUID", True, {"quote_guid": results["quote_guid"]})
                print(f"  ✓ Quote GUID: {results['quote_guid']}")
                if logger:
                    logger.info(f"✓ Quote GUID: {results['quote_guid']}")
            else:
                test_result.add_step("Validate Quote GUID", False, results, "Quote GUID not found in results")
                print(f"  ✗ Quote GUID missing from results")
                if logger:
                    logger.error(f"✗ Quote GUID missing from results")
            
            # Check issue-specific results
            if results.get("issue_status") == "completed":
                issue_date = results.get("issue_date")
                if issue_date:
                    test_result.add_step("Validate issue", True, {"issue_date": issue_date})
                    print(f"\n✓ Policy issued successfully: {issue_date}")
                    if logger:
                        logger.info(f"✓ Policy issued successfully: {issue_date}")
                else:
                    test_result.add_step("Validate issue", False, results, "No issue date returned")
                    print(f"  ✗ No issue date returned")
            else:
                test_result.add_step("Validate issue", False, results, 
                                   f"Issue status: {results.get('issue_status', 'unknown')}")
                print(f"  ✗ Issue status: {results.get('issue_status', 'unknown')}")
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {str(e)}")
        traceback.print_exc()
        if logger:
            logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
        test_result.add_step("Exception", False, None, str(e))
    
    # Save results
    summary = test_result.get_summary()
    save_test_results("issue_policy", summary)
    
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
    print("ISSUE POLICY TEST")
    print("="*80)
    
    parser = argparse.ArgumentParser(description='Test issue policy workflow')
    parser.add_argument('--json', '-j', type=str, default='TEST.json', 
                       help='Path to JSON file containing test payload (default: TEST.json)')
    
    try:
        args = parser.parse_args()
        print(f"\nArguments: json={args.json}")
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        return 1
    
    try:
        result = test_issue_policy(json_file=args.json)
        return 0 if result.success else 1
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())