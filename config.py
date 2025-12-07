import os
from dotenv import load_dotenv
import sys

load_dotenv()

class Config:
    """Configuration Class v15.0.00"""
    
    # 🔐 ESSENTIAL CREDENTIALS
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", 0))
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")
    OWNER_USERNAME = os.getenv("OWNER_USERNAME", "")
    NAGOD_NUMBER = os.getenv("NAGOD_NUMBER", "018XXXXXXX")
    BIKASH_NUMBER = os.getenv("BIKASH_NUMBER", "018XXXXXXX")
    
    # 🤖 BOT INFORMATION
    BOT_NAME = "🔥 MARPd Ultra Pro Max"
    VERSION = "v15.0.00"
    CURRENCY = "৳"
    COIN_EMOJI = "🪙"
    
    # 🎁 BONUS SETTINGS
    WELCOME_BONUS = 500
    DAILY_BONUS = 100
    REFERRAL_BONUS = 300
    LEVEL_UP_BONUS = 50
    
    # ⚙️ SYSTEM SETTINGS
    MAX_COINS = 999999999
    MIN_DEPOSIT = 10
    MIN_WITHDRAW = 50
    MAX_WITHDRAW_DAILY = 10000
    
    # 🛡️ SECURITY
    ADMINS = [BOT_OWNER_ID]
    SUPPORT_GROUP = "@marpd_support"
    
    # 📊 GAME SETTINGS
    MIN_DICE_BET = 10
    MIN_SLOT_BET = 20
    QUIZ_REWARD = 50
    
    @staticmethod
    def validate():
        """Validate all required credentials"""
        missing = []
        
        if not Config.BOT_TOKEN or "your_bot_token" in Config.BOT_TOKEN:
            missing.append("BOT_TOKEN")
        
        if Config.BOT_OWNER_ID == 0:
            missing.append("BOT_OWNER_ID")
            
        if missing:
            print(f"\n❌ Missing or invalid credentials: {', '.join(missing)}")
            print("⚠️ Please edit .env file with your credentials!")
            return False
            
        return True
    
    @staticmethod
    def show_banner():
        """Show beautiful banner"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        banner = f"""
\033[1;35m╔══════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              🤖 MARPd ULTRA PRO MAX BOT 🤖                     ║
║                     Version: {Config.VERSION}                        ║
║                                                                      ║
║         Owner: @{Config.OWNER_USERNAME}                              ║
║         Bot: @{Config.BOT_USERNAME}                                  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════╝\033[0m
        
\033[1;36m✓ Config Loaded Successfully!
💰 Currency: {Config.CURRENCY}
📱 Payment: Nagod({Config.NAGOD_NUMBER}), Bikash({Config.BIKASH_NUMBER})
\033[0m"""
        print(banner)