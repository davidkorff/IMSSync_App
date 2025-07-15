import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from uuid import UUID

from app.services.ims import AuthService, InsuredService, QuoteService, InvoiceService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ims", tags=["ims"])

# Initialize services
auth_service = AuthService()
insured_service = InsuredService(auth_service)
quote_service = QuoteService(auth_service)
invoice_service = InvoiceService(auth_service)

@router.get("/insured/search")
async def search_insured(
    name: str = Query(..., description="Insured name"),
    address: str = Query(..., description="Street address"),
    city: str = Query(..., description="City"),
    state: str = Query(..., description="State code"),
    zip_code: str = Query(..., description="ZIP code")
) -> Dict[str, Any]:
    """Search for insured by name and address"""
    try:
        insured_guid = insured_service.find_by_name_and_address(
            name=name,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code
        )
        
        if insured_guid:
            return {
                "found": True,
                "insured_guid": str(insured_guid)
            }
        else:
            return {
                "found": False,
                "insured_guid": None
            }
            
    except Exception as e:
        logger.error(f"Error searching insured: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/insured")
async def create_insured(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new insured with location"""
    try:
        insured_guid = insured_service.create_with_location(data)
        return {
            "success": True,
            "insured_guid": str(insured_guid)
        }
    except Exception as e:
        logger.error(f"Error creating insured: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/invoice/{policy_guid}")
async def get_invoice(policy_guid: UUID) -> Dict[str, Any]:
    """Get invoice for a policy"""
    try:
        invoice = invoice_service.get_invoice(policy_guid)
        if invoice:
            return invoice
        else:
            raise HTTPException(status_code=404, detail="Invoice not found")
    except Exception as e:
        logger.error(f"Error getting invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/invoice/{policy_guid}/pdf")
async def get_invoice_pdf(policy_guid: UUID):
    """Get invoice as PDF"""
    try:
        pdf_data = invoice_service.get_invoice_pdf(policy_guid)
        if pdf_data:
            from fastapi.responses import Response
            return Response(
                content=pdf_data,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=invoice_{policy_guid}.pdf"}
            )
        else:
            raise HTTPException(status_code=404, detail="Invoice PDF not found")
    except Exception as e:
        logger.error(f"Error getting invoice PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))