import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config import Config
from db import Database
from utils import Utils

class Moderation:
    """Advanced Chat Moderation System v15.0.00"""
    
    def __init__(self, db: Database):
        self.db = db
        self.config = Config()
        self.moderation_logs = []
        self.warn_reasons = {
            "spam": {
                "name": "স্প্যাম মেসেজ",
                "points": 10,
                "duration": "1 hour mute"
            },
            "bad_words": {
                "name": "অপমানজনক ভাষা",
                "points": 15,
                "duration": "3 hour mute"
            },
            "links": {
                "name": "অনুমোদনহীন লিংক",
                "points": 20,
                "duration": "6 hour mute"
            },
            "harassment": {
                "name": "হ্যারাসমেন্ট",
                "points": 25,
                "duration": "12 hour mute"
            },
            "scam": {
                "name": "স্ক্যাম প্রচেষ্টা",
                "points": 30,
                "duration": "24 hour ban"
            },
            "impersonation": {
                "name": "অন্যের পরিচয় নেওয়া",
                "points": 40,
                "duration": "Permanent ban"
            },
            "other": {
                "name": "অন্যান্য",
                "points": 5,
                "duration": "Warning"
            }
        }
        
        # Auto-moderation rules
        self.auto_mod_rules = {
            "spam_detection": {
                "enabled": True,
                "max_messages_per_minute": 10,
                "action": "mute_5_minutes"
            },
            "link_protection": {
                "enabled": True,
                "allowed_domains": ["telegram.org", "github.com", "google.com"],
                "action": "delete_and_warn"
            },
            "bad_word_filter": {
                "enabled": True,
                "words": ["খারাপ", "অপমান", "গালি", "অশ্লীল", "abuse", "fuck"],
                "action": "delete_and_mute_1h"
            },
            "caps_lock_detection": {
                "enabled": True,
                "max_caps_ratio": 0.7,
                "min_length": 10,
                "action": "warn"
            }
        }
        
        # Load moderation data
        self.moderation_data = self._load_moderation_data()
    
    def _load_moderation_data(self) -> Dict:
        """Load moderation data"""
        # In production, this would load from a file
        return {
            "auto_mod_stats": {
                "messages_checked": 0,
                "actions_taken": 0,
                "last_cleanup": datetime.now().isoformat()
            },
            "moderation_queue": [],
            "reports": []
        }
    
    async def auto_moderate_message(self, user_id: int, message: str, 
                                   chat_type: str = "private") -> Dict:
        """Auto-moderate incoming message"""
        self.moderation_data["auto_mod_stats"]["messages_checked"] += 1
        
        actions = []
        violations = []
        points = 0
        
        # Check for spam
        if self.auto_mod_rules["spam_detection"]["enabled"]:
            spam_check = await self._check_spam(user_id, message, chat_type)
            if spam_check["is_spam"]:
                actions.append(spam_check["action"])
                violations.append("স্প্যাম ডিটেক্টেড")
                points += 10
        
        # Check for links
        if self.auto_mod_rules["link_protection"]["enabled"]:
            link_check = await self._check_links(message)
            if link_check["has_blocked_links"]:
                actions.append(link_check["action"])
                violations.extend(link_check["violations"])
                points += 20
        
        # Check for bad words
        if self.auto_mod_rules["bad_word_filter"]["enabled"]:
            bad_word_check = await self._check_bad_words(message)
            if bad_word_check["has_bad_words"]:
                actions.append(bad_word_check["action"])
                violations.extend(bad_word_check["violations"])
                points += 15
        
        # Check for caps lock
        if self.auto_mod_rules["caps_lock_detection"]["enabled"]:
            caps_check = await self._check_caps_lock(message)
            if caps_check["excessive_caps"]:
                actions.append(caps_check["action"])
                violations.append("অত্যধিক ক্যাপিটাল লেটার")
                points += 5
        
        # Determine final action
        final_action = "ALLOW"
        if points >= 30:
            final_action = "BAN"
            duration = "24h"
        elif points >= 20:
            final_action = "MUTE"
            duration = "6h"
        elif points >= 15:
            final_action = "MUTE"
            duration = "1h"
        elif points >= 10:
            final_action = "WARN"
        elif points >= 5:
            final_action = "DELETE"
        
        if final_action != "ALLOW":
            self.moderation_data["auto_mod_stats"]["actions_taken"] += 1
            
            # Log auto-moderation action
            self._log_moderation_action(
                "auto_moderation",
                user_id,
                {
                    "action": final_action,
                    "duration": duration if final_action in ["MUTE", "BAN"] else None,
                    "points": points,
                    "violations": violations,
                    "message_preview": message[:50]
                }
            )
        
        return {
            "action": final_action,
            "points": points,
            "violations": violations,
            "duration": duration if final_action in ["MUTE", "BAN"] else None,
            "message": "Message approved" if final_action == "ALLOW" else f"Auto-mod: {', '.join(violations)}"
        }
    
    async def _check_spam(self, user_id: int, message: str, chat_type: str) -> Dict:
        """Check for spam patterns"""
        # Simple spam detection
        is_spam = False
        action = None
        
        # Check for repeated messages
        if len(message) < 10 and len(set(message)) < 5:
            is_spam = True
            action = self.auto_mod_rules["spam_detection"]["action"]
        
        # Check for excessive repetition
        if re.search(r'(.)\1{5,}', message):  # 6 or more repeated characters
            is_spam = True
            action = self.auto_mod_rules["spam_detection"]["action"]
        
        # Check for common spam phrases
        spam_phrases = [
            "click here", "free money", "make money fast",
            "work from home", "earn daily", "get rich"
        ]
        
        message_lower = message.lower()
        for phrase in spam_phrases:
            if phrase in message_lower:
                is_spam = True
                action = self.auto_mod_rules["spam_detection"]["action"]
                break
        
        return {
            "is_spam": is_spam,
            "action": action
        }
    
    async def _check_links(self, message: str) -> Dict:
        """Check for unauthorized links"""
        # Extract URLs from message
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, message)
        
        has_blocked_links = False
        violations = []
        action = None
        
        allowed_domains = self.auto_mod_rules["link_protection"]["allowed_domains"]
        
        for url in urls:
            # Check if domain is allowed
            domain_allowed = False
            for allowed_domain in allowed_domains:
                if allowed_domain in url:
                    domain_allowed = True
                    break
            
            if not domain_allowed:
                has_blocked_links = True
                violations.append(f"অনুমোদনহীন লিংক: {url[:30]}...")
                action = self.auto_mod_rules["link_protection"]["action"]
        
        return {
            "has_blocked_links": has_blocked_links,
            "violations": violations,
            "action": action
        }
    
    async def _check_bad_words(self, message: str) -> Dict:
        """Check for bad words"""
        bad_words = self.auto_mod_rules["bad_word_filter"]["words"]
        message_lower = message.lower()
        
        found_words = []
        for word in bad_words:
            if word.lower() in message_lower:
                found_words.append(word)
        
        has_bad_words = len(found_words) > 0
        
        return {
            "has_bad_words": has_bad_words,
            "violations": [f"অনুপযুক্ত শব্দ: {', '.join(found_words)}"] if found_words else [],
            "action": self.auto_mod_rules["bad_word_filter"]["action"] if has_bad_words else None
        }
    
    async def _check_caps_lock(self, message: str) -> Dict:
        """Check for excessive caps lock"""
        if len(message) < self.auto_mod_rules["caps_lock_detection"]["min_length"]:
            return {"excessive_caps": False, "action": None}
        
        caps_count = sum(1 for c in message if c.isupper())
        caps_ratio = caps_count / len(message)
        
        excessive_caps = caps_ratio > self.auto_mod_rules["caps_lock_detection"]["max_caps_ratio"]
        
        return {
            "excessive_caps": excessive_caps,
            "action": self.auto_mod_rules["caps_lock_detection"]["action"] if excessive_caps else None
        }
    
    async def warn_user(self, user_id: int, reason: str, warned_by: int, 
                       notes: str = "", points: int = None) -> Dict:
        """Warn a user with point system"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        # Get warning reason details
        reason_details = self.warn_reasons.get(reason, self.warn_reasons["other"])
        warning_points = points or reason_details["points"]
        
        # Get current warning points
        current_points = user.get("warning_points", 0)
        new_points = current_points + warning_points
        
        # Get warning history
        warning_history = user.get("warning_history", [])
        
        # Create warning entry
        warning_entry = {
            "id": f"warn_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "reason": reason,
            "reason_text": reason_details["name"],
            "points": warning_points,
            "warned_by": warned_by,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
            "total_points": new_points
        }
        
        warning_history.append(warning_entry)
        
        # Update user
        user["warning_points"] = new_points
        user["warning_history"] = warning_history
        user["last_warning"] = datetime.now().isoformat()
        
        self.db.update_user(user_id, {
            "warning_points": new_points,
            "warning_history": warning_history,
            "last_warning": user["last_warning"]
        })
        
        # Check for auto-action based on points
        auto_action = await self._check_auto_action(user_id, new_points)
        
        # Log the warning
        self._log_moderation_action(
            "user_warned",
            warned_by,
            {
                "target_id": user_id,
                "reason": reason,
                "points": warning_points,
                "total_points": new_points,
                "auto_action": auto_action
            }
        )
        
        message = f"⚠️ {user_id} কে সতর্কতা দেওয়া হয়েছে। কারণ: {reason_details['name']} ({warning_points} পয়েন্ট)"
        
        if auto_action["action"] != "NONE":
            message += f"\n⚡ অটো-একশন: {auto_action['message']}"
        
        return {
            "success": True,
            "message": message,
            "warning_points": new_points,
            "warning_entry": warning_entry,
            "auto_action": auto_action
        }
    
    async def _check_auto_action(self, user_id: int, total_points: int) -> Dict:
        """Check for automatic action based on warning points"""
        if total_points >= 100:
            # Permanent ban
            await self.ban_user(
                user_id,
                "Auto-ban: 100+ warning points",
                0,  # System
                0   # Permanent
            )
            return {
                "action": "PERMANENT_BAN",
                "message": "স্থায়ী ব্যান",
                "duration": "Permanent"
            }
        
        elif total_points >= 80:
            # 7 day ban
            await self.ban_user(
                user_id,
                "Auto-ban: 80+ warning points",
                0,
                168  # 7 days in hours
            )
            return {
                "action": "BAN",
                "message": "৭ দিনের ব্যান",
                "duration": "7 days"
            }
        
        elif total_points >= 60:
            # 3 day ban
            await self.ban_user(
                user_id,
                "Auto-ban: 60+ warning points",
                0,
                72  # 3 days in hours
            )
            return {
                "action": "BAN",
                "message": "৩ দিনের ব্যান",
                "duration": "3 days"
            }
        
        elif total_points >= 40:
            # 1 day mute
            await self.mute_user(
                user_id,
                "Auto-mute: 40+ warning points",
                0,
                24  # 1 day in hours
            )
            return {
                "action": "MUTE",
                "message": "১ দিনের মিউট",
                "duration": "1 day"
            }
        
        elif total_points >= 20:
            # 6 hour mute
            await self.mute_user(
                user_id,
                "Auto-mute: 20+ warning points",
                0,
                6  # 6 hours
            )
            return {
                "action": "MUTE",
                "message": "৬ ঘন্টার মিউট",
                "duration": "6 hours"
            }
        
        return {
            "action": "NONE",
            "message": "কোনো অটো-একশন নেই",
            "duration": None
        }
    
    async def ban_user(self, user_id: int, reason: str, banned_by: int, 
                      duration_hours: int = 24) -> Dict:
        """Ban a user"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        # Calculate ban expiration
        if duration_hours <= 0:
            # Permanent ban
            ban_until = None
            duration_text = "স্থায়ী"
        else:
            ban_until = datetime.now() + timedelta(hours=duration_hours)
            duration_text = f"{duration_hours} ঘন্টা"
        
        # Update user
        user["is_banned"] = True
        user["ban_reason"] = reason
        user["banned_by"] = banned_by
        user["banned_at"] = datetime.now().isoformat()
        
        if ban_until:
            user["ban_until"] = ban_until.isoformat()
        else:
            user["ban_until"] = None
        
        # Add to ban history
        ban_history = user.get("ban_history", [])
        
        ban_entry = {
            "id": f"ban_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "reason": reason,
            "banned_by": banned_by,
            "duration_hours": duration_hours,
            "banned_at": datetime.now().isoformat(),
            "ban_until": ban_until.isoformat() if ban_until else None,
            "warning_points": user.get("warning_points", 0)
        }
        
        ban_history.append(ban_entry)
        user["ban_history"] = ban_history
        
        self.db.update_user(user_id, {
            "is_banned": True,
            "ban_reason": reason,
            "banned_by": banned_by,
            "banned_at": user["banned_at"],
            "ban_until": user["ban_until"],
            "ban_history": ban_history
        })
        
        # Log the ban
        self._log_moderation_action(
            "user_banned",
            banned_by,
            {
                "target_id": user_id,
                "reason": reason,
                "duration": duration_hours,
                "permanent": duration_hours <= 0
            }
        )
        
        return {
            "success": True,
            "message": f"❌ {user_id} কে {duration_text} ব্যান করা হয়েছে। কারণ: {reason}",
            "user_id": user_id,
            "reason": reason,
            "duration": duration_hours,
            "permanent": duration_hours <= 0,
            "ends_at": ban_until.isoformat() if ban_until else "Never"
        }
    
    async def unban_user(self, user_id: int, unbanned_by: int, 
                        reason: str = "Appeal approved") -> Dict:
        """Unban a user"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        if not user.get("is_banned", False):
            return {
                "success": False,
                "message": "ইউজার ব্যান করা নেই!"
            }
        
        # Update user
        user["is_banned"] = False
        user["unbanned_by"] = unbanned_by
        user["unban_reason"] = reason
        user["unbanned_at"] = datetime.now().isoformat()
        
        # Reduce warning points (for good behavior)
        current_points = user.get("warning_points", 0)
        if current_points > 0:
            user["warning_points"] = max(current_points - 10, 0)
        
        self.db.update_user(user_id, {
            "is_banned": False,
            "unbanned_by": unbanned_by,
            "unban_reason": reason,
            "unbanned_at": user["unbanned_at"],
            "warning_points": user.get("warning_points", current_points)
        })
        
        # Log the unban
        self._log_moderation_action(
            "user_unbanned",
            unbanned_by,
            {
                "target_id": user_id,
                "reason": reason,
                "previous_warning_points": current_points,
                "new_warning_points": user.get("warning_points", 0)
            }
        )
        
        return {
            "success": True,
            "message": f"✅ {user_id} আনব্যান করা হয়েছে। কারণ: {reason}",
            "user_id": user_id,
            "unbanned_by": unbanned_by,
            "warning_points_reduced": current_points - user.get("warning_points", 0)
        }
    
    async def mute_user(self, user_id: int, reason: str, muted_by: int, 
                       duration_minutes: int = 60) -> Dict:
        """Mute a user (temporary restriction)"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        # Calculate mute expiration
        mute_until = datetime.now() + timedelta(minutes=duration_minutes)
        
        # Update user
        user["is_muted"] = True
        user["mute_reason"] = reason
        user["muted_by"] = muted_by
        user["muted_at"] = datetime.now().isoformat()
        user["mute_until"] = mute_until.isoformat()
        user["mute_duration"] = duration_minutes
        
        self.db.update_user(user_id, {
            "is_muted": True,
            "mute_reason": reason,
            "muted_by": muted_by,
            "muted_at": user["muted_at"],
            "mute_until": user["mute_until"],
            "mute_duration": duration_minutes
        })
        
        # Log the mute
        self._log_moderation_action(
            "user_muted",
            muted_by,
            {
                "target_id": user_id,
                "reason": reason,
                "duration": duration_minutes
            }
        )
        
        return {
            "success": True,
            "message": f"🔇 {user_id} কে {duration_minutes} মিনিটের জন্য মিউট করা হয়েছে। কারণ: {reason}",
            "user_id": user_id,
            "reason": reason,
            "duration": duration_minutes,
            "ends_at": mute_until.isoformat()
        }
    
    async def check_user_status(self, user_id: int) -> Dict:
        """Check user's ban/mute status"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "banned": False,
                "muted": False,
                "warnings": 0
            }
        
        status = {
            "banned": user.get("is_banned", False),
            "muted": user.get("is_muted", False),
            "warnings": user.get("warning_points", 0),
            "warning_history": len(user.get("warning_history", [])),
            "ban_history": len(user.get("ban_history", [])),
            "last_warning": user.get("last_warning")
        }
        
        # Check if ban has expired
        if status["banned"]:
            ban_until = user.get("ban_until")
            if ban_until:
                try:
                    ban_end = datetime.fromisoformat(ban_until)
                    if datetime.now() > ban_end:
                        # Auto unban
                        await self.unban_user(user_id, 0, "Auto-unban: Ban expired")
                        status["banned"] = False
                except:
                    pass
        
        # Check if mute has expired
        if status["muted"]:
            mute_until = user.get("mute_until")
            if mute_until:
                try:
                    mute_end = datetime.fromisoformat(mute_until)
                    if datetime.now() > mute_end:
                        # Auto unmute
                        self.db.update_user(user_id, {"is_muted": False})
                        status["muted"] = False
                except:
                    pass
        
        return status
    
    async def clear_warnings(self, user_id: int, cleared_by: int, 
                           reason: str = "Good behavior") -> Dict:
        """Clear all warnings for a user"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        points_cleared = user.get("warning_points", 0)
        warnings_cleared = len(user.get("warning_history", []))
        
        # Update user
        user["warning_points"] = 0
        user["warnings_cleared_by"] = cleared_by
        user["warnings_cleared_at"] = datetime.now().isoformat()
        user["warnings_clear_reason"] = reason
        
        self.db.update_user(user_id, {
            "warning_points": 0,
            "warnings_cleared_by": cleared_by,
            "warnings_cleared_at": user["warnings_cleared_at"],
            "warnings_clear_reason": reason
        })
        
        # Log the clearance
        self._log_moderation_action(
            "warnings_cleared",
            cleared_by,
            {
                "target_id": user_id,
                "reason": reason,
                "points_cleared": points_cleared,
                "warnings_cleared": warnings_cleared
            }
        )
        
        return {
            "success": True,
            "message": f"🧹 {user_id} এর {points_cleared} পয়েন্ট ({warnings_cleared}টি সতর্কতা) ক্লিয়ার করা হয়েছে। কারণ: {reason}",
            "points_cleared": points_cleared,
            "warnings_cleared": warnings_cleared,
            "cleared_by": cleared_by
        }
    
    async def get_moderation_logs(self, limit: int = 50, 
                                 filter_type: str = None) -> List[Dict]:
        """Get moderation logs"""
        logs = []
        
        for log in self.moderation_logs:
            if filter_type and log.get("type") != filter_type:
                continue
            
            logs.append(log)
        
        # Also get from database logs
        for log_id, log_data in self.db.logs.items():
            if log_data.get("type", "").startswith("user_"):
                if filter_type and log_data.get("type") != filter_type:
                    continue
                
                logs.append({
                    "id": log_id,
                    "type": log_data.get("type", "unknown"),
                    "moderator_id": log_data.get("user_id"),
                    "timestamp": log_data.get("timestamp", ""),
                    "data": log_data.get("data", {})
                })
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return logs[:limit]
    
    def _log_moderation_action(self, action_type: str, moderator_id: int, data: Dict):
        """Log moderation action"""
        log_entry = {
            "id": f"mod_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": action_type,
            "moderator_id": moderator_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        self.moderation_logs.append(log_entry)
        
        # Keep only last 1000 logs
        if len(self.moderation_logs) > 1000:
            self.moderation_logs = self.moderation_logs[-1000:]
        
        # Also add to database logs
        self.db.add_log(
            action_type,
            f"Moderation action: {action_type}",
            moderator_id,
            data
        )
    
    async def get_moderation_stats(self) -> Dict:
        """Get moderation statistics"""
        total_users = len(self.db.users)
        
        banned_users = 0
        muted_users = 0
        warned_users = 0
        total_warning_points = 0
        
        for user in self.db.users.values():
            if user.get("is_banned", False):
                banned_users += 1
            
            if user.get("is_muted", False):
                muted_users += 1
            
            points = user.get("warning_points", 0)
            if points > 0:
                warned_users += 1
                total_warning_points += points
        
        # Recent moderation actions
        recent_actions = []
        cutoff = datetime.now() - timedelta(days=7)
        
        for log in self.moderation_logs:
            timestamp = datetime.fromisoformat(log.get("timestamp", "2000-01-01"))
            if timestamp > cutoff:
                recent_actions.append(log)
        
        action_types = {}
        for action in recent_actions:
            action_type = action.get("type", "unknown")
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        # Auto-moderation stats
        auto_mod_stats = self.moderation_data["auto_mod_stats"]
        
        return {
            "total_users": total_users,
            "banned_users": banned_users,
            "muted_users": muted_users,
            "warned_users": warned_users,
            "total_warning_points": total_warning_points,
            "recent_actions": len(recent_actions),
            "action_types": action_types,
            "auto_moderation": {
                "messages_checked": auto_mod_stats["messages_checked"],
                "actions_taken": auto_mod_stats["actions_taken"],
                "success_rate": (auto_mod_stats["actions_taken"] / max(auto_mod_stats["messages_checked"], 1)) * 100
            },
            "moderation_queue": len(self.moderation_data["moderation_queue"]),
            "reports_pending": len(self.moderation_data["reports"])
        }
    
    async def add_to_moderation_queue(self, user_id: int, reporter_id: int, 
                                     reason: str, evidence: str = "") -> Dict:
        """Add user to moderation queue"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        queue_entry = {
            "id": f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "user_id": user_id,
            "username": user.get("username", "N/A"),
            "reporter_id": reporter_id,
            "reason": reason,
            "evidence": evidence,
            "status": "PENDING",
            "created_at": datetime.now().isoformat(),
            "priority": "normal"
        }
        
        self.moderation_data["reports"].append(queue_entry)
        
        # Log the report
        self._log_moderation_action(
            "user_reported",
            reporter_id,
            {
                "target_id": user_id,
                "reason": reason,
                "queue_id": queue_entry["id"]
            }
        )
        
        return {
            "success": True,
            "message": f"📋 {user_id} রিপোর্ট করা হয়েছে। কারণ: {reason}",
            "queue_id": queue_entry["id"],
            "priority": queue_entry["priority"]
        }
    
    async def process_moderation_queue(self, admin_id: int, queue_id: str, 
                                      action: str, notes: str = "") -> Dict:
        """Process moderation queue item"""
        # Find the report
        report = None
        report_index = -1
        
        for i, r in enumerate(self.moderation_data["reports"]):
            if r["id"] == queue_id:
                report = r
                report_index = i
                break
        
        if not report:
            return {
                "success": False,
                "message": "রিপোর্ট খুঁজে পাওয়া যায়নি!"
            }
        
        if report["status"] != "PENDING":
            return {
                "success": False,
                "message": f"রিপোর্ট ইতিমধ্যে {report['status']}!"
            }
        
        user_id = report["user_id"]
        
        # Take action based on admin decision
        if action == "warn":
            result = await self.warn_user(
                user_id,
                report["reason"],
                admin_id,
                notes
            )
            status = "WARNED"
        
        elif action == "mute":
            result = await self.mute_user(
                user_id,
                report["reason"],
                admin_id,
                60  # 1 hour mute
            )
            status = "MUTED"
        
        elif action == "ban":
            result = await self.ban_user(
                user_id,
                report["reason"],
                admin_id,
                24  # 1 day ban
            )
            status = "BANNED"
        
        elif action == "dismiss":
            result = {"success": True, "message": "রিপোর্ট ডিসমিস করা হয়েছে।"}
            status = "DISMISSED"
        
        else:
            return {
                "success": False,
                "message": "অজানা একশন!"
            }
        
        if not result["success"]:
            return result
        
        # Update report status
        self.moderation_data["reports"][report_index]["status"] = status
        self.moderation_data["reports"][report_index]["processed_by"] = admin_id
        self.moderation_data["reports"][report_index]["processed_at"] = datetime.now().isoformat()
        self.moderation_data["reports"][report_index]["action_taken"] = action
        self.moderation_data["reports"][report_index]["notes"] = notes
        
        # Log the processing
        self._log_moderation_action(
            "queue_processed",
            admin_id,
            {
                "queue_id": queue_id,
                "action": action,
                "target_id": user_id,
                "reason": report["reason"],
                "status": status
            }
        )
        
        return {
            "success": True,
            "message": f"✅ মডারেশন কিউ প্রসেস করা হয়েছে। একশন: {action}",
            "queue_id": queue_id,
            "action": action,
            "status": status,
            "user_id": user_id
        }
    
    async def get_moderation_queue(self, status: str = "PENDING") -> List[Dict]:
        """Get moderation queue items"""
        queue_items = []
        
        for report in self.moderation_data["reports"]:
            if report["status"] == status:
                queue_items.append(report)
        
        # Sort by creation time (oldest first)
        queue_items.sort(key=lambda x: x.get("created_at", ""))
        
        return queue_items