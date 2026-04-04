# Railway Deployment Quick Start

Get your bot running on Railway.app in 5 minutes!

## Prerequisites
- Telegram bot token from @BotFather
- GitHub/GitLab account with code pushed
- Railway.app account (free)

## Fast Setup (5 steps)

### 1. Create Railway Project
- Go to [railway.app](https://railway.app)
- Click "New Project" → "Deploy from Git"
- Select your repository

### 2. Set Environment Variables

In Railway dashboard → Variables tab:

⚠️ **IMPORTANT: Mark `BOT_TOKEN` and `CRON_SECRET` as secrets (click the lock icon!)**

```
BOT_TOKEN=<your-actual-token-from-BotFather>
CRON_SECRET=<generate-a-secure-random-string>
CALL_HOUR=19
CALL_MINUTE=0
TIMEZONE=Europe/Berlin
GROUP_CHAT_ID=<leave-blank-for-now>
```

📅 **Smart Scheduling**: Bot automatically detects the **last Monday of each month** - no need to set a fixed date!

**How to generate a secure `CRON_SECRET`:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**How to mark as secret in Railway:**
1. Paste the value in the variable field
2. Click the **lock icon 🔒** next to the variable name
3. It's now encrypted and hidden from logs

### 3. Wait for Deployment

Railway auto-builds and deploys. Check "Deployments" tab.
Once green, note your public URL: `https://your-app-name.up.railway.app`

### 4. Add Bot to Group

1. Create or select a Telegram group
2. Add bot to group by username
3. Check Railway logs for `Bot added to group [CHAT_ID]`
4. Update Railway variables with `GROUP_CHAT_ID = [that ID]`

### 5. Set Up Cron Jobs (GitHub Actions - Already Configured!)

The easiest way is **GitHub Actions** - it's already set up in your repo!

**What you need to do:**

1. Go to GitHub repository → **Settings** → **Secrets and variables** → **Actions**

2. Click **New repository secret** and add:
   - Secret name: `RAILWAY_URL`
   - Secret value: `https://your-app-name.up.railway.app`

3. Click **New repository secret** again and add:
   - Secret name: `CRON_SECRET`
   - Secret value: Your `CRON_SECRET` from Railway variables

4. **That's it!** The workflow at `.github/workflows/cron-jobs.yml` will:
   - ✅ Run every Monday at 19:00 UTC automatically
   - ✅ Call `/cron/ask` to ask the group
   - ✅ Wait 10 minutes, then call `/cron/pair` to create pairs

5. **Want to test?**
   - Go to Actions tab → Connector Bot Cron Jobs
   - Click "Run workflow" to trigger immediately

**Customize timing (optional):**
Edit `.github/workflows/cron-jobs.yml` and change:
```yaml
schedule:
  - cron: '0 19 * * 1'  # Change this to different time
```

**Clean up** (optional):
You can delete `.github/workflows/daily-polling.yml` since registrations happen on-demand via `/start`

**Registration**: Users message `/start` to the bot privately anytime - no polling needed!

✅ Done! Bot is now running 24/7 for ~$0.50/month

## Verify It Works

Test endpoints:
```bash
curl -X POST https://your-app-name.up.railway.app/health
```

Should return: `{"status":"ok"}`

## Troubleshooting

| Problem | Solution |
|---------|----------|
| 401 Unauthorized | Check `CRON_SECRET` header matches Railway variable |
| 404 on endpoints | Ensure bot is deployed (check Railway dashboard) |
| Bot not responding | Set `GROUP_CHAT_ID` in Railway variables |
| No database | SQLite works, but Railway's filesystem resets on redeploy. Consider PostgreSQL add-on for production |

## Full Documentation

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed guide.

## Need Help?

- [Railway Docs](https://docs.railway.app)
- [EasyCron FAQ](https://www.easycron.com/page/faq)
- [Telegram Bot API](https://core.telegram.org/bots)
