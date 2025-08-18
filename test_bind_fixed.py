#!/usr/bin/env python3
"""
Test the bind transaction with fixed BindQuote method
"""
import asyncio
import json
from datetime import datetime
from app.services.triton_processor import TritonProcessor
from app.models.triton_models import TritonPayload

async def test_bind():
    """Test bind transaction"""
    # Load test data
    with open("TEST.json", "r") as f:
        test_data = json.load(f)
    
    # Create payload
    payload = TritonPayload(**test_data)
    
    # Process transaction
    processor = TritonProcessor()
    result = await processor.process_transaction(payload)
    
    # Print results
    print(f"\nTransaction Result: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Transaction ID: {result.transaction_id}")
    print(f"Transaction Type: {result.transaction_type}")
    
    if result.service_response:
        print("\nService Response:")
        for key, value in result.service_response.items():
            print(f"  {key}: {value}")
    
    if result.ims_responses:
        print("\nIMS Responses:")
        for response in result.ims_responses:
            print(f"  Action: {response['action']}")
            print(f"  Result: {response['result']}")
    
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")
    
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
    
    if result.invoice_details:
        print("\nInvoice Details:")
        print(f"  {result.invoice_details}")

if __name__ == "__main__":
    asyncio.run(test_bind())