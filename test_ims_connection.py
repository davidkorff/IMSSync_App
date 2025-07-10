#!/usr/bin/env python3
"""
Test FULL Triton → Service → IMS Workflow
This script tests the complete workflow with TEST.json
"""

import sys
import os
import json
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.ims_client import IMSClient
from services.triton_processor import TritonProcessor, TritonError
from config.triton_config import get_config_for_environment
import logging

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_workflow.log')
    ]
)
logger = logging.getLogger(__name__)


def test_full_workflow():
    """Test the complete workflow: TEST.json → Service → IMS → Response"""
    
    print("=" * 80)
    print("FULL TRITON → SERVICE → IMS WORKFLOW TEST")
    print("=" * 80)
    print("📝 Logging to: test_workflow.log")
    
    # Load environment variables
    load_dotenv()
    
    # Step 1: Load TEST.json
    print("\n1️⃣ LOADING TEST.JSON")
    print("-" * 40)
    try:
        test_file = 'TEST.json'
        if not os.path.exists(test_file):
            # Try other locations
            test_file = 'tests/data/TEST.json'
            if not os.path.exists(test_file):
                test_file = 'data/TEST.json'
        
        print(f"  📁 Reading from: {test_file}")
        with open(test_file, 'r') as f:
            test_data = json.load(f)
        
        print(f"  ✅ Loaded successfully")
        print(f"  📋 Policy: {test_data.get('policy_number')}")
        print(f"  🏢 Insured: {test_data.get('insured_name')}")
        print(f"  💰 Premium: ${test_data.get('gross_premium')}")
        print(f"  📅 Effective: {test_data.get('effective_date')}")
        
        logger.info(f"Loaded TEST.json: {json.dumps(test_data, indent=2)}")
        
    except Exception as e:
        print(f"  ❌ Failed to load TEST.json: {str(e)}")
        logger.error(f"Failed to load TEST.json: {str(e)}")
        return False
    
    # Step 2: Load configuration
    print("\n2️⃣ LOADING CONFIGURATION")
    print("-" * 40)
    try:
        config = get_config_for_environment('ims_one')
        print(f"  ⚙️ Environment: ims_one")
        print(f"  🌐 IMS URL: {config['ims_base_url']}")
        print(f"  👤 Username: {config['ims_username']}")
        print(f"  🔑 Password: {'*' * 8}")
        print(f"  📊 Excel Rating: {config.get('use_excel_rating', True)}")
        
        logger.info(f"Configuration loaded: {json.dumps({k:v for k,v in config.items() if 'password' not in k}, indent=2)}")
        
    except Exception as e:
        print(f"  ❌ Failed to load configuration: {str(e)}")
        logger.error(f"Failed to load configuration: {str(e)}")
        return False
    
    # Step 3: Create IMS client
    print("\n3️⃣ CREATING IMS CLIENT")
    print("-" * 40)
    try:
        ims_client = IMSClient(config)
        print("  ✅ IMS client created")
        logger.info("IMS client created successfully")
    except Exception as e:
        print(f"  ❌ Failed to create IMS client: {str(e)}")
        logger.error(f"Failed to create IMS client: {str(e)}")
        return False
    
    # Step 4: Test IMS login
    print("\n4️⃣ AUTHENTICATING WITH IMS")
    print("-" * 40)
    try:
        print("  🔐 Attempting login...")
        if ims_client.login():
            print(f"  ✅ Successfully authenticated!")
            print(f"  🎫 Token: {ims_client.token[:30]}...")
            logger.info(f"IMS authentication successful. Token: {ims_client.token}")
        else:
            print("  ❌ Authentication failed")
            logger.error("IMS authentication failed")
            return False
    except Exception as e:
        print(f"  ❌ Login error: {str(e)}")
        logger.error(f"IMS login error: {str(e)}")
        traceback.print_exc()
        return False
    
    # Step 5: Create Triton processor
    print("\n5️⃣ INITIALIZING TRITON PROCESSOR")
    print("-" * 40)
    try:
        processor = TritonProcessor(ims_client, config)
        print("  ✅ Triton processor ready")
        logger.info("Triton processor initialized")
    except Exception as e:
        print(f"  ❌ Failed to create processor: {str(e)}")
        logger.error(f"Failed to create processor: {str(e)}")
        return False
    
    # Step 6: Process the transaction
    print("\n6️⃣ PROCESSING TRANSACTION")
    print("-" * 40)
    print(f"  📤 Transaction Type: {test_data.get('transaction_type', 'Unknown')}")
    print(f"  🔄 Processing...")
    
    try:
        # Log the full request
        logger.info("=" * 60)
        logger.info("STARTING TRANSACTION PROCESSING")
        logger.info("=" * 60)
        logger.info(f"Input data: {json.dumps(test_data, indent=2)}")
        
        # Process the transaction
        result = processor.process_transaction(test_data)
        
        # Log the full response
        logger.info("=" * 60)
        logger.info("TRANSACTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Result: {json.dumps(result, indent=2)}")
        
        print(f"\n  ✅ TRANSACTION SUCCESSFUL!")
        print(f"  📋 Transaction ID: {result.get('transaction_id')}")
        print(f"  📄 Policy Number: {result.get('policy_number')}")
        print(f"  🆔 Quote GUID: {result.get('quote_guid')}")
        print(f"  📃 Invoice Number: {result.get('invoice_number', 'Not yet available')}")
        
        # Show the workflow steps
        print("\n7️⃣ WORKFLOW STEPS COMPLETED")
        print("-" * 40)
        print("  ✅ 1. Validated Triton data")
        print("  ✅ 2. Transformed to IMS format")
        print("  ✅ 3. Created/found insured in IMS")
        print("  ✅ 4. Created submission")
        print("  ✅ 5. Created quote")
        print("  ✅ 6. Applied rating/premium")
        print("  ✅ 7. Bound policy")
        print("  ✅ 8. Linked external ID")
        
        return True
        
    except TritonError as e:
        print(f"\n  ❌ WORKFLOW FAILED!")
        print(f"  🚨 Stage: {e.stage}")
        print(f"  📝 Error: {e.message}")
        print(f"  📋 Details: {json.dumps(e.details, indent=2)}")
        
        logger.error("=" * 60)
        logger.error("TRITON ERROR")
        logger.error("=" * 60)
        logger.error(f"Stage: {e.stage}")
        logger.error(f"Message: {e.message}")
        logger.error(f"Details: {json.dumps(e.details, indent=2)}")
        logger.error("Stack trace:", exc_info=True)
        
        # Provide troubleshooting tips
        print("\n💡 TROUBLESHOOTING TIPS:")
        if e.stage == "VALIDATION":
            print("  - Check transaction_type field is valid")
            print("  - Ensure all required fields are present")
            print("  - Verify date formats (YYYY-MM-DD)")
        elif e.stage == "TRANSFORMATION":
            print("  - Check producer mapping in config")
            print("  - Verify insured data is complete")
        elif e.stage == "IMS_CALL":
            print("  - Check IMS connection is active")
            print("  - Verify credentials are correct")
            print("  - Ensure GUIDs in config are valid")
        elif e.stage == "BINDING":
            print("  - Check all required IMS data was created")
            print("  - Verify premium calculation succeeded")
        
        return False
        
    except Exception as e:
        print(f"\n  ❌ UNEXPECTED ERROR!")
        print(f"  🚨 Error: {str(e)}")
        
        logger.error("=" * 60)
        logger.error("UNEXPECTED ERROR")
        logger.error("=" * 60)
        logger.error(str(e))
        logger.error("Full stack trace:", exc_info=True)
        
        traceback.print_exc()
        return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test full Triton-IMS workflow')
    parser.add_argument('--skip-confirm', action='store_true', 
                       help='Skip confirmation prompt')
    parser.add_argument('--test-file', default='TEST.json',
                       help='Path to test JSON file (default: TEST.json)')
    
    args = parser.parse_args()
    
    if not args.skip_confirm:
        print("\n⚠️  WARNING: This will:")
        print("  1. Load TEST.json data")
        print("  2. Connect to REAL IMS system")
        print("  3. Create actual records in IMS")
        print("  4. Generate a real policy number")
        print("\nThis is NOT a mock test!")
        response = input("\nContinue? (y/n): ")
        
        if response.lower() != 'y':
            print("Aborted.")
            return 1
    
    print("\n🚀 Starting full workflow test...\n")
    
    success = test_full_workflow()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\n📊 Next Steps:")
        print("  1. Check test_workflow.log for detailed logs")
        print("  2. Verify the policy was created in IMS")
        print("  3. Test other transaction types (cancellation, endorsement)")
    else:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED!")
        print("=" * 80)
        print("\n📊 Debugging:")
        print("  1. Check test_workflow.log for detailed error logs")
        print("  2. Review the error stage and troubleshooting tips above")
        print("  3. Verify IMS credentials and network connectivity")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())