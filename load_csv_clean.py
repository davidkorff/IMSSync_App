#!/usr/bin/env python3
"""
Clean CSV loader for Windows - no emojis, no imports from original
"""

import csv
import json
import requests
import hashlib
import time
import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CSVToIMSLoader:
    def __init__(self, csv_file, base_url="http://localhost:8000", api_key="test_api_key",
                 sync_mode=False, poll_status=False):
        self.csv_file = csv_file
        self.base_url = base_url
        self.api_key = api_key
        self.sync_mode = sync_mode
        self.poll_status = poll_status
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        })
        self.successful = 0
        self.failed = 0
        self.results = []
        
        logger.info("=" * 80)
        logger.info("CSV TO IMS LOADER INITIALIZED")
        logger.info("=" * 80)
        logger.info(f"CSV File: {self.csv_file}")
        logger.info(f"API Base URL: {self.base_url}")
        logger.info(f"API Key: {self.api_key}")
        logger.info(f"Sync Mode: {'ENABLED' if sync_mode else 'DISABLED'}")
        logger.info(f"Status Polling: {'ENABLED' if poll_status else 'DISABLED'}")
        logger.info(f"Session Started: {datetime.now().isoformat()}")
        
        self.get_service_info()
    
    def get_service_info(self):
        """Get service health status"""
        try:
            logger.info("GETTING SERVICE INFORMATION")
            logger.info("-" * 40)
            response = self.session.get(f"{self.base_url}/api/health")
            logger.info(f"Health Check Request: GET {self.base_url}/api/health")
            logger.info(f"Health Check Response: {response.status_code}")
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"Service Health: {json.dumps(health_data, indent=2)}")
            else:
                logger.warning(f"Health check failed with status: {response.status_code}")
            
            logger.info("-" * 40)
        except Exception as e:
            logger.error(f"Error getting service info: {str(e)}")
    
    def test_health(self):
        """Test if the API service is running"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                print("API service is healthy")
                return True
            else:
                print(f"API service health check failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"Cannot connect to API service: {e}")
            return False
    
    def transform_csv_row_to_json(self, row):
        """Transform a CSV row to JSON format for the API"""
        # Generate unique transaction ID
        transaction_id = f"TXN_{hashlib.md5(json.dumps(row, sort_keys=True).encode()).hexdigest()[:12].upper()}"
        
        return {
            "transaction_id": transaction_id,
            "transaction_date": datetime.now().strftime("%Y-%m-%d"),
            "transaction_type": "NEW_BUSINESS",
            "source_system": "triton",
            "policy": {
                "policy_number": row.get('Policy Number/Certificate Ref.', ''),
                "program_name": row.get('Program Name', ''),
                "class_of_business": row.get('Class of Business', ''),
                "insured_name": row.get('Insured', ''),
                "producer_name": row.get('Producer', ''),
                "underwriter_name": row.get('Underwriter', ''),
                "insured_address": row.get('Insured Address', ''),
                "insured_city": row.get('Insured City', ''),
                "insured_state": row.get('Insured State', ''),
                "insured_zip": row.get('Insured Zip', ''),
                "business_type": row.get('Business Type', ''),
                "effective_date": self.parse_date(row.get('Effective Date', '')),
                "expiration_date": self.parse_date(row.get('Expiration Date', '')),
                "bound_date": self.parse_date(row.get('Bound Date', '')),
                "limit_amount": row.get('Limit Amounts', ''),
                "limit_general_liability": row.get('General Liability Limit', ''),
                "deductible_amount": row.get('Deductible', ''),
                "gross_premium": self.parse_float(row.get('Gross Premium', 0)),
                "policy_fee": self.parse_float(row.get('Policy Fee', 0)),
                "commission_rate": self.parse_float(row.get('Commission', 0)),
                "net_premium": self.parse_float(row.get('Net Premium', 0)),
                "status": "bound",
                "type_of_business": row.get('Type of Business', ''),
                "coverage": row.get('Coverage', '')
            }
        }
    
    def parse_date(self, date_str):
        """Parse date string to ISO format"""
        if not date_str:
            return None
        try:
            # Try MM/DD/YYYY format
            dt = datetime.strptime(date_str.strip(), "%m/%d/%Y")
            return dt.strftime("%Y-%m-%d")
        except:
            return date_str
    
    def parse_float(self, value):
        """Parse float value from string"""
        if not value:
            return 0.0
        try:
            # Remove commas and dollar signs
            cleaned = str(value).replace(',', '').replace('$', '').strip()
            return float(cleaned)
        except:
            return 0.0
    
    def process_csv_file(self):
        """Process the CSV file"""
        print(f"\nFound CSV file: {self.csv_file}")
        
        with open(self.csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        print(f"Found {len(rows)} policies to process")
        print("=" * 60)
        
        for i, row in enumerate(rows, 1):
            print(f"\nProcessing row {i}/{len(rows)}")
            time.sleep(0.5)  # Small delay between requests
            self.process_row(row, i)
        
        print("\n" + "=" * 60)
        print(f"Successful: {self.successful}")
        print(f"Failed: {self.failed}")
        print(f"Total: {len(rows)}")
        
        self.save_results()
    
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
            
            # Send to API
            url = f"{self.base_url}/api/transaction/new"
            params = {"source": "triton"}
            
            if self.sync_mode:
                params["sync_mode"] = "true"
                logger.info("Using SYNCHRONOUS mode - will wait for IMS processing")
            
            logger.info("SENDING TO INTEGRATION API")
            logger.info("-" * 40)
            logger.info(f"API CALL: POST {url}?{'&'.join(f'{k}={v}' for k,v in params.items())}")
            logger.info(f"Request Data: {json.dumps(transaction_data, indent=2)[:500]}... [TRUNCATED]")
            
            response = self.session.post(url, json=transaction_data, params=params)
            
            logger.info("RECEIVED API RESPONSE")
            logger.info("-" * 40)
            logger.info(f"Response Status: {response.status_code}")
            logger.info(f"Response Headers: {dict(response.headers)}")
            logger.info(f"Response Data: {json.dumps(response.json(), indent=2)}")
            
            if response.status_code == 200:
                result = response.json()
                transaction_id = result.get("transaction_id", "unknown")
                
                logger.info("TRANSACTION SUCCESSFUL")
                logger.info(f"API Transaction ID: {transaction_id}")
                
                # Log IMS details if available
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
                        for log in ims_details['processing_logs'][-5:]:
                            logger.info(f"      {log}")
                
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
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            self.failed += 1
            self.results.append({
                "row": row_number,
                "policy_number": policy_number,
                "insured": insured_name,
                "status": "error",
                "message": str(e),
                "exception_type": type(e).__name__
            })
    
    def save_results(self):
        """Save processing results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"csv_load_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                "summary": {
                    "total": len(self.results),
                    "successful": self.successful,
                    "failed": self.failed,
                    "csv_file": self.csv_file,
                    "processed_at": datetime.now().isoformat()
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")

def main():
    """Main function"""
    logger.info("CSV TO IMS LOADER STARTING")
    logger.info("=" * 80)
    
    # Check for CSV file argument
    if len(sys.argv) < 2:
        print("Usage: python load_csv_clean.py <csv_number> [--sync] [--poll]")
        print("Example: python load_csv_clean.py 2 --sync")
        sys.exit(1)
    
    # Get CSV file
    csv_number = sys.argv[1]
    csv_files = sorted(Path("CSV_Samples").glob("*.csv"))
    
    if not csv_files:
        logger.error("No CSV files found in CSV_Samples/")
        sys.exit(1)
    
    try:
        file_index = int(csv_number) - 1
        if 0 <= file_index < len(csv_files):
            csv_file = str(csv_files[file_index])
        else:
            logger.error(f"Invalid file number. Choose 1-{len(csv_files)}")
            sys.exit(1)
    except ValueError:
        logger.error("Please provide a file number")
        sys.exit(1)
    
    # Parse options
    sync_mode = "--sync" in sys.argv
    poll_status = "--poll" in sys.argv
    
    logger.info(f"Selected CSV File: {csv_file}")
    logger.info(f"Sync Mode: {'ENABLED' if sync_mode else 'DISABLED'}")
    logger.info(f"Poll Status: {'ENABLED' if poll_status else 'DISABLED'}")
    
    # Create loader
    loader = CSVToIMSLoader(csv_file, sync_mode=sync_mode, poll_status=poll_status)
    
    # Test health
    if not loader.test_health():
        logger.error("API service is not running. Start it first.")
        sys.exit(1)
    
    # Confirm
    print("\nThis will process all rows as NEW BUSINESS transactions.")
    if sync_mode:
        print("SYNC MODE: Will wait for IMS processing results.")
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    # Process
    logger.info("STARTING CSV PROCESSING")
    loader.process_csv_file()
    logger.info("CSV PROCESSING COMPLETED")

if __name__ == "__main__":
    main()