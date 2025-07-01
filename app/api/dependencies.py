from fastapi import Security, HTTPException, status, Header
from fastapi.security import APIKeyHeader
from app.core.config import settings
from typing import Optional

# Regular API key header
api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=False)

# Triton-specific settings
TRITON_API_KEYS = settings.TRITON_API_KEYS
TRITON_ALLOWED_CLIENT_IDS = settings.TRITON_CLIENT_IDS

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """
    Validate standard API key for regular endpoints.
    """
    if api_key_header not in settings.API_KEYS and api_key_header not in TRITON_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key_header 

async def validate_triton_api_key(x_api_key: str = Header(...)):
    """
    Validate that the API key is specifically authorized for Triton integration.
    """
    if x_api_key not in TRITON_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Triton API Key"
        )
    return x_api_key

async def validate_triton_client(
    x_api_key: str = Header(...),
    x_client_id: str = Header(...)
):
    """
    Validate both the Triton API key and client ID.
    Used for Triton integration endpoints.
    """
    # First validate the API key
    await validate_triton_api_key(x_api_key)
    
    # Then check the client ID
    if x_client_id not in TRITON_ALLOWED_CLIENT_IDS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Triton Client ID"
        )
        
    return True