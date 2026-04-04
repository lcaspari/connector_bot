# Railway Deployment Guide for Connector Bot

This guide explains how to deploy the Telegram bot on Railway.app using their free tier.

## Architecture Overview

Instead of running the bot 24/7 (which uses free tier resources), the bot uses:

1. **Flask Web Server** - Runs 24/7 to handle HTTP requests
2. **Cron Jobs** - Trigger `ask_for_calls` (monthly) and `pair_and_notify` (monthly)
3. **Polling Sessions** - Short 1-hour polling window daily for user interactions (registration, responses)

This approach uses minimal resources and stays within Railway's free tier!

## Step 1: Prepare Your Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy your bot token (looks like: `123456789:ABCDEFGHIjklmnopqrstuvwxyz...`)

## Step 2: Set Up Railway Project

### Option A: Via Git (Recommended)

1. Push your code to GitHub/GitLab
2. Go to [railway.app](https://railway.app)
3. Click "New Project" → "Deploy from Git"
4. Connect your repository
5. Railway will auto-detect Python and build the app

### Option B: Via CLI

1. Install Railway CLI: `npm install -g @railway/cli` (requires Node.js)
2. Login: `railway login`
3. From project directory: `railway init`
4. Follow prompts and select "Python"

## Step 3: Configure Environment Variables

In Railway dashboard:

1. Go to your project
2. Click "Variables" tab
3. Add these variables:

| Name | Value | Notes |
|------|-------|-------|
| `BOT_TOKEN` | Your Telegram bot token | Required |
| `CRON_SECRET` | `change-me-to-something-secure` | Change this! Used to authorize cron jobs |
| `GROUP_CHAT_ID` | Leave blank initially | Will be set after bot joins your group |
| `CALL_DAY` | `1` | Day of month (1-28) |
| `CALL_HOUR` | `19` | Hour in 24-hour format (0-23) |
| `CALL_MINUTE` | `0` | Minute (0-59) |
| `TIMEZONE` | `Europe/Berlin` | Change to your timezone |
| `POLLING_DURATION` | `60` | Minutes to run polling session daily |

### Example Timezone Values
- `Europe/Berlin` - Central Europe
- `Europe/London` - UK
- `Europe/Paris` - France
- `America/New_York` - Eastern US
- `America/Los_Angeles` - Pacific US
- `Asia/Tokyo` - Japan
- `Australia/Sydney` - Australia

## Step 4: Deploy

Railway will automatically:
1. Install Python dependencies from `requirements.txt`
2. Build the app
3. Start the Flask web server on `PORT` 8000

You should see your app running in the Railway dashboard.

## Step 5: Configure Cron Jobs

Railway apps need cron jobs triggered externally (Railway doesn't have built-in cron scheduling like Heroku).

### Option A: Use EasyCron (Recommended for Free)

EasyCron.com provides free cron scheduling:

1. Sign up at [easycron.com](https://www.easycron.com) (free)
2. Create cron job for "Ask for Calls" (1st of month):
   - **URL:** `https://your-railway-url.up.railway.app/cron/ask`
   - **Cron Expression:** `0 19 1 * *` (adjust hour/minute as needed)
   - **Method:** POST
   - **Authorization Header:** `Authorization: Bearer YOUR_CRON_SECRET`
   - **Description:** Monthly call request

3. Create cron job for "Pair and Notify" (10 minutes later):
   - **URL:** `https://your-railway-url.up.railway.app/cron/pair`
   - **Cron Expression:** `10 19 1 * *` (10 minutes after ask)
   - **Method:** POST
   - **Authorization Header:** `Authorization: Bearer YOUR_CRON_SECRET`

4. Create cron job for "Polling Session" (daily):
   - **URL:** `https://your-railway-url.up.railway.app/polling/start?duration_minutes=60`
   - **Cron Expression:** `0 10 * * *` (daily at 10 AM)
   - **Method:** POST
   - **Authorization Header:** `Authorization: Bearer YOUR_CRON_SECRET`

### Option B: Use Railway Background Jobs (Coming Soon)

Railway is developing native cron support. Check their blog for updates.

### Option C: Use External CI/CD

Use GitHub Actions or GitLab CI to trigger cron jobs:

```yaml
# .github/workflows/cron-ask.yml
name: Monthly Cron - Ask for Calls

on:
  schedule:
    - cron: '0 19 1 * *'  # 1st of month at 19:00

jobs:
  ask-for-calls:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger ask_for_calls
        run: |
          curl -X POST ${{ secrets.RAILWAY_URL }}/cron/ask \
            -H "Authorization: Bearer ${{ secrets.CRON_SECRET }}"
```

## Step 6: Add Bot to Your Group & Get Chat ID

1. Create a Telegram group or select existing one
2. Add your bot to the group (search by username)
3. Send a message in the group to trigger activity
4. In Railway logs, look for: `Bot added to group [CHAT_ID]`
5. Copy that CHAT_ID and set it as `GROUP_CHAT_ID` variable in Railway

## Step 7: Testing

### Manually Test Cron Jobs

Before relying on the scheduler, test the endpoints:

```bash
# Test ask_for_calls
curl -X POST https://your-railway-url.up.railway.app/cron/ask \
  -H "Authorization: Bearer YOUR_CRON_SECRET"

# Test pair_and_notify
curl -X POST https://your-railway-url.up.railway.app/cron/pair \
  -H "Authorization: Bearer YOUR_CRON_SECRET"

# Test polling
curl -X POST https://your-railway-url.up.railway.app/polling/start \
  -H "Authorization: Bearer YOUR_CRON_SECRET"
```

### Test Registration & Responses

1. In private chat with bot, send `/start`
2. You should get a registration prompt
3. Click to register
4. Once registered, create test conditions or wait for next scheduled ask

## How It Works

```
Monthly Cycle:
├─ Cron Job 1 (scheduled time)
│  └─ Sends "Do you have time for a call?" to group
│  └─ Polling session starts (15 min) to collect responses
│
├─ Cron Job 2 (10 min later)
│  └─ Pairs users randomly
│  └─ Sends private notifications to callers
│
└─ Daily
   └─ Polling session (1 hour) handles:
      - User registrations (/start)
      - Private chat interactions
```

## Monitoring

### View Logs

1. In Railway dashboard, click your project
2. Go to "Deployments" → select latest deployment
3. Click "Logs" to see real-time logs
4. Check for errors or confirmation messages

### Check Bot Status

- Health check: `https://your-url.up.railway.app/health`
- Should return: `{"status": "ok"}`

## Troubleshooting

### Bot not responding to /start?

- Verify `BOT_TOKEN` is correct
- Check bot was added to group properly
- Look for errors in Railway logs

### Cron jobs not running?

- Verify the cron service (EasyCron/Railway) is hitting the correct URL
- Check that `CRON_SECRET` header matches in your cron job configuration
- Look at Railway logs for any 401 Unauthorized errors
- Test manually: `curl -X POST https://your-url.up.railway.app/health`

### GROUP_CHAT_ID not set?

- Make sure bot was added to the group
- Manually add bot and send a message to trigger the handler
- Check Railway logs for the chat ID

### Database errors?

- Railway provides ephemeral file storage
- Database persists between deployments, but gets deleted if app dies
- Consider adding a database service (PostgreSQL, Redis) for persistence

## Free Tier Limits

Railway free tier includes:
- **$5/month** free credits
- Ample for a bot that:
  - Runs Flask server (low CPU when idle)
  - Polls for 1 hour daily (minimal network)
  - Sends ~2 messages monthly (very minimal data)

With this architecture, you'll use <$1/month typically!

## Upgrading to Production

When ready for production:

1. Add a proper database (PostgreSQL) instead of SQLite
2. Set up error monitoring (Sentry)
3. Implement backup/restore procedures
4. Set up more robust cron job service (Temporal, Bull Queue, etc.)

## Support

- [Railway Documentation](https://docs.railway.app)
- [Python-telegram-bot Docs](https://python-telegram-bot.readthedocs.io)
- EasyCron: [easycron.com/faq](https://www.easycron.com/page/faq)

## Important Security Notes

⚠️ **Never commit these to Git:**
- `BOT_TOKEN` - Use Railway's environment variables
- `.env` files - Add to `.gitignore`

✅ **Always use strong `CRON_SECRET`:**
- Change from default
- Make it long and random: `python -c "import secrets; print(secrets.token_hex(32))"`
- Store securely in Railway variables
