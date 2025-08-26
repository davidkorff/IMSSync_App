import logging
import logging.handlers
import os
from datetime import datetime
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import APP_CONFIG
from app.api import triton, ims

# Create logs directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Generate log filename with timestamp for this session
log_filename = os.path.join(log_dir, f"api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging with both file and console handlers
log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# File handler - writes to log file
file_handler = logging.FileHandler(log_filename, mode='w')  # 'w' mode ensures file is reset on restart
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)  # Capture all levels in file

# Console handler - for terminal output
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(APP_CONFIG["log_level"])

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.handlers.clear()  # Clear any existing handlers
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)
logger.info(f"Logging initialized. Log file: {log_filename}")

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
    logger.info("Root endpoint accessed")
    return {"status": "ok", "service": "RSG Integration Service"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "triton": "/api/triton",
            "ims": "/api/ims"
        }
    }

if __name__ == "__main__":
    logger.info("="*80)
    logger.info(f"Starting RSG Integration Service on {APP_CONFIG['host']}:{APP_CONFIG['port']}")
    logger.info(f"Debug mode: {APP_CONFIG['debug']}")
    logger.info(f"Log level: {APP_CONFIG['log_level']}")
    logger.info("="*80)
    
    uvicorn.run(
        "main:app",
        host=APP_CONFIG["host"],
        port=APP_CONFIG["port"],
        reload=APP_CONFIG["debug"],
        log_config=None  # Disable uvicorn's default logging config to use ours
    )