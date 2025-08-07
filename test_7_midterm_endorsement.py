#!/usr/bin/env python3
"""
Test 7: Midterm Endorsement Workflow
Tests the creation of a midterm endorsement when transaction_type = midterm_endorsement
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


def test_midterm_endorsement(json_file=None):
    """Test complete midterm endorsement workflow with enhanced error handling"""
    print("\n" + "="*60)
    print("Starting Midterm Endorsement Test")
    print("="*60)
    
    test_result = TestResult("midterm_endorsement")
    
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
        # Step 1: Create endorsement payload
        log_test_step("Create midterm endorsement payload")
        
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
                    
                    # Ensure transaction_type is set to "midterm_endorsement"
                    if payload.get('transaction_type', '').lower() != 'midterm_endorsement':
                        print(f"  Updating transaction_type from '{payload.get('transaction_type')}' to 'midterm_endorsement'")
                        payload['transaction_type'] = 'midterm_endorsement'
                    
                    # Validate required fields for endorsement transaction
                    required = ['transaction_id', 'transaction_type']
                    required_lookup = ['opportunity_id', 'policy_number']  # Need at least one
                    endorsement_fields = ['gross_premium', 'midterm_endt_effective_from', 'midterm_endt_description']
                    
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
                        print(f"  Error: Endorsement transaction requires either 'opportunity_id' or 'policy_number'")
                        test_result.add_step("Validate payload", False, None, 
                                           "Missing required lookup field (opportunity_id or policy_number)")
                        return test_result
                    
                    # Check endorsement-specific fields
                    for field in endorsement_fields:
                        if field in payload:
                            print(f"  ✓ {field}: {payload[field]}")
                    
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
                transaction_type="midterm_endorsement",
                opportunity_id=12345,
                policy_number="POL-2025-001",
                opportunity_type=""  # Not needed for endorsement
            )
            
            # Add endorsement-specific fields
            payload.update({
                "gross_premium": 750.00,
                "midterm_endt_effective_from": datetime.now().strftime("%m/%d/%Y"),
                "midterm_endt_description": "Add additional coverage",
                "midterm_endt_id": 1,
                "invoice_date": datetime.now().strftime("%m/%d/%Y")
            })
            print("✓ Generated default payload")
        
        # Log payload creation success
        test_result.add_step("Create payload", True, {
            "transaction_id": payload.get("transaction_id", "N/A"),
            "transaction_type": payload.get("transaction_type", "N/A"),
            "opportunity_id": payload.get("opportunity_id", "N/A"),
            "policy_number": payload.get("policy_number", "N/A"),
            "endorsement_premium": payload.get("gross_premium", "N/A"),
            "effective_date": payload.get("midterm_endt_effective_from", "N/A")
        })
        
        print(f"\nTesting midterm endorsement with:")
        print(f"  Transaction ID: {payload.get('transaction_id', 'N/A')}")
        print(f"  Transaction Type: {payload.get('transaction_type', 'N/A')}")
        print(f"  Opportunity ID: {payload.get('opportunity_id', 'N/A')}")
        print(f"  Policy Number: {payload.get('policy_number', 'N/A')}")
        print(f"  Endorsement Premium: ${payload.get('gross_premium', 0):,.2f}")
        print(f"  Effective Date: {payload.get('midterm_endt_effective_from', 'N/A')}")
        print(f"  Description: {payload.get('midterm_endt_description', 'N/A')}")
        
        if logger:
            logger.info(f"Testing midterm endorsement with:")
            logger.info(f"  Transaction ID: {payload['transaction_id']}")
            logger.info(f"  Transaction Type: {payload['transaction_type']}")
            if payload.get('opportunity_id'):
                logger.info(f"  Opportunity ID: {payload['opportunity_id']}")
            if payload.get('policy_number'):
                logger.info(f"  Policy Number: {payload['policy_number']}")
            logger.info(f"  Endorsement Premium: ${payload.get('gross_premium', 0):,.2f}")
        
        # Step 2: Process the transaction
        log_test_step("Process midterm endorsement transaction", {
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
                test_result.add_step("Validate Original Quote GUID", True, {"quote_guid": results["quote_guid"]})
                print(f"  ✓ Original Quote GUID: {results['quote_guid']}")
                if logger:
                    logger.info(f"✓ Original Quote GUID: {results['quote_guid']}")
            else:
                test_result.add_step("Validate Original Quote GUID", False, results, "Quote GUID not found in results")
                print(f"  ✗ Original Quote GUID missing from results")
                if logger:
                    logger.error(f"✗ Original Quote GUID missing from results")
            
            # Check endorsement-specific results
            if results.get("endorsement_status") == "completed":
                endorsement_guid = results.get("endorsement_quote_guid")
                endorsement_option_guid = results.get("endorsement_quote_option_guid")
                endorsement_number = results.get("endorsement_number")
                
                if endorsement_guid:
                    test_result.add_step("Validate endorsement", True, {
                        "endorsement_quote_guid": endorsement_guid,
                        "endorsement_quote_option_guid": endorsement_option_guid,
                        "endorsement_number": endorsement_number
                    })
                    print(f"\n✓ Endorsement created successfully:")
                    print(f"  Endorsement Quote GUID: {endorsement_guid}")
                    if endorsement_option_guid:
                        print(f"  Endorsement Quote Option GUID: {endorsement_option_guid}")
                    print(f"  Endorsement Number: {endorsement_number}")
                    print(f"  Endorsement Premium: ${results.get('endorsement_premium', 0):,.2f}")
                    print(f"  Effective Date: {results.get('endorsement_effective_date')}")
                    
                    if results.get('invoice_number'):
                        print(f"  Invoice Number: {results.get('invoice_number')}")
                    
                    if logger:
                        logger.info(f"✓ Endorsement created successfully: {endorsement_guid}")
                        logger.info(f"  Endorsement Number: {endorsement_number}")
                else:
                    test_result.add_step("Validate endorsement", False, results, "No endorsement quote GUID returned")
                    print(f"  ✗ No endorsement quote GUID returned")
            else:
                test_result.add_step("Validate endorsement", False, results, 
                                   f"Endorsement status: {results.get('endorsement_status', 'unknown')}")
                print(f"  ✗ Endorsement status: {results.get('endorsement_status', 'unknown')}")
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {str(e)}")
        traceback.print_exc()
        if logger:
            logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
        test_result.add_step("Exception", False, None, str(e))
    
    # Save results
    summary = test_result.get_summary()
    save_test_results("midterm_endorsement", summary)
    
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
    print("MIDTERM ENDORSEMENT TEST")
    print("="*80)
    
    parser = argparse.ArgumentParser(description='Test midterm endorsement workflow')
    parser.add_argument('--json', '-j', type=str, default='TEST.json', 
                       help='Path to JSON file containing test payload (default: TEST.json)')
    
    try:
        args = parser.parse_args()
        print(f"\nArguments: json={args.json}")
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        return 1
    
    try:
        result = test_midterm_endorsement(json_file=args.json)
        return 0 if result.success else 1
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())