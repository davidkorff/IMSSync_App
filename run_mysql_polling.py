#!/usr/bin/env python3
"""
Standalone runner for MySQL Polling Service
Run this to start polling Triton DB and pushing to IMS
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.mysql_polling_service import MySQLPollingService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("mysql_polling.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to run the polling service"""
    logger.info("Starting MySQL Polling Service...")
    
    # Check required environment variables
    required_env_vars = [
        'TRITON_MYSQL_HOST',
        'TRITON_MYSQL_DATABASE', 
        'TRITON_MYSQL_USER',
        'TRITON_MYSQL_PASSWORD'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set these in your .env file or environment")
        return
    
    # Create and start the polling service
    service = MySQLPollingService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Error running polling service: {str(e)}")
    finally:
        await service.stop()
        logger.info("MySQL Polling Service stopped")

if __name__ == "__main__":
    asyncio.run(main())