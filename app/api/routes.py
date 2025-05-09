from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_api_key
from app.services.ims_integration_service import IMSIntegrationService
from app.models.policy_data import PolicySubmission, IntegrationResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/policy", response_model=IntegrationResponse, status_code=201)
async def create_policy(
    submission: PolicySubmission,
    api_key: str = Depends(get_api_key),
    environment: str = None
):
    """
    Create a new policy in IMS from external data
    """
    try:
        logger.info(f"Received policy submission from external system")
        integration_service = IMSIntegrationService(environment)
        result = integration_service.process_submission(submission)
        return result
    except Exception as e:
        logger.error(f"Error processing policy submission: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"} 