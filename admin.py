import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
from config import Config
from db import Database
from utils import Utils

class AdminManager:
    """Advanced Admin Management System v15.0.00"""
    
    def __init__(self, db: Database):
        self.db = db
        self.config = Config()
        self.admin_actions = {}
        self.admin_logs = []
        
        # Admin permissions
        self.permissions = {
            "super_admin": {
                "name": "Super Admin",
                "level": 100,
                "permissions": [
                    "manage_admins", "manage_users", "manage_payments",
                    "manage_shop", "manage_games", "broadcast",
                    "view_logs", "backup_restore", "system_settings",
                    "financial_reports", "ban_users", "give_coins"
                ]
            },
            "admin": {
                "name": "Admin",
                "level": 50,
                "permissions": [
                    "manage_users", "manage_payments", "broadcast",
                    "view_logs", "ban_users", "give_coins"
                ]
            },
            "moderator": {
                "name": "Moderator",
                "level": 20,
                "permissions": [
                    "manage_users", "view_logs", "ban_users"
                ]
            },
            "support": {
                "name": "Support",
                "level": 10,
                "permissions": [
                    "view_logs", "manage_payments"
                ]
            }
        }
        
        # Load admin data
        self.admins = self._load_admins()
    
    def _load_admins(self) -> Dict:
        """Load admin data"""
        admin_file = os.path.join(self.db.data_dir, "admins.json")
        if os.path.exists(admin_file):
            try:
                with open(admin_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Default admins (owner)
        default_admins = {
            str(self.config.BOT_OWNER_ID): {
                "user_id": self.config.BOT_OWNER_ID,
                "username": self.config.OWNER_USERNAME,
                "role": "super_admin",
                "added_by": "system",
                "added_at": datetime.now().isoformat(),
                "permissions": self.permissions["super_admin"]["permissions"],
                "stats": {
                    "actions_taken": 0,
                    "users_banned": 0,
                    "payments_processed": 0,
                    "last_active": datetime.now().isoformat()
                }
            }
        }
        
        self._save_admins(default_admins)
        return default_admins
    
    def _save_admins(self, admins: Dict):
        """Save admin data"""
        admin_file = os.path.join(self.db.data_dir, "admins.json")
        with open(admin_file, 'w', encoding='utf-8') as f:
            json.dump(admins, f, indent=2, ensure_ascii=False)
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return str(user_id) in self.admins or user_id == self.config.BOT_OWNER_ID
    
    def get_admin_role(self, user_id: int) -> Optional[str]:
        """Get admin role"""
        admin_data = self.admins.get(str(user_id))
        if admin_data:
            return admin_data.get("role", "support")
        return None
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if admin has specific permission"""
        if not self.is_admin(user_id):
            return False
        
        # Owner has all permissions
        if user_id == self.config.BOT_OWNER_ID:
            return True
        
        admin_data = self.admins.get(str(user_id))
        if not admin_data:
            return False
        
        permissions = admin_data.get("permissions", [])
        return permission in permissions
    
    async def get_bot_stats(self) -> str:
        """Get comprehensive bot statistics"""
        stats = self.db.get_stats()
        
        # Calculate additional stats
        total_users = stats["total_users"]
        active_users = stats["active_users"]
        
        # Payment stats
        payment_stats = await self._get_payment_stats()
        
        # Game stats
        game_stats = await self._get_game_stats()
        
        # System info
        system_info = await self._get_system_info()
        
        stats_text = f"""
📊 **বট পরিসংখ্যান (রিয়েল-টাইম)**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 **ইউজার পরিসংখ্যান:**
• মোট ইউজার: {total_users:,}
• অ্যাকটিভ ইউজার: {active_users:,} ({active_users/total_users*100 if total_users > 0 else 0:.1f}%)
• নতুন ইউজার (আজ): {stats['today_stats']['new_users']:,}
• গড় অ্যাকটিভিটি: {self._calculate_avg_activity()}%

💰 **আর্থিক পরিসংখ্যান:**
• মোট কয়েন: {Utils.format_coins(stats['total_coins'])}
• মোট ব্যালেন্স: {Utils.format_currency(stats['total_balance'])}
• আজকের ডিপোজিট: {Utils.format_currency(payment_stats['today_deposits'])}
• আজকের উইথড্র: {Utils.format_currency(payment_stats['today_withdrawals'])}
• নেট প্রবাহ: {Utils.format_currency(payment_stats['net_flow'])}
• সাকসেস রেট: {payment_stats['success_rate']:.1f}%

🎮 **গেম পরিসংখ্যান:**
• আজকের গেম: {game_stats['today_games']:,}
• উইন রেট: {game_stats['win_rate']:.1f}%
• জনপ্রিয় গেম: {game_stats['popular_game']}
• টোটাল বেট: {Utils.format_coins(game_stats['total_bet'])}
• টোটাল পেওয়াউট: {Utils.format_coins(game_stats['total_payout'])}

🛍️ **শপ পরিসংখ্যান:**
• টোটাল আইটেম: {stats['shop_items']:,}
• টোটাল সেল: {self._get_total_sales():,}
• টোটাল আয়: {Utils.format_coins(self._get_shop_revenue())}

⚙️ **সিস্টেম তথ্য:**
• আপটাইম: {system_info['uptime']}
• মেমোরি ব্যবহার: {system_info['memory_usage']}
• ব্যাকআপ: {stats.get('last_backup', 'কখনোই নয়')[:10]}
• লগ এন্ট্রি: {len(self.db.logs):,}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 **সারাংশ:** {self._get_summary_message(stats)}
        """
        
        return stats_text
    
    async def _get_payment_stats(self) -> Dict:
        """Get payment statistics"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_deposits = 0
        today_withdrawals = 0
        successful_payments = 0
        total_payments = 0
        
        for payment in self.db.payments.values():
            total_payments += 1
            
            if payment.get("status") == "COMPLETED":
                successful_payments += 1
            
            if payment.get("created_at", "").startswith(today):
                if payment["type"] == "DEPOSIT" and payment["status"] == "COMPLETED":
                    today_deposits += payment.get("amount", 0)
                elif payment["type"] == "WITHDRAW" and payment["status"] == "COMPLETED":
                    today_withdrawals += payment.get("amount", 0)
        
        success_rate = (successful_payments / max(total_payments, 1)) * 100
        
        return {
            "today_deposits": today_deposits,
            "today_withdrawals": today_withdrawals,
            "net_flow": today_deposits - today_withdrawals,
            "success_rate": success_rate,
            "total_payments": total_payments,
            "successful_payments": successful_payments
        }
    
    async def _get_game_stats(self) -> Dict:
        """Get game statistics"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_games = 0
        total_bet = 0
        total_payout = 0
        wins = 0
        total_games = 0
        
        # Count games from game history
        for game_id, game_data in self.db.game_history.items():
            if game_data.get("timestamp", "").startswith(today):
                today_games += 1
            
            total_games += 1
            bet = game_data.get("bet", 0) or game_data.get("entry_fee", 0)
            payout = game_data.get("payout", 0)
            
            total_bet += bet
            total_payout += payout
            
            if game_data.get("result") in ["WIN", "JACKPOT"]:
                wins += 1
        
        win_rate = (wins / max(total_games, 1)) * 100
        
        # Find popular game
        game_counts = {}
        for game_data in self.db.game_history.values():
            game_type = game_data.get("game", "unknown")
            game_counts[game_type] = game_counts.get(game_type, 0) + 1
        
        popular_game = max(game_counts.items(), key=lambda x: x[1])[0] if game_counts else "কোনোটিই না"
        
        return {
            "today_games": today_games,
            "total_bet": total_bet,
            "total_payout": total_payout,
            "net_profit": total_bet - total_payout,
            "win_rate": win_rate,
            "popular_game": popular_game,
            "total_games": total_games
        }
    
    async def _get_system_info(self) -> Dict:
        """Get system information"""
        try:
            import psutil
            process = psutil.Process()
            
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            
            # Calculate uptime (simulated)
            uptime_days = (datetime.now() - datetime.fromisoformat("2024-01-01")).days
            
            return {
                "memory_usage": f"{memory_usage:.1f} MB",
                "uptime": f"{uptime_days} দিন",
                "python_version": "3.12.x",
                "bot_version": self.config.VERSION
            }
        except:
            return {
                "memory_usage": "N/A",
                "uptime": "N/A",
                "python_version": "3.12.x",
                "bot_version": self.config.VERSION
            }
    
    def _calculate_avg_activity(self) -> float:
        """Calculate average user activity"""
        if not self.db.users:
            return 0.0
        
        active_count = 0
        cutoff = datetime.now() - timedelta(days=7)
        
        for user in self.db.users.values():
            last_active = datetime.fromisoformat(user.get("last_active", "2000-01-01"))
            if last_active > cutoff:
                active_count += 1
        
        return (active_count / len(self.db.users)) * 100
    
    def _get_total_sales(self) -> int:
        """Get total shop sales"""
        total_sales = 0
        for user in self.db.users.values():
            total_sales += len(user.get("inventory", []))
        return total_sales
    
    def _get_shop_revenue(self) -> int:
        """Get total shop revenue"""
        total_revenue = 0
        for user in self.db.users.values():
            for item in user.get("inventory", []):
                total_revenue += item.get("price_paid", 0) * item.get("quantity", 1)
        return total_revenue
    
    def _get_summary_message(self, stats: Dict) -> str:
        """Get summary message based on stats"""
        active_rate = (stats["active_users"] / max(stats["total_users"], 1)) * 100
        
        if active_rate > 50:
            return "অত্যন্ত অ্যাকটিভ কমিউনিটি! 👏"
        elif active_rate > 30:
            return "ভালো অ্যাকটিভিটি চলছে! 👍"
        elif active_rate > 15:
            return "মাঝারি অ্যাকটিভিটি। 📊"
        else:
            return "অ্যাকটিভিটি বাড়ানো প্রয়োজন! 📈"
    
    async def broadcast_message(self, admin_id: int, message: str, 
                               target: str = "all", filters: Dict = None) -> Dict:
        """Broadcast message to users with filtering"""
        if not self.has_permission(admin_id, "broadcast"):
            return {
                "success": False,
                "message": "এই অনুমতি আপনার নেই!"
            }
        
        if len(message) < 10:
            return {
                "success": False,
                "message": "বার্তাটি খুব ছোট! অন্তত ১০টি অক্ষর লিখুন।"
            }
        
        # Apply filters
        target_users = self._filter_users(target, filters)
        
        if not target_users:
            return {
                "success": False,
                "message": "কোনো ইউজার পাওয়া যায়নি এই ফিল্টারে!"
            }
        
        # In real implementation, you would send messages here
        # This is simulation
        
        broadcast_id = f"broadcast_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        broadcast_data = {
            "id": broadcast_id,
            "admin_id": admin_id,
            "message": message,
            "target": target,
            "filters": filters,
            "total_users": len(target_users),
            "sent_at": datetime.now().isoformat(),
            "status": "SENT"
        }
        
        # Log the broadcast
        self.db.add_log(
            "admin_broadcast",
            f"Broadcast sent to {len(target_users)} users",
            admin_id,
            broadcast_data
        )
        
        # Update admin stats
        self._update_admin_stats(admin_id, "broadcasts_sent", 1)
        
        return {
            "success": True,
            "message": f"✅ ব্রডকাস্ট পাঠানো হয়েছে {len(target_users)} জন ইউজারকে!",
            "broadcast_id": broadcast_id,
            "users_reached": len(target_users),
            "sample_users": target_users[:3] if target_users else []
        }
    
    def _filter_users(self, target: str, filters: Dict = None) -> List[int]:
        """Filter users based on criteria"""
        filters = filters or {}
        
        if target == "all":
            user_ids = [int(uid) for uid in self.db.users.keys()]
        elif target == "active":
            cutoff = datetime.now() - timedelta(days=7)
            user_ids = []
            for uid, user in self.db.users.items():
                last_active = datetime.fromisoformat(user.get("last_active", "2000-01-01"))
                if last_active > cutoff:
                    user_ids.append(int(uid))
        elif target == "inactive":
            cutoff = datetime.now() - timedelta(days=30)
            user_ids = []
            for uid, user in self.db.users.items():
                last_active = datetime.fromisoformat(user.get("last_active", "2000-01-01"))
                if last_active < cutoff:
                    user_ids.append(int(uid))
        elif target == "vip":
            user_ids = [int(uid) for uid, user in self.db.users.items() 
                       if user.get("is_vip", False)]
        else:
            user_ids = [int(uid) for uid in self.db.users.keys()]
        
        # Apply additional filters
        if filters:
            filtered_ids = []
            
            for uid in user_ids:
                user = self.db.get_user(uid)
                if not user:
                    continue
                
                passes = True
                
                # Min level filter
                if "min_level" in filters and user.get("level", 1) < filters["min_level"]:
                    passes = False
                
                # Max level filter
                if "max_level" in filters and user.get("level", 1) > filters["max_level"]:
                    passes = False
                
                # Min coins filter
                if "min_coins" in filters and user.get("coins", 0) < filters["min_coins"]:
                    passes = False
                
                # Max coins filter
                if "max_coins" in filters and user.get("coins", 0) > filters["max_coins"]:
                    passes = False
                
                # Has warnings filter
                if "has_warnings" in filters and user.get("warnings", 0) == 0:
                    passes = False
                
                if passes:
                    filtered_ids.append(uid)
            
            user_ids = filtered_ids
        
        return user_ids
    
    async def manage_user(self, admin_id: int, target_id: int, action: str, 
                         data: Dict = None) -> Dict:
        """Manage user (ban, warn, give coins, etc.)"""
        data = data or {}
        
        # Check permissions based on action
        if action in ["ban", "unban", "warn"] and not self.has_permission(admin_id, "ban_users"):
            return {
                "success": False,
                "message": "ব্যবহারকারী ব্যান/সতর্ক করার অনুমতি নেই!"
            }
        
        if action in ["give_coins", "take_coins"] and not self.has_permission(admin_id, "give_coins"):
            return {
                "success": False,
                "message": "কয়েন দেবার/নেবার অনুমতি নেই!"
            }
        
        user = self.db.get_user(target_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        if action == "ban":
            duration = data.get("duration", 24)  # hours
            reason = data.get("reason", "No reason provided")
            
            # Calculate ban expiration
            ban_until = datetime.now() + timedelta(hours=duration)
            
            self.db.update_user(target_id, {
                "is_banned": True,
                "ban_reason": reason,
                "ban_until": ban_until.isoformat(),
                "banned_by": admin_id,
                "banned_at": datetime.now().isoformat()
            })
            
            message = f"❌ ইউজার {target_id} কে {duration} ঘন্টার জন্য ব্যান করা হয়েছে। কারণ: {reason}"
            action_type = "user_banned"
        
        elif action == "unban":
            self.db.update_user(target_id, {
                "is_banned": False,
                "unbanned_by": admin_id,
                "unbanned_at": datetime.now().isoformat()
            })
            
            message = f"✅ ইউজার {target_id} আনব্যান করা হয়েছে।"
            action_type = "user_unbanned"
        
        elif action == "warn":
            warnings = user.get("warnings", 0) + 1
            reason = data.get("reason", "No reason provided")
            
            # Add to warning history
            warning_history = user.get("warning_history", [])
            warning_history.append({
                "warning_number": warnings,
                "reason": reason,
                "warned_by": admin_id,
                "timestamp": datetime.now().isoformat()
            })
            
            self.db.update_user(target_id, {
                "warnings": warnings,
                "warning_history": warning_history,
                "last_warning": datetime.now().isoformat()
            })
            
            if warnings >= 3:
                # Auto ban for 3 warnings
                self.db.update_user(target_id, {
                    "is_banned": True,
                    "ban_reason": f"Auto-ban: {warnings} warnings",
                    "ban_until": (datetime.now() + timedelta(hours=24)).isoformat()
                })
                message = f"⚠️ সতর্কতা #{warnings} দেওয়া হয়েছে এবং অটো-ব্যান করা হয়েছে। কারণ: {reason}"
                action_type = "user_auto_banned"
            else:
                message = f"⚠️ সতর্কতা #{warnings} দেওয়া হয়েছে। কারণ: {reason}"
                action_type = "user_warned"
        
        elif action == "give_coins":
            amount = data.get("amount", 0)
            if amount <= 0:
                return {
                    "success": False,
                    "message": "সঠিক পরিমাণ দিন!"
                }
            
            user["coins"] += amount
            self.db.update_user(target_id, {"coins": user["coins"]})
            
            message = f"✅ {target_id} কে {Utils.format_coins(amount)} দেওয়া হয়েছে।"
            action_type = "coins_given"
        
        elif action == "take_coins":
            amount = data.get("amount", 0)
            if amount <= 0:
                return {
                    "success": False,
                    "message": "সঠিক পরিমাণ দিন!"
                }
            
            if user["coins"] < amount:
                amount = user["coins"]  # Take all if not enough
            
            user["coins"] -= amount
            self.db.update_user(target_id, {"coins": user["coins"]})
            
            message = f"⚠️ {target_id} থেকে {Utils.format_coins(amount)} নেওয়া হয়েছে।"
            action_type = "coins_taken"
        
        elif action == "reset_stats":
            self.db.update_user(target_id, {
                "coins": 0,
                "warnings": 0,
                "daily_streak": 0,
                "stats": {
                    "dice_played": 0,
                    "dice_won": 0,
                    "slot_played": 0,
                    "slot_won": 0,
                    "quiz_played": 0,
                    "quiz_correct": 0
                }
            })
            
            message = f"🔄 ইউজার {target_id} এর পরিসংখ্যান রিসেট করা হয়েছে।"
            action_type = "stats_reset"
        
        else:
            return {
                "success": False,
                "message": "অজানা একশন!"
            }
        
        # Log the action
        self.db.add_log(
            "admin_action",
            f"Admin {action}: {target_id}",
            admin_id,
            {
                "action": action,
                "target_id": target_id,
                "data": data,
                "message": message
            }
        )
        
        # Update admin stats
        self._update_admin_stats(admin_id, f"{action}_count", 1)
        
        return {
            "success": True,
            "message": message,
            "action": action,
            "target_id": target_id,
            "action_type": action_type
        }
    
    def _update_admin_stats(self, admin_id: int, stat_name: str, increment: int = 1):
        """Update admin statistics"""
        admin_key = str(admin_id)
        if admin_key in self.admins:
            if "stats" not in self.admins[admin_key]:
                self.admins[admin_key]["stats"] = {}
            
            self.admins[admin_key]["stats"][stat_name] = \
                self.admins[admin_key]["stats"].get(stat_name, 0) + increment
            
            self.admins[admin_key]["stats"]["last_active"] = datetime.now().isoformat()
            
            self._save_admins(self.admins)
    
    async def get_user_info(self, user_id: int, detailed: bool = False) -> Dict:
        """Get detailed user information"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        level_info = Utils.calculate_level(user.get("xp", 0))
        
        basic_info = {
            "user_id": user_id,
            "username": user.get("username", "N/A"),
            "first_name": user.get("first_name", "N/A"),
            "last_name": user.get("last_name", ""),
            "language": user.get("language_code", "bn"),
            "joined": user.get("first_seen", "N/A"),
            "last_active": user.get("last_active", "N/A")
        }
        
        status_info = {
            "level": level_info["level"],
            "xp": f"{level_info['xp']}/{level_info['xp_needed']}",
            "progress": Utils.create_progress_bar(level_info["xp"], level_info["xp_needed"]),
            "is_vip": user.get("is_vip", False),
            "vip_until": user.get("vip_until"),
            "is_banned": user.get("is_banned", False),
            "ban_reason": user.get("ban_reason"),
            "ban_until": user.get("ban_until"),
            "warnings": user.get("warnings", 0)
        }
        
        economy_info = {
            "balance": user.get("balance", 0),
            "coins": user.get("coins", 0),
            "total_earned": user.get("total_earned", 0),
            "total_spent": user.get("total_spent", 0),
            "daily_streak": user.get("daily_streak", 0),
            "max_streak": user.get("max_streak", 0)
        }
        
        activity_info = {
            "total_messages": user.get("total_messages", 0),
            "total_games": user.get("total_games", 0),
            "games_won": user.get("games_won", 0),
            "inventory_items": len(user.get("inventory", [])),
            "referrals": len(user.get("referrals", [])),
            "referral_earnings": user.get("referral_earnings", 0)
        }
        
        info = {
            "success": True,
            "basic": basic_info,
            "status": status_info,
            "economy": economy_info,
            "activity": activity_info
        }
        
        if detailed:
            # Add detailed information
            info["detailed"] = {
                "inventory": user.get("inventory", []),
                "warning_history": user.get("warning_history", []),
                "settings": user.get("settings", {}),
                "stats": user.get("stats", {}),
                "boosts": user.get("boosts", []),
                "equipped_items": user.get("equipped_items", {})
            }
            
            # Get payment history
            payments = self.db.get_user_payments(user_id, limit=20)
            info["detailed"]["recent_payments"] = payments
            
            # Get game history
            game_history = []
            for game_id, game_data in self.db.game_history.items():
                if game_data.get("user_id") == user_id:
                    game_history.append(game_data)
            
            info["detailed"]["recent_games"] = game_history[-10:]  # Last 10 games
        
        return info
    
    async def create_backup(self, admin_id: int) -> Dict:
        """Create database backup"""
        if not self.has_permission(admin_id, "backup_restore"):
            return {
                "success": False,
                "message": "ব্যাকআপ/রিস্টোর করার অনুমতি নেই!"
            }
        
        try:
            backup_file = self.db.create_backup()
            
            # Log the backup
            self.db.add_log(
                "admin_backup",
                "Database backup created",
                admin_id,
                {"backup_file": backup_file}
            )
            
            # Update admin stats
            self._update_admin_stats(admin_id, "backups_created", 1)
            
            return {
                "success": True,
                "message": f"✅ ডাটাবেস ব্যাকআপ তৈরি হয়েছে: {os.path.basename(backup_file)}",
                "backup_file": backup_file,
                "size": os.path.getsize(backup_file) if os.path.exists(backup_file) else 0,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ ব্যাকআপ ব্যর্থ হয়েছে: {str(e)}"
            }
    
    async def get_system_logs(self, log_type: str = None, limit: int = 50) -> List[Dict]:
        """Get system logs"""
        logs = []
        
        for log_id, log_data in self.db.logs.items():
            if log_type and log_data.get("type") != log_type:
                continue
            
            logs.append({
                "id": log_id,
                "type": log_data.get("type", "unknown"),
                "message": log_data.get("message", ""),
                "user_id": log_data.get("user_id"),
                "timestamp": log_data.get("timestamp", ""),
                "data": log_data.get("data", {})
            })
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return logs[:limit]
    
    async def add_admin(self, admin_id: int, target_id: int, role: str) -> Dict:
        """Add new admin (super admin only)"""
        if not self.has_permission(admin_id, "manage_admins"):
            return {
                "success": False,
                "message": "অ্যাডমিন ম্যানেজ করার অনুমতি নেই!"
            }
        
        if role not in self.permissions:
            return {
                "success": False,
                "message": f"ভুল রোল! সঠিক রোল: {', '.join(self.permissions.keys())}"
            }
        
        target_user = self.db.get_user(target_id)
        if not target_user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        if str(target_id) in self.admins:
            return {
                "success": False,
                "message": "এই ইউজার ইতিমধ্যেই অ্যাডমিন!"
            }
        
        # Add as admin
        self.admins[str(target_id)] = {
            "user_id": target_id,
            "username": target_user.get("username", ""),
            "role": role,
            "added_by": admin_id,
            "added_at": datetime.now().isoformat(),
            "permissions": self.permissions[role]["permissions"],
            "stats": {
                "actions_taken": 0,
                "last_active": datetime.now().isoformat()
            }
        }
        
        self._save_admins(self.admins)
        
        # Log the action
        self.db.add_log(
            "admin_added",
            f"New admin added: {target_id} as {role}",
            admin_id,
            {"target_id": target_id, "role": role}
        )
        
        return {
            "success": True,
            "message": f"✅ @{target_user.get('username', 'User')} কে {self.permissions[role]['name']} হিসেবে অ্যাডমিন করা হয়েছে।",
            "target_id": target_id,
            "role": role,
            "permissions": self.permissions[role]["permissions"]
        }
    
    async def remove_admin(self, admin_id: int, target_id: int) -> Dict:
        """Remove admin (super admin only)"""
        if not self.has_permission(admin_id, "manage_admins"):
            return {
                "success": False,
                "message": "অ্যাডমিন ম্যানেজ করার অনুমতি নেই!"
            }
        
        # Cannot remove self
        if target_id == admin_id:
            return {
                "success": False,
                "message": "নিজেকে রিমুভ করতে পারবেন না!"
            }
        
        # Cannot remove owner
        if target_id == self.config.BOT_OWNER_ID:
            return {
                "success": False,
                "message": "বট মালিককে রিমুভ করা যাবে না!"
            }
        
        if str(target_id) not in self.admins:
            return {
                "success": False,
                "message": "এই ইউজার অ্যাডমিন নয়!"
            }
        
        # Get target info before removal
        target_info = self.admins[str(target_id)]
        
        # Remove admin
        del self.admins[str(target_id)]
        self._save_admins(self.admins)
        
        # Log the action
        self.db.add_log(
            "admin_removed",
            f"Admin removed: {target_id}",
            admin_id,
            {"target_id": target_id, "role": target_info.get("role")}
        )
        
        return {
            "success": True,
            "message": f"✅ @{target_info.get('username', 'User')} এর অ্যাডমিন পারমিশন রিমুভ করা হয়েছে।",
            "target_id": target_id,
            "removed_role": target_info.get("role")
        }
    
    async def get_admin_list(self) -> List[Dict]:
        """Get list of all admins"""
        admins_list = []
        
        for admin_data in self.admins.values():
            admin_info = {
                "user_id": admin_data["user_id"],
                "username": admin_data.get("username", "N/A"),
                "role": admin_data["role"],
                "role_name": self.permissions.get(admin_data["role"], {}).get("name", "Unknown"),
                "added_at": admin_data.get("added_at", "N/A"),
                "added_by": admin_data.get("added_by", "system"),
                "last_active": admin_data.get("stats", {}).get("last_active", "N/A"),
                "actions_taken": admin_data.get("stats", {}).get("actions_taken", 0)
            }
            
            admins_list.append(admin_info)
        
        # Sort by role level
        admins_list.sort(key=lambda x: self.permissions.get(x["role"], {}).get("level", 0), reverse=True)
        
        return admins_list
    
    async def get_admin_stats(self, admin_id: int) -> Dict:
        """Get admin's statistics"""
        if not self.is_admin(admin_id):
            return {
                "success": False,
                "message": "আপনি অ্যাডমিন নন!"
            }
        
        admin_data = self.admins.get(str(admin_id), {})
        
        # Calculate time as admin
        added_at = datetime.fromisoformat(admin_data.get("added_at", datetime.now().isoformat()))
        days_as_admin = (datetime.now() - added_at).days
        
        stats = admin_data.get("stats", {})
        
        return {
            "success": True,
            "user_id": admin_id,
            "username": admin_data.get("username", "N/A"),
            "role": admin_data.get("role", "unknown"),
            "role_name": self.permissions.get(admin_data.get("role", ""), {}).get("name", "Unknown"),
            "days_as_admin": days_as_admin,
            "actions_taken": stats.get("actions_taken", 0),
            "users_banned": stats.get("user_banned_count", 0),
            "payments_processed": stats.get("payments_processed", 0),
            "broadcasts_sent": stats.get("broadcasts_sent", 0),
            "last_active": stats.get("last_active", "N/A"),
            "permissions": admin_data.get("permissions", [])
        }
    
    async def view_financial_report(self, admin_id: int, period: str = "today") -> Dict:
        """View financial report"""
        if not self.has_permission(admin_id, "financial_reports"):
            return {
                "success": False,
                "message": "ফাইন্যান্সিয়াল রিপোর্ট দেখার অনুমতি নেই!"
            }
        
        # Calculate period
        if period == "today":
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            period_name = "আজ"
        elif period == "yesterday":
            start_date = datetime.now() - timedelta(days=1)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            period_name = "গতকাল"
        elif period == "week":
            start_date = datetime.now() - timedelta(days=7)
            period_name = "গত ৭ দিন"
        elif period == "month":
            start_date = datetime.now() - timedelta(days=30)
            period_name = "গত ৩০ দিন"
        else:
            start_date = datetime.now() - timedelta(days=1)
            period_name = "গতকাল"
        
        end_date = datetime.now()
        
        # Calculate financial data
        total_deposits = 0
        total_withdrawals = 0
        successful_deposits = 0
        successful_withdrawals = 0
        failed_transactions = 0
        pending_transactions = 0
        
        for payment in self.db.payments.values():
            created_at = datetime.fromisoformat(payment.get("created_at", "2000-01-01"))
            
            if start_date <= created_at <= end_date:
                amount = payment.get("amount", 0)
                status = payment.get("status", "PENDING")
                
                if payment["type"] == "DEPOSIT":
                    if status == "COMPLETED":
                        total_deposits += amount
                        successful_deposits += 1
                    elif status == "PENDING":
                        pending_transactions += 1
                    else:
                        failed_transactions += 1
                
                elif payment["type"] == "WITHDRAW":
                    if status == "COMPLETED":
                        total_withdrawals += amount
                        successful_withdrawals += 1
                    elif status == "PENDING":
                        pending_transactions += 1
                    else:
                        failed_transactions += 1
        
        net_flow = total_deposits - total_withdrawals
        
        # Calculate success rates
        total_completed = successful_deposits + successful_withdrawals
        total_attempted = total_completed + failed_transactions
        
        deposit_success_rate = (successful_deposits / max(successful_deposits + failed_transactions, 1)) * 100
        withdrawal_success_rate = (successful_withdrawals / max(successful_withdrawals + failed_transactions, 1)) * 100
        overall_success_rate = (total_completed / max(total_attempted, 1)) * 100
        
        report = {
            "period": period_name,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "deposits": {
                "total": total_deposits,
                "successful": successful_deposits,
                "success_rate": deposit_success_rate
            },
            "withdrawals": {
                "total": total_withdrawals,
                "successful": successful_withdrawals,
                "success_rate": withdrawal_success_rate
            },
            "net_flow": net_flow,
            "pending_transactions": pending_transactions,
            "failed_transactions": failed_transactions,
            "overall_success_rate": overall_success_rate,
            "average_deposit": total_deposits / max(successful_deposits, 1),
            "average_withdrawal": total_withdrawals / max(successful_withdrawals, 1)
        }
        
        return {
            "success": True,
            "report": report,
            "formatted_report": self._format_financial_report(report)
        }
    
    def _format_financial_report(self, report: Dict) -> str:
        """Format financial report for display"""
        return f"""
💰 **ফাইন্যান্সিয়াল রিপোর্ট** ({report['period']})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 **পিরিয়ড:** {report['start_date']} থেকে {report['end_date']}

💵 **ডিপোজিট:**
• মোট ডিপোজিট: {Utils.format_currency(report['deposits']['total'])}
• সফল ডিপোজিট: {report['deposits']['successful']:,}
• সাকসেস রেট: {report['deposits']['success_rate']:.1f}%
• গড় ডিপোজিট: {Utils.format_currency(report['average_deposit'])}

🏧 **উইথড্র:**
• মোট উইথড্র: {Utils.format_currency(report['withdrawals']['total'])}
• সফল উইথড্র: {report['withdrawals']['successful']:,}
• সাকসেস রেট: {report['withdrawals']['success_rate']:.1f}%
• গড় উইথড্র: {Utils.format_currency(report['average_withdrawal'])}

📊 **সারাংশ:**
• নেট প্রবাহ: {Utils.format_currency(report['net_flow'])}
• পেন্ডিং ট্রানজেকশন: {report['pending_transactions']:,}
• ব্যর্থ ট্রানজেকশন: {report['failed_transactions']:,}
• সামগ্রিক সাকসেস রেট: {report['overall_success_rate']:.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 **ভবিষ্যদ্বাণী:** {self._get_financial_prediction(report)}
        """
    
    def _get_financial_prediction(self, report: Dict) -> str:
        """Get financial prediction based on report"""
        net_flow = report["net_flow"]
        
        if net_flow > 10000:
            return "অত্যন্ত ইতিবাচক প্রবাহ! 🚀"
        elif net_flow > 5000:
            return "ভালো প্রবাহ চলছে! 📈"
        elif net_flow > 0:
            return "ইতিবাচক প্রবাহ 👍"
        elif net_flow > -5000:
            return "সামান্য নেতিবাচক প্রবাহ 📉"
        else:
            return "নেতিবাচক প্রবাহ, মনিটরিং প্রয়োজন! ⚠️"
    
    async def cleanup_system(self, admin_id: int, cleanup_type: str) -> Dict:
        """Cleanup system data"""
        if not self.has_permission(admin_id, "system_settings"):
            return {
                "success": False,
                "message": "সিস্টেম সেটিংস ম্যানেজ করার অনুমতি নেই!"
            }
        
        cleaned_count = 0
        
        if cleanup_type == "inactive_users":
            # Remove users inactive for more than 90 days
            cutoff = datetime.now() - timedelta(days=90)
            
            users_to_remove = []
            for uid, user in self.db.users.items():
                last_active = datetime.fromisoformat(user.get("last_active", "2000-01-01"))
                if last_active < cutoff:
                    users_to_remove.append(uid)
            
            for uid in users_to_remove:
                del self.db.users[uid]
                cleaned_count += 1
            
            self.db._save_data("users", self.db.users)
            message = f"🧹 {cleaned_count} জন নিষ্ক্রিয় ইউজার রিমুভ করা হয়েছে।"
        
        elif cleanup_type == "old_logs":
            # Keep only last 1000 logs
            total_logs = len(self.db.logs)
            if total_logs > 1000:
                # Sort logs by timestamp
                sorted_logs = sorted(self.db.logs.items(), 
                                   key=lambda x: x[1].get("timestamp", ""))
                
                # Remove oldest logs
                logs_to_remove = sorted_logs[:total_logs - 1000]
                for log_id, _ in logs_to_remove:
                    del self.db.logs[log_id]
                
                cleaned_count = len(logs_to_remove)
                self.db._save_data("logs", self.db.logs)
                message = f"🧹 {cleaned_count}টি পুরনো লগ রিমুভ করা হয়েছে।"
            else:
                message = "❌ পর্যাপ্ত লগ নেই ক্লিনআপের জন্য।"
        
        elif cleanup_type == "expired_items":
            # Remove expired items from user inventories
            cleaned_count = 0
            now = datetime.now()
            
            for uid, user in self.db.users.items():
                inventory = user.get("inventory", [])
                active_items = []
                
                for item in inventory:
                    expires_at = item.get("expires_at")
                    if expires_at:
                        try:
                            expiry_date = datetime.fromisoformat(expires_at)
                            if expiry_date > now:
                                active_items.append(item)
                            else:
                                cleaned_count += 1
                        except:
                            active_items.append(item)
                    else:
                        active_items.append(item)
                
                if len(active_items) != len(inventory):
                    user["inventory"] = active_items
                    self.db.update_user(int(uid), {"inventory": active_items})
            
            message = f"🧹 {cleaned_count}টি এক্সপায়ার্ড আইটেম রিমুভ করা হয়েছে।"
        
        else:
            return {
                "success": False,
                "message": "অজানা ক্লিনআপ টাইপ!"
            }
        
        # Log the cleanup
        self.db.add_log(
            "system_cleanup",
            f"System cleanup: {cleanup_type}",
            admin_id,
            {"type": cleanup_type, "cleaned_count": cleaned_count}
        )
        
        return {
            "success": True,
            "message": message,
            "type": cleanup_type,
            "cleaned_count": cleaned_count
        }