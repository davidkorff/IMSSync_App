#!/usr/bin/env python3
"""
Load CSV submissions into IMS - Windows compatible version without emojis
"""

import csv
import json
import requests
import hashlib
import sys
import os
import logging
import time
from datetime import datetime
from pathlib import Path

# Configure logging without emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ],
    encoding='utf-8'  # Force UTF-8 encoding
)
logger = logging.getLogger(__name__)

# Rest of the imports from original file
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from load_csv_to_ims import CSVToIMSLoader as OriginalLoader

class CSVToIMSLoader(OriginalLoader):
    """Windows-compatible version without emojis"""
    
    def get_service_info(self):
        """Get detailed service information"""
        try:
            logger.info("GETTING SERVICE INFORMATION")
            logger.info("-" * 40)
            response = self.session.get(f"{self.base_url}/api/health")
            logger.info(f"Health Check Request: GET {self.base_url}/api/health")
            logger.info(f"Health Check Response: {response.status_code}")
            
            if response.status_code == 200:
                health_data = response.json()
                # Print nicely formatted health info
                logger.info(f"Service Health: {json.dumps(health_data, indent=2)}")
            else:
                logger.warning(f"Health check failed with status: {response.status_code}")
            
            logger.info("-" * 40)
            
        except Exception as e:
            logger.error(f"Error getting service info: {str(e)}")
    
    def process_row(self, row, row_number):
        """Process a single CSV row"""
        policy_number = row.get('Policy Number/Certificate Ref.', f'Row_{row_number}')
        insured_name = row.get('Insured', 'Unknown')
        
        logger.info("=" * 60)
        logger.info(f"PROCESSING ROW {row_number}")
        logger.info("=" * 60)
        logger.info(f"Policy Number: {policy_number}")
        logger.info(f"Insured Name: {insured_name}")
        logger.info(f"Producer: {row.get('Producer', 'Unknown')}")
        logger.info(f"Underwriter: {row.get('Underwriter', 'Unknown')}")
        logger.info(f"Gross Premium: {row.get('Gross Premium', 'Unknown')}")
        
        try:
            # Transform to JSON
            logger.info("Transforming CSV row to JSON format...")
            transaction_data = self.transform_csv_row_to_json(row)
            logger.info(f"Generated Transaction ID: {transaction_data['transaction_id']}")
            
            # Send to API with detailed logging
            url = f"{self.base_url}/api/transaction/new"
            params = {"source": "triton"}
            
            # Add sync_mode parameter if enabled
            if self.sync_mode:
                params["sync_mode"] = "true"
                logger.info("Using SYNCHRONOUS mode - will wait for IMS processing")
            
            logger.info("SENDING TO INTEGRATION API")
            logger.info("-" * 40)
            self.log_api_call("POST", f"{url}?{'&'.join(f'{k}={v}' for k,v in params.items())}", transaction_data)
            
            response = self.session.post(url, json=transaction_data, params=params)
            
            logger.info("RECEIVED API RESPONSE")
            logger.info("-" * 40)
            self.log_api_call("POST", f"{url}?source=triton", response=response)
            
            if response.status_code == 200:
                result = response.json()
                transaction_id = result.get("transaction_id", "unknown")
                
                logger.info("TRANSACTION SUCCESSFUL")
                logger.info(f"API Transaction ID: {transaction_id}")
                
                # Log IMS details if available (from sync mode)
                if "ims_details" in result and result["ims_details"]:
                    ims_details = result["ims_details"]
                    logger.info("IMS PROCESSING DETAILS:")
                    logger.info(f"   Status: {ims_details.get('processing_status', 'unknown')}")
                    logger.info(f"   Policy Number: {ims_details.get('policy_number', 'N/A')}")
                    logger.info(f"   Insured GUID: {ims_details.get('insured_guid', 'N/A')}")
                    logger.info(f"   Quote GUID: {ims_details.get('quote_guid', 'N/A')}")
                    if ims_details.get('error'):
                        logger.error(f"   ERROR: {ims_details['error']}")
                    if ims_details.get('processing_logs'):
                        logger.info("   Processing Logs:")
                        for log in ims_details['processing_logs'][-5:]:  # Last 5 logs
                            logger.info(f"      {log}")
                
                # Poll for status if enabled and not in sync mode
                if self.poll_status and not self.sync_mode:
                    self._poll_transaction_status(transaction_id)
                
                self.successful += 1
                self.results.append({
                    "row": row_number,
                    "policy_number": policy_number,
                    "insured": insured_name,
                    "transaction_id": transaction_id,
                    "status": "success",
                    "message": "Transaction created successfully",
                    "api_response": result
                })
            else:
                logger.error("TRANSACTION FAILED")
                logger.error(f"HTTP Status: {response.status_code}")
                logger.error(f"Error Response: {response.text}")
                
                self.failed += 1
                self.results.append({
                    "row": row_number,
                    "policy_number": policy_number,
                    "insured": insured_name,
                    "status": "failed",
                    "message": f"HTTP {response.status_code}: {response.text}",
                    "api_response": response.text
                })
                
        except Exception as e:
            logger.error(f"ERROR PROCESSING ROW {row_number}")
            logger.error(f"Exception: {str(e)}")
            logger.error(f"Exception Type: {type(e).__name__}")
            
            self.failed += 1
            self.results.append({
                "row": row_number,
                "policy_number": policy_number,
                "insured": insured_name,
                "status": "error",
                "message": str(e),
                "exception_type": type(e).__name__
            })

def get_csv_file():
    """Get CSV file from user input or command line - Windows compatible"""
    from load_csv_to_ims import list_csv_files
    available_files = list_csv_files()
    
    if not available_files:
        logger.error("No CSV files found in CSV_Samples/")
        sys.exit(1)
    
    logger.info("Available CSV files in CSV_Samples/:")
    for i, filename in enumerate(available_files, 1):
        logger.info(f"   {i}. {filename}")
    
    # Check if file specified via command line
    if len(sys.argv) > 1:
        specified_file = sys.argv[1]
        
        # If it's a number, treat as selection
        try:
            file_index = int(specified_file) - 1
            if 0 <= file_index < len(available_files):
                selected_file = available_files[file_index]
                logger.info(f"Selected file {specified_file}: {selected_file}")
                return f"CSV_Samples/{selected_file}"
        except ValueError:
            pass
        
        # If it's a filename, check if it exists
        if specified_file in available_files:
            logger.info(f"Selected file: {specified_file}")
            return f"CSV_Samples/{specified_file}"
        elif specified_file.endswith('.csv'):
            full_path = f"CSV_Samples/{specified_file}"
            if Path(full_path).exists():
                logger.info(f"Selected file: {specified_file}")
                return full_path
    
    # Interactive selection
    while True:
        try:
            choice = input(f"\nSelect CSV file (1-{len(available_files)}): ")
            file_index = int(choice) - 1
            if 0 <= file_index < len(available_files):
                selected_file = available_files[file_index]
                logger.info(f"Selected file: {selected_file}")
                return f"CSV_Samples/{selected_file}"
            else:
                print(f"Please enter a number between 1 and {len(available_files)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)

def main():
    """Main function - Windows compatible"""
    logger.info("CSV TO IMS LOADER STARTING")
    logger.info("=" * 80)
    
    # Get CSV file
    csv_file = get_csv_file()
    
    # Default values for API
    base_url = "http://localhost:8000"
    api_key = "test_api_key"
    sync_mode = False
    poll_status = False
    
    # Parse additional command line arguments (after CSV file)
    # Check for mode flags
    args = sys.argv[2:]  # Skip script name and CSV file
    for arg in args:
        if arg == "--sync":
            sync_mode = True
        elif arg == "--poll":
            poll_status = True
        elif arg.startswith("http"):
            base_url = arg
        elif not arg.startswith("--"):
            api_key = arg
    
    logger.info(f"Final CSV File: {csv_file}")
    logger.info(f"API URL: {base_url}")
    logger.info(f"API Key: {api_key}")
    if sync_mode or poll_status:
        logger.info(f"Sync Mode: {'ENABLED' if sync_mode else 'DISABLED'}")
        logger.info(f"Status Polling: {'ENABLED' if poll_status else 'DISABLED'}")
    
    # Create loader (this will do detailed service inspection)
    loader = CSVToIMSLoader(csv_file, base_url, api_key, sync_mode, poll_status)
    
    # Test health first
    if not loader.test_health():
        logger.error("Make sure the API service is running:")
        logger.error("   python run_service.py")
        sys.exit(1)
    
    # Ask for confirmation
    logger.info("This will process all rows in the CSV as NEW BUSINESS transactions.")
    if sync_mode:
        logger.info("SYNC MODE: Each transaction will wait for IMS processing to complete.")
        logger.info("   This provides immediate feedback but is slower.")
    elif poll_status:
        logger.info("POLL MODE: Transactions will be submitted asynchronously,")
        logger.info("   then polled for status updates.")
    else:
        logger.info("ASYNC MODE: Transactions will be submitted without waiting.")
        logger.info("   Check transaction status later using the API.")
    
    try:
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            logger.info("Cancelled by user.")
            sys.exit(0)
    except KeyboardInterrupt:
        logger.info("\nCancelled by user.")
        sys.exit(0)
    
    # Process the CSV
    logger.info("STARTING CSV PROCESSING")
    loader.process_csv_file()
    logger.info("CSV PROCESSING COMPLETED")

if __name__ == "__main__":
    main()