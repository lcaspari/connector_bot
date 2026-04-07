## Telegram Webhook Setup

This bot now uses **webhooks** instead of polling. This is more efficient and avoids the Python 3.13 threading issues.

### How It Works

1. **Your Flask app runs on Railway** - Listens for HTTP requests
2. **Telegram sends updates via webhook** - POSTs to `https://your-app.railway.app/telegram`
3. **Bot processes updates immediately** - No polling loop needed

### Setup Steps

#### 1. Get Your Railway App URL

Go to your Railway dashboard:
- Click on your "Connector_Bot" deployment
- Look for the **Public URL** (something like `https://connector-bot-abcd1234.railway.app`)
- This is your `WEBHOOK_URL`

#### 2. Set Environment Variables in Railway

In the Railway dashboard, go to **Variables** and set:

```
WEBHOOK_URL = https://connector-bot-abcd1234.railway.app/telegram
```

(Replace with your actual Railway URL from step 1)

#### 3. Register Webhook with Telegram

Run this command in your terminal (replace `YOUR_BOT_TOKEN` and `YOUR_WEBHOOK_URL`):

```bash
curl -X POST https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook \
  -d "url=YOUR_WEBHOOK_URL"
```

**Example:**
```bash
curl -X POST https://api.telegram.org/bot1234567890:ABCdefGHIjklMNOpqrsTUVwxyz/setWebhook \
  -d "url=https://connector-bot-abcd1234.railway.app/telegram"
```

#### 4. Verify Webhook

Check if webhook is active:

```bash
curl https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo
```

You should see:
```json
{
  "ok": true,
  "result": {
    "url": "https://your-app.railway.app/telegram",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

### Testing

1. **Deploy your code:**
   ```bash
   git push origin main
   ```

2. **Send `/start` to your bot in Telegram**
   - Message your bot in a private chat
   - You should get the registration prompt
   - If it works, the webhook setup is correct!

3. **Check logs in Railway:**
   - Go to Railway dashboard
   - Click "Logs" tab
   - You should see: `Received telegram update <ID>`

### Troubleshooting

**Webhook not receiving updates:**
- Check `WEBHOOK_URL` env var is set correctly
- Run the verification command above
- Make sure Railway app is running (check health endpoint: `https://your-app.railway.app/health`)

**Update processes but no response:**
- Check bot logs for errors
- Make sure `BOT_TOKEN` is set and valid

**To reset webhook:**
```bash
curl -X POST https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook \
  -d "url="
```

This removes the webhook and falls back to polling (not recommended).

### Benefits of Webhooks

**No background polling loops** - More efficient
**No threading issues** - Avoids Python 3.13 __slots__ problems
**Immediate updates** - Telegram sends updates directly
**Production standard** - Best practice for Telegram bots
**Lower resource usage** - No polling means less CPU/bandwidth  

### Cron Jobs Still Work

GitHub Actions cron jobs still work the same:
- Monday 19:00 UTC: `GET /cron/ask?secret=YOUR_CRON_SECRET`
- Monday 19:10 UTC: `GET /cron/pair?secret=YOUR_CRON_SECRET`

No changes needed there!
