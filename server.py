#!/usr/bin/env python3
"""
Flask Server for Railway.app Integration
Handles HTTP endpoints for cron job triggers + background polling for user messages
"""

import logging
import os
import asyncio
import threading
import time
from flask import Flask, jsonify, request
from main import (
    build_app,
    send_ask_for_calls,
    send_pair_and_notify,
    run_polling_session,
    BOT_TOKEN,
    logger as main_logger
)
from telegram import Bot

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security: Require a secret token for cron job endpoints
CRON_SECRET = os.getenv("CRON_SECRET", "your-secret-token-change-this")

def verify_cron_secret(request):
    """Verify the cron job secret token."""
    token = request.headers.get("Authorization", "")
    if token != f"Bearer {CRON_SECRET}":
        return False
    return True

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Railway."""
    return jsonify({"status": "ok"}), 200

@app.route("/cron/ask", methods=["POST"])
def cron_ask_for_calls():
    """
    Cron job endpoint to trigger ask_for_calls.
    
    Set up in Railway:
    - POST /cron/ask
    - Scheduled for: 1st of month at desired time
    - Add header: Authorization: Bearer {CRON_SECRET}
    """
    if not verify_cron_secret(request):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        logger.info("Cron job triggered: ask_for_calls")
        bot = Bot(token=BOT_TOKEN)
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_ask_for_calls(bot))
        loop.close()
        
        logger.info(f"Cron result: {result}")
        return jsonify({
            "status": "success",
            "message": "ask_for_calls triggered",
            "result": result
        }), 200
    except Exception as e:
        logger.error(f"Error in cron_ask_for_calls: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/cron/pair", methods=["POST"])
def cron_pair_and_notify():
    """
    Cron job endpoint to trigger pair_and_notify.
    
    Set up in Railway:
    - POST /cron/pair
    - Scheduled for: 1st of month, ~10 min after ask_for_calls
    - Add header: Authorization: Bearer {CRON_SECRET}
    """
    if not verify_cron_secret(request):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        logger.info("Cron job triggered: pair_and_notify")
        bot = Bot(token=BOT_TOKEN)
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_pair_and_notify(bot))
        loop.close()
        
        logger.info(f"Cron result: {result}")
        return jsonify({
            "status": "success",
            "message": "pair_and_notify triggered",
            "result": result
        }), 200
    except Exception as e:
        logger.error(f"Error in cron_pair_and_notify: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/polling/start", methods=["POST"])
def start_polling():
    """
    Start a polling session for user interactions.
    
    Set up in Railway:
    - POST /polling/start
    - Scheduled daily for 1 hour
    - Optional query param: duration_minutes (default 60)
    - Add header: Authorization: Bearer {CRON_SECRET}
    """
    if not verify_cron_secret(request):
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        duration = request.args.get("duration_minutes", 60, type=int)
        logger.info(f"Starting polling session for {duration} minutes")
        
        # Run the async polling session
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_polling_session(duration))
        loop.close()
        
        return jsonify({
            "status": "success",
            "message": f"Polling session completed ({duration} minutes)"
        }), 200
    except Exception as e:
        logger.error(f"Error in start_polling: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

# ==================== BACKGROUND POLLING ====================

async def start_polling_and_run(app):
    """Start the bot polling updater and let it run continuously."""
    await app.initialize()
    await app.start()
    
    try:
        logger.info("Bot polling started and running continuously...")
        # This will run until the app is stopped
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, timeout=30)
    except Exception as e:
        logger.error(f"Polling error: {e}", exc_info=True)
        raise
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

def polling_worker():
    """
    Background worker that runs bot polling continuously.
    Creates a single event loop for the entire lifetime of the worker.
    """
    logger.info("=" * 70)
    logger.info("Starting background polling worker...")
    logger.info(f"BOT_TOKEN set: {bool(BOT_TOKEN and BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE')}")
    logger.info("=" * 70)
    
    # Create ONE event loop for this thread (not multiple)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Build the app once
        logger.info("Building bot application...")
        app = loop.run_until_complete(build_app())
        logger.info("✓ Bot application built successfully")
        
        # Start polling - this will run until interrupted
        logger.info("Starting polling...")
        loop.run_until_complete(start_polling_and_run(app))
        
    except KeyboardInterrupt:
        logger.info("Polling worker stopped via KeyboardInterrupt")
    except Exception as e:
        logger.error(f"Fatal polling error: {type(e).__name__}: {e}", exc_info=True)
    finally:
        logger.info("Closing event loop...")
        loop.close()
        logger.info("Polling worker thread ended")

def start_background_polling():
    """Start the background polling thread."""
    # Only start if BOT_TOKEN is set
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN not set or is placeholder. Background polling disabled!")
        logger.error("   Please set BOT_TOKEN environment variable in Railway.")
        return
    
    logger.info("✓ BOT_TOKEN is configured, starting polling thread...")
    thread = threading.Thread(target=polling_worker, daemon=True)
    thread.start()
    logger.info("✓ Background polling thread started (daemon)")
    logger.info("  Bot will now respond to user messages like /start")

# ==================== START POLLING WHEN APP LOADS ====================
# This runs when the app is imported by gunicorn, not just when run directly
logger.info("=" * 70)
logger.info("Flask app initialized. Starting background polling thread...")
logger.info("=" * 70)
start_background_polling()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting Flask server on port {port}")
    
    # Start Flask server (blocking)
    # Note: Polling thread already started above at module import time
