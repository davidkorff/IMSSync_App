#!/usr/bin/env python3
"""Direct test of IMS client with minimal setup"""

import os
import sys
import logging
from datetime import datetime, date

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.ims_client import IMSClient

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Test configuration
config = {
    'ims_username': os.getenv('IMS_USERNAME'),
    'ims_password': os.getenv('IMS_PASSWORD')
}

print("Starting direct IMS test...")
print(f"IMS Username: {config['ims_username']}")

try:
    # Create IMS client
    ims = IMSClient(config)
    
    # Login
    print("\n1. Logging in to IMS...")
    if ims.login():
        print("   ✓ Login successful")
    else:
        print("   ✗ Login failed")
        sys.exit(1)
    
    # Create test insured
    print("\n2. Creating insured...")
    insured_data = {
        'name': 'Direct Test LLC',
        'business_type_id': 9,  # LLC/LLP
        'tax_id': '12-3456789',
        'address': '123 Test St',
        'city': 'TestCity',
        'state': 'TX',
        'zip': '75001',
        'phone': '555-1234',
        'dba': ''
    }
    
    insured_guid = ims.find_or_create_insured(insured_data)
    print(f"   ✓ Insured created: {insured_guid}")
    
    # Create submission
    print("\n3. Creating submission...")
    submission_data = {
        'insured_guid': insured_guid,
        'producer_guid': 'f68f20d8-fde0-e511-80e1-00155d5e88c6',  # Mike Woodworth
        'underwriter_guid': 'f3a08a47-cf0d-4bae-b8fc-92ed98c89dca',  # Default underwriter
        'submission_date': date.today()
    }
    
    submission_guid = ims.create_submission(submission_data)
    print(f"   ✓ Submission created: {submission_guid}")
    
    # Create quote
    print("\n4. Creating quote...")
    quote_data = {
        'submission_guid': submission_guid,
        'effective_date': date(2025, 9, 24),
        'expiration_date': date(2026, 9, 24),
        'state': 'TX',
        'line_guid': '2b93c2c4-d810-474f-9b2f-bf456e36fec0',  # Primary
        'producer_guid': 'f68f20d8-fde0-e511-80e1-00155d5e88c6',
        'location_guids': {
            'issuing': '74f97e66-0eab-e311-be89-78e3b596e756',
            'company': '74f97e66-0eab-e311-be89-78e3b596e756',
            'quoting': '74f97e66-0eab-e311-be89-78e3b596e756'
        },
        'underwriter_guid': 'f3a08a47-cf0d-4bae-b8fc-92ed98c89dca',
        'insured_business_type_id': 9,
        # Add RiskInformation fields
        'insured_name': 'Direct Test LLC',
        'insured_dba': '',
        'tax_id': '12-3456789',
        'address': '123 Test St',
        'city': 'TestCity',
        'zip': '75001',
        'phone': '555-1234'
    }
    
    quote_guid = ims.create_quote(quote_data)
    print(f"   ✓ Quote created: {quote_guid}")
    
    print("\n✓ TEST COMPLETED SUCCESSFULLY!")
    
except Exception as e:
    print(f"\n✗ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)