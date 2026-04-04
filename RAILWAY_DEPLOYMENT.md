# Railway Deployment Guide for Connector Bot

This guide explains how to deploy the Telegram bot on Railway.app using their free tier.

## Architecture Overview

The bot uses this architecture for minimal resource usage:

1. **Flask Web Server** - Runs 24/7 to handle HTTP requests and user interactions
2. **GitHub Actions Cron Jobs** - Automatically trigger `ask_for_calls` and `pair_and_notify` every Monday
3. **SQLite Database** - Tracks users, responses, and job execution history

This approach uses minimal resources (typically <$1/month) and stays well within Railway's free tier!

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
| `CALL_HOUR` | `19` | Used to calculate time on last Monday |
| `CALL_MINUTE` | `0` | Used to calculate time on last Monday |
| `TIMEZONE` | `Europe/Berlin` | Used to determine "last Monday" of month |

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

The bot automatically detects if it's the **last Monday of the month** before executing ask/pair operations.

### Smart Scheduling
- **Cron jobs run weekly on Monday** (simple, reliable)
- **Bot checks internally** if it's the last Monday
- **Jobs are idempotent** - safe to run multiple times per day
- **Database tracking prevents duplicate execution** per month

### Option A: Use GitHub Actions (Recommended - Built-in & Free!)

GitHub Actions is built into GitHub and triggers directly from your repo. No external services needed!

#### Setup GitHub Actions

1. **Add Secrets to your Repository:**
   - Go to GitHub → Your repository
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add these two secrets:

   | Secret Name | Value |
   |-------------|-------|
   | `RAILWAY_URL` | `https://your-railway-app.up.railway.app` |
   | `CRON_SECRET` | Your CRON_SECRET from Railway variables |

2. **The workflow is already configured!**
   - GitHub Actions file exists at `.github/workflows/cron-jobs.yml`
   - Automatically runs every **Monday at 19:00 UTC**
   - Calls `/cron/ask` → waits 10 min → calls `/cron/pair`

3. **Customize the schedule (optional):**
   - Edit `.github/workflows/cron-jobs.yml`
   - Change the `cron` value in the `schedule` section
   - Example to run at different time:
     ```yaml
     on:
       schedule:
         - cron: '0 10 * * 1'  # Monday 10:00 UTC instead
     ```

4. **Monitor workflow runs:**
   - Go to "Actions" tab in your GitHub repository
   - See all scheduled and manual runs
   - Check logs for any failures
   - Green ✅ = Successful, Red ❌ = Failed

5. **Manual trigger for testing:**
   - Actions tab → "Connector Bot Cron Jobs"
   - Click "Run workflow" → "Run workflow"
   - Tests immediately without waiting for Monday

#### GitHub Actions Workflow Details

The file `.github/workflows/cron-jobs.yml` contains three jobs:

1. **ask-for-calls** (Every Monday 19:00 UTC)
   - Sends POST request to `/cron/ask`
   - Bot checks: Is today last Monday of month?
   - If yes: Sends "Do you have time for a call?" to group

2. **pair-and-notify** (Every Monday 19:10 UTC)
   - Waits 10 minutes after ask-for-calls
   - Sends POST request to `/cron/pair`
   - Bot pairs users & sends private notifications

3. **polling-session** (Removed - Not needed)
   - Registration now happens on demand via `/start` command
   - No daily polling window needed

### Option B: Use EasyCron (Alternative - Free External Service)

If you prefer not to use GitHub Actions:

1. Sign up at [easycron.com](https://www.easycron.com) (free)

2. Create cron job for "Ask for Calls" (every Monday):
   - **URL:** `https://your-railway-url.up.railway.app/cron/ask`
   - **Cron Expression:** `0 19 * * 1` (every Monday at 19:00)
   - **Method:** POST
   - **Authorization Header:** `Authorization: Bearer YOUR_CRON_SECRET`
   - **Description:** Weekly Monday check - only executes on last Monday of month

3. Create cron job for "Pair and Notify" (every Monday, 10 min later):
   - **URL:** `https://your-railway-url.up.railway.app/cron/pair`
   - **Cron Expression:** `10 19 * * 1` (every Monday at 19:10)
   - **Method:** POST
   - **Authorization Header:** `Authorization: Bearer YOUR_CRON_SECRET`
   - **Description:** Pairs users and notifies - only executes on last Monday of month

4. **Registration:** Users can register anytime by /start messaging the bot privately
   - No scheduled polling needed - registrations happen on-demand

### Cron Expression Guide

```
* * * * * 
│ │ │ │ └─ Day of week (0=Sunday, 1=Monday, ..., 6=Saturday)
│ │ │ └─── Month (1-12)
│ │ └───── Day of month (1-31)
│ └─────── Hour (0-23 UTC)
└───────── Minute (0-59)

Examples:
0 19 * * 1    = Every Monday at 19:00
10 19 * * 1   = Every Monday at 19:10
0 10 * * *    = Every day at 10:00
30 14 * * 0   = Every Sunday at 14:30
```

### How the "Last Monday" Logic Works

1. **Bot receives weekly Monday cron jobs**
2. **Bot checks:** Is today the last Monday of the month?
   - Monday at start of month → Do nothing
   - Monday at middle of month → Do nothing
   - Monday at end of month (no more Mondays this month) → Execute! ✅
3. **Database tracking:** Records that job was executed in `cron_executions` table
   - Prevents running twice even if cron fires again
   - Resets monthly with new month_year

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
```

### Test Registration & Responses

1. In private chat with bot, send `/start`
2. You should get a registration prompt
3. Click to register
4. Once registered, wait for the next scheduled Monday ask to see full workflow

## How It Works

```
Monthly Cycle (Every Last Monday):
├─ GitHub Actions triggers at 19:00 UTC
│  └─ POST /cron/ask endpoint
│  └─ Bot checks: "Is today the last Monday?" → YES
│  └─ Sends "Do you have time for a call?" to group
│  └─ Message includes reminder to /start if not registered
│
└─ Wait 10 minutes, then trigger pair job (19:10 UTC)
   ├─ POST /cron/pair endpoint  
   ├─ Collects responses from group members
   ├─ Pairs users randomly
   └─ Sends private notifications to callers

User Registration (Anytime):
└─ User sends /start in private chat
   ├─ Bot asks if they want to participate
   └─ Saves registration to database
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
