# 🔐 Security Guide: Storing Secrets

Your bot handles sensitive information:
- `BOT_TOKEN` - Grants control over your bot
- `CRON_SECRET` - Protects your cron endpoints
- `GROUP_CHAT_ID` - (less sensitive, but still private)

This guide explains secure ways to store these.

## 🚀 Quick Answer

**Railway users:** Use Railway's built-in secret management (lock icon 🔒)

**Everyone:** Never commit secrets to Git. Use `.env` files locally.

---

## Option 1: Railway's Secret Management ⭐ Recommended

Best for production on Railway.

### How to Use

1. **Dashboard:** Go to Railway → Your Project
2. **Variables Tab:** Click Variables
3. **For each sensitive variable:**
   - Enter the value
   - Click the **lock icon 🔒** next to it
   - Save

### What This Does

✅ Encrypts at rest (secure storage)
✅ Encrypts in transit (safe during deployment)
✅ Hidden from logs (won't appear in output)
✅ Restricted viewing (can limit team access)
✅ Auto-injected into environment

### Example Setup

```
BOT_TOKEN     [•••••••••••] 🔒 <- Encrypted
CRON_SECRET   [•••••••••••] 🔒 <- Encrypted
GROUP_CHAT_ID [123456789]       <- Not sensitive, no lock needed
TIMEZONE      [Europe/Berlin]   <- Not sensitive
```

### Generate Secure `CRON_SECRET`

```bash
# Using Python (cross-platform)
python3 -c "import secrets; print(secrets.token_hex(32))"

# Using OpenSSL
openssl rand -hex 32

# Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

Output example:
```
a7f3b8c2e9d4f1a6c3e8b2d7f4a9c1e6a2d5f8c1e4b7a9d2f5c8e1a4b7d0c3e6
```

Use that as your `CRON_SECRET`.

---

## Option 2: Local `.env` Files

Best for local development.

### Setup

1. Create `.env` in your project root:
```bash
cd /Users/lucaspari/Projects/Connector_Bot
echo "BOT_TOKEN=your-real-token-here" > .env
echo "CRON_SECRET=your-secure-secret" >> .env
echo "GROUP_CHAT_ID=123456789" >> .env
```

2. It's already in `.gitignore` ✅
```bash
cat .gitignore | grep "\.env"
# Output: .env
```

3. **Never add real tokens to example files:**
```bash
# This is OK:
echo "BOT_TOKEN=" > .env.example
echo "CRON_SECRET=" >> .env.example

# This is BAD (don't do this):
echo "BOT_TOKEN=abc123..." > .env.example
```

### Using in Python

Already works! Your code uses `os.getenv()`:

```python
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CRON_SECRET = os.getenv("CRON_SECRET", "your-secret")
```

With `python-dotenv` for auto-loading:

```bash
pip install python-dotenv
```

Then in your code:
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env automatically
BOT_TOKEN = os.getenv("BOT_TOKEN")
```

---

## Option 3: Git-Crypt (Encrypted Git Storage)

For encrypting secrets directly in your Git repository.

### Installation

```bash
# macOS
brew install git-crypt

# Linux
sudo apt-get install git-crypt

# Windows (WSL or Git Bash)
sudo apt-get install git-crypt
```

### Setup

```bash
cd /Users/lucaspari/Projects/Connector_Bot

# Initialize encryption in this repo
git-crypt init

# Create .gitattributes to specify what to encrypt
echo ".env filter=git-crypt diff=git-crypt" >> .gitattributes
echo ".env.local filter=git-crypt diff=git-crypt" >> .gitattributes

# Add your GPG key (one-time)
git-crypt add-gpg-user YOUR_GPG_EMAIL@example.com

# Commit
git add .gitattributes .env
git commit -m "Add encrypted secrets"
```

### How It Works

- `.env` is encrypted when pushed to Git
- Only people with the GPG key can decrypt
- When you pull, it auto-decrypts locally
- Commands: `git-crypt lock/unlock`

### Pros & Cons

**Pros:**
- Secrets stay in repo with code
- Automatically encrypted/decrypted
- No external services needed

**Cons:**
- Requires GPG key setup
- More complex for teams
- Overhead for hobby projects

---

## Option 4: External Secret Managers

For serious production use.

### AWS Secrets Manager
```python
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='connector-bot/tokens')
BOT_TOKEN = secret['SecretString']
```

### HashiCorp Vault
```python
from hvac import Client

client = Client(url='https://vault.example.com')
secret = client.secrets.kv.read_secret_version(path='connector-bot')
BOT_TOKEN = secret['data']['data']['BOT_TOKEN']
```

### When to Use
- 🏢 Enterprise/production
- 👥 Large teams
- 🔄 Multiple environments
- 🔍 Audit logging needed

For a hobby bot on Railway: **Don't use this.** Overkill.

---

## 🎯 Recommendation by Scenario

### Scenario 1: Railway Deployment ⭐
```
Use: Railway Secrets + .env locally
Process:
├─ Locally: Store in .env (in .gitignore)
├─ GitHub: Never commit real secrets
├─ Railway: Mark BOT_TOKEN & CRON_SECRET as secrets
└─ Deploy: Railway injects encrypted secrets
```

### Scenario 2: Self-Hosted Server
```
Use: Environment variables + .env file
Process:
├─ Create /opt/connector-bot/.env
├─ Set environment: export BOT_TOKEN=$(cat .env | grep BOT_TOKEN)
├─ Or use systemd with EnvironmentFile=
└─ Deploy: systemctl restart bot
```

### Scenario 3: Docker Containerized
```
Use: Docker secrets + environment files
Process:
├─ Create secrets: echo "token" | docker secret create bot_token -
├─ Or use docker-compose.yml secrets section
├─ Or pass at runtime: docker run -e BOT_TOKEN=xxx
└─ Deploy: Container auto-injects
```

### Scenario 4: Hobby Project (Your Case)
```
✅ DO:
   ├─ Use Railway secrets (lock icon)
   ├─ Use .env locally (in .gitignore)
   ├─ Generate strong CRON_SECRET
   └─ Never commit .env to Git

❌ DON'T:
   ├─ Put tokens in code
   ├─ Commit .env file
   ├─ Use same secret everywhere
   └─ Share secrets in messages/Slack
```

---

## 🔧 Checklist: Did You Secure Your Bot?

- [ ] `BOT_TOKEN` marked as secret in Railway (lock icon 🔒)
- [ ] `CRON_SECRET` marked as secret in Railway (lock icon 🔒)
- [ ] `.env` file in `.gitignore` (not committed to Git)
- [ ] Never tested with real tokens in code examples
- [ ] Different `CRON_SECRET` from default/example
- [ ] Generated `CRON_SECRET` is 32+ characters long
- [ ] Only you know the actual `CRON_SECRET` value
- [ ] Verified `.env.example` has NO real values

---

## 🚨 If You Accidentally Exposed Your Token

### Immediate Actions

**If token leaked to public repo:**
```
1. Go to @BotFather on Telegram
2. Send /mybots
3. Select your bot
4. Edit Bot
5. Edit tokens
6. Revoke old token
7. Get new token
```

**If token shared in messages/logs:**
```
1. Same as above - revoke immediately
2. Update Railway variables
3. Update EasyCron cron jobs
4. Test that bot still works
```

### Prevention

- Add to `.gitignore`:
```
.env
.env.local
.env.*.local
secrets/
*.key
*.pem
```

- Git pre-commit hook:
```bash
#!/bin/bash
# .git/hooks/pre-commit
if grep -r "AAHB2ZnT\|8790558518" . --exclude-dir=.git; then
  echo "ERROR: Possible bot token in staged files!"
  exit 1
fi
```

---

## Useful Commands

```bash
# Generate secure random secret
python3 -c "import secrets; print(secrets.token_hex(32))"

# Check what secrets are in current directory
grep -r "Bearer\|token=\|secret=" . --exclude-dir=.git

# Test Railway health endpoint
curl https://your-app.up.railway.app/health

# Check if .env is in .gitignore
cat .gitignore | grep ".env"

# Verify .env not in Git
git log --all --full-history -- ".env"
```

---

## Summary

| Method | Local | Railway | Difficulty | Cost |
|--------|-------|---------|-----------|------|
| `.env` + Railway Secrets | ✅ | ✅ | Easy | Free |
| Git-Crypt | ✅ | ✅ | Medium | Free |
| Docker Secrets | ✅ | ❌ | Medium | Free |
| AWS Secrets Manager | ❌ | ✅ | Hard | $0.40/month |
| Vault | ✅ | ✅ | Hard | Self-hosted |

**👉 For you:** Use `.env` locally + Railway Secrets (lock icon). Done!

---

## Resources

- [Railway Secrets Documentation](https://docs.railway.app/guides/variables)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Git-crypt Documentation](https://github.com/AGWA/git-crypt)
- [Python-dotenv](https://github.com/theskumar/python-dotenv)
