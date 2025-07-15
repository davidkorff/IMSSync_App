import logging
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import Optional

from app.models.triton_models import TritonPayload, ProcessingResult
from app.services.triton_processor import TritonProcessor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/triton", tags=["triton"])

# Initialize processor
processor = TritonProcessor()

@router.post("/transaction/new", response_model=ProcessingResult)
async def process_new_transaction(payload: TritonPayload):
    """
    Process a new transaction from Triton
    
    Transaction types:
    - Bind: Create insured, submission, quote and bind
    - Unbind: Unbind an existing policy
    - Issue: Issue a bound policy
    - Midterm Endorsement: Create and bind an endorsement
    - Cancellation: Cancel a policy
    """
    try:
        result = await processor.process_transaction(payload)
        
        if not result.success:
            logger.error(f"Transaction failed: {result.errors}")
            raise HTTPException(status_code=400, detail=result.errors)
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error processing transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transaction/{transaction_id}/excel-rater")
async def upload_excel_rater(
    transaction_id: str,
    file: UploadFile = File(...),
    quote_guid: str = Form(...)
):
    """Upload Excel rater data for a quote"""
    try:
        # Validate file type
        if not file.filename.endswith(('.xls', '.xlsx')):
            raise HTTPException(status_code=400, detail="Invalid file type. Must be Excel file.")
        
        # Read file content
        content = await file.read()
        
        # Import to IMS
        from app.services.ims import AuthService, QuoteService
        auth = AuthService()
        quote_service = QuoteService(auth)
        
        result = quote_service.import_excel_rater(quote_guid, content)
        
        return {
            "transaction_id": transaction_id,
            "quote_guid": quote_guid,
            "filename": file.filename,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error uploading Excel rater: {e}")
        raise HTTPException(status_code=500, detail=str(e))