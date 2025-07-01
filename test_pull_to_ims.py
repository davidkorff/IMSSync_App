#!/usr/bin/env python3
"""
Test Script: Pull from Triton-Dev and Push to IMS
This script pulls transactions from Triton database and attempts to process them through IMS
Shows real failures that need to be addressed
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Add the app directory to the path and fix imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_pull_to_ims():
    """
    Main test function that:
    1. Pulls transactions from Triton-dev database
    2. Converts them to StandardTransaction format
    3. Attempts to process them through IMS
    4. Reports all failures for fixing
    """
    
    print("🚀 TRITON → IMS INTEGRATION TEST")
    print("="*80)
    
    try:
        # Configuration
        triton_config = {
            'host': 'localhost',
            'port': 13307,
            'database': 'greenhill_db',
            'user': 'greenhill',
            'password': '62OEqb9sjR4ZX5vBMdB521hx6W2A',
            'autocommit': False
        }
        
        ims_config = {
            'endpoint': 'https://iscmgawebservice.iscmga.com/ISCMGA_IMSWebService.asmx',
            'username': 'RSGRSGRSG',
            'password': 'RSGRSG22!',
            'company_guid': 'A9C4E1FA-C77C-4F7E-B1FB-7EACF35BF90A'
        }
        
        print("📊 STEP 1: Initialize Components")
        print("-" * 40)
        
        # Initialize Triton pull adapter
        from app.sources.triton.pull_adapter import TritonPullAdapter
        triton_adapter = TritonPullAdapter(triton_config)
        
        # Initialize IMS destination adapter
        from app.destinations.ims.destination_adapter import IMSDestinationAdapter
        ims_adapter = IMSDestinationAdapter(ims_config)
        
        # Initialize transaction log service
        from app.services.transaction_log_service import TransactionLogService
        log_service = TransactionLogService(triton_config)
        
        # Initialize core processor with logging
        from app.core.transaction_processor import TransactionProcessor
        processor = TransactionProcessor(log_service=log_service)
        processor.register_destination("ims", ims_adapter)
        
        print("✅ Components initialized")
        
        print("\n📥 STEP 2: Pull Transactions from Triton-Dev")
        print("-" * 40)
        
        # Connect to Triton database
        await triton_adapter.connect()
        
        # Get pending transactions (limit to 3 for testing)
        transactions = await triton_adapter.get_pending_transactions(limit=3)
        
        print(f"✅ Found {len(transactions)} transactions to process")
        
        if not transactions:
            print("❌ No transactions found - check database connection")
            return
        
        print("\n🔄 STEP 3: Process Each Transaction Through IMS")
        print("-" * 40)
        
        results = []
        
        for i, transaction in enumerate(transactions, 1):
            print(f"\n🔄 Processing Transaction #{i}")
            print(f"   Policy: {transaction.policy_number}")
            print(f"   Type: {transaction.transaction_type.value}")
            print(f"   Insured: {transaction.insured.name if transaction.insured else 'Unknown'}")
            print(f"   Premium: ${transaction.financials.gross_premium if transaction.financials else 0:,.2f}")
            
            try:
                # Validate transaction
                validation_errors = transaction.validate()
                if validation_errors:
                    print(f"   ❌ Validation Failed:")
                    for error in validation_errors:
                        print(f"      - {error}")
                    
                    results.append({
                        'transaction_id': transaction.source_transaction_id,
                        'policy_number': transaction.policy_number,
                        'status': 'validation_failed',
                        'errors': validation_errors
                    })
                    continue
                
                print(f"   ✅ Validation passed")
                
                # Process through IMS
                print(f"   🚀 Sending to IMS...")
                
                start_time = datetime.now()
                result = await processor.process_transaction(transaction, "ims")
                end_time = datetime.now()
                
                processing_time = (end_time - start_time).total_seconds()
                
                if result['status'] == 'completed':
                    print(f"   ✅ SUCCESS! IMS Policy: {result.get('ims_policy_number')}")
                    print(f"   ⏱️  Processing time: {processing_time:.2f}s")
                else:
                    print(f"   ❌ FAILED: {result['message']}")
                    if result.get('errors'):
                        for error in result['errors']:
                            print(f"      - {error}")
                
                results.append({
                    'transaction_id': transaction.source_transaction_id,
                    'policy_number': transaction.policy_number,
                    'status': result['status'],
                    'message': result['message'],
                    'errors': result.get('errors', []),
                    'ims_policy_number': result.get('ims_policy_number'),
                    'processing_time': processing_time
                })
                
            except Exception as e:
                print(f"   💥 EXCEPTION: {str(e)}")
                logger.exception(f"Exception processing transaction {transaction.source_transaction_id}")
                
                results.append({
                    'transaction_id': transaction.source_transaction_id,
                    'policy_number': transaction.policy_number,
                    'status': 'exception',
                    'message': str(e),
                    'errors': [str(e)]
                })
        
        print("\n📋 STEP 4: Summary Report")
        print("-" * 40)
        
        # Generate summary
        total = len(results)
        successful = len([r for r in results if r['status'] == 'completed'])
        failed = total - successful
        
        print(f"Total Transactions: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(successful/total*100) if total > 0 else 0:.1f}%")
        
        # Detailed results
        print("\n📝 DETAILED RESULTS:")
        print("-" * 60)
        
        for i, result in enumerate(results, 1):
            status_icon = "✅" if result['status'] == 'completed' else "❌"
            print(f"\n{i}. {status_icon} Transaction {result['transaction_id']}")
            print(f"   Policy: {result['policy_number']}")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
            
            if result.get('ims_policy_number'):
                print(f"   IMS Policy: {result['ims_policy_number']}")
            
            if result.get('processing_time'):
                print(f"   Time: {result['processing_time']:.2f}s")
            
            if result.get('errors'):
                print(f"   Errors:")
                for error in result['errors']:
                    print(f"     - {error}")
        
        print("\n🎯 FAILURE ANALYSIS:")
        print("-" * 40)
        
        # Analyze common failure patterns
        error_patterns = {}
        for result in results:
            if result['status'] != 'completed':
                for error in result.get('errors', [result.get('message', 'Unknown error')]):
                    error_key = error[:50] + "..." if len(error) > 50 else error
                    error_patterns[error_key] = error_patterns.get(error_key, 0) + 1
        
        if error_patterns:
            print("Common Error Patterns:")
            for error, count in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True):
                print(f"  {count}x: {error}")
        else:
            print("🎉 No failures to analyze!")
        
        print("\n✅ Test completed!")
        
        # Cleanup
        await triton_adapter.disconnect()
        
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {str(e)}")
        logger.exception("Fatal error in test")


if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_pull_to_ims())