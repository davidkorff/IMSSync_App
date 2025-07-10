#!/usr/bin/env python3
"""
Test the FULL Triton → Service → IMS workflow
This test shows exactly what happens at each step
"""

import json
import sys
import os
from datetime import datetime

# Add parent directory to path so we can import the app modules
sys.path.insert(0, os.path.abspath('..'))

from app.services.triton_processor import TritonProcessor, TritonError
from app.services.ims_client import IMSClient
from app.config.triton_config import get_config_for_environment


class MockIMSClient:
    """Mock IMS client for testing without actual IMS connection"""
    
    def __init__(self, config):
        self.config = config
        self.token = "MOCK-TOKEN-12345"
        print("🔌 Mock IMS Client initialized (no real IMS connection)")
    
    def login(self):
        print("  → Mock IMS login successful")
        return True
    
    def find_or_create_insured(self, insured_data):
        print(f"\n📋 IMS: Find or Create Insured")
        print(f"  → Name: {insured_data['name']}")
        print(f"  → State: {insured_data.get('state')}")
        print(f"  → Address: {insured_data.get('address')}")
        # Return mock GUID
        mock_guid = "INSURED-GUID-12345"
        print(f"  ✓ Insured GUID: {mock_guid}")
        return mock_guid
    
    def create_submission(self, submission_data):
        print(f"\n📄 IMS: Create Submission")
        print(f"  → Insured GUID: {submission_data['insured_guid']}")
        print(f"  → Producer GUID: {submission_data['producer_guid']}")
        print(f"  → Date: {submission_data['submission_date']}")
        mock_guid = "SUBMISSION-GUID-67890"
        print(f"  ✓ Submission GUID: {mock_guid}")
        return mock_guid
    
    def create_quote(self, quote_data):
        print(f"\n💰 IMS: Create Quote")
        print(f"  → Submission GUID: {quote_data['submission_guid']}")
        print(f"  → Effective: {quote_data['effective_date']}")
        print(f"  → Expiration: {quote_data['expiration_date']}")
        print(f"  → State: {quote_data['state']}")
        print(f"  → Line GUID: {quote_data['line_guid']}")
        mock_guid = "QUOTE-GUID-11111"
        print(f"  ✓ Quote GUID: {mock_guid}")
        return mock_guid
    
    def add_quote_option(self, quote_guid):
        print(f"\n🔧 IMS: Add Quote Option")
        print(f"  → Quote GUID: {quote_guid}")
        mock_id = 12345
        print(f"  ✓ Option ID: {mock_id}")
        return mock_id
    
    def add_premium(self, quote_guid, option_id, premium):
        print(f"\n💵 IMS: Add Premium")
        print(f"  → Quote GUID: {quote_guid}")
        print(f"  → Option ID: {option_id}")
        print(f"  → Premium: ${premium:,.2f}")
        print(f"  ✓ Premium added")
    
    def import_excel_rater(self, **kwargs):
        print(f"\n📊 IMS: Import Excel Rater")
        print(f"  → Quote GUID: {kwargs['quote_guid']}")
        print(f"  → File: {kwargs['file_name']}")
        print(f"  → Rater ID: {kwargs['rater_id']}")
        print(f"  → Excel file would contain ALL Triton data fields")
        print(f"  ✓ Excel rating successful")
        return {
            'success': True,
            'premiums': [{
                'quote_option_guid': 'OPTION-GUID-99999',
                'premium_total': kwargs.get('premium', 3094),
                'fee_total': 250
            }]
        }
    
    def save_rating_sheet(self, **kwargs):
        print(f"\n💾 IMS: Save Rating Sheet")
        print(f"  → Saving raw Triton data as Excel backup")
        print(f"  ✓ Rating sheet saved")
    
    def bind_quote(self, option_id):
        print(f"\n✅ IMS: Bind Quote")
        print(f"  → Option ID: {option_id}")
        policy_number = "POL-2024-TEST-001"
        print(f"  ✓ Policy Number: {policy_number}")
        return policy_number
    
    def get_latest_invoice(self, policy_number):
        print(f"\n📃 IMS: Get Latest Invoice")
        print(f"  → Policy: {policy_number}")
        print(f"  ✓ Invoice not immediately available (typical)")
        return None
    
    def update_external_id(self, quote_guid, external_id, source):
        print(f"\n🔗 IMS: Link External ID")
        print(f"  → Quote GUID: {quote_guid}")
        print(f"  → External ID: {external_id}")
        print(f"  → Source: {source}")
        print(f"  ✓ External ID linked")
    
    def execute_command(self, procedure, params):
        print(f"\n🗄️ IMS: Execute Custom Procedure")
        print(f"  → Procedure: {procedure}")
        print(f"  → Storing complete Triton JSON data")
        print(f"  ✓ Data stored")


def test_full_workflow(use_real_ims=False):
    """Test the complete workflow from Triton data to IMS"""
    
    print("=" * 80)
    print("FULL TRITON → SERVICE → IMS WORKFLOW TEST")
    print("=" * 80)
    
    # Load TEST.json
    print("\n📁 Loading TEST.json...")
    with open('data/TEST.json', 'r') as f:
        test_data = json.load(f)
    
    print(f"  Policy: {test_data['policy_number']}")
    print(f"  Insured: {test_data['insured_name']}")
    print(f"  Premium: ${test_data['gross_premium']}")
    
    # Get configuration
    print("\n⚙️ Loading configuration...")
    config = get_config_for_environment('ims_one')
    print(f"  Environment: ims_one")
    print(f"  Default Producer: {config['producers']['default'][:8]}...")
    print(f"  Excel Rating: {config.get('use_excel_rating', True)}")
    
    # Create IMS client (mock or real)
    if use_real_ims:
        print("\n🌐 Creating REAL IMS client...")
        ims_client = IMSClient(config)
    else:
        print("\n🧪 Creating MOCK IMS client...")
        ims_client = MockIMSClient(config)
    
    # Create processor
    print("\n🚀 Initializing Triton Processor...")
    processor = TritonProcessor(ims_client, config)
    
    # Process the transaction
    print("\n" + "=" * 80)
    print("PROCESSING TRANSACTION")
    print("=" * 80)
    
    try:
        # Show what we're sending
        print("\n📤 Input Data:")
        print(f"  Transaction Type: {test_data.get('transaction_type')} → will be normalized to 'binding'")
        print(f"  Structure: Flat (TEST.json style)")
        
        # Process it
        result = processor.process_transaction(test_data)
        
        print("\n" + "=" * 80)
        print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        
        print("\n📊 Final Result:")
        print(json.dumps(result, indent=2))
        
        print("\n🎯 Summary:")
        print(f"  1. Triton data received (flat structure)")
        print(f"  2. Insured created/found in IMS")
        print(f"  3. Submission created")
        print(f"  4. Quote created")
        print(f"  5. Premium/Rating applied")
        print(f"  6. Policy bound")
        print(f"  7. External ID linked")
        print(f"  8. All Triton data preserved in Excel/JSON")
        
        return True
        
    except TritonError as e:
        print("\n" + "=" * 80)
        print("❌ WORKFLOW FAILED!")
        print("=" * 80)
        
        print(f"\n🚨 Error Stage: {e.stage}")
        print(f"📝 Message: {e.message}")
        print(f"📋 Details: {json.dumps(e.details, indent=2)}")
        
        print("\n💡 Troubleshooting:")
        if e.stage == "BINDING":
            print("  - Check insured data is complete")
            print("  - Verify producer mapping")
            print("  - Ensure IMS connection is active")
        elif e.stage == "VALIDATION":
            print("  - Check transaction_type field")
            print("  - Verify required fields are present")
        
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test full Triton-IMS workflow')
    parser.add_argument('--real-ims', action='store_true', 
                       help='Use real IMS connection (requires credentials)')
    
    args = parser.parse_args()
    
    if args.real_ims:
        print("⚠️  WARNING: Using REAL IMS connection!")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return 1
    
    success = test_full_workflow(use_real_ims=args.real_ims)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())