#!/usr/bin/env python3
"""
Bulk Transaction Testing Script
Processes transactions from CSV file with customizable parameters
"""
import sys
import os
import csv
import json
import argparse
import traceback
from datetime import datetime
import time
import re

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import transaction handler
from app.services.transaction_handler import get_transaction_handler

class BulkTransactionTester:
    def __init__(self, csv_file, parameter_number=None, use_default_names=False, step_through=False):
        """
        Initialize bulk tester
        
        Args:
            csv_file: Path to CSV file containing transactions
            parameter_number: Number to append to IDs (e.g., 42)
            use_default_names: If True, use default producer/underwriter names
            step_through: If True, pause after each transaction for user input
        """
        self.csv_file = csv_file
        self.parameter_number = parameter_number
        self.use_default_names = use_default_names
        self.step_through = step_through
        self.handler = None
        self.results = []
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.csv_output_rows = []  # For storing modified CSV with results
        
    def modify_payload(self, payload):
        """
        Apply modifications to payload based on parameters
        
        Args:
            payload: Original payload dict
            
        Returns:
            Modified payload dict
        """
        modified = payload.copy()
        
        # Apply parameter number modifications
        if self.parameter_number is not None:
            # Append to IDs
            fields_to_append = [
                'policy_number',
                'expiring_policy_number', 
                'opportunity_id',
                'midterm_endt_id'
            ]
            
            for field in fields_to_append:
                if field in modified and modified[field]:
                    # Convert to string and append number
                    if field == 'opportunity_id':
                        # For opportunity_id, handle as integer
                        try:
                            current_value = str(modified[field])
                            modified[field] = f"{current_value}{self.parameter_number}"
                        except:
                            pass
                    elif field == 'midterm_endt_id':
                        # Only modify if not null/empty
                        if modified[field] and str(modified[field]).lower() not in ['null', 'none', '']:
                            current_value = str(modified[field])
                            modified[field] = f"{current_value}{self.parameter_number}"
                    else:
                        # For string fields
                        current_value = str(modified[field])
                        modified[field] = f"{current_value}{self.parameter_number}"
            
            # Replace last 6 digits of transaction IDs with padded parameter
            padded_param = str(self.parameter_number).zfill(6)
            
            if 'transaction_id' in modified and modified['transaction_id']:
                tid = str(modified['transaction_id'])
                if len(tid) >= 6:
                    modified['transaction_id'] = tid[:-6] + padded_param
                    
            if 'prior_transaction_id' in modified and modified['prior_transaction_id']:
                ptid = str(modified['prior_transaction_id'])
                if ptid and str(ptid).lower() not in ['null', 'none', ''] and len(ptid) >= 6:
                    modified['prior_transaction_id'] = ptid[:-6] + padded_param
        
        # Apply name overrides
        if self.use_default_names:
            modified['producer_name'] = 'Mike Woodworth'
            modified['underwriter_name'] = 'Christina Rentas'
        
        return modified
    
    def process_transaction(self, row_data, row_num):
        """
        Process a single transaction from CSV row
        
        Args:
            row_data: Dictionary containing row data from CSV
            row_num: Current row number in CSV
            
        Returns:
            Tuple (success, result_data, error_message, modified_payload)
        """
        modified_payload = None
        try:
            # Parse the JSON payload
            payload_str = row_data.get('payload', '{}')
            payload = json.loads(payload_str)
            
            # Apply modifications
            modified_payload = self.modify_payload(payload)
            
            # Extract key info for logging
            trans_id = modified_payload.get('transaction_id', 'N/A')
            trans_type = modified_payload.get('transaction_type', row_data.get('transaction_type', 'N/A'))
            opp_id = modified_payload.get('opportunity_id', row_data.get('opportunity_id', 'N/A'))
            policy_num = modified_payload.get('policy_number', 'N/A')
            
            # If step-through mode, show details and wait for user
            if self.step_through:
                print("\n" + "="*60)
                print(f"Row {row_num}: Ready to process transaction")
                print("="*60)
                print(f"  Type: {trans_type}")
                print(f"  Opportunity ID: {opp_id}")
                print(f"  Policy Number: {policy_num}")
                print(f"  Transaction ID: {trans_id}")
                print(f"  Insured: {modified_payload.get('insured_name', 'N/A')}")
                print(f"  Producer: {modified_payload.get('producer_name', 'N/A')}")
                print(f"  Underwriter: {modified_payload.get('underwriter_name', 'N/A')}")
                print(f"  Premium: ${modified_payload.get('base_premium', 0)}")
                
                response = input("\nPress Enter to process, 's' to skip, 'q' to quit: ").strip().lower()
                if response == 'q':
                    return None, None, "User quit", modified_payload
                elif response == 's':
                    logger.info(f"  Skipped by user")
                    return True, {'skipped': True}, "Skipped by user", modified_payload
            
            logger.info(f"Processing: Type={trans_type}, OppID={opp_id}, PolicyNum={policy_num}, TransID={trans_id}")
            
            # Process the transaction
            success, results, message = self.handler.process_transaction(modified_payload)
            
            result_data = {
                'row_number': row_num,
                'opportunity_id': opp_id,
                'transaction_type': trans_type,
                'transaction_id': trans_id,
                'policy_number': policy_num,
                'success': success,
                'message': message,
                'results': results
            }
            
            if success:
                logger.info(f"  ✓ Success: {message}")
                if self.step_through:
                    print(f"\n✓ SUCCESS: {message}")
                    if results:
                        print("Key Results:")
                        for key in ['quote_guid', 'quote_option_guid', 'bound_policy_number', 'invoice_number']:
                            if key in results:
                                print(f"  {key}: {results[key]}")
                return True, result_data, None, modified_payload
            else:
                logger.error(f"  ✗ Failed: {message}")
                if self.step_through:
                    print(f"\n✗ FAILED: {message}")
                return False, result_data, message, modified_payload
                
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in payload: {str(e)}"
            logger.error(f"  ✗ JSON Error: {error_msg}")
            if self.step_through:
                print(f"\n✗ JSON ERROR: {error_msg}")
            return False, {'error': 'JSON_DECODE_ERROR', 'row_number': row_num}, error_msg, modified_payload
            
        except Exception as e:
            error_msg = f"Exception processing transaction: {str(e)}"
            logger.error(f"  ✗ Exception: {error_msg}")
            if self.step_through:
                print(f"\n✗ EXCEPTION: {error_msg}")
            traceback.print_exc()
            return False, {'error': 'PROCESSING_ERROR', 'row_number': row_num}, error_msg, modified_payload
    
    def run(self, start_row=None, end_row=None, continue_on_error=True):
        """
        Run bulk transaction processing
        
        Args:
            start_row: Starting row number (1-based, skips header)
            end_row: Ending row number (inclusive)
            continue_on_error: If True, continue processing on errors
            
        Returns:
            Summary dictionary
        """
        print("\n" + "="*80)
        print("BULK TRANSACTION TESTING")
        print("="*80)
        print(f"CSV File: {self.csv_file}")
        print(f"Parameter Number: {self.parameter_number if self.parameter_number else 'None'}")
        print(f"Use Default Names: {self.use_default_names}")
        print(f"Step Through Mode: {self.step_through}")
        print(f"Row Range: {start_row or 'start'} to {end_row or 'end'}")
        print(f"Continue on Error: {continue_on_error}")
        print("="*80 + "\n")
        
        # Initialize handler
        try:
            logger.info("Initializing transaction handler...")
            self.handler = get_transaction_handler()
            logger.info("✓ Handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize handler: {e}")
            return {'error': 'HANDLER_INIT_FAILED', 'message': str(e)}
        
        # Read and process CSV
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                
                # Add new fields for the output CSV
                output_fieldnames = list(fieldnames) + [
                    'modified_payload',
                    'processing_status',
                    'processing_message',
                    'response_data',
                    'timestamp'
                ]
                
                for row_num, row in enumerate(reader, start=1):
                    # Check row range
                    if start_row and row_num < start_row:
                        # Still add to output CSV but mark as skipped
                        output_row = row.copy()
                        output_row['processing_status'] = 'SKIPPED'
                        output_row['processing_message'] = 'Before start row'
                        output_row['timestamp'] = datetime.now().isoformat()
                        self.csv_output_rows.append(output_row)
                        continue
                        
                    if end_row and row_num > end_row:
                        # Add remaining rows as skipped
                        output_row = row.copy()
                        output_row['processing_status'] = 'SKIPPED'
                        output_row['processing_message'] = 'After end row'
                        output_row['timestamp'] = datetime.now().isoformat()
                        self.csv_output_rows.append(output_row)
                        break
                    
                    if not self.step_through:
                        print(f"\n--- Processing Row {row_num} ---")
                    
                    # Process the transaction
                    success, result_data, error_msg, modified_payload = self.process_transaction(row, row_num)
                    
                    # Check for user quit
                    if success is None and error_msg == "User quit":
                        print("\nUser requested quit. Saving results and exiting...")
                        break
                    
                    # Prepare output row
                    output_row = row.copy()
                    output_row['modified_payload'] = json.dumps(modified_payload, default=str) if modified_payload else ''
                    output_row['processing_status'] = 'SUCCESS' if success else 'FAILED'
                    output_row['processing_message'] = error_msg or (result_data.get('message', '') if result_data else '')
                    output_row['response_data'] = json.dumps(result_data.get('results', {}), default=str) if result_data and 'results' in result_data else ''
                    output_row['timestamp'] = datetime.now().isoformat()
                    
                    self.csv_output_rows.append(output_row)
                    
                    # Store result
                    if result_data:
                        self.results.append(result_data)
                        self.processed_count += 1
                        
                        if success:
                            self.success_count += 1
                        else:
                            self.error_count += 1
                            
                            if not continue_on_error:
                                print(f"\nStopping due to error: {error_msg}")
                                break
                    
                    # Add small delay between transactions to avoid overwhelming the API
                    if not self.step_through:
                        time.sleep(0.5)
                    
        except FileNotFoundError:
            logger.error(f"CSV file not found: {self.csv_file}")
            return {'error': 'FILE_NOT_FOUND', 'message': f"CSV file not found: {self.csv_file}"}
            
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            traceback.print_exc()
            return {'error': 'CSV_READ_ERROR', 'message': str(e)}
        
        # Save CSV output
        self.save_csv_output()
        
        # Generate summary
        summary = self.generate_summary()
        
        # Save results to file
        self.save_results(summary)
        
        return summary
    
    def generate_summary(self):
        """Generate test summary"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'csv_file': self.csv_file,
            'parameter_number': self.parameter_number,
            'use_default_names': self.use_default_names,
            'total_processed': self.processed_count,
            'successful': self.success_count,
            'failed': self.error_count,
            'success_rate': f"{(self.success_count/self.processed_count*100):.1f}%" if self.processed_count > 0 else "0%",
            'results': self.results
        }
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Processed: {self.processed_count}")
        print(f"Successful: {self.success_count}")
        print(f"Failed: {self.error_count}")
        print(f"Success Rate: {summary['success_rate']}")
        
        if self.error_count > 0:
            print("\nFailed Transactions:")
            for result in self.results:
                if not result.get('success', False):
                    print(f"  Row {result.get('row_number', 'N/A')}: "
                          f"Type={result.get('transaction_type', 'N/A')}, "
                          f"OppID={result.get('opportunity_id', 'N/A')}, "
                          f"Message={result.get('message', 'N/A')}")
        
        print("="*80 + "\n")
        
        return summary
    
    def save_csv_output(self):
        """Save modified CSV with processing results"""
        if not self.csv_output_rows:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        param_suffix = f"_p{self.parameter_number}" if self.parameter_number else ""
        output_file = f"bulk_test_output_{timestamp}{param_suffix}.csv"
        
        try:
            # Get fieldnames from first row
            if self.csv_output_rows:
                fieldnames = list(self.csv_output_rows[0].keys())
                
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.csv_output_rows)
                
                logger.info(f"CSV output saved to: {output_file}")
                print(f"CSV output saved to: {output_file}")
                
                # Print summary of errors
                error_count = sum(1 for row in self.csv_output_rows if row.get('processing_status') == 'FAILED')
                if error_count > 0:
                    print(f"  Contains {error_count} failed transactions for review")
                    
        except Exception as e:
            logger.error(f"Failed to save CSV output: {e}")
    
    def save_results(self, summary):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        param_suffix = f"_p{self.parameter_number}" if self.parameter_number else ""
        output_file = f"bulk_test_results_{timestamp}{param_suffix}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {output_file}")
            print(f"\nResults saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Bulk test transactions from CSV file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all transactions with no modifications
  %(prog)s transactions.csv
  
  # Run with parameter number 42
  %(prog)s transactions.csv -p 42
  
  # Run with default names
  %(prog)s transactions.csv --names
  
  # Step through each transaction interactively
  %(prog)s transactions.csv --step
  
  # Run specific row range with parameter 139 and default names
  %(prog)s transactions.csv -p 139 --names --start 10 --end 20
  
  # Step through with parameter and names
  %(prog)s transactions.csv -p 42 --names --step
  
  # Stop on first error
  %(prog)s transactions.csv --stop-on-error
        """
    )
    
    parser.add_argument('csv_file', 
                       help='Path to CSV file containing transactions')
    
    parser.add_argument('-p', '--parameter', type=int, default=None,
                       help='Parameter number to append to IDs (e.g., 42)')
    
    parser.add_argument('--names', action='store_true',
                       help='Use default producer/underwriter names (Mike Woodworth / Christina Rentas)')
    
    parser.add_argument('--step', action='store_true',
                       help='Step through each transaction interactively (press Enter to process, s to skip, q to quit)')
    
    parser.add_argument('--start', type=int, default=None,
                       help='Starting row number (1-based, excludes header)')
    
    parser.add_argument('--end', type=int, default=None,
                       help='Ending row number (inclusive)')
    
    parser.add_argument('--stop-on-error', action='store_true',
                       help='Stop processing on first error (default: continue)')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose debug output')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if CSV file exists
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file not found: {args.csv_file}")
        return 1
    
    # Create and run tester
    tester = BulkTransactionTester(
        csv_file=args.csv_file,
        parameter_number=args.parameter,
        use_default_names=args.names,
        step_through=args.step
    )
    
    summary = tester.run(
        start_row=args.start,
        end_row=args.end,
        continue_on_error=not args.stop_on_error
    )
    
    # Return exit code based on results
    if 'error' in summary:
        return 2  # Critical error
    elif tester.error_count > 0:
        return 1  # Some transactions failed
    else:
        return 0  # All successful


if __name__ == "__main__":
    sys.exit(main())