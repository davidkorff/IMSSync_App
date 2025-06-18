from fastapi import FastAPI, Depends, HTTPException, Security, status, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
import time
from app.api.routes import router as api_router
from app.api.source_routes import router as source_router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ims_integration.log"),
        logging.StreamHandler()
    ]
)

# Set log levels for specific modules
logging.getLogger("app.api.routes").setLevel(logging.DEBUG)
logging.getLogger("app.api.source_routes").setLevel(logging.DEBUG)
logging.getLogger("app.services.transaction_service").setLevel(logging.DEBUG)
logging.getLogger("app.integrations.triton").setLevel(logging.DEBUG)
logging.getLogger("app.integrations.xuber").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IMS Integration API",
    description="API for integrating external systems with IMS",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Get client IP - check for X-Forwarded-For header first (for proxies)
    client_ip = request.headers.get("X-Forwarded-For")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    # Log incoming request
    logger.info(f"INCOMING REQUEST - IP: {client_ip}, Method: {request.method}, Path: {request.url.path}, Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"RESPONSE - IP: {client_ip}, Method: {request.method}, Path: {request.url.path}, Status: {response.status_code}, Time: {process_time:.3f}s")
    
    return response

# Include API routes
app.include_router(api_router, prefix="/api")

# Include source-specific routes
app.include_router(source_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    logger.info("===================================================")
    logger.info("IMS Integration Service started and ready to receive transactions")
    logger.info("Endpoints:")
    logger.info("  POST /api/transaction/{transaction_type} - Create a transaction (new, update, cancellation, etc.)")
    logger.info("  GET /api/transaction/{id} - Check transaction status")
    logger.info("  GET /api/transactions - Search transactions")
    logger.info("  GET /api/health - Health check")
    logger.info("")
    logger.info("Source-specific endpoints:")
    logger.info("  POST /api/triton/transaction/{transaction_type} - Create Triton transaction")
    logger.info("  POST /api/xuber/transaction/{transaction_type} - Create Xuber transaction")
    logger.info("")
    logger.info("Transaction types: new, update, cancellation, endorsement, reinstatement")
    logger.info("Example: POST /api/transaction/new?source=triton")
    logger.info("===================================================")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)