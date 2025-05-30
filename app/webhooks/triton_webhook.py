"""
Triton Webhook Handler
Receives push notifications from Triton and processes them through the standard pipeline
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

from ..sources.triton.push_adapter import TritonPushAdapter
from ..core.transaction_processor import processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/triton", tags=["triton-webhooks"])


@router.post("/transaction")
async def handle_triton_transaction(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Handle incoming transaction webhook from Triton
    
    Endpoint that Triton will POST to when transactions occur
    """
    try:
        logger.info(f"Received Triton webhook: {payload.get('transaction_id')}")
        
        # Validate payload has required fields
        if not payload.get('transaction_id'):
            raise HTTPException(status_code=400, detail="Missing transaction_id")
        
        # Convert Triton data to standard format
        adapter = TritonPushAdapter()
        transaction = await adapter.process_webhook_data(payload)
        
        # Process in background
        background_tasks.add_task(
            process_transaction_async,
            transaction,
            "ims"
        )
        
        return {
            "status": "accepted",
            "transaction_id": transaction.source_transaction_id,
            "message": "Transaction queued for processing"
        }
        
    except Exception as e:
        logger.error(f"Error processing Triton webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_triton_webhook(payload: Dict[str, Any]):
    """
    Test endpoint for Triton webhook integration
    """
    logger.info("Received test webhook from Triton")
    
    return {
        "status": "success",
        "message": "Triton webhook endpoint is working",
        "received_data": payload
    }


async def process_transaction_async(transaction, destination: str):
    """Background task to process transaction"""
    try:
        result = await processor.process_transaction(transaction, destination)
        logger.info(f"Transaction {transaction.source_transaction_id} processed: {result['status']}")
    except Exception as e:
        logger.error(f"Failed to process transaction {transaction.source_transaction_id}: {e}")