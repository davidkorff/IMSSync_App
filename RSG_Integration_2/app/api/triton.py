from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from app.api.process_transaction import process_triton_transaction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/triton", tags=["triton"])


class TritonPayload(BaseModel):
    """Triton transaction payload model."""
    transaction_id: str
    transaction_type: str
    policy_number: str
    insured_name: str
    net_premium: float
    # Add other fields as needed
    class Config:
        extra = "allow"  # Allow additional fields


class TransactionResponse(BaseModel):
    """Response model for transaction processing."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/transaction/new", response_model=TransactionResponse)
async def process_transaction(payload: Dict[str, Any]):
    """
    Process a new transaction from Triton.
    
    This is the single endpoint that receives ALL transaction types from Triton.
    The workflow is determined by the transaction_type field in the payload.
    
    Workflow for all transaction types:
    1. Find/create insured
    2. Lookup producer and underwriter
    3. Create quote
    4. Add quote options
    5. Store data and register premium
    6. Execute transaction-specific action:
       - bind: Binds quote to get policy number
       - issue: Issues policy to get issue date (assumes already bound)
       - Others: No additional action
    
    Supported transaction types:
    - bind: Creates quote and binds it to get policy number
    - unbind: Creates quote without binding
    - issue: Issues the policy to get issue date (assumes policy is already bound)
    - midterm_endorsement: Process endorsement
    - cancellation: Cancel policy
    - reinstatement: Reinstate policy
    
    Returns the processing results including all created GUIDs and 
    policy numbers.
    """
    try:
        logger.info(f"Received transaction: {payload.get('transaction_id')} - Type: {payload.get('transaction_type')}")
        
        # Process the transaction
        result = process_triton_transaction(payload)
        
        if result["success"]:
            logger.info(f"Successfully processed transaction: {payload.get('transaction_id')}")
            return TransactionResponse(**result)
        else:
            error_message = result.get('message', 'Transaction processing failed')
            logger.error(f"Failed to process transaction: {payload.get('transaction_id')} - {error_message}")
            
            # Determine appropriate error code based on the error message
            if "Authentication failed" in error_message:
                raise HTTPException(status_code=401, detail=error_message)
            elif "validation failed" in error_message or "requires" in error_message:
                raise HTTPException(status_code=400, detail=error_message)
            elif "not found" in error_message or "Failed to find" in error_message:
                raise HTTPException(status_code=404, detail=error_message)
            elif "already exists" in error_message:
                raise HTTPException(status_code=409, detail=error_message)
            else:
                # For bind failures, quote failures, etc. - unprocessable entity
                raise HTTPException(status_code=422, detail=error_message)
        
    except Exception as e:
        logger.error(f"Error processing transaction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transaction-types")
async def get_transaction_types():
    """Get supported transaction types."""
    return {
        "transaction_types": [
            "bind",
            "unbind", 
            "issue",
            "midterm_endorsement",
            "cancellation",
            "reinstatement"
        ]
    }


@router.get("/status")
async def status():
    """Check Triton API status."""
    return {"status": "operational", "api": "triton"}