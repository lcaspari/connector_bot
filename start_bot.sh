#!/bin/bash
# Startup script for Connector Bot

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🎤 Monthly Call Connector Bot Startup 🎤"
echo "======================================="
echo ""

# Check if token is set
if grep -q 'BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"' main.py; then
    echo -e "${RED}❌ Error: Bot token not configured!${NC}"
    echo ""
    echo "Please do the following:"
    echo "1. Get a bot token from @BotFather on Telegram"
    echo "2. Edit main.py and replace:"
    echo "   BOT_TOKEN = \"YOUR_BOT_TOKEN_HERE\""
    echo "   with your actual token"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to activate virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Run the bot
echo -e "${GREEN}🚀 Starting bot...${NC}"
echo "Press Ctrl+C to stop"
echo ""

python main.py

deactivate
