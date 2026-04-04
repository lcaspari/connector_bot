# Monthly Call Connector Bot 🎤

A Telegram bot that organizes monthly call connections between group members with privacy protection.

**Perfect for**: Organizing regular calls within friend groups, teams, classes, communities, etc.

## Architecture: Railway-Optimized

This bot is designed to run efficiently on Railway.app's free tier:
- **Flask web server** - Runs 24/7 for minimal cost
- **Cron jobs** - Triggered monthly for ask & pair operations
- **Limited polling** - 1 hour daily for user interactions
- **Lightweight database** - SQLite (can upgrade to PostgreSQL)

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed deployment instructions.

## Features

✨ **Monthly Call Check-ins**: Asks group members on a specific date if they have time for a call
🤝 **Random Pairing**: Automatically pairs willing participants randomly
📞 **Private Notifications**: Sends one person from each pair their assignment privately
🤐 **Privacy**: If someone doesn't call, it remains their secret - others won't notice
👥 **User Registration**: Simple /start registration to participate
🚀 **Cloud Ready**: Deploy on Railway.app, stay within free tier

## Quick Start: Choose Your Deployment

### 🚀 Deploy on Railway (Recommended - Free!)

For hands-off operation without running code on your computer:

1. See **[RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)** for complete Railway setup
2. Takes ~15 minutes to have the bot running 24/7
3. Uses free tier ($5/month credits, typical usage <$1/month)
4. No need to keep your computer running

### 💻 Run Locally (Development)

For testing before deploying:

## Setup

### 1. Create Virtual Environment

```bash
# Navigate to project directory
cd /Users/lucaspari/Projects/Connector_Bot

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Bot Token

1. **Get a Bot Token from BotFather**:
   - Go to Telegram and find `@BotFather`
   - Send `/newbot` command
   - Follow instructions to create your bot
   - Copy the API token

2. **Edit main.py**:
   - Open `main.py`
   - Find line with `BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"`
   - Replace with your actual token:
   ```python
   BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
   ```

### 4. Configure Schedule (Optional)

In `main.py`, customize these variables:

```python
CALL_DAY = 1           # Day of month (1-28)
CALL_HOUR = 19         # Hour (0-23)
CALL_MINUTE = 0        # Minute (0-59)
TIMEZONE = pytz.timezone("Europe/Berlin")  # Your timezone
```

### 5. Add Bot to Group

1. Create or select a Telegram group
2. Add your bot to the group (search by username)
3. Give bot admin permissions (for sending messages)
4. The bot will announce itself and set the group ID automatically

## Usage

### User Commands (Private Chat)

- `/start` - Register with the bot
- `/help` - Show help information
- `/status` - Check registration status

### What Happens

1. **On scheduled date**: Bot asks group "Do you have time for a call?"
2. **Members respond**: Click Yes or No buttons
3. **After 10 minutes**: Bot pairs registered "Yes" members
4. **Private messages**: One person from each pair gets notification to call the other
5. **Privacy maintained**: If someone doesn't call, no one finds out!

## How Pairing Works

- If 5 people say yes: 2 pairs are created, 1 person is unpaired
- Unpaired person doesn't know why (could be odd number or they might get paired differently next month)
- The caller is chosen randomly from each pair
- Only the caller is notified (to maintain privacy)

## Database

The bot uses SQLite for local storage:

- `users` table: Stores registered users
- `monthly_responses` table: Stores yes/no responses and pairing information

Database file: `connector_bot.db` (created automatically)

## Running the Bot Locally

The bot has two modes for local testing:

### Option 1: Run Polling Session (Recommended for Testing)

Runs for a limited time (default 1 hour) to test registration/responses:

```bash
source venv/bin/activate
python main.py
```

### Option 2: Run Flask Server + Polling Manually

For testing the full architecture:

```bash
# Terminal 1: Start Flask server
source venv/bin/activate
python server.py

# Terminal 2: Start a polling session
source venv/bin/activate
python -c "import asyncio; from main import run_polling_session; asyncio.run(run_polling_session(60))"

# Terminal 3 (after some time): Manually test cron endpoints
curl -X POST http://localhost:5000/cron/ask \
  -H "Authorization: Bearer your-secret-token"
```

## Stopping the Bot

Press `Ctrl+C` in the terminal

## Requirements

- Python 3.9+
- Telegram Account
- Bot token from BotFather

## Troubleshooting

**Bot not responding?**
- Check that `BOT_TOKEN` is correctly set
- Verify bot has been added to the group
- Check logs for errors

**Scheduling not working?**
- Verify `TIMEZONE` is correct
- Check `CALL_DAY`, `CALL_HOUR`, `CALL_MINUTE` are valid
- Bot needs to be running continuously (consider using screen, tmux, or systemd)

**Database issues?**
- Delete `connector_bot.db` to reset (users will need to re-register)
- Check file permissions

## Project Structure

```
Connector_Bot/
├── main.py              # Main bot code
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── .gitignore          # Git ignore rules
├── venv/               # Virtual environment (created by you)
└── connector_bot.db    # Database (created automatically)
```

## Privacy Notes

- Users' Telegram IDs and names are stored locally in the database
- No data is sent to external services except Telegram API
- Users can review what they've shared by checking `/status`

## Support

For issues with the code, check the logs or review the error messages in the terminal where you're running the bot.

For Telegram bot issues, consult the [python-telegram-bot documentation](https://python-telegram-bot.readthedocs.io/).
