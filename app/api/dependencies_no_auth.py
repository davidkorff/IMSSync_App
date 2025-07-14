"""
No-auth version of dependencies for testing
"""

async def get_api_key(api_key_header: str = None):
    """Bypass API key validation for testing"""
    return "test_bypass"

async def validate_triton_api_key(x_api_key: str = None):
    """Bypass Triton API key validation for testing"""
    return "test_bypass"

async def validate_triton_client(x_api_key: str = None, x_client_id: str = None):
    """Bypass Triton client validation for testing"""
    return True