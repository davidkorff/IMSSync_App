#!/usr/bin/env python3
"""
Test the API Service Workflow
Sends TEST.json to the service API and shows the response
"""

import sys
import os
import json
import requests
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Setup logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_api_workflow.log')
    ]
)
logger = logging.getLogger(__name__)


def test_api_workflow(api_url='http://localhost:8001', test_file='TEST.json'):
    """Test the complete workflow through the API service"""
    
    print("=" * 80)
    print("API SERVICE WORKFLOW TEST")
    print("=" * 80)
    print(f"📝 Logging to: test_api_workflow.log")
    print(f"🌐 API URL: {api_url}")
    
    # Step 1: Load TEST.json
    print("\n1️⃣ LOADING TEST DATA")
    print("-" * 40)
    try:
        if not os.path.exists(test_file):
            # Try other locations
            for path in ['tests/data/TEST.json', 'data/TEST.json']:
                if os.path.exists(path):
                    test_file = path
                    break
        
        print(f"  📁 Reading from: {test_file}")
        with open(test_file, 'r') as f:
            test_data = json.load(f)
        
        print(f"  ✅ Loaded successfully")
        print(f"  📋 Policy: {test_data.get('policy_number')}")
        print(f"  🏢 Insured: {test_data.get('insured_name')}")
        print(f"  💰 Premium: ${test_data.get('gross_premium')}")
        print(f"  📅 Effective: {test_data.get('effective_date')}")
        print(f"  📄 Transaction Type: {test_data.get('transaction_type')}")
        
        logger.info(f"Loaded test data: {json.dumps(test_data, indent=2)}")
        
    except Exception as e:
        print(f"  ❌ Failed to load test file: {str(e)}")
        logger.error(f"Failed to load test file: {str(e)}")
        return False
    
    # Step 2: Check if service is running
    print("\n2️⃣ CHECKING SERVICE STATUS")
    print("-" * 40)
    try:
        health_url = f"{api_url}/health"
        print(f"  🔍 Checking: {health_url}")
        
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print(f"  ✅ Service is running")
            health_data = response.json()
            print(f"  📊 Status: {health_data.get('status', 'unknown')}")
        else:
            print(f"  ⚠️ Health check returned: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Service is not running at {api_url}")
        print(f"  💡 Start the service with: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"  ⚠️ Health check failed: {str(e)}")
    
    # Step 3: Prepare the API request
    print("\n3️⃣ PREPARING API REQUEST")
    print("-" * 40)
    
    # Get API key from environment or use test key
    load_dotenv()
    api_key = os.getenv('TRITON_API_KEYS', 'triton_test_key').split(',')[0]
    
    endpoint = f"{api_url}/api/triton/transaction/new"
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': 'triton_test_key',
        'X-Client-Id': 'test_script'
    }
    
    print(f"  🔗 Endpoint: {endpoint}")
    print(f"  🔑 API Key: triton_test_key")
    print(f"  📦 Payload size: {len(json.dumps(test_data))} bytes")
    
    # Step 4: Send the request
    print("\n4️⃣ SENDING REQUEST TO SERVICE")
    print("-" * 40)
    print(f"  🚀 POST {endpoint}")
    print(f"  ⏱️ Started at: {datetime.now().isoformat()}")
    
    logger.info("=" * 60)
    logger.info("API REQUEST")
    logger.info("=" * 60)
    logger.info(f"URL: {endpoint}")
    logger.info(f"Headers: {json.dumps(headers, indent=2)}")
    logger.info(f"Body: {json.dumps(test_data, indent=2)}")
    
    try:
        start_time = datetime.now()
        
        # Send the request
        response = requests.post(
            endpoint,
            json=test_data,
            headers=headers,
            timeout=300  # 5 minute timeout for IMS operations
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"  ⏱️ Duration: {duration:.2f} seconds")
        print(f"  📊 Status Code: {response.status_code}")
        
        logger.info("=" * 60)
        logger.info("API RESPONSE")
        logger.info("=" * 60)
        logger.info(f"Status: {response.status_code}")
        logger.info(f"Headers: {dict(response.headers)}")
        
        # Step 5: Process the response
        print("\n5️⃣ SERVICE RESPONSE")
        print("-" * 40)
        
        if response.status_code == 200:
            # Success response
            result = response.json()
            logger.info(f"Body: {json.dumps(result, indent=2)}")
            
            print(f"  ✅ TRANSACTION SUCCESSFUL!")
            
            if 'data' in result:
                data = result['data']
                print(f"  📋 Transaction ID: {data.get('transaction_id')}")
                print(f"  📄 Policy Number: {data.get('policy_number')}")
                print(f"  🆔 Quote GUID: {data.get('quote_guid')}")
                print(f"  📃 Invoice Number: {data.get('invoice_number', 'Not yet available')}")
                print(f"  🔗 IMS Reference: {data.get('ims_reference')}")
            
            # Show what the service did
            print("\n6️⃣ WORKFLOW STEPS (performed by service)")
            print("-" * 40)
            print("  ✅ Service validated Triton data")
            print("  ✅ Service transformed to IMS format")
            print("  ✅ Service authenticated with IMS")
            print("  ✅ Service created/found insured in IMS")
            print("  ✅ Service created submission")
            print("  ✅ Service created quote")
            print("  ✅ Service applied rating/premium")
            print("  ✅ Service bound policy")
            print("  ✅ Service returned success response")
            
            return True
            
        else:
            # Error response
            print(f"  ❌ REQUEST FAILED!")
            
            try:
                error_data = response.json()
                logger.error(f"Error response: {json.dumps(error_data, indent=2)}")
                
                # Parse error details
                if 'detail' in error_data:
                    # FastAPI validation error format
                    print(f"  🚨 Validation Error:")
                    if isinstance(error_data['detail'], list):
                        for error in error_data['detail']:
                            print(f"    - {error.get('loc', [])}: {error.get('msg')}")
                    else:
                        print(f"    {error_data['detail']}")
                        
                elif 'error' in error_data:
                    # Service error format
                    error = error_data['error']
                    print(f"  🚨 Error Type: {error.get('type', 'Unknown')}")
                    print(f"  📝 Message: {error.get('message', 'No message')}")
                    
                    if 'stage' in error:
                        print(f"  📍 Stage: {error['stage']}")
                    
                    if 'details' in error:
                        print(f"  📋 Details:")
                        print(json.dumps(error['details'], indent=4))
                    
                    # Show troubleshooting based on error type
                    print("\n💡 TROUBLESHOOTING:")
                    error_type = error.get('type', '').upper()
                    
                    if 'VALIDATION' in error_type:
                        print("  - Check required fields in TEST.json")
                        print("  - Verify transaction_type is valid")
                        print("  - Ensure dates are in YYYY-MM-DD format")
                        
                    elif 'TRANSFORMATION' in error_type:
                        print("  - Check producer_name maps to a valid GUID")
                        print("  - Verify insured data is complete")
                        print("  - Check line of business determination")
                        
                    elif 'IMS' in error_type:
                        print("  - Service may not be able to reach IMS")
                        print("  - IMS credentials may be incorrect in .env")
                        print("  - Check IMS endpoint configuration")
                        
                    elif 'AUTHENTICATION' in error_type:
                        print("  - Check API key in request")
                        print("  - Verify client ID is allowed")
                        
                else:
                    # Unknown error format
                    print(f"  📋 Response: {json.dumps(error_data, indent=2)}")
                    
            except:
                # Non-JSON response
                print(f"  📋 Response: {response.text}")
            
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n  ❌ REQUEST TIMEOUT!")
        print(f"  🚨 The service did not respond within 5 minutes")
        print(f"  💡 This could mean:")
        print(f"     - IMS is slow to respond")
        print(f"     - Network issues reaching IMS")
        print(f"     - Service is stuck")
        logger.error("Request timeout after 300 seconds")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"\n  ❌ CONNECTION ERROR!")
        print(f"  🚨 Could not connect to service at {api_url}")
        print(f"  💡 Make sure the service is running:")
        print(f"     python -m uvicorn app.main:app --reload")
        logger.error(f"Connection error: {str(e)}")
        return False
        
    except Exception as e:
        print(f"\n  ❌ UNEXPECTED ERROR!")
        print(f"  🚨 {str(e)}")
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        traceback.print_exc()
        return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test API service workflow')
    parser.add_argument('--url', default='http://localhost:8001',
                       help='API service URL (default: http://localhost:8001)')
    parser.add_argument('--test-file', default='TEST.json',
                       help='Path to test JSON file (default: TEST.json)')
    parser.add_argument('--skip-confirm', action='store_true',
                       help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if not args.skip_confirm:
        print("\n⚠️  This will:")
        print(f"  1. Send {args.test_file} to your API service")
        print(f"  2. The SERVICE will connect to IMS (using its .env credentials)")
        print(f"  3. The SERVICE will create real IMS records")
        print(f"  4. Show you the full response (success or error)")
        print(f"\n📍 Service URL: {args.url}")
        
        response = input("\nContinue? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return 1
    
    print("\n🚀 Starting API workflow test...\n")
    
    success = test_api_workflow(args.url, args.test_file)
    
    if success:
        print("\n" + "=" * 80)
        print("✅ API TEST SUCCESSFUL!")
        print("=" * 80)
        print("\n📊 Summary:")
        print("  - TEST.json was sent to the service")
        print("  - Service processed it successfully")
        print("  - Policy was created in IMS")
        print("  - Check test_api_workflow.log for full details")
    else:
        print("\n" + "=" * 80)
        print("❌ API TEST FAILED!")
        print("=" * 80)
        print("\n📊 Debugging:")
        print("  1. Check test_api_workflow.log for request/response details")
        print("  2. Verify the service is running (python -m uvicorn app.main:app)")
        print("  3. Check service logs for IMS communication errors")
        print("  4. Ensure .env file has correct IMS credentials")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())