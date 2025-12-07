#!/bin/bash
# Quick Start Script for MARPD Bot

echo -e "\033[1;35m"
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                      ║"
echo "║              🚀 MARPd ULTRA PRO MAX BOT 🚀                          ║"
echo "║                     Quick Start Script                               ║"
echo "║                     Version: v15.0.00                                ║"
echo "║                                                                      ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo -e "\033[0m"

# Check if in correct directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found!"
    echo "📁 Please run this script from the bot directory"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 not found!"
    echo "📦 Please install Python 3.8 or higher"
    exit 1
fi

# Check requirements
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found!"
    exit 1
fi

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚠️ Warning: .env file not found!"
    echo "📝 Creating sample .env file..."
    cat > .env << 'EOL'
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
BOT_OWNER_ID=your_telegram_id
BOT_USERNAME=your_bot_username
OWNER_USERNAME=your_username

# Payment Numbers
NAGOD_NUMBER=018XXXXXXXX
BIKASH_NUMBER=018XXXXXXXX

# Optional Settings
LOG_LEVEL=INFO
BACKUP_TIME=03:00
MAX_BACKUPS=30
EOL
    echo "✅ Sample .env file created!"
    echo "📋 Please edit .env file with your credentials first"
    exit 1
fi

# Install/update requirements
echo -e "\n📦 Checking dependencies..."
pip3 install -r requirements.txt --upgrade

# Create necessary directories
echo -e "\n📁 Creating directories..."
mkdir -p data logs backups cache

# Clear screen
clear

# Start the bot
echo -e "\n🚀 Starting MARPD Bot v15.0.00...\n"
python3 main.py