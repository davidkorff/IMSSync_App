from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from app.api.process_transaction import process_triton_transaction
from app.services.ims.invoice_service import get_invoice_service

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
    - unbind: Unbinds an existing bound policy (requires option_id or policy_number)
    - issue: Issues the policy to get issue date (requires option_id or policy_number)
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
            
            # Return appropriate HTTP error codes based on the error type
            if "Authentication failed" in error_message:
                raise HTTPException(status_code=401, detail=error_message)
            elif "validation failed" in error_message or "requires" in error_message:
                raise HTTPException(status_code=400, detail=error_message)
            elif "Policy Already Bound" in error_message:
                # Conflict - trying to bind an already bound policy
                raise HTTPException(status_code=409, detail=error_message)
            elif "not found" in error_message.lower() or "Failed to find" in error_message:
                raise HTTPException(status_code=404, detail=error_message)
            elif "not bound" in error_message and payload.get('transaction_type') == 'unbind':
                # Unprocessable - trying to unbind a non-bound policy
                raise HTTPException(status_code=422, detail=error_message)
            else:
                # Generic processing error
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


@router.get("/invoice")
async def get_invoice(
    invoice_num: Optional[int] = Query(None, description="Invoice number"),
    quote_guid: Optional[str] = Query(None, description="Quote GUID"),
    policy_number: Optional[str] = Query(None, description="Policy number"),
    opportunity_id: Optional[str] = Query(None, description="Opportunity ID")
):
    """
    Retrieve invoice data for a policy.
    
    Provide one of the following parameters:
    - invoice_num: The invoice number
    - quote_guid: The quote GUID
    - policy_number: The policy number
    - opportunity_id: The opportunity ID (option_id)
    
    Returns the full invoice dataset as JSON.
    """
    try:
        # Validate that at least one parameter is provided
        if not any([invoice_num, quote_guid, policy_number, opportunity_id]):
            raise HTTPException(
                status_code=400, 
                detail="At least one parameter must be provided: invoice_num, quote_guid, policy_number, or opportunity_id"
            )
        
        # Get the invoice service
        invoice_service = get_invoice_service()
        
        # Call the service to get invoice data
        success, invoice_data, message = invoice_service.get_invoice_by_params(
            invoice_num=invoice_num,
            quote_guid=quote_guid,
            policy_number=policy_number,
            opportunity_id=opportunity_id
        )
        
        if success:
            logger.info(f"Successfully retrieved invoice data")
            return {
                "success": True,
                "message": message,
                "invoice_data": invoice_data
            }
        else:
            logger.error(f"Failed to retrieve invoice data: {message}")
            if "not found" in message.lower():
                raise HTTPException(status_code=404, detail=message)
            else:
                raise HTTPException(status_code=422, detail=message)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving invoice: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def status():
    """Check Triton API status."""
    return {"status": "operational", "api": "triton"}