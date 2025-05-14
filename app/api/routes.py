from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query
from fastapi.responses import JSONResponse
from app.api.dependencies import get_api_key
from app.services.transaction_service import TransactionService
from app.models.transaction_models import TransactionResponse, TransactionType, TransactionStatus, TransactionSearchParams
import logging
import json
import asyncio
from typing import Dict, Any, Union, List, Optional
from datetime import date

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize transaction service
transaction_service = TransactionService()

@router.post("/transaction/{transaction_type}")
async def create_transaction(
    transaction_type: TransactionType,
    request: Request,
    api_key: str = Depends(get_api_key),
    source: str = "triton",
    external_id: Optional[str] = None
):
    """
    Create a new transaction from incoming data (supports both JSON and XML)
    """
    try:
        # Get raw request body
        body = await request.body()
        content_type = request.headers.get("content-type", "").lower()
        
        logger.info(f"Received {transaction_type} transaction from {source}")
        logger.info(f"Content-Type: {content_type}")
        logger.info(f"Raw body: {body.decode('utf-8', errors='replace')}")
        
        if "application/json" in content_type:
            # Parse JSON data
            data = json.loads(body)
            logger.info(f"Parsed JSON data: {json.dumps(data, indent=2)}")
        elif "application/xml" in content_type or "text/xml" in content_type:
            # Keep XML as string for later processing
            data = body.decode("utf-8")
            logger.info(f"Received XML data of length {len(data)}")
        else:
            # If content type is not specified, try to determine from content
            try:
                data = json.loads(body)
                logger.info(f"Auto-detected and parsed JSON data: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                # Assume it's XML if not valid JSON
                data = body.decode("utf-8")
                logger.info(f"Auto-detected XML data of length {len(data)}")
        
        # Get external ID from header or query parameter if not provided in function arguments
        if not external_id:
            external_id = request.headers.get("X-External-ID") or request.query_params.get("external_id")
        
        # Create transaction
        transaction = transaction_service.create_transaction(transaction_type, source, data, external_id)
        logger.info(f"Created transaction {transaction.transaction_id}" + 
                  (f" with external ID {external_id}" if external_id else ""))
        
        # Start processing in background (non-blocking)
        asyncio.create_task(process_transaction_async(transaction.transaction_id))
        logger.info(f"Started async processing for transaction {transaction.transaction_id}")
        
        return TransactionResponse(
            transaction_id=transaction.transaction_id,
            status=transaction.status,
            message=f"{transaction_type.value} transaction created successfully and queued for processing"
        )
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/transaction/{transaction_id}")
async def get_transaction_status(
    transaction_id: str,
    api_key: str = Depends(get_api_key)
):
    """
    Get the status of a transaction
    """
    logger.info(f"Checking status of transaction {transaction_id}")
    transaction = transaction_service.get_transaction(transaction_id)
    if not transaction:
        logger.warning(f"Transaction not found: {transaction_id}")
        raise HTTPException(status_code=404, detail=f"Transaction not found: {transaction_id}")
    
    logger.info(f"Retrieved transaction {transaction_id}, status: {transaction.status.value}")
    return TransactionResponse(
        transaction_id=transaction.transaction_id,
        status=transaction.status,
        ims_status=transaction.ims_processing.status if transaction.ims_processing else None,
        message=f"Transaction status: {transaction.status.value}"
    )

async def process_transaction_async(transaction_id: str):
    """
    Process a transaction asynchronously
    """
    try:
        logger.info(f"Begin async processing of transaction {transaction_id}")
        # Process the transaction
        result = transaction_service.process_transaction(transaction_id)
        logger.info(f"Completed processing transaction {transaction_id}: Status={result.status}, Message={result.message}")
    except Exception as e:
        logger.error(f"Error processing transaction {transaction_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Make sure to update transaction status to failed
        try:
            transaction_service.update_transaction_status(
                transaction_id, 
                TransactionStatus.FAILED,
                f"Error during asynchronous processing: {str(e)}"
            )
        except Exception as update_error:
            logger.error(f"Failed to update transaction status: {str(update_error)}")

@router.get("/transactions")
async def search_transactions(
    api_key: str = Depends(get_api_key),
    source: Optional[str] = None,
    status: Optional[TransactionStatus] = None,
    external_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Search for transactions based on criteria
    """
    search_params = TransactionSearchParams(
        source=source,
        status=status,
        external_id=external_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    transactions = transaction_service.search_transactions(search_params)
    
    # Convert to response format
    results = [
        {
            "transaction_id": t.transaction_id,
            "external_id": t.external_id,
            "type": t.type.value,
            "source": t.source,
            "status": t.status.value,
            "received_at": t.received_at.isoformat(),
            "processed_at": t.processed_at.isoformat() if t.processed_at else None,
            "ims_status": t.ims_processing.status.value if t.ims_processing else None,
            "policy_number": t.ims_processing.policy.policy_number if t.ims_processing and t.ims_processing.policy else None
        }
        for t in transactions
    ]
    
    return {
        "total": len(transactions),
        "offset": offset,
        "limit": limit,
        "results": results
    }

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}