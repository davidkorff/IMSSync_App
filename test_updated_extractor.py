#!/usr/bin/env python3
"""
Test the updated MySQL extractor with correct table structure
"""

import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

def test_updated_extractor():
    """Test the updated MySQL extractor"""
    try:
        from app.services.mysql_extractor import MySQLExtractor
        
        # MySQL configuration
        mysql_config = {
            'host': 'triton-dev.ctfcgagzmyca.us-east-1.rds.amazonaws.com',
            'port': 3306,
            'database': 'greenhill_db',
            'username': 'greenhill',
            'password': '62OEqb9sjR4ZX5vBMdB521hx6W2A'
        }
        
        print("Testing updated MySQL Extractor...")
        extractor = MySQLExtractor(**mysql_config)
        extractor.connect()
        
        # Find a bound opportunity to test with
        cursor = extractor.connection.cursor()
        cursor.execute("""
            SELECT id 
            FROM opportunities 
            WHERE status = 'bound' 
            AND policy_number IS NOT NULL 
            AND policy_number != ''
            ORDER BY bound_date DESC 
            LIMIT 1
        """)
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            print("❌ No bound opportunities found")
            return False
            
        opp_id = result[0]
        print(f"Testing with opportunity ID: {opp_id}")
        
        # Test extracting opportunity data
        print("\nExtracting opportunity data...")
        policy_data = extractor.get_opportunity_data(opp_id)
        
        if policy_data:
            print("✅ Successfully extracted policy data:")
            print(f"  Policy Number: {policy_data.policy_number}")
            print(f"  Insured: {policy_data.insured_name}")
            print(f"  Tax ID: {policy_data.insured_tax_id}")
            print(f"  Address: {policy_data.insured_address}, {policy_data.insured_city}, {policy_data.insured_state}")
            print(f"  Producer: {policy_data.producer_name} ({policy_data.producer_email})")
            print(f"  Agency: {policy_data.agency_name}")
            print(f"  Program: {policy_data.program_name}")
            print(f"  Premium: ${policy_data.gross_premium:,.2f}")
            print(f"  Policy Fee: ${policy_data.policy_fee:,.2f}")
            print(f"  Taxes & Fees: ${policy_data.taxes_and_fees:,.2f}")
            print(f"  Commission Rate: {policy_data.commission_rate}%")
            print(f"  Limits: ${policy_data.limit_amount:,.0f}")
            print(f"  Deductible: ${policy_data.deductible_amount:,.0f}")
            print(f"  Effective: {policy_data.effective_date}")
            print(f"  Expiration: {policy_data.expiration_date}")
            print(f"  Business Type: {policy_data.business_type}")
            
            # Test helper methods
            print("\nTesting helper methods...")
            fees = extractor.get_quote_fees(opp_id)
            print(f"  Fees data: {fees}")
            
            broker_info = extractor.get_broker_information(opp_id)
            print(f"  Broker info: {broker_info}")
            
            print("\n✅ Extraction test completed successfully!")
            
        else:
            print("❌ No policy data returned")
            return False
        
        extractor.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_updated_extractor()
    
    if success:
        print("\n" + "="*60)
        print("EXTRACTOR WORKING! READY FOR IMS INTEGRATION")
        print("Next steps:")
        print("1. Create ims_transaction_logs table") 
        print("2. Test the complete workflow")
        print("3. Start processing real transactions")
        print("="*60)
    else:
        print("\n❌ Fix extractor issues before proceeding")