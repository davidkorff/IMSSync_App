import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import APP_CONFIG
from app.api import triton, ims

# Configure logging
logging.basicConfig(
    level=APP_CONFIG["log_level"],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RSG Integration Service",
    description="Service for processing Triton transactions and integrating with IMS",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(triton.router)
app.include_router(ims.router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "RSG Integration Service"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "triton": "/api/triton",
            "ims": "/api/ims"
        }
    }

if __name__ == "__main__":
    logger.info(f"Starting RSG Integration Service on {APP_CONFIG['host']}:{APP_CONFIG['port']}")
    uvicorn.run(
        "main:app",
        host=APP_CONFIG["host"],
        port=APP_CONFIG["port"],
        reload=APP_CONFIG["debug"]
    )