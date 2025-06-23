"""
Source-specific API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from app.api.dependencies import get_api_key
from app.services.transaction_service import TransactionService
from app.integrations.triton.service import TritonIntegrationService
from app.integrations.xuber.service import XuberIntegrationService
from app.models.transaction_models import TransactionResponse, TransactionType, TransactionStatus
from app.core.config import settings
import logging
import json
import asyncio
from typing import Dict, Any, Union, Optional

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize transaction service
transaction_service = TransactionService()

# Source-specific services will be initialized with appropriate config when needed

# Triton routes
@router.post("/triton/transaction/{transaction_type}")
async def create_triton_transaction(
    transaction_type: TransactionType,
    request: Request,
    api_key: str = Depends(get_api_key),
    external_id: Optional[str] = None,
    sync_mode: bool = True  # Default to synchronous processing
):
    """
    Create a new transaction from Triton data
    
    By default, processes synchronously through IMS and returns the complete result.
    Set sync_mode=false for async processing (returns immediately without IMS result).
    """
    try:
        # Get raw request body
        body = await request.body()
        content_type = request.headers.get("content-type", "").lower()
        
        logger.info(f"Received {transaction_type} transaction from Triton")
        logger.info(f"Content-Type: {content_type}")
        
        # Parse data based on content type
        if "application/json" in content_type:
            data = json.loads(body)
            logger.info(f"Parsed JSON data from Triton")
        elif "application/xml" in content_type or "text/xml" in content_type:
            data = body.decode("utf-8")  # Keep as string for XML
            logger.info(f"Received XML data from Triton")
        else:
            # Try to auto-detect format
            try:
                data = json.loads(body)
                logger.info(f"Auto-detected JSON data from Triton")
            except json.JSONDecodeError:
                data = body.decode("utf-8")
                logger.info(f"Auto-detected non-JSON data from Triton")
        
        # Get external ID from header or query parameter if not provided
        if not external_id:
            external_id = request.headers.get("X-External-ID") or request.query_params.get("external_id")
        
        # Create transaction
        transaction = transaction_service.create_transaction(
            transaction_type, 
            "triton", 
            data, 
            external_id
        )
        logger.info(f"Created Triton transaction {transaction.transaction_id}")
        
        if sync_mode:
            # Process synchronously and wait for IMS result
            logger.info(f"Processing Triton transaction {transaction.transaction_id} synchronously")
            
            # Get environment and source config
            environment = transaction_service.environment
            source_config = settings.IMS_ENVIRONMENTS.get(environment, {}).get("sources", {}).get("triton", {})
            
            # Initialize Triton service with config
            triton_service = TritonIntegrationService(environment, source_config)
            
            # Process with Triton-specific service
            result = triton_service.process_transaction(transaction)
            
            # Save the updated transaction
            transaction_service._save_transaction(result)
            
            logger.info(f"Completed synchronous processing of Triton transaction {transaction.transaction_id}")
            
            return TransactionResponse(
                transaction_id=result.transaction_id,
                status=result.status,
                ims_status=result.ims_processing.status if result.ims_processing else None,
                message=f"Triton {transaction_type.value} transaction processed: {result.status.value}",
                ims_details={
                    "processing_status": result.ims_processing.status.value if result.ims_processing else None,
                    "insured_guid": result.ims_processing.insured.guid if result.ims_processing and result.ims_processing.insured else None,
                    "submission_guid": result.ims_processing.submission.guid if result.ims_processing and result.ims_processing.submission else None,
                    "quote_guid": result.ims_processing.quote.guid if result.ims_processing and result.ims_processing.quote else None,
                    "policy_number": result.ims_processing.policy.policy_number if result.ims_processing and result.ims_processing.policy else None,
                    "error": result.error_message
                } if result.ims_processing else None
            )
        else:
            # Start processing in background (async mode)
            asyncio.create_task(process_triton_transaction_async(transaction.transaction_id))
            
            return TransactionResponse(
                transaction_id=transaction.transaction_id,
                status=transaction.status,
                message=f"Triton {transaction_type.value} transaction created and queued for processing"
            )
    except Exception as e:
        logger.error(f"Error creating Triton transaction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Xuber routes
@router.post("/xuber/transaction/{transaction_type}")
async def create_xuber_transaction(
    transaction_type: TransactionType,
    request: Request,
    api_key: str = Depends(get_api_key),
    external_id: Optional[str] = None
):
    """
    Create a new transaction from Xuber data
    """
    try:
        # Get raw request body
        body = await request.body()
        content_type = request.headers.get("content-type", "").lower()
        
        logger.info(f"Received {transaction_type} transaction from Xuber")
        logger.info(f"Content-Type: {content_type}")
        
        # Parse data based on content type
        if "application/json" in content_type:
            data = json.loads(body)
            logger.info(f"Parsed JSON data from Xuber")
        elif "application/xml" in content_type or "text/xml" in content_type:
            data = body.decode("utf-8")  # Keep as string for XML
            logger.info(f"Received XML data from Xuber")
        else:
            # Try to auto-detect format
            try:
                data = json.loads(body)
                logger.info(f"Auto-detected JSON data from Xuber")
            except json.JSONDecodeError:
                data = body.decode("utf-8")
                logger.info(f"Auto-detected non-JSON data from Xuber")
        
        # Get external ID from header or query parameter if not provided
        if not external_id:
            external_id = request.headers.get("X-External-ID") or request.query_params.get("external_id")
        
        # Create transaction
        transaction = transaction_service.create_transaction(
            transaction_type, 
            "xuber", 
            data, 
            external_id
        )
        logger.info(f"Created Xuber transaction {transaction.transaction_id}")
        
        # Start processing in background
        asyncio.create_task(process_xuber_transaction_async(transaction.transaction_id))
        
        return TransactionResponse(
            transaction_id=transaction.transaction_id,
            status=transaction.status,
            message=f"Xuber {transaction_type.value} transaction created and queued for processing"
        )
    except Exception as e:
        logger.error(f"Error creating Xuber transaction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Asynchronous processing functions
async def process_triton_transaction_async(transaction_id: str):
    """Process a Triton transaction asynchronously"""
    try:
        logger.info(f"Begin async processing of Triton transaction {transaction_id}")
        
        # Get the transaction
        transaction = transaction_service.get_transaction(transaction_id)
        if not transaction:
            logger.error(f"Transaction not found: {transaction_id}")
            return
            
        # Get environment and source config
        environment = transaction_service.environment
        source_config = settings.IMS_ENVIRONMENTS.get(environment, {}).get("sources", {}).get("triton", {})
        
        # Initialize Triton service with config
        triton_service = TritonIntegrationService(environment, source_config)
        
        # Process with Triton-specific service
        result = triton_service.process_transaction(transaction)
        
        # Save the updated transaction
        transaction_service._save_transaction(result)
        
        logger.info(f"Completed processing Triton transaction {transaction_id}")
        
    except Exception as e:
        logger.error(f"Error processing Triton transaction {transaction_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Update transaction status to failed
        try:
            transaction_service.update_transaction_status(
                transaction_id,
                TransactionStatus.FAILED,
                f"Error during Triton processing: {str(e)}"
            )
        except Exception as update_error:
            logger.error(f"Failed to update transaction status: {str(update_error)}")

async def process_xuber_transaction_async(transaction_id: str):
    """Process a Xuber transaction asynchronously"""
    try:
        logger.info(f"Begin async processing of Xuber transaction {transaction_id}")
        
        # Get the transaction
        transaction = transaction_service.get_transaction(transaction_id)
        if not transaction:
            logger.error(f"Transaction not found: {transaction_id}")
            return
            
        # Get environment and source config
        environment = transaction_service.environment
        source_config = settings.IMS_ENVIRONMENTS.get(environment, {}).get("sources", {}).get("xuber", {})
        
        # Initialize Xuber service with config
        xuber_service = XuberIntegrationService(environment, source_config)
        
        # Process with Xuber-specific service
        result = xuber_service.process_transaction(transaction)
        
        # Save the updated transaction
        transaction_service._save_transaction(result)
        
        logger.info(f"Completed processing Xuber transaction {transaction_id}")
        
    except Exception as e:
        logger.error(f"Error processing Xuber transaction {transaction_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Update transaction status to failed
        try:
            transaction_service.update_transaction_status(
                transaction_id,
                TransactionStatus.FAILED,
                f"Error during Xuber processing: {str(e)}"
            )
        except Exception as update_error:
            logger.error(f"Failed to update transaction status: {str(update_error)}")