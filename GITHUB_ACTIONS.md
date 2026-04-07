# GitHub Actions Setup Guide

Use GitHub Actions to automatically trigger your bot's cron jobs. No external services needed!

## Why GitHub Actions?

**Built-in** - No sign-ups or external services
**Free** - Includes thousands of free minutes per month
**Reliable** - GitHub manages infrastructure
**Easy** - Simple secret management
**Visible** - See all runs in your Actions tab  

## Setup (2 minutes)

### Step 1: Add GitHub Repository Secrets

1. Go to your GitHub repository
2. Click **Settings** (top right)
3. Left sidebar → **Secrets and variables** → **Actions**
4. Click **New repository secret**

### Step 2: Add RAILWAY_URL Secret

1. **Secret name:** `RAILWAY_URL`
2. **Secret value:** Your Railway app URL (e.g., `https://connector-bot-prod.up.railway.app`)
3. Click **Add secret**

### Step 3: Add CRON_SECRET Secret

1. Click **New repository secret** again
2. **Secret name:** `CRON_SECRET`
3. **Secret value:** Your CRON_SECRET from Railway variables
4. Click **Add secret**

### Step 4: Done!

The main workflow is already in your repo at:
- `.github/workflows/cron-jobs.yml` - Runs Mondays at 19:00 UTC

**Note:** You can delete `.github/workflows/daily-polling.yml` since registrations now happen on-demand (users send `/start` to the bot anytime).

## What Runs When

### Monday 19:00 UTC - Ask for Calls
```
ask-for-calls
├─ POST /cron/ask
└─ Bot checks: Last Monday? YES → Ask group (with /start registration reminder)
```

### Monday 19:10 UTC - Pair & Notify (10 min after ask)
```
pair-and-notify  
├─ Wait 10 minutes
├─ POST /cron/pair
└─ Bot pairs users & notifies callers
```

**Registration:** Users can register anytime by sending `/start` directly to the bot in a private chat.

## Customize Timing

The workflow uses cron expressions. Edit it to change timing:

**Edit `.github/workflows/cron-jobs.yml`:**
```yaml
on:
  schedule:
    - cron: '0 19 * * 1'  # Monday 19:00 UTC
```

### Cron Expression Format
```
* * * * *
│ │ │ │ └─ Day of week (0=Sunday, 1=Monday, ..., 6=Saturday)
│ │ │ └─── Month (1-12)
│ │ └───── Day of month (1-31)
│ └─────── Hour (0-23, UTC)
└───────── Minute (0-59)

Examples:
0 19 * * 1    = Monday at 19:00 UTC
30 14 * * 0   = Sunday at 14:30 UTC
0 0 15 * *    = 15th of month at 00:00 UTC
```

## Monitor Runs

### View Execution History

1. Go to your GitHub repo
2. Click **Actions** tab
3. Workflow is:
   - "Connector Bot Cron Jobs" (Monday runs)

### Check a Specific Run

1. Click on "Connector Bot Cron Jobs"
2. See all past runs with status (pass or fail)
3. Click a run to see detailed logs
4. With failures, includes curl output and error messages

### Example Successful Run

```
ask-for-calls      - Posted /cron/ask (Monday 19:00 UTC)
pair-and-notify    - Waited 10 min, posted /cron/pair (Monday 19:10 UTC)
```

### Troubleshooting a Failed Run

Click red (failed) run to see logs. Common issues:

**401 Unauthorized**
- Check `CRON_SECRET` matches Railway variable
- Go to Settings → Secrets to verify

**Connection timed out**
- Railway app might be asleep (check Railway dashboard)
- RAILWAY_URL might be wrong (check Settings → Secrets)

**HTTP 500 from bot**
- Check Railway deployment logs
- Might be a bot code issue

## Test Manually

Want to test immediately without waiting for Monday?

**Option 1: Run anytime (with TEST_MODE)**

1. Go to Railway dashboard → Variables
2. Add: `TEST_MODE = true` (this bypasses the Monday date check)
3. Go to GitHub Actions tab
4. Click "Connector Bot Cron Jobs"
5. Click "Run workflow" dropdown → "Run workflow"
6. Workflow runs immediately and executes the full cycle
7. When done testing, set `TEST_MODE = false` in Railway

**Option 2: Run workflow without changes**

1. Go to Actions tab
2. Click "Connector Bot Cron Jobs"
3. Click "Run workflow" dropdown
4. Select branch (main)
5. Click "Run workflow"
6. If it's not Monday, workflow will skip (as expected)

### What TEST_MODE Does

When `TEST_MODE = true`:
- Runs the job regardless of the day/date
- Bypasses the "last Monday" check
- Allows multiple runs in the same month (for testing)
- Useful for development and testing before production

**Remember:** Set `TEST_MODE = false` after testing!

## Troubleshooting

### Secrets not being read

Make sure secret is added to:
- Settings → Secrets and variables → **Actions** (not "Dependabot")

### Workflow not running on schedule

GitHub Actions schedules run on UTC, not your timezone. Check:
- You're using UTC time in cron expression
- Your repo isn't archived or disabled

### Logs show 404 Not Found

- `RAILWAY_URL` is wrong (missing domain or https://)
- App not deployed to Railway
- Add `https://` prefix to URL

### Logs show nothing at all

- Secrets might not be properly passed
- Verify secrets exist in Settings → Secrets
- Try a manual workflow run to see logs

## Advanced: Custom Webhooks

Want to run on a different schedule or trigger? Edit the workflow:

```yaml
on:
  schedule:
    - cron: '0 */2 * * *'  # Every 2 hours
  workflow_dispatch:        # Manual trigger
  push:                      # On every push
    branches:
      - main
```

## Pricing

GitHub Actions free tier includes:
- **Ubuntu**: 2,000 free minutes/month
- **Windows**: 10,000 free minutes for Windows
- **macOS**: 200 free minutes/month

Your bot uses ~2 minutes per month:
- Every Monday: 1 min (ask) + 10 min wait + 1 min (pair) = ~12 min/month

**Monthly usage**: ~12 minutes / 2,000 free = Free!

## FAQ

**Q: Can I change the time?**
A: Yes! Edit the cron expression in `.github/workflows/cron-jobs.yml`

**Q: Will it run if my computer is off?**
A: Yes! GitHub Actions runs on GitHub's servers, not your computer.

**Q: Can multiple people trigger it?**
A: They're run automatically. Only you (repo owner) can manually trigger.

**Q: What if Railway is down?**
A: Workflow will fail. Check Railway status and logs.

**Q: Can I run more than once per day?**
A: Yes, add multiple `- cron:` lines to the schedule.

**Q: Do I see notifications of failures?**
A: Not by default, but you can add email notifications in workflow settings.

## More Info

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Understanding Cron Syntax](https://crontab.guru/)
- [Railway Deployment Guide](RAILWAY_DEPLOYMENT.md)
