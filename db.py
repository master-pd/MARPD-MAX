import json
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import threading
import pickle

class Database:
    """Advanced JSON-based Database with Pickle Support v15.0.00"""
    
    def __init__(self):
        self.data_dir = "data"
        self.backup_dir = "backups"
        self.cache_dir = "cache"
        
        # Create directories
        for directory in [self.data_dir, self.backup_dir, self.cache_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Initialize data
        self.users = self._load_data("users")
        self.payments = self._load_data("payments")
        self.shop = self._load_data("shop", self._default_shop())
        self.games = self._load_data("games")
        self.transactions = self._load_data("transactions")
        self.sessions = self._load_data("sessions")
        self.logs = self._load_data("logs")
        
        # Statistics
        self.stats = self._load_data("stats", self._default_stats())
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        print("✅ Advanced Database v15.0.00 Initialized")
    
    def _load_data(self, name: str, default=None):
        """Load data from pickle or json"""
        pickle_path = os.path.join(self.data_dir, f"{name}.pkl")
        json_path = os.path.join(self.data_dir, f"{name}.json")
        
        try:
            # Try pickle first
            if os.path.exists(pickle_path):
                with open(pickle_path, 'rb') as f:
                    return pickle.load(f)
            # Then JSON
            elif os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading {name}: {e}")
        
        return default if default is not None else {}
    
    def _save_data(self, name: str, data):
        """Save data using pickle"""
        path = os.path.join(self.data_dir, f"{name}.pkl")
        try:
            with open(path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            return True
        except Exception as e:
            print(f"❌ Error saving {name}: {e}")
            return False
    
    def _default_shop(self):
        """Default shop items"""
        return {
            "last_updated": datetime.now().isoformat(),
            "items": [
                {
                    "id": "vip_badge",
                    "name": "VIP Badge",
                    "price": 5000,
                    "description": "এক্সক্লুসিভ VIP স্ট্যাটাস",
                    "icon": "👑",
                    "category": "badge",
                    "rarity": "legendary",
                    "bonus": {"daily_extra": 50, "xp_boost": 20}
                },
                {
                    "id": "color_name",
                    "name": "Color Name",
                    "price": 3000,
                    "description": "চ্যাটে রঙিন নাম",
                    "icon": "🎨",
                    "category": "cosmetic",
                    "rarity": "epic",
                    "duration_days": 30
                },
                {
                    "id": "double_xp_24h",
                    "name": "2x XP (24 ঘন্টা)",
                    "price": 1500,
                    "description": "24 ঘন্টার জন্য 2x এক্সপিরিয়েন্স",
                    "icon": "⚡",
                    "category": "booster",
                    "rarity": "rare",
                    "duration_hours": 24
                },
                {
                    "id": "coin_booster",
                    "name": "কয়েন বুস্টার",
                    "price": 2500,
                    "description": "3 দিনের জন্য 50% অতিরিক্ত কয়েন",
                    "icon": "💰",
                    "category": "booster",
                    "rarity": "epic",
                    "duration_days": 3
                },
                {
                    "id": "lucky_charm",
                    "name": "লাকি চার্ম",
                    "price": 1000,
                    "description": "গেম জেতার সুযোগ 10% বাড়ায়",
                    "icon": "🍀",
                    "category": "charm",
                    "rarity": "rare",
                    "duration_games": 50
                }
            ]
        }
    
    def _default_stats(self):
        """Default statistics"""
        return {
            "total_users": 0,
            "active_users": 0,
            "total_coins": 0,
            "total_transactions": 0,
            "total_games_played": 0,
            "total_deposits": 0,
            "total_withdrawals": 0,
            "daily_stats": {},
            "monthly_stats": {},
            "peak_hours": {}
        }
    
    # =============== USER MANAGEMENT ===============
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data with caching"""
        with self.lock:
            return self.users.get(str(user_id))
    
    def create_user(self, user_id: int, user_info: Dict) -> Dict:
        """Create new user with advanced profile"""
        with self.lock:
            timestamp = datetime.now().isoformat()
            
            user_data = {
                "id": user_id,
                "username": user_info.get("username", ""),
                "first_name": user_info.get("first_name", ""),
                "last_name": user_info.get("last_name", ""),
                "language_code": user_info.get("language_code", "bn"),
                
                # Economy
                "balance": Config.WELCOME_BONUS,
                "coins": Config.WELCOME_BONUS,
                "total_earned": 0,
                "total_spent": 0,
                
                # Level System
                "level": 1,
                "xp": 0,
                "xp_to_next_level": 100,
                "total_xp": 0,
                
                # Activity
                "daily_streak": 0,
                "max_streak": 0,
                "last_daily": None,
                "last_active": timestamp,
                "first_seen": timestamp,
                "total_messages": 0,
                "total_games": 0,
                "games_won": 0,
                
                # Inventory
                "inventory": [],
                "equipped_items": {},
                "achievements": [],
                
                # Settings
                "settings": {
                    "notifications": True,
                    "language": "bn",
                    "private_mode": False,
                    "auto_confirm": False
                },
                
                # Security
                "warnings": 0,
                "warning_history": [],
                "is_banned": False,
                "ban_reason": None,
                "ban_until": None,
                
                # Referral
                "referral_code": f"MARPD{user_id}",
                "referred_by": None,
                "referrals": [],
                "referral_earnings": 0,
                
                # Statistics
                "stats": {
                    "dice_played": 0,
                    "dice_won": 0,
                    "slot_played": 0,
                    "slot_won": 0,
                    "quiz_played": 0,
                    "quiz_correct": 0,
                    "daily_claims": 0,
                    "items_bought": 0
                },
                
                # Premium Features
                "is_vip": False,
                "vip_until": None,
                "premium_features": []
            }
            
            self.users[str(user_id)] = user_data
            self._save_data("users", self.users)
            
            # Update global stats
            self.stats["total_users"] = len(self.users)
            self._save_data("stats", self.stats)
            
            return user_data
    
    def update_user(self, user_id: int, updates: Dict) -> bool:
        """Update user data with timestamp"""
        with self.lock:
            user_id_str = str(user_id)
            if user_id_str in self.users:
                # Add timestamp
                updates["last_active"] = datetime.now().isoformat()
                
                # Update user
                self.users[user_id_str].update(updates)
                self._save_data("users", self.users)
                return True
            return False
    
    def get_all_users(self, active_only: bool = False) -> List[Dict]:
        """Get all users"""
        users = list(self.users.values())
        
        if active_only:
            cutoff = datetime.now() - timedelta(days=7)
            users = [u for u in users 
                    if datetime.fromisoformat(u.get("last_active", "2000-01-01")) > cutoff]
        
        return users
    
    # =============== PAYMENTS ===============
    
    def add_payment(self, payment_data: Dict) -> str:
        """Add payment record"""
        with self.lock:
            payment_id = f"pay_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            payment_data.update({
                "id": payment_id,
                "created_at": datetime.now().isoformat(),
                "status": "PENDING",
                "confirmed_by": None,
                "confirmed_at": None,
                "notes": ""
            })
            
            self.payments[payment_id] = payment_data
            self._save_data("payments", self.payments)
            
            # Add to transactions
            transaction_id = f"tx_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.transactions[transaction_id] = {
                "id": transaction_id,
                "user_id": payment_data.get("user_id"),
                "type": payment_data.get("type", "UNKNOWN"),
                "amount": payment_data.get("amount", 0),
                "status": "PENDING",
                "timestamp": datetime.now().isoformat(),
                "reference": payment_id
            }
            self._save_data("transactions", self.transactions)
            
            return payment_id
    
    def get_user_payments(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's payment history"""
        user_payments = []
        for payment in self.payments.values():
            if payment.get("user_id") == user_id:
                user_payments.append(payment)
        
        # Sort by date (newest first)
        user_payments.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return user_payments[:limit]
    
    # =============== SHOP ===============
    
    def get_shop_items(self, category: str = None) -> List[Dict]:
        """Get shop items with optional category filter"""
        items = self.shop.get("items", [])
        
        if category:
            items = [item for item in items if item.get("category") == category]
        
        return items
    
    def get_item(self, item_id: str) -> Optional[Dict]:
        """Get item by ID"""
        for item in self.shop.get("items", []):
            if item.get("id") == item_id:
                return item
        return None
    
    # =============== GAMES ===============
    
    def update_game_stats(self, user_id: int, game_type: str, result: Dict):
        """Update game statistics"""
        with self.lock:
            # Update user game stats
            user = self.get_user(user_id)
            if user:
                if f"{game_type}_played" in user["stats"]:
                    user["stats"][f"{game_type}_played"] += 1
                
                if result.get("won") and f"{game_type}_won" in user["stats"]:
                    user["stats"][f"{game_type}_won"] += 1
                
                self.update_user(user_id, {"stats": user["stats"]})
            
            # Update global game stats
            game_key = f"{game_type}_{datetime.now().strftime('%Y%m%d')}"
            if game_key not in self.games:
                self.games[game_key] = {
                    "plays": 0,
                    "wins": 0,
                    "total_bet": 0,
                    "total_payout": 0
                }
            
            self.games[game_key]["plays"] += 1
            if result.get("won"):
                self.games[game_key]["wins"] += 1
            
            if "bet" in result:
                self.games[game_key]["total_bet"] += result["bet"]
            if "payout" in result:
                self.games[game_key]["total_payout"] += result["payout"]
            
            self._save_data("games", self.games)
    
    # =============== BACKUP ===============
    
    def create_backup(self, backup_name: str = None) -> str:
        """Create database backup"""
        with self.lock:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            os.makedirs(backup_path, exist_ok=True)
            
            # Save all data
            data_to_backup = {
                "users": self.users,
                "payments": self.payments,
                "shop": self.shop,
                "games": self.games,
                "transactions": self.transactions,
                "stats": self.stats
            }
            
            backup_file = os.path.join(backup_path, "data.pkl")
            with open(backup_file, 'wb') as f:
                pickle.dump(data_to_backup, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Create info file
            info = {
                "name": backup_name,
                "timestamp": datetime.now().isoformat(),
                "version": "15.0.00",
                "data_stats": {
                    "users": len(self.users),
                    "payments": len(self.payments),
                    "transactions": len(self.transactions)
                }
            }
            
            info_file = os.path.join(backup_path, "info.json")
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)
            
            # Create zip archive
            zip_file = f"{backup_path}.zip"
            shutil.make_archive(backup_path, 'zip', backup_path)
            
            # Remove temp directory
            shutil.rmtree(backup_path)
            
            return zip_file
    
    def restore_backup(self, backup_file: str) -> bool:
        """Restore from backup"""
        try:
            # Extract backup
            temp_dir = os.path.join(self.backup_dir, "temp_restore")
            shutil.unpack_archive(backup_file, temp_dir)
            
            # Load backup data
            data_file = os.path.join(temp_dir, "data.pkl")
            with open(data_file, 'rb') as f:
                backup_data = pickle.load(f)
            
            # Restore data
            self.users = backup_data.get("users", {})
            self.payments = backup_data.get("payments", {})
            self.shop = backup_data.get("shop", self._default_shop())
            self.games = backup_data.get("games", {})
            self.transactions = backup_data.get("transactions", {})
            self.stats = backup_data.get("stats", self._default_stats())
            
            # Save restored data
            self._save_data("users", self.users)
            self._save_data("payments", self.payments)
            self._save_data("shop", self.shop)
            self._save_data("games", self.games)
            self._save_data("transactions", self.transactions)
            self._save_data("stats", self.stats)
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            return True
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    # =============== STATISTICS ===============
    
    def get_stats(self) -> Dict:
        """Get comprehensive bot statistics"""
        with self.lock:
            # Calculate active users (active in last 7 days)
            cutoff = datetime.now() - timedelta(days=7)
            active_users = 0
            total_coins = 0
            total_balance = 0
            
            for user in self.users.values():
                last_active = datetime.fromisoformat(user.get("last_active", "2000-01-01"))
                if last_active > cutoff:
                    active_users += 1
                
                total_coins += user.get("coins", 0)
                total_balance += user.get("balance", 0)
            
            # Calculate today's stats
            today = datetime.now().strftime("%Y-%m-%d")
            today_stats = {
                "new_users": 0,
                "deposits": 0,
                "withdrawals": 0,
                "games_played": 0
            }
            
            # Get today's date in proper format for comparison
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            for user in self.users.values():
                joined = datetime.fromisoformat(user.get("first_seen", "2000-01-01"))
                if joined > today_start:
                    today_stats["new_users"] += 1
            
            for payment in self.payments.values():
                created = datetime.fromisoformat(payment.get("created_at", "2000-01-01"))
                if created > today_start and payment.get("type") == "DEPOSIT":
                    today_stats["deposits"] += 1
                elif created > today_start and payment.get("type") == "WITHDRAW":
                    today_stats["withdrawals"] += 1
            
            return {
                "total_users": len(self.users),
                "active_users": active_users,
                "total_coins": total_coins,
                "total_balance": total_balance,
                "total_payments": len(self.payments),
                "total_transactions": len(self.transactions),
                "today_stats": today_stats,
                "shop_items": len(self.shop.get("items", [])),
                "last_backup": self.stats.get("last_backup"),
                "system_uptime": datetime.now().isoformat()
            }
    
    def add_log(self, log_type: str, message: str, user_id: int = None, data: Dict = None):
        """Add system log"""
        with self.lock:
            log_id = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            log_entry = {
                "id": log_id,
                "type": log_type,
                "message": message,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "data": data or {}
            }
            
            self.logs[log_id] = log_entry
            self._save_data("logs", self.logs)
            
            # Keep only last 1000 logs
            if len(self.logs) > 1000:
                # Sort by timestamp and remove oldest
                sorted_logs = sorted(self.logs.items(), 
                                   key=lambda x: x[1].get("timestamp", ""))
                for i in range(len(sorted_logs) - 1000):
                    del self.logs[sorted_logs[i][0]]
                self._save_data("logs", self.logs)