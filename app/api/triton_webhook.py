"""
Simplified Triton webhook endpoint
Single entry point for all Triton transactions
"""

from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.triton_processor import TritonProcessor, TritonError
from app.services.ims_client import IMSClient
from app.api.dependencies import get_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/triton", tags=["triton"])

# Global processor instance (initialized on first request)
_processor = None


def get_triton_config() -> Dict[str, Any]:
    """Get Triton configuration"""
    from app.config.triton_config import get_config_for_environment
    
    # Get environment from settings or environment variable
    import os
    env = os.getenv('IMS_ENVIRONMENT', 'ims_one')
    
    return get_config_for_environment(env)


def get_processor() -> TritonProcessor:
    """Get or create the Triton processor instance"""
    global _processor
    
    if _processor is None:
        config = get_triton_config()
        ims_client = IMSClient(config)
        _processor = TritonProcessor(ims_client, config)
    
    return _processor


@router.post("/webhook")
async def triton_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key),
    sync_mode: bool = True  # Default to synchronous
):
    """
    Main webhook endpoint for all Triton transactions
    
    Accepts:
    - binding (new policies)
    - cancellation
    - endorsement/midterm_endorsement
    - reinstatement
    
    Query params:
    - sync_mode: true (default) = wait for IMS processing, false = return immediately
    """
    try:
        # Parse request body
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
        
        # Extract transaction info
        transaction_type = data.get('transaction_type', '').lower()
        transaction_id = data.get('transaction_id', f"triton_{datetime.now().timestamp()}")
        
        # Log incoming transaction
        logger.info("TRITON_WEBHOOK_RECEIVED", extra={
            'transaction_id': transaction_id,
            'transaction_type': transaction_type,
            'policy_number': data.get('policy_number'),
            'sync_mode': sync_mode
        })
        
        # Get processor
        processor = get_processor()
        
        if sync_mode:
            # Process synchronously
            try:
                result = processor.process_transaction(data)
                
                logger.info("TRITON_WEBHOOK_SUCCESS", extra={
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
                logger.error("TRITON_WEBHOOK_ERROR", extra={
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
                logger.exception("TRITON_WEBHOOK_UNEXPECTED_ERROR", extra={
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
        logger.exception("TRITON_WEBHOOK_REQUEST_ERROR")
        raise HTTPException(status_code=400, detail=str(e))


async def process_async(processor: TritonProcessor, data: Dict[str, Any], transaction_id: str):
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


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        processor = get_processor()
        # Try to check IMS connection
        if processor.ims.token or processor.ims.login():
            return {
                'status': 'healthy',
                'service': 'triton-webhook',
                'ims_connected': True,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    'status': 'unhealthy',
                    'service': 'triton-webhook',
                    'ims_connected': False,
                    'error': 'Cannot connect to IMS',
                    'timestamp': datetime.now().isoformat()
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'service': 'triton-webhook',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )


@router.get("/config")
async def get_config(api_key: str = Depends(get_api_key)):
    """Get current configuration (for debugging)"""
    config = get_triton_config()
    
    # Mask sensitive data
    safe_config = config.copy()
    safe_config['password'] = '***'
    
    return {
        'environment': get_triton_config.get('environment', 'unknown'),
        'config': safe_config
    }