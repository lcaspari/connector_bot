#!/usr/bin/env python3
"""
Telegram Bot for Monthly Group Call Scheduling
Deployed on Railway.app with GitHub Actions cron jobs

Architecture:
- Flask Web Server: Runs 24/7 to handle HTTP requests and user interactions
- GitHub Actions Cron Jobs (Every Monday):
  * 19:00 UTC: ask_for_calls - Asks group if they have time
  * 19:10 UTC: pair_and_notify - Creates pairs and notifies callers
- User Registration: On-demand via /start command (anytime)
- Database: SQLite for storing users, responses, and job execution history
"""

import sqlite3
import random
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==================== CONFIGURATION ====================

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0")) if os.getenv("GROUP_CHAT_ID") else None

CALL_DAY = int(os.getenv("CALL_DAY", "1"))
CALL_HOUR = int(os.getenv("CALL_HOUR", "19"))
CALL_MINUTE = int(os.getenv("CALL_MINUTE", "0"))

TIMEZONE = pytz.timezone(os.getenv("TIMEZONE", "Europe/Berlin"))
DATABASE = os.getenv("DATABASE", "connector_bot.db")

# Test mode: allows running jobs anytime, bypasses date restrictions
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# ==================== LOGGING ====================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== HELPERS ====================

def is_last_monday_of_month() -> bool:
    """
    Check if today is the last Monday of the current month.
    
    Returns:
        True if today is the last Monday of the month, False otherwise
    """
    today = datetime.now(TIMEZONE).date()
    
    # Check if today is a Monday (weekday 0 = Monday)
    if today.weekday() != 0:
        return False
    
    # Check if there's another Monday in this month
    next_week = today + timedelta(days=7)
    return next_week.month != today.month

# ==================== DATABASE ====================

def init_database():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            registered INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Monthly responses table
    c.execute("""
        CREATE TABLE IF NOT EXISTS monthly_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month_year TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            response TEXT,
            paired_with INTEGER,
            notified_as_caller INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(month_year, user_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    
    # Cron execution tracking table
    c.execute("""
        CREATE TABLE IF NOT EXISTS cron_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            month_year TEXT NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(job_name, month_year)
        )
    """)
    
    conn.commit()
    conn.close()

def get_or_create_user(user_id: int, username: str = None, first_name: str = None) -> bool:
    """Get or create a user. Returns True if user is registered."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute("SELECT registered FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    
    if row:
        conn.close()
        return row[0] == 1
    
    c.execute(
        "INSERT INTO users (user_id, username, first_name, registered) VALUES (?, ?, ?, ?)",
        (user_id, username, first_name, 0)
    )
    conn.commit()
    conn.close()
    return False

def register_user(user_id: int):
    """Mark user as registered."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE users SET registered = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def is_user_registered(user_id: int) -> bool:
    """Check if user is registered."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT registered FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] == 1 if row else False

def record_response(month_year: str, user_id: int, response: str):
    """Record user's yes/no response for the month."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute(
        """INSERT OR REPLACE INTO monthly_responses 
           (month_year, user_id, response) VALUES (?, ?, ?)""",
        (month_year, user_id, response)
    )
    conn.commit()
    conn.close()

def get_yes_responses(month_year: str) -> List[int]:
    """Get all user IDs who responded 'yes' for a month."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute(
        """SELECT user_id FROM monthly_responses 
           WHERE month_year = ? AND response = 'yes'""",
        (month_year,)
    )
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def save_pairs(month_year: str, pairs: List[Tuple[int, int]]):
    """Save the pairs generated for the month."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    for caller_id, receiver_id in pairs:
        c.execute(
            """UPDATE monthly_responses 
               SET paired_with = ?, notified_as_caller = 1 
               WHERE month_year = ? AND user_id = ?""",
            (receiver_id, month_year, caller_id)
        )
    
    conn.commit()
    conn.close()

def get_paired_users(month_year: str) -> List[Tuple[int, int]]:
    """Get pairs for a month (caller_id, receiver_id)."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    c.execute(
        """SELECT user_id, paired_with FROM monthly_responses 
           WHERE month_year = ? AND notified_as_caller = 1""",
        (month_year,)
    )
    pairs = [(row[0], row[1]) for row in c.fetchall()]
    conn.close()
    return pairs

def job_already_executed_this_month(job_name: str) -> bool:
    """Check if a cron job was already executed this month."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    month_year = datetime.now(TIMEZONE).strftime("%Y-%m")
    c.execute(
        "SELECT id FROM cron_executions WHERE job_name = ? AND month_year = ?",
        (job_name, month_year)
    )
    result = c.fetchone()
    conn.close()
    return result is not None

def record_job_execution(job_name: str):
    """Record that a cron job was executed this month."""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    month_year = datetime.now(TIMEZONE).strftime("%Y-%m")
    c.execute(
        "INSERT OR IGNORE INTO cron_executions (job_name, month_year) VALUES (?, ?)",
        (job_name, month_year)
    )
    conn.commit()
    conn.close()

# ==================== BOT EVENT HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - initiates user registration."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    is_registered = get_or_create_user(user_id, username, first_name)
    
    if is_registered:
        await update.message.reply_text(
            f"Welcome back, {first_name}! You're already registered with the Call Bot."
        )
    else:
        keyboard = [
            [InlineKeyboardButton("Yes, register me!", callback_data="register_yes")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Hi {first_name}! 👋\n\n"
            "I'm the Monthly Call Connector Bot. Here's what I do:\n\n"
            "1️⃣ Each month on a set date, I ask if you have time for a quick call\n"
            "2️⃣ I randomly pair people who say 'yes'\n"
            "3️⃣ I tell one person from each pair to call the other\n\n"
            "No one will notice if you don't call - it's between you and me! 🤫\n\n"
            "Want to join?",
            reply_markup=reply_markup
        )

async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle registration confirmation."""
    query = update.callback_query
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    
    register_user(user_id)
    
    await query.answer()
    await query.edit_message_text(
        text=f"✅ You're registered, {first_name}! "
             "You'll get notifications when it's time for the monthly call check-in."
    )
    
    logger.info(f"User {user_id} ({first_name}) registered.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help information."""
    await update.message.reply_text(
        "📱 *Connector Bot Help*\n\n"
        "*Commands:*\n"
        "/start - Register with the bot\n"
        "/help - Show this help message\n"
        "/status - Check your registration status\n\n"
        "*How it works:*\n"
        "1. I'll ask the group monthly if people have time for a call\n"
        "2. You respond with Yes or No\n"
        "3. If you say yes, you might get paired with someone\n"
        "4. I'll message you privately who to call\n"
        "5. If you don't call, it's your secret - no one will know! 🤐",
        parse_mode="Markdown"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's registration status."""
    user_id = update.effective_user.id
    is_registered = is_user_registered(user_id)
    
    if is_registered:
        await update.message.reply_text("✅ You are registered with the Call Bot!")
    else:
        await update.message.reply_text(
            "❌ You are not registered. Use /start to register."
        )

async def ask_for_calls(context: ContextTypes.DEFAULT_TYPE):
    """
    Monthly scheduled task: Ask group if anyone wants to have calls.
    Gets called on CALL_DAY at CALL_HOUR:CALL_MINUTE
    """
    global GROUP_CHAT_ID
    
    if GROUP_CHAT_ID is None:
        logger.error("GROUP_CHAT_ID not set. Bot hasn't been added to group yet.")
        return
    
    month_year = datetime.now(TIMEZONE).strftime("%Y-%m")
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, I have time!", callback_data=f"response_yes_{month_year}"),
            InlineKeyboardButton("❌ No, busy", callback_data=f"response_no_{month_year}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text="🎤 *Monthly Call Check-in!* 🎤\n\n"
             "Hey everyone! Do you have time for a call in about 10 minutes? "
             "Let me know below! ⬇️",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    logger.info(f"Asked group for monthly call participation ({month_year})")

# ==================== CRON JOB FUNCTIONS ====================

async def send_ask_for_calls(bot):
    """
    CRON JOB 1: Called to ask group for participation.
    Only executes on the last Monday of the month.
    Run this via HTTP endpoint from Railway's cron scheduler (weekly on Mondays).
    
    Args:
        bot: Telegram Bot instance
    
    Returns:
        Dict with status and message
    """
    # Check if today is the last Monday of the month (skip if TEST_MODE enabled)
    if not TEST_MODE and not is_last_monday_of_month():
        return {
            "status": "skipped",
            "message": "Not the last Monday of the month. No action taken."
        }
    
    # Check if already executed this month (skip if TEST_MODE enabled)
    if not TEST_MODE and job_already_executed_this_month("ask_for_calls"):
        return {
            "status": "skipped",
            "message": "ask_for_calls already executed this month."
        }
    
    if GROUP_CHAT_ID is None:
        logger.error("GROUP_CHAT_ID not set. Bot hasn't been added to group yet.")
        return {"status": "error", "message": "GROUP_CHAT_ID not set"}
    
    month_year = datetime.now(TIMEZONE).strftime("%Y-%m")
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, I have time!", callback_data=f"response_yes_{month_year}"),
            InlineKeyboardButton("❌ No, busy", callback_data=f"response_no_{month_year}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text="🎤 *Monthly Call Check-in!* 🎤\n\n"
                 "Hey everyone! Do you have time for a call in about 10 minutes? "
                 "Let me know below! ⬇️\n\n"
                 "_Note: If you haven't registered yet, send /start to me in a private chat first!_",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        record_job_execution("ask_for_calls")
        logger.info(f"Asked group for monthly call participation ({month_year})")
        return {"status": "success", "message": f"Message sent to group {GROUP_CHAT_ID}"}
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return {"status": "error", "message": str(e)}

async def send_pair_and_notify(bot):
    """
    CRON JOB 2: Called to pair users and send notifications.
    Only executes on the last Monday of the month (after ask_for_calls).
    Run this via HTTP endpoint from Railway's cron scheduler (weekly on Mondays).
    
    Args:
        bot: Telegram Bot instance
    
    Returns:
        Dict with status and results
    """
    # Check if today is the last Monday of the month (skip if TEST_MODE enabled)
    if not TEST_MODE and not is_last_monday_of_month():
        return {
            "status": "skipped",
            "message": "Not the last Monday of the month. No action taken."
        }
    
    # Check if already executed this month (skip if TEST_MODE enabled)
    if not TEST_MODE and job_already_executed_this_month("pair_and_notify"):
        return {
            "status": "skipped",
            "message": "pair_and_notify already executed this month."
        }
    
    month_year = datetime.now(TIMEZONE).strftime("%Y-%m")
    
    yes_users = get_yes_responses(month_year)
    
    if len(yes_users) < 2:
        msg = "Not enough people said yes for calls this month. See you next month! 👋"
        if GROUP_CHAT_ID:
            try:
                await bot.send_message(chat_id=GROUP_CHAT_ID, text=msg)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
        logger.info(f"Not enough yes responses for {month_year} (only {len(yes_users)})")
        return {"status": "success", "message": f"Only {len(yes_users)} yes responses"}
    
    # Randomly shuffle and pair
    random.shuffle(yes_users)
    pairs: List[Tuple[int, int]] = []
    
    for i in range(0, len(yes_users) - 1, 2):
        caller_id = yes_users[i]
        receiver_id = yes_users[i + 1]
        pairs.append((caller_id, receiver_id))
    
    save_pairs(month_year, pairs)
    
    # Send notifications
    notification_count = 0
    for caller_id, receiver_id in pairs:
        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("SELECT first_name FROM users WHERE user_id = ?", (receiver_id,))
            receiver_data = c.fetchone()
            conn.close()
            
            receiver_name = receiver_data[0] if receiver_data else f"User {receiver_id}"
            
            await bot.send_message(
                chat_id=caller_id,
                text=f"📞 *Your Monthly Call Assignment* 📞\n\n"
                     f"Please call {receiver_name} now or within the next 10 minutes!\n\n"
                     f"They're expecting your call. If you can't make it right now, "
                     f"it's okay - they won't know it was you who was supposed to call. 🤐",
                parse_mode="Markdown"
            )
            notification_count += 1
            logger.info(f"Notified user {caller_id} to call {receiver_id}")
        except Exception as e:
            logger.error(f"Failed to notify user {caller_id}: {e}")
    
    # Notify group
    if GROUP_CHAT_ID:
        paired_count = len(pairs)
        unpaired_text = ""
        if len(yes_users) % 2 == 1:
            unpaired_text = f"\n(One person got a surprise day off this month! 🎁)"
        
        try:
            await bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"✅ *Pairs created!* ✅\n\n"
                     f"{paired_count} pair{'s' if paired_count != 1 else ''} have been assigned. "
                     f"Those who were selected to call have received their assignments privately. "
                     f"Good luck! 🍀{unpaired_text}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send group message: {e}")
    
    record_job_execution("pair_and_notify")
    
    return {
        "status": "success",
        "pairs_created": len(pairs),
        "notifications_sent": notification_count
    }

async def handle_response_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's yes/no response to monthly call."""
    query = update.callback_query
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    
    # Check if registered
    if not is_user_registered(user_id):
        await query.answer("❌ You must register first. Use /start in private chat.", show_alert=True)
        return
    
    # Extract response and month_year from callback data
    parts = query.data.split("_")
    response = parts[1]  # 'yes' or 'no'
    month_year = "_".join(parts[2:])  # handle dates with underscores
    
    record_response(month_year, user_id, response)
    
    emoji = "✅" if response == "yes" else "❌"
    await query.answer(f"{emoji} Response recorded!", show_alert=False)
    
    logger.info(f"User {user_id} ({first_name}) responded '{response}' for {month_year}")

async def pair_and_notify(context: ContextTypes.DEFAULT_TYPE):
    """
    Run after response period ends to pair users and send notifications.
    Should be scheduled ~10 minutes after ask_for_calls.
    """
    month_year = datetime.now(TIMEZONE).strftime("%Y-%m")
    
    yes_users = get_yes_responses(month_year)
    
    if len(yes_users) < 2:
        if GROUP_CHAT_ID:
            message = "Not enough people said yes for calls this month. See you next month! 👋"
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message)
        logger.info(f"Not enough yes responses for {month_year} (only {len(yes_users)})")
        return
    
    # Randomly shuffle and pair
    random.shuffle(yes_users)
    pairs: List[Tuple[int, int]] = []
    
    # If odd number, last person won't be paired (and won't know why)
    for i in range(0, len(yes_users) - 1, 2):
        caller_id = yes_users[i]
        receiver_id = yes_users[i + 1]
        pairs.append((caller_id, receiver_id))
    
    # Save pairs to database
    save_pairs(month_year, pairs)
    
    # Send notifications
    for caller_id, receiver_id in pairs:
        try:
            # Get receiver's name
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("SELECT first_name FROM users WHERE user_id = ?", (receiver_id,))
            receiver_data = c.fetchone()
            conn.close()
            
            receiver_name = receiver_data[0] if receiver_data else f"User {receiver_id}"
            
            await context.bot.send_message(
                chat_id=caller_id,
                text=f"📞 *Your Monthly Call Assignment* 📞\n\n"
                     f"Please call {receiver_name} now or within the next 10 minutes!\n\n"
                     f"They're expecting your call. If you can't make it right now, "
                     f"it's okay - they won't know it was you who was supposed to call. 🤐",
                parse_mode="Markdown"
            )
            logger.info(f"Notified user {caller_id} to call {receiver_id}")
        except Exception as e:
            logger.error(f"Failed to notify user {caller_id}: {e}")
    
    # Notify group
    if GROUP_CHAT_ID:
        paired_count = len(pairs)
        unpaired_text = ""
        if len(yes_users) % 2 == 1:
            unpaired_text = f"\n(One person got a surprise day off this month! 🎁)"
        
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=f"✅ *Pairs created!* ✅\n\n"
                 f"{paired_count} pair{'s' if paired_count != 1 else ''} have been assigned. "
                 f"Those who were selected to call have received their assignments privately. "
                 f"Good luck! 🍀{unpaired_text}",
            parse_mode="Markdown"
        )

async def post_init(application: Application):
    """Set up scheduler after bot starts."""
    # NOTE: For Railway cron jobs, the scheduler is NOT set up here
    # Instead, use Railway's cron job feature to call the functions directly
    logger.info("Bot initialized (scheduler disabled for Railway cron jobs)")

async def handle_new_group_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when bot joins a group."""
    global GROUP_CHAT_ID
    
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.is_bot and member.username == (await context.bot.get_me()).username:
                GROUP_CHAT_ID = update.message.chat_id
                await update.message.reply_text(
                    "👋 Hi everyone! I'm the Call Connector Bot.\n\n"
                    "I'll ask you once a month if you have time for a call, "
                    "and I'll randomly pair you with someone else to chat. "
                    "No pressure - if you don't call, it's between us! 🤐\n\n"
                    "Use /start in private chat to register with me."
                )
                logger.info(f"Bot added to group {GROUP_CHAT_ID}")

def build_app_sync() -> Application:
    """
    Build and configure the Telegram bot application (synchronous version).
    Called at module import time to ensure it runs in the main thread.
    Does NOT start the scheduler - that's handled separately by cron jobs.
    """
    init_database()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers for private chat (registration)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    
    app.add_handler(CallbackQueryHandler(register_callback, pattern="^register_yes$"))
    app.add_handler(CallbackQueryHandler(handle_response_callback, pattern="^response_"))
    
    # Handler for bot joining group
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_group_member))
    
    return app

async def build_app() -> Application:
    """
    Async wrapper for build_app_sync (for backward compatibility).
    """
    return build_app_sync()

async def run_polling_session(duration_minutes: int = 60):
    """
    Run the bot in polling mode for a limited time.
    Used for handling registrations and responses.
    
    Args:
        duration_minutes: How long to poll (default 60 minutes for registration window)
    """
    app = await build_app()
    
    await app.initialize()
    await app.start()
    
    logger.info(f"Starting polling session for {duration_minutes} minutes...")
    
    try:
        # Start polling with timeout
        async with app.updater:
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, timeout=30)
            
            # Keep polling for specified duration
            import asyncio
            await asyncio.sleep(duration_minutes * 60)
            
            # Clean shutdown
            await app.updater.stop()
    finally:
        await app.stop()
        await app.shutdown()
    
    logger.info("Polling session ended")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_polling_session())
