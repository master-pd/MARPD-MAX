import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
from config import Config
from db import Database
from utils import Utils

class AutoMessager:
    """Advanced Automatic Messaging System v15.0.00"""
    
    def __init__(self, db: Database):
        self.db = db
        self.config = Config()
        self.scheduled_messages = {}
        self.active_campaigns = {}
        self.message_templates = self._load_message_templates()
        self.user_preferences = {}
        
        # Message categories with templates
        self.categories = {
            "greeting": {
                "name": "শুভেচ্ছা বার্তা",
                "emoji": "🌅",
                "enabled": True,
                "frequency": "daily"
            },
            "tip": {
                "name": "টিপস ও পরামর্শ",
                "emoji": "💡",
                "enabled": True,
                "frequency": "daily"
            },
            "reminder": {
                "name": "রিমাইন্ডার",
                "emoji": "⏰",
                "enabled": True,
                "frequency": "weekly"
            },
            "promotion": {
                "name": "প্রোমোশন",
                "emoji": "🎁",
                "enabled": True,
                "frequency": "weekly"
            },
            "birthday": {
                "name": "জন্মদিন",
                "emoji": "🎂",
                "enabled": True,
                "frequency": "on_date"
            },
            "achievement": {
                "name": "অর্জন",
                "emoji": "🏆",
                "enabled": True,
                "frequency": "on_event"
            }
        }
        
        # Time slots for different message types
        self.time_slots = {
            "morning": {"start": 6, "end": 10, "category": "greeting"},
            "afternoon": {"start": 12, "end": 14, "category": "tip"},
            "evening": {"start": 17, "end": 19, "category": "reminder"},
            "night": {"start": 21, "end": 23, "category": "promotion"}
        }
        
        print("🤖 Auto Messager v15.0.00 Initialized")
    
    def _load_message_templates(self) -> Dict:
        """Load message templates"""
        return {
            "greetings": [
                {
                    "text": "সুপ্রভাত {name}! 🌅 নতুন দিনের শুরুতে আপনার জন্য শুভকামনা।",
                    "variables": ["name"],
                    "emoji": "🌅"
                },
                {
                    "text": "শুভ সকাল {name}! ☀️ আজকের দিনটি আপনার জন্য সুন্দর ও সফল হোক।",
                    "variables": ["name"],
                    "emoji": "☀️"
                },
                {
                    "text": "হ্যালো {name}! 🤗 আশা করি ভালো আছেন। আজকের দিনটি আনন্দময় হোক।",
                    "variables": ["name"],
                    "emoji": "🤗"
                }
            ],
            "tips": [
                {
                    "text": "💡 টিপ: প্রতিদিন /daily কমান্ড দিয়ে ডেইলি বোনাস নিন!",
                    "variables": [],
                    "emoji": "💡"
                },
                {
                    "text": "💰 টিপ: গেম খেলে আরও কয়েন জিতুন! আজই /games কমান্ড ট্রাই করুন।",
                    "variables": [],
                    "emoji": "💰"
                },
                {
                    "text": "🛍️ টিপ: শপ থেকে বিশেষ আইটেম কিনে আপনার এক্সপিরিয়েন্স বাড়ান!",
                    "variables": [],
                    "emoji": "🛍️"
                },
                {
                    "text": "👥 টিপ: বন্ধুদের রেফার করুন এবং অতিরিক্ত বোনাস পান!",
                    "variables": [],
                    "emoji": "👥"
                },
                {
                    "text": "⚡ টিপ: অ্যাকটিভ থাকলে এক্সট্রা বোনাস পান!",
                    "variables": [],
                    "emoji": "⚡"
                },
                {
                    "text": "🧠 টিপ: কুইজ গেমে অংশ নিয়ে আপনার জ্ঞান পরীক্ষা করুন!",
                    "variables": [],
                    "emoji": "🧠"
                }
            ],
            "reminders": [
                {
                    "text": "👋 আমরা আপনাকে মিস করছি! আপনি {days} দিন অ্যাকটিভ নেই। আসুন আবার গেম খেলি!",
                    "variables": ["days"],
                    "emoji": "👋"
                },
                {
                    "text": "💰 আপনার ডেইলি বোনাস অপেক্ষা করছে! /daily কমান্ড দিন।",
                    "variables": [],
                    "emoji": "💰"
                },
                {
                    "text": "🎮 গেম খেলতে ভুলে গেছেন? আসুন এখনই কিছু গেম খেলি!",
                    "variables": [],
                    "emoji": "🎮"
                },
                {
                    "text": "🛍️ শপে নতুন আইটেম যোগ হয়েছে! এখনই দেখে নিন।",
                    "variables": [],
                    "emoji": "🛍️"
                }
            ],
            "promotions": [
                {
                    "text": "🔥 **নতুন গেম আসছে!** শীঘ্রই এক্সাইটিং গেম যোগ হবে!",
                    "variables": [],
                    "emoji": "🔥"
                },
                {
                    "text": "🎉 **স্পেশাল অফার!** সীমিত সময়ের জন্য ২x কয়েন!",
                    "variables": [],
                    "emoji": "🎉"
                },
                {
                    "text": "🏆 **লিডারবোর্ড কন্টেস্ট!** শীর্ষ ১০ জন পাবে পুরস্কার!",
                    "variables": [],
                    "emoji": "🏆"
                },
                {
                    "text": "🛒 **নতুন আইটেম!** শপে এক্সক্লুসিভ আইটেম যোগ হয়েছে!",
                    "variables": [],
                    "emoji": "🛒"
                },
                {
                    "text": "🤝 **রেফার প্রোগ্রাম!** বন্ধুকে রেফার করে ২০০ কয়েন বোনাস!",
                    "variables": [],
                    "emoji": "🤝"
                }
            ],
            "birthdays": [
                {
                    "text": "🎉 **শুভ জন্মদিন {name}!** 🎂\n\nআপনার বিশেষ দিনে অগ্রীম শুভেচ্ছা!\nআপনার জীবন সুখ, শান্তি ও সাফল্যে পূর্ণ হোক!\n\n🎁 **জন্মদিন উপহার:** 500 কয়েন!",
                    "variables": ["name"],
                    "emoji": "🎉"
                }
            ],
            "achievements": [
                {
                    "text": "🏆 **অভিনন্দন {name}!**\nআপনি লেভেল {level} এ পৌঁছেছেন!\n\nজয়ন্তী উপহার: {coins} কয়েন!",
                    "variables": ["name", "level", "coins"],
                    "emoji": "🏆"
                },
                {
                    "text": "🔥 **স্ট্রীক রেকর্ড!**\nআপনি {days} দিন ধরে ডেইলি বোনাস নিয়েছেন!\nঅভিনন্দন!",
                    "variables": ["days"],
                    "emoji": "🔥"
                }
            ]
        }
    
    async def schedule_daily_greeting(self, user_id: int) -> Dict:
        """Schedule daily greeting for user"""
        user = self.db.get_user(user_id)
        if not user:
            return {"success": False, "message": "ইউজার খুঁজে পাওয়া যায়নি!"}
        
        # Get user's preferred time (if set)
        user_prefs = self.user_preferences.get(user_id, {})
        preferred_time = user_prefs.get("greeting_time")
        
        if preferred_time:
            # Use user's preferred time
            hour, minute = map(int, preferred_time.split(":"))
        else:
            # Random time between 8 AM to 10 AM
            hour = random.randint(8, 10)
            minute = random.randint(0, 59)
        
        schedule_time = f"{hour:02d}:{minute:02d}"
        
        if user_id not in self.scheduled_messages:
            self.scheduled_messages[user_id] = []
        
        # Check if already scheduled
        existing = next((m for m in self.scheduled_messages[user_id] 
                        if m["type"] == "greeting"), None)
        
        if existing:
            existing["time"] = schedule_time
            existing["next_send"] = self._calculate_next_send(hour, minute)
            message = f"🔄 শুভেচ্ছা বার্তার সময় আপডেট করা হয়েছে: {schedule_time}"
        else:
            schedule_entry = {
                "type": "greeting",
                "category": "greeting",
                "time": schedule_time,
                "next_send": self._calculate_next_send(hour, minute),
                "enabled": True,
                "created_at": datetime.now().isoformat(),
                "last_sent": None
            }
            
            self.scheduled_messages[user_id].append(schedule_entry)
            message = f"✅ দৈনিক শুভেচ্ছা বার্তা শিডিউল করা হয়েছে: {schedule_time}"
        
        return {
            "success": True,
            "message": message,
            "schedule_time": schedule_time,
            "next_send": self.scheduled_messages[user_id][-1]["next_send"]
        }
    
    def _calculate_next_send(self, hour: int, minute: int) -> str:
        """Calculate next send time"""
        now = datetime.now()
        next_send = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time already passed today, schedule for tomorrow
        if next_send < now:
            next_send += timedelta(days=1)
        
        return next_send.isoformat()
    
    async def send_scheduled_message(self, user_id: int, message_type: str) -> Optional[str]:
        """Send scheduled message to user"""
        user = self.db.get_user(user_id)
        if not user:
            return None
        
        # Check user preferences
        user_prefs = self.user_preferences.get(user_id, {})
        if not user_prefs.get("notifications", True):
            return None  # User has disabled notifications
        
        # Get message based on type
        message = None
        
        if message_type == "greeting":
            message = await self._get_greeting_message(user)
        elif message_type == "tip":
            message = await self._get_tip_message(user)
        elif message_type == "reminder":
            message = await self._get_reminder_message(user)
        elif message_type == "promotion":
            message = await self._get_promotion_message()
        elif message_type == "birthday":
            message = await self._get_birthday_message(user)
        
        # Update last sent time
        if user_id in self.scheduled_messages:
            for msg in self.scheduled_messages[user_id]:
                if msg["type"] == message_type:
                    msg["last_sent"] = datetime.now().isoformat()
                    msg["next_send"] = self._calculate_next_send(
                        int(msg["time"].split(":")[0]),
                        int(msg["time"].split(":")[1])
                    )
                    break
        
        return message
    
    async def _get_greeting_message(self, user: Dict) -> str:
        """Get greeting message for user"""
        template = random.choice(self.message_templates["greetings"])
        message = template["text"]
        
        # Replace variables
        if "{name}" in message:
            message = message.replace("{name}", user.get("first_name", "বন্ধু"))
        
        # Add daily bonus reminder
        message += f"\n\n💰 **ডেইলি বোনাস নিতে ভুলবেন না!** /daily"
        
        return message
    
    async def _get_tip_message(self, user: Dict) -> str:
        """Get tip message"""
        template = random.choice(self.message_templates["tips"])
        return template["text"]
    
    async def _get_reminder_message(self, user: Dict) -> Optional[str]:
        """Get reminder message for inactive users"""
        last_active = user.get("last_active")
        if not last_active:
            return None
        
        try:
            last_active_time = datetime.fromisoformat(last_active)
            days_inactive = (datetime.now() - last_active_time).days
            
            if days_inactive >= 2:
                template = random.choice(self.message_templates["reminders"])
                message = template["text"]
                
                if "{days}" in message:
                    message = message.replace("{days}", str(days_inactive))
                
                # Add bonus offer
                bonus_amount = min(days_inactive * 50, 500)
                message += f"\n\n🎁 **রিটার্নিং বোনাস:** {bonus_amount} কয়েন!\nশুধু /daily কমান্ড দিন।"
                
                return message
        
        except:
            return None
        
        return None
    
    async def _get_promotion_message(self) -> str:
        """Get promotion message"""
        template = random.choice(self.message_templates["promotions"])
        return template["text"]
    
    async def _get_birthday_message(self, user: Dict) -> Optional[str]:
        """Get birthday message"""
        # Check if today is user's birthday
        # This is a placeholder - in production, you'd check user's birthday field
        today = datetime.now().strftime("%m-%d")
        
        # Simulate birthday check
        is_birthday = random.random() < 0.01  # 1% chance for demo
        
        if is_birthday:
            template = random.choice(self.message_templates["birthdays"])
            message = template["text"]
            
            if "{name}" in message:
                message = message.replace("{name}", user.get("first_name", "বন্ধু"))
            
            # Add birthday bonus to user
            user["coins"] = user.get("coins", 0) + 500
            self.db.update_user(user["id"], {"coins": user["coins"]})
            
            return message
        
        return None
    
    async def check_birthdays(self) -> List[int]:
        """Check for user birthdays (placeholder)"""
        # In production, you would check user's birthday field
        # For now, return empty list
        return []
    
    async def send_achievement_message(self, user_id: int, achievement_type: str, 
                                      data: Dict = None) -> str:
        """Send achievement message"""
        user = self.db.get_user(user_id)
        if not user:
            return ""
        
        data = data or {}
        
        if achievement_type == "level_up":
            template = self.message_templates["achievements"][0]
            message = template["text"]
            
            # Replace variables
            message = message.replace("{name}", user.get("first_name", "বন্ধু"))
            message = message.replace("{level}", str(data.get("level", 1)))
            message = message.replace("{coins}", str(data.get("coins", 100)))
            
        elif achievement_type == "streak":
            template = self.message_templates["achievements"][1]
            message = template["text"]
            message = message.replace("{days}", str(data.get("days", 7)))
        
        else:
            return ""
        
        return message
    
    async def create_campaign(self, name: str, message: str, target_users: List[int],
                             schedule_time: str = None) -> Dict:
        """Create message campaign"""
        campaign_id = f"campaign_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        campaign = {
            "id": campaign_id,
            "name": name,
            "message": message,
            "target_users": target_users,
            "total_users": len(target_users),
            "sent_count": 0,
            "failed_count": 0,
            "status": "SCHEDULED",
            "created_at": datetime.now().isoformat(),
            "scheduled_for": schedule_time or datetime.now().isoformat(),
            "completed_at": None
        }
        
        self.active_campaigns[campaign_id] = campaign
        
        # Schedule if future time
        if schedule_time:
            try:
                schedule_time_obj = datetime.fromisoformat(schedule_time)
                if schedule_time_obj > datetime.now():
                    # Schedule for future
                    delay = (schedule_time_obj - datetime.now()).total_seconds()
                    asyncio.create_task(self._execute_campaign(campaign_id, delay))
                else:
                    # Execute immediately
                    asyncio.create_task(self._execute_campaign(campaign_id))
            except:
                # Execute immediately on error
                asyncio.create_task(self._execute_campaign(campaign_id))
        else:
            # Execute immediately
            asyncio.create_task(self._execute_campaign(campaign_id))
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "message": f"✅ ক্যাম্পেইন তৈরি হয়েছে: {name} ({len(target_users)} জন ইউজার)",
            "campaign": campaign
        }
    
    async def _execute_campaign(self, campaign_id: str, delay: float = 0):
        """Execute campaign"""
        if delay > 0:
            await asyncio.sleep(delay)
        
        campaign = self.active_campaigns.get(campaign_id)
        if not campaign or campaign["status"] != "SCHEDULED":
            return
        
        campaign["status"] = "RUNNING"
        campaign["started_at"] = datetime.now().isoformat()
        
        print(f"🚀 Executing campaign: {campaign['name']}")
        
        # Send to all target users
        for user_id in campaign["target_users"]:
            try:
                # In production, you would send actual message here
                # For now, just simulate
                await asyncio.sleep(0.1)  # Small delay to prevent rate limiting
                
                campaign["sent_count"] += 1
                
                # Log each send
                self.db.add_log(
                    "campaign_message",
                    f"Campaign message sent: {campaign['name']}",
                    user_id,
                    {"campaign_id": campaign_id, "user_id": user_id}
                )
                
            except Exception as e:
                campaign["failed_count"] += 1
                print(f"❌ Failed to send to {user_id}: {e}")
        
        campaign["status"] = "COMPLETED"
        campaign["completed_at"] = datetime.now().isoformat()
        
        print(f"✅ Campaign completed: {campaign['name']} - "
              f"Sent: {campaign['sent_count']}, Failed: {campaign['failed_count']}")
    
    async def get_campaign_stats(self, campaign_id: str = None) -> Dict:
        """Get campaign statistics"""
        if campaign_id:
            campaign = self.active_campaigns.get(campaign_id)
            if not campaign:
                return {"success": False, "message": "ক্যাম্পেইন খুঁজে পাওয়া যায়নি!"}
            
            return {
                "success": True,
                "campaign": campaign,
                "success_rate": (campaign["sent_count"] / max(campaign["total_users"], 1)) * 100
            }
        
        # Overall stats
        total_campaigns = len(self.active_campaigns)
        active_campaigns = sum(1 for c in self.active_campaigns.values() 
                              if c["status"] == "RUNNING")
        completed_campaigns = sum(1 for c in self.active_campaigns.values() 
                                 if c["status"] == "COMPLETED")
        
        total_sent = sum(c["sent_count"] for c in self.active_campaigns.values())
        total_failed = sum(c["failed_count"] for c in self.active_campaigns.values())
        total_targets = sum(c["total_users"] for c in self.active_campaigns.values())
        
        return {
            "success": True,
            "stats": {
                "total_campaigns": total_campaigns,
                "active_campaigns": active_campaigns,
                "completed_campaigns": completed_campaigns,
                "total_sent": total_sent,
                "total_failed": total_failed,
                "total_targets": total_targets,
                "success_rate": (total_sent / max(total_targets, 1)) * 100,
                "average_users_per_campaign": total_targets / max(total_campaigns, 1)
            },
            "recent_campaigns": list(self.active_campaigns.values())[-5:]  # Last 5 campaigns
        }
    
    async def schedule_all_tasks(self):
        """Schedule all automated tasks"""
        print("⏰ Scheduling automated messages...")
        
        # Schedule daily tasks
        schedule.every().day.at("08:00").do(self._morning_greetings)
        schedule.every().day.at("12:00").do(self._noon_tips)
        schedule.every().day.at("18:00").do(self._evening_reminders)
        schedule.every().day.at("21:00").do(self._night_promotions)
        
        # Schedule weekly tasks
        schedule.every().monday.at("10:00").do(self._weekly_summary)
        schedule.every().sunday.at("23:00").do(self._weekly_cleanup)
        
        # Schedule hourly checks
        schedule.every().hour.do(self._check_inactive_users)
        schedule.every(30).minutes.do(self._check_birthdays_task)
        
        print("✅ Automated messages scheduled!")
    
    def _morning_greetings(self):
        """Morning greetings task"""
        print(f"[{datetime.now()}] 🌅 Sending morning greetings...")
        # In production, this would send to all users
    
    def _noon_tips(self):
        """Noon tips task"""
        print(f"[{datetime.now()}] ☀️ Sending noon tips...")
    
    def _evening_reminders(self):
        """Evening reminders task"""
        print(f"[{datetime.now()}] 🌇 Sending evening reminders...")
    
    def _night_promotions(self):
        """Night promotions task"""
        print(f"[{datetime.now()}] 🌙 Sending night promotions...")
    
    def _weekly_summary(self):
        """Weekly summary task"""
        print(f"[{datetime.now()}] 📊 Sending weekly summary...")
    
    def _weekly_cleanup(self):
        """Weekly cleanup task"""
        print(f"[{datetime.now()}] 🧹 Running weekly cleanup...")
    
    def _check_inactive_users(self):
        """Check inactive users task"""
        print(f"[{datetime.now()}] 👥 Checking inactive users...")
    
    def _check_birthdays_task(self):
        """Check birthdays task"""
        print(f"[{datetime.now()}] 🎂 Checking birthdays...")
    
    async def set_user_preferences(self, user_id: int, preferences: Dict) -> Dict:
        """Set user message preferences"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}
        
        self.user_preferences[user_id].update(preferences)
        
        # Update greeting schedule if time preference changed
        if "greeting_time" in preferences:
            await self.schedule_daily_greeting(user_id)
        
        return {
            "success": True,
            "message": "✅ বার্তা প্রেফারেন্স আপডেট করা হয়েছে!",
            "preferences": self.user_preferences[user_id]
        }
    
    async def get_user_preferences(self, user_id: int) -> Dict:
        """Get user message preferences"""
        default_prefs = {
            "notifications": True,
            "greeting_messages": True,
            "tip_messages": True,
            "reminder_messages": True,
            "promotion_messages": True,
            "birthday_messages": True,
            "achievement_messages": True,
            "greeting_time": "09:00"
        }
        
        user_prefs = self.user_preferences.get(user_id, {})
        
        # Merge with defaults
        merged_prefs = default_prefs.copy()
        merged_prefs.update(user_prefs)
        
        return {
            "success": True,
            "preferences": merged_prefs,
            "categories": self.categories
        }
    
    async def get_message_stats(self) -> Dict:
        """Get message statistics"""
        total_users = len(self.db.users)
        users_with_schedules = len(self.scheduled_messages)
        
        # Calculate scheduled messages by type
        scheduled_by_type = {}
        for user_msgs in self.scheduled_messages.values():
            for msg in user_msgs:
                msg_type = msg["type"]
                scheduled_by_type[msg_type] = scheduled_by_type.get(msg_type, 0) + 1
        
        # Calculate delivery stats (simulated)
        today = datetime.now().strftime("%Y-%m-%d")
        deliveries_today = random.randint(50, 200)  # Simulated
        failures_today = random.randint(0, 10)      # Simulated
        
        return {
            "total_users": total_users,
            "users_with_schedules": users_with_schedules,
            "coverage_percentage": (users_with_schedules / max(total_users, 1)) * 100,
            "scheduled_by_type": scheduled_by_type,
            "deliveries_today": deliveries_today,
            "failures_today": failures_today,
            "success_rate_today": (deliveries_today / max(deliveries_today + failures_today, 1)) * 100,
            "active_campaigns": len([c for c in self.active_campaigns.values() 
                                    if c["status"] == "RUNNING"]),
            "user_preferences_set": len(self.user_preferences)
        }
    
    def run_scheduler(self):
        """Run the scheduler in background"""
        print("⏳ Starting message scheduler...")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    async def cleanup_old_data(self, days_old: int = 30):
        """Cleanup old data"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0
        
        # Clean old scheduled messages
        for user_id in list(self.scheduled_messages.keys()):
            user_msgs = self.scheduled_messages[user_id]
            initial_count = len(user_msgs)
            
            # Remove messages not sent in last 30 days
            self.scheduled_messages[user_id] = [
                msg for msg in user_msgs
                if msg.get("last_sent") and 
                datetime.fromisoformat(msg["last_sent"]) > cutoff_date
            ]
            
            cleaned_count += initial_count - len(self.scheduled_messages[user_id])
            
            # Remove user entry if empty
            if not self.scheduled_messages[user_id]:
                del self.scheduled_messages[user_id]
        
        # Clean old campaigns
        campaign_ids_to_remove = []
        for campaign_id, campaign in self.active_campaigns.items():
            completed_at = campaign.get("completed_at")
            if completed_at:
                completed_date = datetime.fromisoformat(completed_at)
                if completed_date < cutoff_date:
                    campaign_ids_to_remove.append(campaign_id)
        
        for campaign_id in campaign_ids_to_remove:
            del self.active_campaigns[campaign_id]
            cleaned_count += 1
        
        print(f"🧹 Cleaned {cleaned_count} old auto-messager data entries")
        return cleaned_count