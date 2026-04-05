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

def polling_worker():
    """
    Background worker that continuously polls for Telegram updates.
    This allows the bot to respond to user messages like /start.
    """
    logger.info("Starting background polling worker...")
    while True:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # Run polling for 5 minutes at a time, then retry
            # This allows graceful shutdown and recovery
            loop.run_until_complete(run_polling_session(duration_minutes=5))
            loop.close()
        except Exception as e:
            logger.error(f"Polling worker error: {e}")
            # Wait before retrying to avoid spamming logs
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Polling worker stopped")
            break

def start_background_polling():
    """Start the background polling thread."""
    # Only start if BOT_TOKEN is set
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.warning("BOT_TOKEN not set. Skipping background polling.")
        return
    
    thread = threading.Thread(target=polling_worker, daemon=True)
    thread.start()
    logger.info("Background polling thread started (daemon)")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting Flask server on port {port}")
    
    # Start background polling in a daemon thread
    start_background_polling()
    
    # Start Flask server (blocking)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
