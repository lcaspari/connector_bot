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
CALL_DAY=1
CALL_HOUR=19
CALL_MINUTE=0
TIMEZONE=Europe/Berlin
POLLING_DURATION=60
GROUP_CHAT_ID=<leave-blank-for-now>
```

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

### 5. Set Up Cron Jobs

Go to [easycron.com](https://www.easycron.com):

**Cron 1 - Ask (1st of month at 19:00)**
```
URL: https://your-app-name.up.railway.app/cron/ask
Schedule: 0 19 1 * *
Method: POST
Header: Authorization: Bearer <your-CRON_SECRET-from-Railway>
```

**Cron 2 - Pair (1st at 19:10)**
```
URL: https://your-app-name.up.railway.app/cron/pair
Schedule: 10 19 1 * *
Method: POST
Header: Authorization: Bearer <your-CRON_SECRET-from-Railway>
```

**Cron 3 - Polling (Daily at 10:00)**
```
URL: https://your-app-name.up.railway.app/polling/start?duration_minutes=60
Schedule: 0 10 * * *
Method: POST
Header: Authorization: Bearer <your-CRON_SECRET-from-Railway>
```

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
