from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.api.dependencies import get_api_key
from app.services.ims.invoice_service import InvoiceService
from app.core.config import settings
import logging

router = APIRouter(prefix="/api/v1/invoice", tags=["invoice"])
logger = logging.getLogger(__name__)

# Initialize service
invoice_service = InvoiceService()

@router.get("/policy/{policy_number}/latest")
async def get_latest_invoice_by_policy(
    policy_number: str,
    api_key: str = Depends(get_api_key),
    include_payment_info: bool = Query(True, description="Include payment method details"),
    format_currency: bool = Query(True, description="Include formatted currency strings")
):
    """
    Retrieve the latest invoice data for a given policy number from IMS.
    
    This endpoint queries IMS for existing invoice data and transforms it
    into the format expected by Triton for PDF generation.
    
    Args:
        policy_number: The IMS policy number (e.g., "POL-2024-001234")
        include_payment_info: Whether to include detailed payment method information
        format_currency: Whether to include formatted currency strings (e.g., "$1,234.56")
    
    Returns:
        JSON response with invoice data formatted for Triton's PDF generator
    """
    try:
        logger.info(f"Retrieving invoice data for policy: {policy_number}")
        
        # Get invoice data from IMS
        invoice_data = await invoice_service.get_invoice_by_policy_number(
            policy_number=policy_number,
            include_payment_info=include_payment_info,
            format_currency=format_currency
        )
        
        if not invoice_data:
            logger.warning(f"No invoice found for policy: {policy_number}")
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVOICE_NOT_FOUND",
                        "message": f"No invoice found for policy number: {policy_number}",
                        "details": "The policy may not have an invoice generated yet"
                    }
                }
            )
        
        # Return successful response
        return {
            "success": True,
            "invoice_data": invoice_data,
            "external_references": {
                "policy_number": policy_number,
                "retrieved_at": invoice_data.get("retrieved_at")
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error retrieving invoice for policy {policy_number}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "INVOICE_RETRIEVAL_ERROR",
                    "message": "Unable to retrieve invoice data",
                    "details": str(e)
                }
            }
        )

@router.get("/quote/{quote_id}/latest")
async def get_latest_invoice_by_quote(
    quote_id: str,
    api_key: str = Depends(get_api_key),
    include_payment_info: bool = Query(True, description="Include payment method details"),
    format_currency: bool = Query(True, description="Include formatted currency strings")
):
    """
    Retrieve the latest invoice data for a given quote ID from IMS.
    
    This is an alternative endpoint that allows querying by quote ID
    instead of policy number.
    
    Args:
        quote_id: The quote ID (external reference)
        include_payment_info: Whether to include detailed payment method information
        format_currency: Whether to include formatted currency strings
    
    Returns:
        JSON response with invoice data formatted for Triton's PDF generator
    """
    try:
        logger.info(f"Retrieving invoice data for quote: {quote_id}")
        
        # Get invoice data from IMS by quote ID
        invoice_data = await invoice_service.get_invoice_by_quote_id(
            quote_id=quote_id,
            include_payment_info=include_payment_info,
            format_currency=format_currency
        )
        
        if not invoice_data:
            logger.warning(f"No invoice found for quote: {quote_id}")
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVOICE_NOT_FOUND",
                        "message": f"No invoice found for quote ID: {quote_id}",
                        "details": "The quote may not have been bound or invoice not generated yet"
                    }
                }
            )
        
        # Return successful response
        return {
            "success": True,
            "invoice_data": invoice_data,
            "external_references": {
                "quote_id": quote_id,
                "policy_number": invoice_data.get("policy_info", {}).get("policy_number"),
                "retrieved_at": invoice_data.get("retrieved_at")
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error retrieving invoice for quote {quote_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "INVOICE_RETRIEVAL_ERROR",
                    "message": "Unable to retrieve invoice data",
                    "details": str(e)
                }
            }
        )