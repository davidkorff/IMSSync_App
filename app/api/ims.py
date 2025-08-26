from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ims", tags=["ims"])


@router.get("/status")
async def status():
    """Check IMS API status."""
    logger.debug("IMS status check requested")
    return {"status": "operational", "api": "ims"}


@router.get("/health")
async def health_check():
    """IMS integration health check."""
    logger.debug("IMS health check requested")
    # This could check IMS connectivity in the future
    return {
        "status": "healthy",
        "services": [
            "auth_service",
            "insured_service",
            "data_access_service",
            "underwriter_service",
            "quote_service",
            "quote_options_service",
            "payload_processor_service",
            "bind_service"
        ]
    }