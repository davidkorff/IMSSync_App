#!/usr/bin/env python3
"""Direct test of the bind transaction logic"""

import sys
import os
import json
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our services directly
from app.services.ims.auth_service import AuthService
from app.services.ims.quote_service import QuoteService

def test_bind_with_quote_insured():
    """Test the new AddQuoteWithInsured approach"""
    
    print("=== Testing AddQuoteWithInsured ===\n")
    
    try:
        # Initialize services
        auth_service = AuthService()
        quote_service = QuoteService(auth_service)
        
        # Load test data
        with open("TEST.json", "r") as f:
            test_data = json.load(f)
        
        # Convert dates
        effective_date = datetime.strptime(test_data["effective_date"], "%m/%d/%Y").strftime("%Y-%m-%d")
        expiration_date = datetime.strptime(test_data["expiration_date"], "%m/%d/%Y").strftime("%Y-%m-%d")
        
        # Prepare quote data
        quote_data = {
            # Insured data
            "insured_name": test_data["insured_name"],
            "business_type": test_data["business_type"],
            "address_1": test_data["address_1"],
            "address_2": test_data["address_2"],
            "city": test_data["city"],
            "state": test_data["state"],
            "zip": test_data["zip"],
            # Submission/Quote data
            "effective_date": effective_date,
            "expiration_date": expiration_date,
            "program_name": test_data["program_name"],
            "class_of_business": test_data["class_of_business"],
            "producer_name": test_data["producer_name"],
            "underwriter_name": test_data["underwriter_name"],
            # Quote specifics
            "limit_amount": test_data["limit_amount"],
            "deductible_amount": test_data["deductible_amount"],
            "premium": test_data["gross_premium"],
            "commission_rate": test_data["commission_rate"]
        }
        
        print("1. Creating insured, location, submission and quote...")
        result = quote_service.create_quote_with_insured(quote_data)
        
        print("\n✅ Success! Created entities:")
        print(f"   - Insured GUID: {result['insured_guid']}")
        print(f"   - Location GUID: {result['insured_location_guid']}")
        print(f"   - Submission GUID: {result['submission_guid']}")
        print(f"   - Quote GUID: {result['quote_guid']}")
        
        # Now try to bind the quote
        print("\n2. Binding the quote...")
        bound_date = datetime.strptime(test_data["bound_date"], "%m/%d/%Y").strftime("%Y-%m-%d")
        bind_data = {
            "bound_date": bound_date,
            "policy_number": test_data["policy_number"]
        }
        
        bind_result = quote_service.bind(result['quote_guid'], bind_data)
        print(f"\n✅ Quote bound successfully!")
        print(f"   - Policy GUID: {bind_result.get('policy_guid')}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bind_with_quote_insured()