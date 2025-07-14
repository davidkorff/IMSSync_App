"""
Source-specific API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from app.api.dependencies_no_auth import get_api_key  # Using no-auth for testing
from app.services.transaction_service import TransactionService
from app.integrations.triton.service import TritonIntegrationService
from app.integrations.xuber.service import XuberIntegrationService
from app.models.transaction_models import TransactionResponse, TransactionType, TransactionStatus
from app.core.config import settings
import logging
import json
import asyncio
import os
from typing import Dict, Any, Union, Optional
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize transaction service
transaction_service = TransactionService()

# Source-specific services will be initialized with appropriate config when needed

# Triton routes
@router.post("/triton/transaction/new")
async def create_triton_transaction(
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key),
    external_id: Optional[str] = None,
    sync_mode: bool = True  # Default to synchronous processing
):
    """
    Create a new Triton transaction
    
    The transaction type is determined by the 'transaction_type' field in the JSON payload.
    Supports: binding, cancellation, endorsement, reinstatement
    
    By default, processes synchronously through IMS and returns the complete result.
    Set sync_mode=false for async processing (returns immediately without IMS result).
    """
    try:
        # Get raw request body
        body = await request.body()
        content_type = request.headers.get("content-type", "").lower()
        
        # Parse JSON data
        if "application/json" in content_type:
            data = json.loads(body)
        else:
            # Try to parse as JSON anyway
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Get external ID from header or query parameter if not provided
        if not external_id:
            external_id = request.headers.get("X-External-ID") or request.query_params.get("external_id")
        
        # Extract transaction type from payload
        transaction_type = data.get('transaction_type', '').lower()
        transaction_id = data.get('transaction_id', f"triton_{datetime.now().timestamp()}")
        
        # Log incoming transaction
        logger.info("TRITON_TRANSACTION_RECEIVED", extra={
            'transaction_id': transaction_id,
            'transaction_type': transaction_type,
            'policy_number': data.get('policy_number'),
            'sync_mode': sync_mode
        })
        
        # Import and use the simplified processor
        from app.services.triton_processor import TritonProcessor, TritonError
        from app.services.ims_client import IMSClient
        from app.config.triton_config import get_config_for_environment
        
        # Get configuration
        env = os.getenv('IMS_ENVIRONMENT', 'ims_one')
        config = get_config_for_environment(env)
        
        # Create IMS client and processor
        ims_client = IMSClient(config)
        processor = TritonProcessor(ims_client, config)
        
        if sync_mode:
            # Process synchronously
            try:
                result = processor.process_transaction(data)
                
                logger.info("TRITON_TRANSACTION_SUCCESS", extra={
                    'transaction_id': transaction_id,
                    'result': result
                })
                
                return JSONResponse(
                    status_code=200,
                    content={
                        'status': 'success',
                        'data': result
                    }
                )
                
            except TritonError as e:
                logger.error("TRITON_TRANSACTION_ERROR", extra={
                    'transaction_id': transaction_id,
                    'stage': e.stage,
                    'error': e.message,
                    'details': e.details
                })
                
                return JSONResponse(
                    status_code=400,
                    content={
                        'status': 'error',
                        'error': {
                            'stage': e.stage,
                            'message': e.message,
                            'details': e.details
                        }
                    }
                )
                
            except Exception as e:
                logger.exception("TRITON_TRANSACTION_UNEXPECTED_ERROR", extra={
                    'transaction_id': transaction_id,
                    'error': str(e)
                })
                
                return JSONResponse(
                    status_code=500,
                    content={
                        'status': 'error',
                        'error': {
                            'stage': 'UNKNOWN',
                            'message': 'Internal server error',
                            'details': {'error': str(e)}
                        }
                    }
                )
        else:
            # Process asynchronously
            background_tasks.add_task(process_async, processor, data, transaction_id)
            
            return JSONResponse(
                status_code=202,
                content={
                    'status': 'accepted',
                    'data': {
                        'transaction_id': transaction_id,
                        'message': 'Transaction queued for processing'
                    }
                }
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

# Asynchronous processing function
async def process_async(processor, data: Dict[str, Any], transaction_id: str):
    """Process transaction asynchronously"""
    try:
        logger.info("TRITON_ASYNC_START", extra={'transaction_id': transaction_id})
        
        result = processor.process_transaction(data)
        
        logger.info("TRITON_ASYNC_SUCCESS", extra={
            'transaction_id': transaction_id,
            'result': result
        })
        
        # Here you would typically:
        # 1. Store the result in a database
        # 2. Send a webhook back to Triton with the result
        # 3. Send an email notification
        
    except Exception as e:
        logger.exception("TRITON_ASYNC_ERROR", extra={
            'transaction_id': transaction_id,
            'error': str(e)
        })
        
        # Here you would typically:
        # 1. Store the error in a database
        # 2. Send an error notification
        # 3. Potentially retry the operation

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