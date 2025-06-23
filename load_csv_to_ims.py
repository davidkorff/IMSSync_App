#!/usr/bin/env python3
"""
Load CSV submissions into IMS.
Processes each row as a New Business transaction with generated transaction IDs
"""

import csv
import json
import requests
import hashlib
import time
from datetime import datetime
import sys
import os
import logging
from pathlib import Path

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('csv_to_ims_load.log'),
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
        
        # Enhanced logging
        logger.info("=" * 80)
        logger.info("CSV TO IMS LOADER INITIALIZED")
        logger.info("=" * 80)
        logger.info(f"📄 CSV File: {self.csv_file}")
        logger.info(f"🌐 API Base URL: {self.base_url}")
        logger.info(f"🔑 API Key: {self.api_key}")
        logger.info(f"⚡ Sync Mode: {'ENABLED' if sync_mode else 'DISABLED'}")
        logger.info(f"🔄 Status Polling: {'ENABLED' if poll_status else 'DISABLED'}")
        logger.info(f"⏰ Session Started: {datetime.now().isoformat()}")
        
        # Get service info
        self.get_service_info()
    
    def get_service_info(self):
        """Get detailed service information"""
        try:
            logger.info("🔍 GETTING SERVICE INFORMATION")
            logger.info("-" * 40)
            
            # Health check with detailed info
            response = self.session.get(f"{self.base_url}/api/health")
            logger.info(f"📡 Health Check Request: GET {self.base_url}/api/health")
            logger.info(f"📊 Health Check Response: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    health_data = response.json()
                    logger.info(f"✅ Service Health: {json.dumps(health_data, indent=2)}")
                except:
                    logger.info(f"✅ Service Health: {response.text}")
            else:
                logger.error(f"❌ Health check failed: {response.text}")
            
            # Try to get service configuration/info if endpoint exists
            try:
                config_response = self.session.get(f"{self.base_url}/config")
                if config_response.status_code == 200:
                    config_data = config_response.json()
                    logger.info(f"⚙️ Service Config: {json.dumps(config_data, indent=2)}")
            except:
                logger.info("ℹ️ No /config endpoint available")
            
            logger.info("-" * 40)
            
        except Exception as e:
            logger.error(f"❌ Error getting service info: {str(e)}")
    
    def log_api_call(self, method, url, data=None, response=None):
        """Log detailed API call information"""
        logger.info(f"📡 API CALL: {method} {url}")
        
        if data:
            # Log request data (truncate if too long)
            data_str = json.dumps(data, indent=2)
            if len(data_str) > 1000:
                data_str = data_str[:1000] + "... [TRUNCATED]"
            logger.info(f"📤 Request Data: {data_str}")
        
        if response:
            logger.info(f"📊 Response Status: {response.status_code}")
            logger.info(f"📋 Response Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                response_str = json.dumps(response_data, indent=2)
                if len(response_str) > 2000:
                    response_str = response_str[:2000] + "... [TRUNCATED]"
                logger.info(f"📥 Response Data: {response_str}")
            except:
                logger.info(f"📥 Response Text: {response.text}")
    
    def generate_transaction_id(self, row_data):
        """Generate unique transaction ID based on row data"""
        # Create hash from policy number + bound date + timestamp
        unique_string = f"{row_data['Policy Number/Certificate Ref.']}{row_data['Bound Date']}{time.time()}"
        hash_id = hashlib.md5(unique_string.encode()).hexdigest()[:12].upper()
        return f"TXN_{hash_id}"
    
    def transform_csv_row_to_json(self, row):
        """Transform CSV row to JSON format expected by API"""
        
        # Generate transaction ID
        transaction_id = self.generate_transaction_id(row)
        
        # Parse dates to proper format
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                # Try MM/DD/YYYY format
                dt = datetime.strptime(date_str, "%m/%d/%Y")
                return dt.strftime("%Y-%m-%d")
            except:
                return date_str
        
        # Parse premium/fees to float
        def parse_currency(value):
            if not value:
                return 0.0
            try:
                # Remove $ and commas
                clean_value = str(value).replace('$', '').replace(',', '').strip()
                return float(clean_value) if clean_value else 0.0
            except:
                return 0.0
        
        # Determine business type from insured name
        insured_name = row.get('Insured', '')
        business_type = "Corporation"  # Default
        if "LLC" in insured_name:
            business_type = "LLC"
        elif "Inc" in insured_name or "Corporation" in insured_name:
            business_type = "Corporation"
        elif "Partnership" in insured_name:
            business_type = "Partnership"
        
        # Build the JSON structure
        transaction_data = {
            "transaction_id": transaction_id,
            "transaction_date": datetime.now().strftime("%Y-%m-%d"),
            "transaction_type": "NEW_BUSINESS",
            "source_system": "triton",
            "policy": {
                # Policy identification
                "policy_number": row.get('Policy Number/Certificate Ref.', ''),
                "program_name": row.get('Program', ''),
                "class_of_business": row.get('Class of Business', ''),
                
                # People
                "insured_name": insured_name,
                "producer_name": row.get('Producer', ''),
                "underwriter_name": row.get('Underwriter', ''),
                
                # Insured details
                "insured_address": row.get('Insured Address', ''),
                "insured_city": row.get('Insured City', ''),
                "insured_state": row.get('Insured State', ''),
                "insured_zip": row.get('Insured Zip', ''),
                "business_type": business_type,
                
                # Dates
                "effective_date": parse_date(row.get('Effective Date', '')),
                "expiration_date": parse_date(row.get('Expiration Date', '')),
                "bound_date": parse_date(row.get('Bound Date', '')),
                
                # Coverage
                "limit_amount": row.get('Limit', ''),
                "limit_general_liability": row.get('Limit (General Liability)', ''),
                "deductible_amount": row.get('Deductible', ''),
                
                # Financial
                "gross_premium": parse_currency(row.get('Gross Premium', 0)),
                "policy_fee": parse_currency(row.get('Policy Fee', 0)),
                "commission_rate": parse_currency(row.get('Commission Percent', 0)),
                "net_premium": parse_currency(row.get('Gross Premium', 0)) - parse_currency(row.get('Policy Fee', 0)),
                
                # Status
                "status": row.get('Opportunity Status', 'bound'),
                "type_of_business": row.get('Type of Business', 'New'),
                
                # Additional fields from CSV
                "coverage": row.get('Coverage', ''),
                "exposure_class": row.get('Exposure Class', ''),
                "exposure_factor": row.get('Exposure Factor', ''),
                "count": row.get('Count', ''),
                "rate": row.get('Rate', ''),
                
                # Retroactive dates if available
                "pl_retroactive_date": parse_date(row.get('PL Retroactive Date', '')),
                "gl_retroactive_date": parse_date(row.get('GL Retroactive Date', ''))
            }
        }
        
        return transaction_data
    
    def process_csv_file(self):
        """Process all rows in the CSV file"""
        try:
            with open(self.csv_file, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.DictReader(file)
                rows = list(csv_reader)
                
                print(f"📊 Found {len(rows)} policies to process")
                print("=" * 60)
                
                for index, row in enumerate(rows, 1):
                    print(f"\n🔄 Processing row {index}/{len(rows)}")
                    self.process_single_row(row, index)
                    
                    # Add small delay to avoid overwhelming the API
                    time.sleep(0.5)
                
                print("\n" + "=" * 60)
                print(f"✅ Successful: {self.successful}")
                print(f"❌ Failed: {self.failed}")
                print(f"📊 Total: {len(rows)}")
                
                # Save results to file
                self.save_results()
                
        except FileNotFoundError:
            print(f"❌ Error: CSV file not found: {self.csv_file}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error reading CSV file: {str(e)}")
            sys.exit(1)
    
    def process_single_row(self, row, row_number):
        """Process a single CSV row"""
        policy_number = row.get('Policy Number/Certificate Ref.', f'Row_{row_number}')
        insured_name = row.get('Insured', 'Unknown')
        
        logger.info("=" * 60)
        logger.info(f"🔄 PROCESSING ROW {row_number}")
        logger.info("=" * 60)
        logger.info(f"📋 Policy Number: {policy_number}")
        logger.info(f"🏢 Insured Name: {insured_name}")
        logger.info(f"🏛️ Producer: {row.get('Producer', 'Unknown')}")
        logger.info(f"👤 Underwriter: {row.get('Underwriter', 'Unknown')}")
        logger.info(f"💰 Gross Premium: {row.get('Gross Premium', 'Unknown')}")
        
        try:
            # Transform to JSON
            logger.info("🔄 Transforming CSV row to JSON format...")
            transaction_data = self.transform_csv_row_to_json(row)
            logger.info(f"🆔 Generated Transaction ID: {transaction_data['transaction_id']}")
            
            # Send to API with detailed logging
            url = f"{self.base_url}/api/transaction/new"
            params = {"source": "triton"}
            
            # Add sync_mode parameter if enabled
            if self.sync_mode:
                params["sync_mode"] = "true"
                logger.info("⚡ Using SYNCHRONOUS mode - will wait for IMS processing")
            
            logger.info("📡 SENDING TO INTEGRATION API")
            logger.info("-" * 40)
            self.log_api_call("POST", f"{url}?{'&'.join(f'{k}={v}' for k,v in params.items())}", transaction_data)
            
            response = self.session.post(url, json=transaction_data, params=params)
            
            logger.info("📥 RECEIVED API RESPONSE")
            logger.info("-" * 40)
            self.log_api_call("POST", f"{url}?source=triton", response=response)
            
            if response.status_code == 200:
                result = response.json()
                transaction_id = result.get("transaction_id", "unknown")
                
                logger.info("✅ TRANSACTION SUCCESSFUL")
                logger.info(f"🆔 API Transaction ID: {transaction_id}")
                
                # Log IMS details if available (from sync mode)
                if "ims_details" in result and result["ims_details"]:
                    ims_details = result["ims_details"]
                    logger.info("🏢 IMS PROCESSING DETAILS:")
                    logger.info(f"   Status: {ims_details.get('processing_status', 'unknown')}")
                    logger.info(f"   Policy Number: {ims_details.get('policy_number', 'N/A')}")
                    logger.info(f"   Insured GUID: {ims_details.get('insured_guid', 'N/A')}")
                    logger.info(f"   Quote GUID: {ims_details.get('quote_guid', 'N/A')}")
                    if ims_details.get('error'):
                        logger.error(f"   ❌ Error: {ims_details['error']}")
                    if ims_details.get('processing_logs'):
                        logger.info("   📝 Processing Logs:")
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
                logger.error("❌ TRANSACTION FAILED")
                logger.error(f"📊 HTTP Status: {response.status_code}")
                logger.error(f"📥 Error Response: {response.text}")
                
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
            logger.error(f"❌ ERROR PROCESSING ROW {row_number}")
            logger.error(f"🐛 Exception: {str(e)}")
            logger.error(f"🔍 Exception Type: {type(e).__name__}")
            
            self.failed += 1
            self.results.append({
                "row": row_number,
                "policy_number": policy_number,
                "insured": insured_name,
                "status": "error",
                "message": str(e),
                "exception_type": type(e).__name__
            })
    
    def _poll_transaction_status(self, transaction_id, max_polls=10, poll_interval=2):
        """Poll transaction status until it's completed or failed"""
        logger.info(f"🔄 Polling transaction status for {transaction_id}")
        
        for i in range(max_polls):
            time.sleep(poll_interval)
            
            try:
                response = self.session.get(f"{self.base_url}/api/transaction/{transaction_id}")
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status", "unknown")
                    ims_status = result.get("ims_status", "unknown")
                    
                    logger.info(f"   Poll {i+1}/{max_polls}: Status={status}, IMS Status={ims_status}")
                    
                    # Check for IMS details
                    if "ims_details" in result and result["ims_details"]:
                        ims_details = result["ims_details"]
                        if ims_details.get("policy_number"):
                            logger.info(f"   ✅ Policy Created: {ims_details['policy_number']}")
                        if ims_details.get("error"):
                            logger.error(f"   ❌ Error: {ims_details['error']}")
                    
                    # Stop polling if transaction is complete or failed
                    if status in ["completed", "failed"]:
                        break
                else:
                    logger.warning(f"   Poll {i+1} failed with status {response.status_code}")
            except Exception as e:
                logger.error(f"   Poll {i+1} error: {str(e)}")
        
        logger.info(f"   Polling complete for {transaction_id}")
    
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
        
        print(f"\n📄 Results saved to: {results_file}")
    
    def test_health(self):
        """Test if the API service is running"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                print("✅ API service is healthy")
                return True
            else:
                print(f"❌ API service health check failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Cannot connect to API service: {e}")
            return False

def list_csv_files():
    """List available CSV files in CSV_Samples directory"""
    csv_dir = Path("CSV_Samples")
    if not csv_dir.exists():
        logger.error("❌ CSV_Samples directory not found!")
        return []
    
    csv_files = list(csv_dir.glob("*.csv"))
    return [f.name for f in csv_files]

def get_csv_file():
    """Get CSV file from user input or command line"""
    available_files = list_csv_files()
    
    if not available_files:
        logger.error("❌ No CSV files found in CSV_Samples/")
        sys.exit(1)
    
    logger.info("📁 Available CSV files in CSV_Samples/:")
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
                logger.info(f"📄 Selected file {specified_file}: {selected_file}")
                return f"CSV_Samples/{selected_file}"
        except ValueError:
            pass
        
        # If it's a filename, check if it exists
        if specified_file in available_files:
            logger.info(f"📄 Selected file: {specified_file}")
            return f"CSV_Samples/{specified_file}"
        elif specified_file.endswith('.csv'):
            full_path = f"CSV_Samples/{specified_file}"
            if Path(full_path).exists():
                logger.info(f"📄 Selected file: {specified_file}")
                return full_path
    
    # Interactive selection
    while True:
        try:
            choice = input(f"\nSelect CSV file (1-{len(available_files)}): ")
            file_index = int(choice) - 1
            if 0 <= file_index < len(available_files):
                selected_file = available_files[file_index]
                logger.info(f"📄 Selected file: {selected_file}")
                return f"CSV_Samples/{selected_file}"
            else:
                print(f"Please enter a number between 1 and {len(available_files)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)

def main():
    """Main function"""
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
    
    logger.info(f"📄 Final CSV File: {csv_file}")
    logger.info(f"🌐 API URL: {base_url}")
    logger.info(f"🔑 API Key: {api_key}")
    if sync_mode or poll_status:
        logger.info(f"⚡ Sync Mode: {'ENABLED' if sync_mode else 'DISABLED'}")
        logger.info(f"🔄 Status Polling: {'ENABLED' if poll_status else 'DISABLED'}")
    
    # Create loader (this will do detailed service inspection)
    loader = CSVToIMSLoader(csv_file, base_url, api_key, sync_mode, poll_status)
    
    # Test health first
    if not loader.test_health():
        logger.error("⚠️  Make sure the API service is running:")
        logger.error("   python run_service.py")
        sys.exit(1)
    
    # Ask for confirmation
    logger.info("This will process all rows in the CSV as NEW BUSINESS transactions.")
    if sync_mode:
        logger.info("⚡ SYNC MODE: Each transaction will wait for IMS processing to complete.")
        logger.info("   This provides immediate feedback but is slower.")
    elif poll_status:
        logger.info("🔄 POLL MODE: Transactions will be submitted asynchronously,")
        logger.info("   then polled for status updates.")
    else:
        logger.info("⏩ ASYNC MODE: Transactions will be submitted without waiting.")
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
    logger.info("🚀 STARTING CSV PROCESSING")
    loader.process_csv_file()
    logger.info("🏁 CSV PROCESSING COMPLETED")

if __name__ == "__main__":
    main()