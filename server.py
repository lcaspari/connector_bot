#!/usr/bin/env python3
"""
Flask Server for Railway.app Integration
Handles HTTP endpoints for:
- /telegram - Webhook for receiving Telegram updates (POST)
- /cron/ask - HTTP endpoint for asking group (GET/POST with ?secret=...)
- /cron/pair - HTTP endpoint for pairing and notifying (GET/POST with ?secret=...)
- /health - Health check for Railway (GET)

IMPORTANT: Switch from polling to webhooks to avoid Updater threading issues.
Telegram sends POSTs to /telegram instead of us polling for updates.
"""

import logging
import os
from flask import Flask, jsonify, request
from main import (
    send_ask_for_calls,
    send_pair_and_notify,
    process_telegram_update,
    BOT_TOKEN,
)
from telegram import Bot

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== FLASK APP SETUP ====================

app = Flask(__name__)
CRON_SECRET = os.getenv("CRON_SECRET", "your-secret-here")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-app.railway.app/telegram")

# ==================== HEALTH CHECK ====================

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for Railway."""
    return jsonify({"status": "healthy"}), 200

# ==================== TELEGRAM WEBHOOK ====================

@app.route("/telegram", methods=["POST"])
async def telegram_webhook():
    """
    Receive updates from Telegram via webhook.
    Telegram sends POST requests here when users interact with the bot.
    This replaces polling - much more efficient!
    """
    try:
        # Get the update from Telegram
        update_data = request.get_json()
        
        if not update_data:
            logger.warning("Received empty webhook request")
            return jsonify({"ok": False}), 400
        
        update_id = update_data.get("update_id", "unknown")
        logger.info(f"Received telegram update {update_id}")
        
        # Process the update
        success = await process_telegram_update(update_data)
        
        # Always return 200 OK to Telegram (even if we failed to process)
        # Telegram won't retry if we return 200
        return jsonify({"ok": True}), 200
            
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        # Still return 200 so Telegram doesn't retry
        return jsonify({"ok": True}), 200

# ==================== CRON JOB ENDPOINTS ====================

@app.route("/cron/ask", methods=["GET", "POST"])
async def cron_ask():
    """
    Cron job endpoint: Ask group for participation.
    Called by GitHub Actions on the last Monday of month at 19:00 UTC.
    
    Usage:
    - GET /cron/ask?secret=YOUR_CRON_SECRET
    - POST /cron/ask with JSON: {"secret": "YOUR_CRON_SECRET"}
    """
    # Validate secret from query param or JSON body
    secret = request.args.get("secret")
    if not secret and request.is_json:
        secret = request.get_json().get("secret")
    
    if secret != CRON_SECRET:
        logger.warning(f"Unauthorized cron request to /cron/ask")
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        bot = Bot(token=BOT_TOKEN)
        result = await send_ask_for_calls(bot)
        logger.info(f"Cron ask result: {result}")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Cron ask error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/cron/pair", methods=["GET", "POST"])
async def cron_pair():
    """
    Cron job endpoint: Pair users and send notifications.
    Called by GitHub Actions on the last Monday of month at 19:10 UTC (10 min after ask).
    
    Usage:
    - GET /cron/pair?secret=YOUR_CRON_SECRET
    - POST /cron/pair with JSON: {"secret": "YOUR_CRON_SECRET"}
    """
    # Validate secret from query param or JSON body
    secret = request.args.get("secret")
    if not secret and request.is_json:
        secret = request.get_json().get("secret")
    
    if secret != CRON_SECRET:
        logger.warning(f"Unauthorized cron request to /cron/pair")
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        bot = Bot(token=BOT_TOKEN)
        result = await send_pair_and_notify(bot)
        logger.info(f"Cron pair result: {result}")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Cron pair error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

# ==================== STARTUP ====================

logger.info("=" * 70)
logger.info("Flask app initialized (webhook mode)")
logger.info(f"BOT_TOKEN: {bool(BOT_TOKEN and BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE')}")
logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
logger.info("=" * 70)
logger.info("Bot receives updates via Telegram webhook (no background polling)")
logger.info("Users can send /start anytime and bot will respond immediately")
logger.info("=" * 70)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
