#!/usr/bin/env python3
"""Test the new bind transaction flow with AddQuoteWithInsured"""

import asyncio
import json
import logging
from app.services.triton_processor import TritonProcessor
from app.models.triton_models import TritonPayload

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bind_transaction():
    """Test bind transaction with new AddQuoteWithInsured flow"""
    try:
        # Load test payload
        with open("TEST.json", "r") as f:
            payload_data = json.load(f)
        
        # Create processor and payload
        processor = TritonProcessor()
        payload = TritonPayload(**payload_data)
        
        # Process the transaction
        logger.info("Starting bind transaction test...")
        result = await processor.process_transaction(payload)
        
        # Print results
        print("\n=== TRANSACTION RESULT ===")
        print(f"Success: {result.success}")
        print(f"Transaction ID: {result.transaction_id}")
        print(f"Transaction Type: {result.transaction_type}")
        
        if result.success:
            print("\n=== SERVICE RESPONSE ===")
            print(json.dumps(result.service_response, indent=2))
            
            print("\n=== IMS RESPONSES ===")
            for response in result.ims_responses:
                print(f"\nAction: {response['action']}")
                print(f"Result: {json.dumps(response['result'], indent=2)}")
                
            if result.invoice_details:
                print("\n=== INVOICE DETAILS ===")
                print(json.dumps(result.invoice_details, indent=2))
        else:
            print("\n=== ERRORS ===")
            for error in result.errors:
                print(f"- {error}")
        
        if result.warnings:
            print("\n=== WARNINGS ===")
            for warning in result.warnings:
                print(f"- {warning}")
                
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_bind_transaction())