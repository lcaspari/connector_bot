#!/usr/bin/env python3
"""
Polling Worker for Railway
Runs the polling session for collecting user interactions
"""

import asyncio
import os
import logging
from main import run_polling_session

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    duration = int(os.getenv("POLLING_DURATION", "60"))
    logger.info(f"Starting polling worker for {duration} minutes")
    
    asyncio.run(run_polling_session(duration))
    
    logger.info("Polling worker finished")
