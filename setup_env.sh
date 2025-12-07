#!/data/data/com.termux/files/usr/bin/bash

echo "⚙️ Setting up MARPd .env file..."
echo "================================="

cd ~/MARPD-MAX

# Create .env if doesn't exist
if [ ! -f ".env" ]; then
    echo "📄 Creating .env file..."
    cat > .env << 'EOF'
# MARPd Configuration
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
BOT_OWNER_ID=YOUR_TELEGRAM_ID
BOT_USERNAME=your_bot_username
OWNER_USERNAME=your_username
NAGOD_NUMBER=018XXXXXXXX
BIKASH_NUMBER=018XXXXXXXX
WELCOME_BONUS=500
DAILY_BONUS=100
LOG_LEVEL=INFO
EOF
    echo "✅ .env file created!"
else
    echo "📁 .env file already exists"
fi

# Instructions
echo ""
echo "📝 INSTRUCTIONS:"
echo "1. Edit .env file: nano .env"
echo "2. Replace YOUR_BOT_TOKEN_HERE with your actual bot token"
echo "3. Replace YOUR_TELEGRAM_ID with your Telegram ID"
echo "4. Replace payment numbers with your numbers"
echo ""
echo "🔑 How to get Bot Token:"
echo "   - Open Telegram"
echo "   - Search @BotFather"
echo "   - Send /newbot"
echo "   - Follow instructions"
echo "   - Copy the token"
echo ""
echo "🆔 How to get Telegram ID:"
echo "   - Open Telegram"
echo "   - Search @userinfobot"
echo "   - Send /start"
echo "   - It will show your ID"
