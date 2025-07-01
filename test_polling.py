#!/usr/bin/env python3
"""
Test the MySQL polling service
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add app to path
sys.path.append('/mnt/c/Users/david/OneDrive/Documents/RSG/RSG Integration')

from app.services.mysql_extractor import MySQLExtractor

# Load environment variables
load_dotenv()

async def test_polling():
    """Test the polling service components"""
    try:
        # MySQL configuration
        mysql_config = {
            'host': os.getenv('TRITON_MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('TRITON_MYSQL_PORT', '13306')),
            'database': os.getenv('TRITON_MYSQL_DATABASE', 'triton_staging'),
            'username': os.getenv('TRITON_MYSQL_USER'),
            'password': os.getenv('TRITON_MYSQL_PASSWORD')
        }
        
        print("Testing MySQL Extractor...")
        extractor = MySQLExtractor(**mysql_config)
        extractor.connect()
        
        # Test getting pending transactions
        print("Checking for pending transactions...")
        transactions = extractor.get_pending_transactions(limit=5)
        print(f"Found {len(transactions)} pending transactions")
        
        if transactions:
            for tx in transactions:
                print(f"  - ID: {tx['id']}, Type: {tx['transaction_type']}, Resource: {tx['resource_id']}")
        
        # Test getting opportunity data (if we have opportunities)
        print("\nTesting opportunity data extraction...")
        
        # Get a sample opportunity
        cursor = extractor.connection.cursor(dictionary=True)
        cursor.execute("SELECT id FROM opportunities LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            opp_id = result['id']
            print(f"Testing with opportunity ID: {opp_id}")
            
            policy_data = extractor.get_opportunity_data(opp_id)
            if policy_data:
                print(f"✅ Successfully extracted policy data:")
                print(f"  - Policy Number: {policy_data.policy_number}")
                print(f"  - Insured: {policy_data.insured_name}")
                print(f"  - Producer: {policy_data.producer_name}")
                print(f"  - Premium: ${policy_data.gross_premium}")
            else:
                print("❌ No policy data returned")
        else:
            print("No opportunities found in database")
        
        extractor.disconnect()
        print("\n✅ Polling test completed successfully!")
        
    except Exception as e:
        print(f"❌ Polling test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_polling())