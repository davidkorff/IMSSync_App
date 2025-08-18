"""
Test bind workflow with JSON file input
Calls the transaction handler directly with JSON payload
"""
import sys
import os
import json
import argparse
from datetime import datetime
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.transaction_handler import get_transaction_handler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_bind_with_json(json_file: str):
    """Test bind workflow with JSON file"""
    print(f"\n{'='*60}")
    print(f"Testing bind with: {json_file}")
    print(f"{'='*60}\n")
    
    try:
        # Load JSON file
        with open(json_file, 'r') as f:
            payload = json.load(f)
        
        print(f"Loaded transaction:")
        print(f"  Transaction ID: {payload.get('transaction_id')}")
        print(f"  Type: {payload.get('transaction_type')}")
        print(f"  Opportunity ID: {payload.get('opportunity_id')}")
        print(f"  Policy Number: {payload.get('policy_number')}")
        print(f"  Opportunity Type: {payload.get('opportunity_type')}")
        
        # Get transaction handler
        handler = get_transaction_handler()
        
        # Process the transaction
        print(f"\nProcessing transaction...")
        success, results, message = handler.process_transaction(payload)
        
        # Display results
        print(f"\n{'='*60}")
        print(f"RESULTS")
        print(f"{'='*60}")
        print(f"Success: {success}")
        print(f"Message: {message}")
        
        if success:
            print(f"\nCreated Resources:")
            if results.get("insured_guid"):
                print(f"  Insured GUID: {results['insured_guid']}")
            if results.get("quote_guid"):
                print(f"  Quote GUID: {results['quote_guid']}")
            if results.get("quote_option_guid"):
                print(f"  Quote Option GUID: {results['quote_option_guid']}")
            if results.get("bound_policy_number"):
                print(f"  Bound Policy Number: {results['bound_policy_number']}")
            if results.get("bind_status"):
                print(f"  Bind Status: {results['bind_status']}")
        else:
            print(f"\nError Details:")
            if results.get("error"):
                print(f"  {results['error']}")
        
        # Save detailed results
        result_file = f"result_{os.path.basename(json_file).replace('.json', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w') as f:
            json.dump({
                "input_file": json_file,
                "payload": payload,
                "success": success,
                "message": message,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {result_file}")
        
        return success, results, message
        
    except FileNotFoundError:
        print(f"ERROR: File not found: {json_file}")
        return False, {}, "File not found"
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in file: {str(e)}")
        return False, {}, "Invalid JSON"
    except Exception as e:
        print(f"ERROR: {str(e)}")
        logger.error("Exception details:", exc_info=True)
        return False, {}, str(e)

def main():
    parser = argparse.ArgumentParser(description="Test bind workflow with JSON file")
    parser.add_argument("json_file", help="JSON file containing transaction payload")
    
    args = parser.parse_args()
    
    test_bind_with_json(args.json_file)

if __name__ == "__main__":
    main()