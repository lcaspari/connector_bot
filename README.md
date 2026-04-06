# Monthly Call Connector Bot 🎤

A Telegram bot that organizes monthly call connections between group members with privacy protection.

**Perfect for**: Organizing regular calls within friend groups, teams, classes, communities, etc.

## Architecture: Railway-Optimized

This bot is designed to run efficiently on Railway.app's free tier:
- **Flask web server** - Runs 24/7 for minimal cost
- **Telegram webhooks** - Bot receives updates instantly via HTTP POST (no polling needed!)
- **GitHub Actions cron jobs** - Triggered automatically on Mondays
- **Lightweight database** - SQLite (can upgrade to PostgreSQL)
- **On-demand registration** - Users can /start anytime and get instant responses

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed deployment instructions.  
See [TELEGRAM_WEBHOOK_SETUP.md](TELEGRAM_WEBHOOK_SETUP.md) for webhook configuration.

## Features

✨ **Last Monday of Month**: Automatically triggers on the last Monday of each month (not a fixed date!)
🎯 **Smart Scheduling**: Cron jobs run weekly, bot intelligently detects the right day
✨ **Monthly Call Check-ins**: Asks group members if they have time for a call
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

The bot automatically runs on the **last Monday of each month**. You can optionally customize the time:

```python
CALL_HOUR = 19         # Hour (0-23) when ask/pair runs
CALL_MINUTE = 0        # Minute (0-59)
TIMEZONE = pytz.timezone("Europe/Berlin")  # Your timezone
```

**Note:** `CALL_DAY` is deprecated - the bot now always uses the last Monday of the month.

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

1. **Last Monday of every month**: Bot asks group "Do you have time for a call?"
2. **Members respond**: Click Yes or No buttons
3. **10 minutes later (still last Monday)**: Bot pairs registered "Yes" members
4. **Private messages**: One person from each pair gets notification to call the other
5. **Privacy maintained**: If someone doesn't call, no one finds out!

## How Pairing Works

- **Monthly cadence**: Always happens on the last Monday of the month (never skipped, automatic date detection)
- **Smart scheduling**: Cron jobs run weekly on Mondays, bot detects "last" Monday internally
- **Pairing logic**: If 5 people say yes → 2 pairs created, 1 person unpaired
- **Unpaired mystery**: Person doesn't know why they weren't called (could be odd number, different pairing next month, etc.)
- **Random selection**: The caller is chosen randomly from each pair
- **Privacy protection**: Only the caller is notified, receiver doesn't know if they were supposed to be called

## Database

The bot uses SQLite for local storage:

- `users` table: Stores registered users
- `monthly_responses` table: Stores yes/no responses and pairing information
- `cron_executions` table: Tracks monthly job executions (prevents duplicate runs)

Database file: `connector_bot.db` (created automatically)

## Running the Bot Locally

### Run Flask Server (For Testing)

For testing the HTTP endpoints locally:

```bash
# Terminal 1: Start Flask server
source venv/bin/activate
python server.py

# Terminal 2: In another terminal, test cron endpoints
curl -X POST http://localhost:5000/cron/ask \
  -H "Authorization: Bearer your-secret-token"
```

This starts a local Flask server. In production (Railway), the server runs 24/7 and automatically receives webhook updates from Telegram.

### Webhook Configuration

For production deployment on Railway, you need to register the webhook with Telegram so it sends updates to your bot.

See **[TELEGRAM_WEBHOOK_SETUP.md](TELEGRAM_WEBHOOK_SETUP.md)** for complete webhook setup instructions.

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
