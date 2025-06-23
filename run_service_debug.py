#!/usr/bin/env python3
"""Run the service with debug logging"""

import os
import sys
import logging

# Set debug logging
os.environ['LOG_LEVEL'] = 'DEBUG'
logging.basicConfig(level=logging.DEBUG)

# Import and run the service
from app.main import app
import uvicorn

if __name__ == "__main__":
    print("Starting service with DEBUG logging...")
    print("This will show all SOAP requests and responses")
    print("-" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")