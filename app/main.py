from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from app.api.routes import router as api_router
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
logging.getLogger("app.services.transaction_service").setLevel(logging.DEBUG)
logging.getLogger("app.services.transaction_processor").setLevel(logging.DEBUG)
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

# Include API routes
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    logger.info("===================================================")
    logger.info("IMS Integration Service started and ready to receive transactions")
    logger.info("Endpoints:")
    logger.info("  POST /api/transaction/new - Create a new policy transaction")
    logger.info("  POST /api/transaction/update - Create a policy update transaction")
    logger.info("  GET /api/transaction/{id} - Check transaction status")
    logger.info("  GET /api/health - Health check")
    logger.info("===================================================")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 