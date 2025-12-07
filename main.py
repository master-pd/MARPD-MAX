#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MARPD ULTRA PRO MAX BOT v15.0.00
Main Entry Point for Termux/CLI
"""

import os
import sys
import time
import threading
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from db import Database
from bot import MARPD_Bot
from scheduler import TaskScheduler
from backup import BackupManager
from notifier import Notifier
from logger import Logger
from error_handler import ErrorHandler

def show_welcome():
    """Show welcome message and setup"""
    print("""
\033[1;35m╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              🎯 MARPd ULTRA PRO MAX BOT 🎯                          ║
║                     Version: v15.0.00                                ║
║                                                                      ║
║         Developed for Termux/Server Environments                    ║
║         Complete Gaming & Payment Bot System                        ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝\033[0m

📋 \033[1;36mFeatures Included:\033[0m
• 🎮 Multiple Games (Dice, Slot, Quiz, etc.)
• 💰 Payment System (Nagod, Bikash, Rocket)
• 🛍️ Shop & Inventory System
• 👑 Advanced Admin Panel
• 🔒 Security & Moderation
• 📊 Analytics & Statistics
• 💾 Auto Backup System
• 🔔 Smart Notifications
• ⏰ Task Scheduler
• 📝 Advanced Logging
• 🚀 And Much More!

""")

def setup_environment():
    """Setup environment and check requirements"""
    print("🔍 Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        sys.exit(1)
    
    # Check required directories
    required_dirs = ['data', 'logs', 'backups', 'cache']
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
    
    # Check .env file
    if not os.path.exists('.env'):
        print("⚠️  .env file not found!")
        print("📝 Creating sample .env file...")
        
        sample_env = """# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_here
BOT_OWNER_ID=your_telegram_id
BOT_USERNAME=your_bot_username
OWNER_USERNAME=your_username

# Payment Numbers
NAGOD_NUMBER=018XXXXXXXX
BIKASH_NUMBER=018XXXXXXXX

# Optional: Firebase/Firestore for cloud database
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_CREDENTIALS=path/to/credentials.json
"""
        
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(sample_env)
        
        print("✅ Sample .env file created!")
        print("📋 Please edit .env file with your credentials")
        sys.exit(0)
    
    print("✅ Environment check completed")

def interactive_setup():
    """Interactive setup for first-time users"""
    print("\n🎯 Interactive Setup\n")
    
    config_data = {}
    
    # Bot Token
    token = input("🤖 Enter your Bot Token (from @BotFather): ").strip()
    if token:
        config_data['BOT_TOKEN'] = token
    
    # Owner ID
    owner_id = input("👑 Enter your Telegram ID (use @userinfobot to find): ").strip()
    if owner_id.isdigit():
        config_data['BOT_OWNER_ID'] = int(owner_id)
    
    # Bot Username
    bot_username = input("💬 Enter your Bot Username (without @): ").strip()
    if bot_username:
        config_data['BOT_USERNAME'] = bot_username
    
    # Owner Username
    owner_username = input("👤 Enter your Telegram Username (without @): ").strip()
    if owner_username:
        config_data['OWNER_USERNAME'] = owner_username
    
    # Payment Numbers
    nagod = input("💳 Enter Nagod Number: ").strip()
    if nagod:
        config_data['NAGOD_NUMBER'] = nagod
    
    bikash = input("📱 Enter Bikash Number: ").strip()
    if bikash:
        config_data['BIKASH_NUMBER'] = bikash
    
    # Save to .env
    if config_data:
        update_env_file(config_data)
        print("\n✅ Configuration saved to .env file!")
        return True
    
    return False

def update_env_file(config_data):
    """Update .env file with new configuration"""
    env_lines = []
    
    # Read existing .env file
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            env_lines = f.readlines()
    
    # Update or add configuration
    new_lines = []
    updated_keys = set()
    
    for line in env_lines:
        if '=' in line:
            key = line.split('=')[0].strip()
            if key in config_data:
                new_lines.append(f"{key}={config_data[key]}\n")
                updated_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Add new keys
    for key, value in config_data.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}\n")
    
    # Write back to .env
    with open('.env', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def show_menu():
    """Show main menu"""
    print("""
\033[1;36m╔══════════════════════════════════════════════════════════════════════╗
║                     MAIN MENU                                               ║
╚══════════════════════════════════════════════════════════════════════╝\033[0m

1. 🚀 Start Bot
2. ⚙️  Configure Settings
3. 💾 Create Backup
4. 🔄 Restore Backup
5. 📊 View Statistics
6. 📝 View Logs
7. 🧹 Cleanup System
8. ❓ Help
9. 🚪 Exit

""")

def run_option(option):
    """Run selected menu option"""
    if option == '1':
        start_bot()
    elif option == '2':
        configure_settings()
    elif option == '3':
        create_backup()
    elif option == '4':
        restore_backup()
    elif option == '5':
        view_statistics()
    elif option == '6':
        view_logs()
    elif option == '7':
        cleanup_system()
    elif option == '8':
        show_help()
    elif option == '9':
        print("👋 Goodbye!")
        sys.exit(0)
    else:
        print("❌ Invalid option!")

def start_bot():
    """Start the Telegram bot"""
    print("\n🚀 Starting MARPD Bot...")
    
    try:
        # Validate configuration
        if not Config.validate():
            print("❌ Please configure your .env file first!")
            return
        
        # Show banner
        Config.show_banner()
        
        # Initialize components
        print("🔄 Initializing components...")
        
        # Database
        db = Database()
        print("✅ Database initialized")
        
        # Logger
        logger = Logger()
        print("✅ Logger initialized")
        
        # Error Handler
        error_handler = ErrorHandler()
        print("✅ Error handler initialized")
        
        # Backup Manager
        backup_manager = BackupManager(db)
        print("✅ Backup manager initialized")
        
        # Notifier
        notifier = Notifier(db)
        print("✅ Notifier initialized")
        
        # Task Scheduler
        scheduler = TaskScheduler(db)
        print("✅ Task scheduler initialized")
        
        # Start background services
        print("🚀 Starting background services...")
        backup_manager.start()
        notifier.start()
        scheduler.start()
        
        # Create and start bot
        print("🤖 Creating bot instance...")
        bot = MARPD_Bot(db)
        
        print("\n✅ All systems ready!")
        print("📱 Bot is now running...")
        print("📝 Logs are being written to 'logs/' directory")
        print("💾 Backups will be created automatically")
        print("\n🛑 Press Ctrl+C to stop the bot")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user")
            print("👋 Goodbye!")
    
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        import traceback
        traceback.print_exc()

def configure_settings():
    """Configure bot settings"""
    print("\n⚙️  Configuration Menu\n")
    
    if interactive_setup():
        print("\n✅ Configuration updated!")
        print("🔄 Please restart the bot for changes to take effect")
    
    input("\nPress Enter to continue...")

def create_backup():
    """Create manual backup"""
    print("\n💾 Creating backup...")
    
    try:
        db = Database()
        backup_manager = BackupManager(db)
        
        result = backup_manager.create_backup(
            backup_name=f"manual_{datetime.now().strftime('%Y%m%d_%H%M')}",
            backup_type='full'
        )
        
        if result['success']:
            backup = result['backup']
            print(f"✅ Backup created: {backup['name']}")
            print(f"📁 Size: {backup_manager._format_size(backup['size'])}")
            print(f"⏱️  Time: {backup['duration']:.2f}s")
        else:
            print(f"❌ Backup failed: {result['message']}")
    
    except Exception as e:
        print(f"❌ Backup error: {e}")
    
    input("\nPress Enter to continue...")

def restore_backup():
    """Restore from backup"""
    print("\n🔄 Restore Backup\n")
    
    try:
        db = Database()
        backup_manager = BackupManager(db)
        
        # List available backups
        backups = backup_manager.list_backups()
        
        if not backups:
            print("❌ No backups found!")
            input("\nPress Enter to continue...")
            return
        
        print("Available backups:")
        for i, backup in enumerate(backups[:10], 1):
            timestamp = datetime.fromisoformat(backup['timestamp']).strftime('%d/%m/%Y %H:%M')
            size = backup_manager._format_size(backup.get('size', 0))
            print(f"{i}. {backup['name']} - {timestamp} ({size})")
        
        choice = input("\nSelect backup number to restore (0 to cancel): ").strip()
        
        if choice == '0':
            return
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(backups):
                backup = backups[index]
                
                print(f"\n⚠️  WARNING: This will overwrite current data!")
                confirm = input(f"Restore backup '{backup['name']}'? (yes/no): ").strip().lower()
                
                if confirm == 'yes':
                    result = backup_manager.restore_backup(backup['id'], 'full')
                    
                    if result['success']:
                        print(f"✅ Backup restored: {backup['name']}")
                    else:
                        print(f"❌ Restore failed: {result['message']}")
                else:
                    print("❌ Restore cancelled")
            else:
                print("❌ Invalid backup number")
        
        except ValueError:
            print("❌ Please enter a valid number")
    
    except Exception as e:
        print(f"❌ Restore error: {e}")
    
    input("\nPress Enter to continue...")

def view_statistics():
    """View bot statistics"""
    print("\n📊 Bot Statistics\n")
    
    try:
        db = Database()
        stats = db.get_stats()
        
        print(f"👥 Total Users: {stats['total_users']:,}")
        print(f"📈 Active Users: {stats['active_users']:,}")
        print(f"💰 Total Coins: {stats['total_coins']:,}")
        print(f"💵 Total Balance: {stats['total_balance']:,}")
        print(f"💳 Total Payments: {stats['total_payments']:,}")
        print(f"🔄 Total Transactions: {stats['total_transactions']:,}")
        print(f"🛍️ Shop Items: {stats['shop_items']:,}")
        
        # Today's stats
        today = stats['today_stats']
        print(f"\n📅 Today's Stats:")
        print(f"• New Users: {today['new_users']:,}")
        print(f"• Deposits: {today['deposits']:,}")
        print(f"• Withdrawals: {today['withdrawals']:,}")
        
        # System info
        if 'last_backup' in stats and stats['last_backup']:
            print(f"\n💾 Last Backup: {stats['last_backup'][:10]}")
        
        print(f"⏰ System Uptime: {stats.get('system_uptime', 'N/A')}")
    
    except Exception as e:
        print(f"❌ Error loading statistics: {e}")
    
    input("\nPress Enter to continue...")

def view_logs():
    """View log files"""
    print("\n📝 Log Files\n")
    
    try:
        logger = Logger()
        log_files = logger.get_log_files()
        
        if not log_files:
            print("❌ No log files found!")
        else:
            print("Available log files:")
            for i, log in enumerate(log_files[:10], 1):
                size_kb = log['size'] / 1024
                print(f"{i}. {log['name']} - {size_kb:.1f} KB - {log['modified'][:10]}")
            
            choice = input("\nView log file (enter number, 0 to cancel): ").strip()
            
            if choice != '0':
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(log_files):
                        log_file = log_files[index]['name']
                        log_path = os.path.join('logs', log_file)
                        
                        if os.path.exists(log_path):
                            print(f"\n📄 Contents of {log_file} (last 50 lines):\n")
                            with open(log_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                for line in lines[-50:]:
                                    print(line.rstrip())
                        else:
                            print(f"❌ Log file not found: {log_file}")
                    else:
                        print("❌ Invalid log file number")
                except ValueError:
                    print("❌ Please enter a valid number")
    
    except Exception as e:
        print(f"❌ Error viewing logs: {e}")
    
    input("\nPress Enter to continue...")

def cleanup_system():
    """Cleanup system files"""
    print("\n🧹 System Cleanup\n")
    
    try:
        # Cleanup old logs
        logger = Logger()
        logs_cleaned = logger.cleanup_old_logs(days_to_keep=7)
        print(f"✅ Cleaned {logs_cleaned} old log files")
        
        # Cleanup old backups
        db = Database()
        backup_manager = BackupManager(db)
        backup_manager._cleanup_old_backups()
        print("✅ Cleaned old backups")
        
        # Cleanup cache
        import shutil
        cache_dir = 'cache'
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            os.makedirs(cache_dir)
            print("✅ Cleared cache directory")
        
        print("\n✅ System cleanup completed!")
    
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
    
    input("\nPress Enter to continue...")

def show_help():
    """Show help information"""
    print("""
\033[1;36m╔══════════════════════════════════════════════════════════════════════╗
║                             HELP & SUPPORT                                 ║
╚══════════════════════════════════════════════════════════════════════╝\033[0m

📖 \033[1;33mBot Commands:\033[0m
• /start - Start the bot
• /help - Show help
• /games - Play games
• /shop - Visit shop
• /profile - View profile
• /daily - Claim daily bonus
• /deposit - Deposit money
• /withdraw - Withdraw money
• /referral - Referral system

🛠️ \033[1;33mAdmin Commands:\033[0m
• /admin - Admin panel
• /stats - Bot statistics
• /broadcast - Send message to users
• /ban - Ban user
• /unban - Unban user
• /addcoins - Add coins to user

📁 \033[1;33mFile Structure:\033[0m
• bot.py - Main bot file
• config.py - Configuration
• db.py - Database
• payments.py - Payment system
• games.py - Games
• shop.py - Shop system
• admin.py - Admin panel
• moderation.py - Moderation
• utils.py - Utilities
• scheduler.py - Task scheduler
• backup.py - Backup system
• logger.py - Logging system
• notifier.py - Notifications
• cache.py - Cache system
• requirements.txt - Python libraries

🔧 \033[1;33mSetup Instructions:\033[0m
1. Install Python 3.8+
2. Install requirements: pip install -r requirements.txt
3. Configure .env file with your credentials
4. Run: python main.py
5. Select option 1 to start bot

📞 \033[1;33mSupport:\033[0m
• Owner: @{}
• Bot: @{}
• Version: v15.0.00

""".format(Config.OWNER_USERNAME, Config.BOT_USERNAME))
    
    input("\nPress Enter to continue...")

def main():
    """Main function"""
    show_welcome()
    setup_environment()
    
    # Check if configuration is valid
    if not Config.validate():
        print("\n⚠️  Configuration incomplete!")
        if input("Run interactive setup? (yes/no): ").strip().lower() == 'yes':
            if interactive_setup():
                print("\n✅ Configuration saved!")
                print("🔄 Please restart the application")
                return
        else:
            print("\n❌ Please configure .env file manually")
            return
    
    # Main menu loop
    while True:
        try:
            show_menu()
            choice = input("Select option (1-9): ").strip()
            os.system('clear' if os.name == 'posix' else 'cls')
            run_option(choice)
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()