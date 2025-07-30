#!/usr/bin/env python3
"""
Comprehensive test script for all 4 IMS bind methods
Tests each method with the best possible parameters
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent))

from app.services.ims.auth_service import AuthService
from app.services.ims.insured_service import InsuredService
from app.services.ims.quote_service import QuoteService
from app.services.ims.data_access_service import DataAccessService

async def test_all_bind_methods():
    """Test all 4 bind methods comprehensively"""
    
    print("="*80)
    print("COMPREHENSIVE IMS BIND METHOD TESTING")
    print(f"Test started at: {datetime.now()}")
    print("="*80)
    
    # Initialize services
    auth_service = AuthService()
    insured_service = InsuredService(auth_service)
    quote_service = QuoteService(auth_service)
    data_access_service = DataAccessService(auth_service)
    
    # Test data
    test_data = {
        "insured_name": f"Bind Test Company {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "address_1": "123 Test Street",
        "city": "Test City",
        "state": "MI",
        "zip": "12345",
        "effective_date": "2025-01-01",
        "expiration_date": "2026-01-01",
        "commission_rate": 10.0,
        "company_commission": 5.0
    }
    
    try:
        # Step 1: Create insured
        print("\n1. Creating test insured...")
        insured_guid = insured_service.create_insured(test_data)
        print(f"   ✓ Insured created: {insured_guid}")
        
        # Step 2: Create quote
        print("\n2. Creating test quote...")
        result = quote_service.create_submission_and_quote(insured_guid, test_data)
        quote_guid = result['quote_guid']
        print(f"   ✓ Quote created: {quote_guid}")
        
        # Step 3: Add quote option
        print("\n3. Adding quote option...")
        option_guid = quote_service.add_quote_option(quote_guid)
        print(f"   ✓ Quote option added: {option_guid}")
        
        # Step 4: Try to get integer quote option ID via DataAccess
        print("\n4. Attempting to get integer quote option ID...")
        try:
            options = data_access_service.get_quote_options(quote_guid)
            if options and len(options) > 0:
                option_id = options[0].get('QuoteOptionID')
                print(f"   ✓ Found quote option ID: {option_id}")
            else:
                option_id = None
                print("   ✗ No quote options returned from DataAccess")
        except Exception as e:
            option_id = None
            print(f"   ✗ DataAccess failed: {str(e)[:100]}")
        
        # Now test all 4 bind methods
        print("\n" + "="*80)
        print("TESTING ALL 4 BIND METHODS")
        print("="*80)
        
        bind_data = {"bind_date": datetime.now().strftime("%Y-%m-%d")}
        success = False
        
        # Method 1: BindQuoteWithInstallment with -1
        print("\nMethod 1: BindQuoteWithInstallment(quoteGuid, -1)")
        print("- Documentation says: 'Passing in a -1 will bill as single pay'")
        try:
            result = quote_service.bind_single_pay(quote_guid, bind_data)
            print(f"✓ SUCCESS! Policy GUID: {result.get('policy_guid')}")
            success = True
        except Exception as e:
            print(f"✗ FAILED: {str(e)[:200]}")
        
        # Method 2: BindQuote (simple)
        if not success:
            print("\nMethod 2: BindQuote(quoteGuid)")
            print("- Simple method with just quote GUID")
            try:
                result = quote_service.bind(quote_guid, bind_data)
                print(f"✓ SUCCESS! Policy GUID: {result.get('policy_guid')}")
                success = True
            except Exception as e:
                print(f"✗ FAILED: {str(e)[:200]}")
        
        # Method 3: Bind with integer ID
        if not success and option_id:
            print(f"\nMethod 3: Bind({option_id})")
            print("- Using integer quote option ID from database")
            try:
                result = quote_service.bind_with_option_id(option_id, bind_data)
                print(f"✓ SUCCESS! Policy GUID: {result.get('policy_guid')}")
                success = True
            except Exception as e:
                print(f"✗ FAILED: {str(e)[:200]}")
        elif not success:
            print("\nMethod 3: Bind(quoteOptionID) - SKIPPED")
            print("- Need integer quote option ID (not available)")
        
        # Method 4: BindWithInstallment with integer ID and -1
        if not success and option_id:
            print(f"\nMethod 4: BindWithInstallment({option_id}, -1)")
            print("- Using integer ID with -1 for single pay")
            try:
                result = quote_service.bind_single_pay_with_option(option_id, bind_data)
                print(f"✓ SUCCESS! Policy GUID: {result.get('policy_guid')}")
                success = True
            except Exception as e:
                print(f"✗ FAILED: {str(e)[:200]}")
        elif not success:
            print("\nMethod 4: BindWithInstallment(quoteOptionID, -1) - SKIPPED")
            print("- Need integer quote option ID (not available)")
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        if success:
            print("✓ At least one bind method succeeded!")
        else:
            print("✗ All bind methods failed")
            print("\nRoot causes:")
            print("1. IMS database lacks installment billing configuration")
            print("2. AddQuoteOption returns GUID but Bind methods need integer ID")
            print("3. Missing spGetQuoteOptions_WS stored procedure")
            print("4. All methods internally check for installment configuration")
            
            print("\nRecommendations:")
            print("1. Ask IMS administrator to configure installment billing")
            print("2. Create spGetQuoteOptions_WS stored procedure")
            print("3. OR investigate creating quotes in 'bound' state initially")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting comprehensive bind test...")
    asyncio.run(test_all_bind_methods())