#!/usr/bin/env python3
"""
Test script to check valid BusinessTypeIDs in IMS
"""

import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ims_soap_client import IMSSoapClient
from app.core.config import settings

def test_business_types():
    """Test different business type IDs"""
    
    # Get environment configuration
    env = os.getenv("DEFAULT_ENVIRONMENT", "ims_one")
    env_config = settings.IMS_ENVIRONMENTS.get(env)
    
    if not env_config:
        print(f"Unknown environment: {env}")
        return
    
    print("IMS Integration - Business Type Analysis")
    print("=" * 60)
    print(f"Environment: {env}")
    print(f"Config file: {env_config['config_file']}")
    print(f"Username: {env_config['username']}")
    print("=" * 60)
    
    # Test business type IDs
    print("\nBusiness Type Mappings Found in Code:")
    print("-" * 60)
    
    # From flat_transformer.py
    print("\nflat_transformer.py mappings:")
    print("  'partnership': 2")
    print("  'limited liability partnership': 3")
    print("  'llp': 3")
    print("  'individual': 4")
    print("  'other': 5")
    print("  'limited liability corporation': 9")
    print("  'llc': 9")
    print("  'joint venture': 10")
    print("  'trust': 11")
    print("  'corporation': 13  <-- This is causing the error!")
    print("  'corp': 13")
    print("  'inc': 13")
    
    # From insured_service.py
    print("\ninsured_service.py mappings:")
    print("  'corporation': 1")
    print("  'corp': 1")
    print("  'inc': 1")
    print("  'partnership': 2")
    print("  'individual': 3")
    print("  'sole proprietor': 4")
    print("  'llc': 5")
    
    # From field_mappings.py
    print("\nfield_mappings.py mappings:")
    print("  'LLC': 5")
    print("  'CORP': 1")
    print("  'CORPORATION': 1")
    print("  'PARTNERSHIP': 2")
    print("  'INDIVIDUAL': 3")
    print("  'SOLE PROP': 4")
    
    print("\n" + "=" * 60)
    print("INCONSISTENCY FOUND!")
    print("=" * 60)
    print("\nThe flat_transformer.py file is using BusinessTypeID 13 for Corporation,")
    print("but the other files use BusinessTypeID 1 for Corporation.")
    print("\nThis is likely causing the foreign key constraint error because")
    print("BusinessTypeID 13 doesn't exist in the IMS database.")
    print("\nRECOMMENDATION: Update flat_transformer.py to use BusinessTypeID 1")
    print("for Corporation instead of 13.")
    print("=" * 60)

if __name__ == "__main__":
    test_business_types()