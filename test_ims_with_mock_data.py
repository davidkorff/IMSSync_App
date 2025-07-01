#!/usr/bin/env python3
"""
Mock Data Test: Direct IMS API Testing
This script uses sample transaction data to test IMS API calls directly
Shows real IMS failures without needing database connection
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, date

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_sample_transaction():
    """Create a sample StandardTransaction for testing"""
    from app.core.models import (
        StandardTransaction, StandardInsured, StandardProducer, StandardAgency,
        StandardAddress, StandardContact, StandardFinancials, StandardCoverage,
        TransactionType
    )
    
    # Sample address
    address = StandardAddress(
        street_1="123 Main Street",
        city="Anytown",
        state="CA",
        zip_code="90210",
        street_2="Suite 100"
    )
    
    # Sample contact
    contact = StandardContact(
        name="John Smith",
        email="john.smith@example.com",
        phone="555-123-4567"
    )
    
    # Sample insured
    insured = StandardInsured(
        name="Sample Business Inc",
        business_type="Technology",
        tax_id="12-3456789",
        address=address,
        contact=contact
    )
    
    # Sample agency
    agency = StandardAgency(
        name="Test Agency",
        license_number="12345",
        address=address,
        contact=contact
    )
    
    # Sample producer
    producer = StandardProducer(
        name="Jane Producer",
        license_number="PROD123",
        agency=agency,
        email="jane@testagency.com",
        phone="555-987-6543"
    )
    
    # Sample coverage
    coverage = StandardCoverage(
        coverage_type="General Liability",
        limit="1000000",
        deductible="1000",
        premium=2500.00
    )
    
    # Sample financials
    financials = StandardFinancials(
        gross_premium=2500.00,
        commission_rate=0.15,
        commission_amount=375.00,
        fees=50.00,
        taxes=125.00,
        total_premium=2675.00
    )
    
    # Create the transaction
    transaction = StandardTransaction(
        source_system="triton",
        source_transaction_id="MOCK_001",
        transaction_type=TransactionType.NEW_BUSINESS,
        policy_number="TEST-POL-001",
        effective_date=date.today(),
        expiration_date=date(2026, 1, 1),
        insured=insured,
        producer=producer,
        agency=agency,
        coverages=[coverage],
        financials=financials,
        created_at=datetime.now()
    )
    
    return transaction


async def test_ims_with_mock_data():
    """
    Test IMS API with mock data to see real failures
    """
    
    print("🧪 MOCK DATA → IMS API TEST")
    print("="*80)
    
    try:
        # IMS Configuration
        ims_config = {
            'endpoint': 'https://iscmgawebservice.iscmga.com/ISCMGA_IMSWebService.asmx',
            'username': 'RSGRSGRSG',
            'password': 'RSGRSG22!',
            'company_guid': 'A9C4E1FA-C77C-4F7E-B1FB-7EACF35BF90A'
        }
        
        print("📊 STEP 1: Initialize IMS Components")
        print("-" * 40)
        
        # Initialize IMS destination adapter
        from app.destinations.ims.destination_adapter import IMSDestinationAdapter
        ims_adapter = IMSDestinationAdapter(ims_config)
        
        # Initialize core processor
        from app.core.transaction_processor import TransactionProcessor
        processor = TransactionProcessor()
        processor.register_destination("ims", ims_adapter)
        
        print("✅ IMS components initialized")
        
        print("\n📝 STEP 2: Create Sample Transaction")
        print("-" * 40)
        
        # Create sample transaction
        transaction = create_sample_transaction()
        
        print(f"✅ Created sample transaction:")
        print(f"   Policy: {transaction.policy_number}")
        print(f"   Type: {transaction.transaction_type.value}")
        print(f"   Insured: {transaction.insured.name}")
        print(f"   Premium: ${transaction.financials.gross_premium:,.2f}")
        print(f"   Producer: {transaction.producer.name}")
        print(f"   Agency: {transaction.agency.name}")
        
        print("\n🔍 STEP 3: Validate Transaction")
        print("-" * 40)
        
        # Validate transaction
        validation_errors = transaction.validate()
        if validation_errors:
            print(f"❌ Validation Failed:")
            for error in validation_errors:
                print(f"   - {error}")
            return
        
        print("✅ Transaction validation passed")
        
        print("\n🚀 STEP 4: Send to IMS API")
        print("-" * 40)
        
        # Process through IMS
        print("Sending transaction to IMS...")
        
        start_time = datetime.now()
        result = await processor.process_transaction(transaction, "ims")
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"\n📋 STEP 5: Results")
        print("-" * 40)
        
        if result['status'] == 'completed':
            print(f"✅ SUCCESS!")
            print(f"   IMS Policy: {result.get('ims_policy_number')}")
            print(f"   Processing time: {processing_time:.2f}s")
            print(f"   Message: {result['message']}")
        else:
            print(f"❌ FAILED!")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
            print(f"   Processing time: {processing_time:.2f}s")
            
            if result.get('errors'):
                print(f"\n🔍 Detailed Errors:")
                for i, error in enumerate(result['errors'], 1):
                    print(f"   {i}. {error}")
            
            if result.get('raw_response'):
                print(f"\n📡 Raw IMS Response:")
                print(f"   {result['raw_response']}")
        
        print("\n🎯 ANALYSIS:")
        print("-" * 40)
        
        if result['status'] != 'completed':
            print("This shows the exact IMS API failures you need to fix:")
            print("1. Check if producer/agency GUIDs need to be looked up first")
            print("2. Verify required fields are properly mapped")
            print("3. Check data format requirements (dates, amounts, etc.)")
            print("4. Validate IMS business rules and constraints")
        else:
            print("🎉 Mock data successfully processed through IMS!")
            print("Ready to connect real Triton data!")
        
        return result
        
    except Exception as e:
        print(f"\n💥 EXCEPTION: {str(e)}")
        logger.exception("Exception in mock data test")
        return {'status': 'exception', 'message': str(e)}


if __name__ == "__main__":
    # Run the async test
    result = asyncio.run(test_ims_with_mock_data())
    
    print(f"\n✅ Test completed with status: {result.get('status', 'unknown')}")