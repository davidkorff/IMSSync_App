from fastapi import FastAPI, Depends, HTTPException, Security, status, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
import time
from app.api.routes import router as api_router
from app.api.source_routes import router as source_router
from app.api.invoice_routes import router as invoice_router
from app.core.config import settings
from app.core.monitoring import setup_monitoring

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

# Include invoice routes
app.include_router(invoice_router)

@app.on_event("startup")
async def startup_event():
    # Setup monitoring
    setup_monitoring(app_name="ims-integration-service", app_version="1.0.0")
    
    logger.info("===================================================")
    logger.info("IMS Integration Service started and ready to receive transactions")
    logger.info("Endpoints:")
    logger.info("  POST /api/transaction/{transaction_type} - Create a transaction (new, update, cancellation, etc.)")
    logger.info("  GET /api/transaction/{id} - Check transaction status")
    logger.info("  GET /api/transactions - Search transactions")
    logger.info("  GET /api/health - Health check with detailed status")
    logger.info("  GET /api/metrics - Prometheus metrics endpoint")
    logger.info("")
    logger.info("Triton endpoints:")
    logger.info("  POST /api/triton/transaction/new - Process ALL Triton transactions (binding, cancellation, endorsement, reinstatement)")
    logger.info("    Transaction type determined by 'transaction_type' field in JSON payload")
    logger.info("")
    logger.info("Invoice endpoints:")
    logger.info("  GET /api/v1/invoice/policy/{policy_number}/latest - Get latest invoice by policy number")
    logger.info("  GET /api/v1/invoice/quote/{quote_id}/latest - Get latest invoice by quote ID")
    logger.info("")
    logger.info("Transaction types: new, update, cancellation, endorsement, reinstatement")
    logger.info("Example: POST /api/transaction/new?source=triton")
    logger.info("===================================================")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)