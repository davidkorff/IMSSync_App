#!/usr/bin/env python3
"""
Test Producer Lookup Functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ims.producer_service import IMSProducerService
from app.services.ims.workflow_orchestrator import IMSWorkflowOrchestrator
from app.models.transaction_models import Transaction, TransactionStatus
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_producer_lookup():
    """Test producer name to GUID lookup"""
    
    # Test data - producer names from the CSV
    test_producers = [
        "Adam Griggs",
        "Melissa Niedelman",
        "Gloria McShane",
        "J.A. Knapp Agency",
        "AmWINS Brokerage of the Midwest - IL",
        "R.E. Chaix & Associates Insurance Brokers Inc.-Irvine"
    ]
    
    # Initialize service
    producer_service = IMSProducerService()
    
    logger.info("=" * 80)
    logger.info("TESTING PRODUCER LOOKUP SERVICE")
    logger.info("=" * 80)
    
    for producer_name in test_producers:
        logger.info(f"\nSearching for producer: '{producer_name}'")
        logger.info("-" * 60)
        
        try:
            # Use the lookup method
            producer_guid = producer_service.get_producer_by_name(producer_name)
            
            if producer_guid:
                logger.info(f"SUCCESS: Found producer GUID: {producer_guid}")
                
                # Get additional info about the producer
                producer_info = producer_service.get_producer_info(producer_guid)
                if producer_info:
                    logger.info(f"Producer details: {producer_info.get('ProducerName', 'Unknown')}")
            else:
                logger.warning(f"No producer found for: '{producer_name}'")
                
        except Exception as e:
            logger.error(f"Error looking up producer '{producer_name}': {str(e)}")
    
    # Test default producer retrieval
    logger.info("\n" + "=" * 80)
    logger.info("TESTING DEFAULT PRODUCER CONFIGURATION")
    logger.info("=" * 80)
    
    default_triton = producer_service.get_default_producer_guid("triton")
    logger.info(f"Default Triton producer GUID: {default_triton}")
    
    default_xuber = producer_service.get_default_producer_guid("xuber")
    logger.info(f"Default Xuber producer GUID: {default_xuber}")

def test_workflow_integration():
    """Test producer lookup within workflow context"""
    
    logger.info("\n" + "=" * 80)
    logger.info("TESTING WORKFLOW INTEGRATION")
    logger.info("=" * 80)
    
    # Create a test transaction
    test_transaction = Transaction(
        id="TEST-001",
        external_id="TEST-POLICY-001",
        source="triton",
        transaction_type="NEW_BUSINESS",
        status=TransactionStatus.PENDING,
        raw_data="{}",
        parsed_data={
            "source_system": "triton",
            "producer_name": "Adam Griggs",
            "underwriter_name": "Sarah Peichel",
            "insured_name": "Test Company LLC",
            "state": "AZ",
            "effective_date": "2025-01-01",
            "expiration_date": "2026-01-01"
        },
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Initialize workflow orchestrator
    orchestrator = IMSWorkflowOrchestrator()
    
    # Test producer lookup
    producer_guid = orchestrator._get_producer_guid(test_transaction)
    logger.info(f"Workflow found producer GUID: {producer_guid}")
    
    # Test underwriter lookup
    underwriter_guid = orchestrator._get_underwriter_guid(test_transaction)
    logger.info(f"Workflow found underwriter GUID: {underwriter_guid}")

if __name__ == "__main__":
    try:
        # Test producer lookup
        test_producer_lookup()
        
        # Test workflow integration
        test_workflow_integration()
        
        logger.info("\n" + "=" * 80)
        logger.info("ALL TESTS COMPLETED")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()