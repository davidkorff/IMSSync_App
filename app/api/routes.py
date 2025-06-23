from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query, Header
from fastapi.responses import JSONResponse
from app.api.dependencies import get_api_key, validate_triton_api_key
from app.services.transaction_service import TransactionService
from app.services.ims_integration_service import IMSIntegrationService
from app.models.transaction_models import TransactionResponse, TransactionType, TransactionStatus, TransactionSearchParams
import logging
import json
import asyncio
from typing import Dict, Any, Union, List, Optional
from datetime import date

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
transaction_service = TransactionService()
ims_service = IMSIntegrationService()

@router.post("/transaction/{transaction_type}")
async def create_transaction(
    transaction_type: TransactionType,
    request: Request,
    api_key: str = Depends(get_api_key),
    source: str = "triton",
    external_id: Optional[str] = None,
    sync_mode: bool = True  # Default to synchronous processing for immediate IMS feedback
):
    """
    Create a new transaction from incoming data (supports both JSON and XML)
    
    By default, processes synchronously through IMS and returns the complete result.
    Set sync_mode=false for async processing (returns immediately without IMS result).
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
        
        if sync_mode:
            # Process synchronously and wait for result
            logger.info(f"Processing transaction {transaction.transaction_id} synchronously")
            result = transaction_service.process_transaction(transaction.transaction_id)
            
            # Reload transaction to get latest status
            transaction = transaction_service.get_transaction(transaction.transaction_id)
            
            return TransactionResponse(
                transaction_id=transaction.transaction_id,
                status=transaction.status,
                ims_status=transaction.ims_processing.status if transaction.ims_processing else None,
                message=result.message,
                ims_details={
                    "processing_status": transaction.ims_processing.status.value if transaction.ims_processing else None,
                    "insured_guid": transaction.ims_processing.insured.guid if transaction.ims_processing and transaction.ims_processing.insured else None,
                    "submission_guid": transaction.ims_processing.submission.guid if transaction.ims_processing and transaction.ims_processing.submission else None,
                    "quote_guid": transaction.ims_processing.quote.guid if transaction.ims_processing and transaction.ims_processing.quote else None,
                    "policy_number": transaction.ims_processing.policy.policy_number if transaction.ims_processing and transaction.ims_processing.policy else None,
                    "error": transaction.error_message
                } if transaction.ims_processing else None
            )
        else:
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
    
    # Build detailed IMS info
    ims_details = None
    if transaction.ims_processing:
        ims_details = {
            "processing_status": transaction.ims_processing.status.value,
            "insured_guid": transaction.ims_processing.insured.guid if transaction.ims_processing.insured else None,
            "submission_guid": transaction.ims_processing.submission.guid if transaction.ims_processing.submission else None,
            "quote_guid": transaction.ims_processing.quote.guid if transaction.ims_processing.quote else None,
            "policy_number": transaction.ims_processing.policy.policy_number if transaction.ims_processing.policy else None,
            "error": transaction.error_message,
            "processing_logs": transaction.ims_processing.processing_logs[-10:] if hasattr(transaction.ims_processing, 'processing_logs') else []
        }
    
    return TransactionResponse(
        transaction_id=transaction.transaction_id,
        status=transaction.status,
        ims_status=transaction.ims_processing.status if transaction.ims_processing else None,
        message=f"Transaction status: {transaction.status.value}",
        ims_details=ims_details
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

# Triton Integration API Endpoints
@router.post("/triton/api/v1/transactions", tags=["triton"])
async def receive_triton_transaction(
    request: Request,
    x_api_key: str = Header(..., description="API key for authentication"),
    x_client_id: str = Header(..., description="Client ID for identification"),
    x_triton_version: Optional[str] = Header(None, description="Triton version info"),
    source: str = Query("triton", description="Source system identifier"),
    sync_mode: bool = Query(True, description="Process synchronously and wait for IMS result")
):
    """
    Receive a transaction from Triton IMS system.
    
    This endpoint accepts transaction data in JSON format from the Triton system
    and processes it in our IMS integration pipeline.
    
    The transaction type is expected within the transaction_data and must be one of:
    - binding: New policy binding
    - midterm_endorsement: Policy endorsement
    - cancellation: Policy cancellation
    """
    # Authenticate the request
    validate_triton_api_key(x_api_key)
    
    try:
        # Get and parse the request body
        body = await request.body()
        data = json.loads(body)
        logger.info(f"Received Triton transaction: {json.dumps(data, indent=2)}")
        
        # Validate required fields
        if "transaction_type" not in data:
            raise HTTPException(status_code=400, detail="Missing transaction_type in request")
            
        transaction_type = data["transaction_type"]
        
        # Map Triton transaction types to our internal types
        type_mapping = {
            "binding": TransactionType.NEW,
            "midterm_endorsement": TransactionType.ENDORSEMENT,
            "cancellation": TransactionType.CANCELLATION
        }
        
        if transaction_type not in type_mapping:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid transaction type: {transaction_type}. Must be one of: binding, midterm_endorsement, cancellation"
            )
        
        # Create internal transaction object from Triton data
        internal_type = type_mapping[transaction_type]
        external_id = data.get("transaction_id", None)
        
        # Create transaction in our system
        transaction = transaction_service.create_transaction(internal_type, source, data, external_id)
        logger.info(f"Created transaction {transaction.transaction_id} from Triton data" + 
                  (f" with external ID {external_id}" if external_id else ""))
        
        if sync_mode:
            # Process synchronously and wait for result
            logger.info(f"Processing transaction {transaction.transaction_id} synchronously")
            result = transaction_service.process_transaction(transaction.transaction_id)
            
            # Reload transaction to get latest status
            transaction = transaction_service.get_transaction(transaction.transaction_id)
            
            return TransactionResponse(
                transaction_id=transaction.transaction_id,
                status=transaction.status,
                ims_status=transaction.ims_processing.status if transaction.ims_processing else None,
                message=f"Triton {transaction_type} transaction processed: {transaction.status.value}",
                reference_id=f"RSG-{transaction.transaction_id}",
                ims_details={
                    "processing_status": transaction.ims_processing.status.value if transaction.ims_processing else None,
                    "insured_guid": transaction.ims_processing.insured.guid if transaction.ims_processing and transaction.ims_processing.insured else None,
                    "submission_guid": transaction.ims_processing.submission.guid if transaction.ims_processing and transaction.ims_processing.submission else None,
                    "quote_guid": transaction.ims_processing.quote.guid if transaction.ims_processing and transaction.ims_processing.quote else None,
                    "policy_number": transaction.ims_processing.policy.policy_number if transaction.ims_processing and transaction.ims_processing.policy else None,
                    "error": transaction.error_message
                } if transaction.ims_processing else None
            )
        else:
            # Start processing in background (non-blocking)
            asyncio.create_task(process_transaction_async(transaction.transaction_id))
            logger.info(f"Started async processing for Triton transaction {transaction.transaction_id}")
            
            return TransactionResponse(
                transaction_id=transaction.transaction_id,
                status=transaction.status,
                message=f"Triton {transaction_type} transaction received successfully and queued for processing",
                reference_id=f"RSG-{transaction.transaction_id}"
            )
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON received from Triton")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logger.error(f"Error processing Triton transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))