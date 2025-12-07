import schedule
import time
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from config import Config
from db import Database

class TaskScheduler:
    """Advanced Background Task Scheduler v15.0.00"""
    
    def __init__(self, db: Database):
        self.db = db
        self.config = Config()
        self.running = False
        self.thread = None
        self.task_queue = asyncio.Queue()
        self.completed_tasks = []
        
        # Task registry with metadata
        self.tasks = {
            "daily_reset": {
                "function": self.daily_reset,
                "schedule": "00:00",
                "enabled": True,
                "last_run": None,
                "next_run": None,
                "execution_time": 0,
                "success_count": 0,
                "fail_count": 0,
                "description": "দৈনিক রিসেট ও ক্লিনআপ",
                "category": "maintenance",
                "priority": "high"
            },
            "weekly_reset": {
                "function": self.weekly_reset,
                "schedule": "00:00",
                "enabled": True,
                "last_run": None,
                "next_run": None,
                "execution_time": 0,
                "success_count": 0,
                "fail_count": 0,
                "description": "সাপ্তাহিক রিসেট ও রিপোর্ট",
                "category": "maintenance",
                "priority": "high"
            },
            "backup": {
                "function": self.backup_task,
                "schedule": "03:00",
                "enabled": True,
                "last_run": None,
                "next_run": None,
                "execution_time": 0,
                "success_count": 0,
                "fail_count": 0,
                "description": "ডাটাবেস ব্যাকআপ",
                "category": "backup",
                "priority": "critical"
            },
            "cleanup": {
                "function": self.cleanup_task,
                "schedule": "04:00",
                "enabled": True,
                "last_run": None,
                "next_run": None,
                "execution_time": 0,
                "success_count": 0,
                "fail_count": 0,
                "description": "পুরনো ডাটা ক্লিনআপ",
                "category": "maintenance",
                "priority": "medium"
            },
            "notifications": {
                "function": self.notification_task,
                "schedule": "09:00",
                "enabled": True,
                "last_run": None,
                "next_run": None,
                "execution_time": 0,
                "success_count": 0,
                "fail_count": 0,
                "description": "ডেইলি নোটিফিকেশন",
                "category": "communication",
                "priority": "medium"
            },
            "statistics": {
                "function": self.statistics_task,
                "schedule": "12:00",
                "enabled": True,
                "last_run": None,
                "next_run": None,
                "execution_time": 0,
                "success_count": 0,
                "fail_count": 0,
                "description": "পরিসংখ্যান আপডেট",
                "category": "analytics",
                "priority": "low"
            },
            "health_check": {
                "function": self.health_check_task,
                "schedule": "*/30",  # Every 30 minutes
                "enabled": True,
                "last_run": None,
                "next_run": None,
                "execution_time": 0,
                "success_count": 0,
                "fail_count": 0,
                "description": "সিস্টেম হেলথ চেক",
                "category": "monitoring",
                "priority": "high"
            }
        }
        
        # Task dependencies
        self.dependencies = {
            "weekly_reset": ["daily_reset"],
            "backup": ["cleanup"],
            "notifications": ["statistics"]
        }
        
        print("⏰ Advanced Task Scheduler v15.0.00 Initialized")
    
    async def daily_reset(self):
        """Daily reset task - reset daily limits and counters"""
        start_time = datetime.now()
        print(f"[{start_time}] 🔄 Running daily reset...")
        
        try:
            # Reset user daily limits
            reset_count = 0
            for user_id_str, user_data in self.db.users.items():
                # Reset daily game limits
                if "daily_games" in user_data:
                    user_data["daily_games"] = 0
                    reset_count += 1
            
            # Update daily statistics
            today = datetime.now().strftime("%Y-%m-%d")
            if "daily_stats" not in self.db.stats:
                self.db.stats["daily_stats"] = {}
            
            self.db.stats["daily_stats"][today] = {
                "date": today,
                "new_users": 0,  # Will be updated during the day
                "reset_at": start_time.isoformat(),
                "users_reset": reset_count
            }
            
            self.db._save_data("stats", self.db.stats)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.tasks["daily_reset"]["execution_time"] = execution_time
            self.tasks["daily_reset"]["success_count"] += 1
            self.tasks["daily_reset"]["last_run"] = start_time.isoformat()
            
            print(f"[{datetime.now()}] ✅ Daily reset completed - {reset_count} users reset "
                  f"({execution_time:.2f}s)")
            
        except Exception as e:
            self.tasks["daily_reset"]["fail_count"] += 1
            print(f"[{datetime.now()}] ❌ Daily reset failed: {e}")
    
    async def weekly_reset(self):
        """Weekly reset task - reset weekly leaderboard and stats"""
        start_time = datetime.now()
        today = datetime.now()
        
        # Only run on Monday
        if today.weekday() != 0:  # 0 = Monday
            print(f"[{start_time}] 📅 Skipping weekly reset (not Monday)")
            return
        
        print(f"[{start_time}] 🔄 Running weekly reset...")
        
        try:
            # Reset weekly leaderboard
            if "weekly_leaderboard" in self.db.stats:
                # Archive current leaderboard
                week_key = f"week_{today.strftime('%Y-%W')}"
                if "leaderboard_history" not in self.db.stats:
                    self.db.stats["leaderboard_history"] = {}
                
                self.db.stats["leaderboard_history"][week_key] = {
                    "week": week_key,
                    "data": self.db.stats["weekly_leaderboard"],
                    "reset_at": start_time.isoformat()
                }
                
                # Reset for new week
                self.db.stats["weekly_leaderboard"] = {}
            
            # Reset weekly user stats
            reset_count = 0
            for user_id_str, user_data in self.db.users.items():
                # Reset weekly counters
                if "weekly_games" in user_data:
                    user_data["weekly_games"] = 0
                    reset_count += 1
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.tasks["weekly_reset"]["execution_time"] = execution_time
            self.tasks["weekly_reset"]["success_count"] += 1
            self.tasks["weekly_reset"]["last_run"] = start_time.isoformat()
            
            print(f"[{datetime.now()}] ✅ Weekly reset completed - {reset_count} users reset "
                  f"({execution_time:.2f}s)")
            
        except Exception as e:
            self.tasks["weekly_reset"]["fail_count"] += 1
            print(f"[{datetime.now()}] ❌ Weekly reset failed: {e}")
    
    async def backup_task(self):
        """Backup task - create database backup"""
        start_time = datetime.now()
        print(f"[{start_time}] 💾 Running backup...")
        
        try:
            # Create backup
            backup_file = self.db.create_backup()
            
            if backup_file:
                # Update stats
                if "backup_stats" not in self.db.stats:
                    self.db.stats["backup_stats"] = []
                
                backup_stats = {
                    "timestamp": start_time.isoformat(),
                    "file": backup_file,
                    "size": "N/A",
                    "users_backed_up": len(self.db.users)
                }
                
                self.db.stats["backup_stats"].append(backup_stats)
                
                # Keep only last 10 backup entries
                if len(self.db.stats["backup_stats"]) > 10:
                    self.db.stats["backup_stats"] = self.db.stats["backup_stats"][-10:]
                
                self.db._save_data("stats", self.db.stats)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                self.tasks["backup"]["execution_time"] = execution_time
                self.tasks["backup"]["success_count"] += 1
                self.tasks["backup"]["last_run"] = start_time.isoformat()
                
                print(f"[{datetime.now()}] ✅ Backup completed ({execution_time:.2f}s)")
            else:
                raise Exception("Backup file not created")
                
        except Exception as e:
            self.tasks["backup"]["fail_count"] += 1
            print(f"[{datetime.now()}] ❌ Backup failed: {e}")
    
    async def cleanup_task(self):
        """Cleanup task - remove old data"""
        start_time = datetime.now()
        print(f"[{start_time}] 🧹 Running cleanup...")
        
        try:
            cleaned_count = 0
            
            # Clean old game history (older than 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            game_keys_to_remove = []
            
            for game_key, game_data in self.db.game_history.items():
                timestamp = game_data.get("timestamp")
                if timestamp:
                    game_date = datetime.fromisoformat(timestamp)
                    if game_date < cutoff_date:
                        game_keys_to_remove.append(game_key)
            
            for key in game_keys_to_remove:
                del self.db.game_history[key]
                cleaned_count += 1
            
            # Clean old logs (older than 7 days)
            log_keys_to_remove = []
            for log_key, log_data in self.db.logs.items():
                timestamp = log_data.get("timestamp")
                if timestamp:
                    log_date = datetime.fromisoformat(timestamp)
                    if log_date < cutoff_date - timedelta(days=23):  # 30-7
                        log_keys_to_remove.append(log_key)
            
            for key in log_keys_to_remove:
                del self.db.logs[key]
                cleaned_count += 1
            
            # Save cleaned data
            self.db._save_data("games", self.db.game_history)
            self.db._save_data("logs", self.db.logs)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.tasks["cleanup"]["execution_time"] = execution_time
            self.tasks["cleanup"]["success_count"] += 1
            self.tasks["cleanup"]["last_run"] = start_time.isoformat()
            
            print(f"[{datetime.now()}] ✅ Cleanup completed - {cleaned_count} items removed "
                  f"({execution_time:.2f}s)")
            
        except Exception as e:
            self.tasks["cleanup"]["fail_count"] += 1
            print(f"[{datetime.now()}] ❌ Cleanup failed: {e}")
    
    async def notification_task(self):
        """Notification task - send scheduled notifications"""
        start_time = datetime.now()
        print(f"[{start_time}] 📢 Running notification task...")
        
        try:
            # This would send notifications in production
            # For now, just simulate
            await asyncio.sleep(1)  # Simulate work
            
            # Update user last notification time
            updated_count = 0
            for user_id_str, user_data in self.db.users.items():
                # Check if user should receive notifications
                last_notification = user_data.get("last_notification")
                if not last_notification:
                    # First notification
                    user_data["last_notification"] = start_time.isoformat()
                    updated_count += 1
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.tasks["notifications"]["execution_time"] = execution_time
            self.tasks["notifications"]["success_count"] += 1
            self.tasks["notifications"]["last_run"] = start_time.isoformat()
            
            print(f"[{datetime.now()}] ✅ Notifications sent - {updated_count} users updated "
                  f"({execution_time:.2f}s)")
            
        except Exception as e:
            self.tasks["notifications"]["fail_count"] += 1
            print(f"[{datetime.now()}] ❌ Notifications failed: {e}")
    
    async def statistics_task(self):
        """Statistics task - update statistics"""
        start_time = datetime.now()
        print(f"[{start_time}] 📊 Running statistics task...")
        
        try:
            # Calculate daily statistics
            today = datetime.now().strftime("%Y-%m-%d")
            
            if "daily_stats" not in self.db.stats:
                self.db.stats["daily_stats"] = {}
            
            if today not in self.db.stats["daily_stats"]:
                self.db.stats["daily_stats"][today] = {
                    "date": today,
                    "new_users": 0,
                    "active_users": 0,
                    "games_played": 0,
                    "transactions": 0
                }
            
            # Update today's stats
            today_stats = self.db.stats["daily_stats"][today]
            
            # Count new users (joined today)
            new_users = 0
            for user_data in self.db.users.values():
                joined = user_data.get("first_seen", "")
                if joined.startswith(today):
                    new_users += 1
            
            today_stats["new_users"] = new_users
            today_stats["updated_at"] = start_time.isoformat()
            
            # Calculate active users (active in last 24 hours)
            cutoff = datetime.now() - timedelta(hours=24)
            active_users = 0
            for user_data in self.db.users.values():
                last_active = datetime.fromisoformat(user_data.get("last_active", "2000-01-01"))
                if last_active > cutoff:
                    active_users += 1
            
            today_stats["active_users"] = active_users
            
            # Count today's games
            today_games = 0
            for game_data in self.db.game_history.values():
                timestamp = game_data.get("timestamp", "")
                if timestamp.startswith(today):
                    today_games += 1
            
            today_stats["games_played"] = today_games
            
            # Count today's transactions
            today_transactions = 0
            for payment in self.db.payments.values():
                created_at = payment.get("created_at", "")
                if created_at.startswith(today):
                    today_transactions += 1
            
            today_stats["transactions"] = today_transactions
            
            self.db._save_data("stats", self.db.stats)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.tasks["statistics"]["execution_time"] = execution_time
            self.tasks["statistics"]["success_count"] += 1
            self.tasks["statistics"]["last_run"] = start_time.isoformat()
            
            print(f"[{datetime.now()}] ✅ Statistics updated - "
                  f"New: {new_users}, Active: {active_users}, Games: {today_games} "
                  f"({execution_time:.2f}s)")
            
        except Exception as e:
            self.tasks["statistics"]["fail_count"] += 1
            print(f"[{datetime.now()}] ❌ Statistics failed: {e}")
    
    async def health_check_task(self):
        """Health check task - monitor system health"""
        start_time = datetime.now()
        
        try:
            # Check database health
            db_status = "OK"
            if not self.db.users:
                db_status = "EMPTY"
            elif len(self.db.users) == 0:
                db_status = "ERROR"
            
            # Check task health
            task_health = {}
            for task_name, task_info in self.tasks.items():
                if task_info["enabled"]:
                    last_run = task_info.get("last_run")
                    if last_run:
                        last_run_time = datetime.fromisoformat(last_run)
                        hours_since_run = (datetime.now() - last_run_time).total_seconds() / 3600
                        
                        if hours_since_run > 24:
                            task_health[task_name] = "STALE"
                        else:
                            task_health[task_name] = "OK"
                    else:
                        task_health[task_name] = "NEVER_RUN"
                else:
                    task_health[task_name] = "DISABLED"
            
            # Check memory usage (simulated)
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # Update health stats
            if "health_stats" not in self.db.stats:
                self.db.stats["health_stats"] = []
            
            health_entry = {
                "timestamp": start_time.isoformat(),
                "db_status": db_status,
                "memory_mb": memory_mb,
                "total_users": len(self.db.users),
                "task_health": task_health,
                "uptime_seconds": (datetime.now() - datetime.fromisoformat(
                    self.db.stats.get("start_time", start_time.isoformat())
                )).total_seconds()
            }
            
            self.db.stats["health_stats"].append(health_entry)
            
            # Keep only last 100 health entries
            if len(self.db.stats["health_stats"]) > 100:
                self.db.stats["health_stats"] = self.db.stats["health_stats"][-100:]
            
            self.db._save_data("stats", self.db.stats)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.tasks["health_check"]["execution_time"] = execution_time
            self.tasks["health_check"]["success_count"] += 1
            self.tasks["health_check"]["last_run"] = start_time.isoformat()
            
            # Log only if there are issues
            if db_status != "OK" or memory_mb > 100:  > 100MB is high
                print(f"[{datetime.now()}] ⚠️ Health check - DB: {db_status}, "
                      f"Memory: {memory_mb:.1f}MB ({execution_time:.2f}s)")
            
        except Exception as e:
            self.tasks["health_check"]["fail_count"] += 1
            print(f"[{datetime.now()}] ❌ Health check failed: {e}")
    
    def setup_schedule(self):
        """Setup scheduled tasks"""
        print("⏰ Setting up scheduled tasks...")
        
        # Schedule all tasks
        for task_name, task_info in self.tasks.items():
            if task_info["enabled"]:
                schedule_str = task_info["schedule"]
                
                if schedule_str == "*/30":  # Every 30 minutes
                    schedule.every(30).minutes.do(
                        self._run_task_wrapper, task_name
                    )
                else:
                    # Parse time like "HH:MM"
                    try:
                        hour, minute = map(int, schedule_str.split(":"))
                        
                        if task_name == "weekly_reset":
                            schedule.every().monday.at(f"{hour:02d}:{minute:02d}").do(
                                self._run_task_wrapper, task_name
                            )
                        else:
                            schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(
                                self._run_task_wrapper, task_name
                            )
                        
                        # Calculate next run time
                        now = datetime.now()
                        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        if next_run < now:
                            if task_name == "weekly_reset":
                                next_run += timedelta(days=(7 - now.weekday()))
                            else:
                                next_run += timedelta(days=1)
                        
                        self.tasks[task_name]["next_run"] = next_run.isoformat()
                        
                    except ValueError:
                        print(f"⚠️ Invalid schedule format for {task_name}: {schedule_str}")
        
        # Add heartbeat task
        schedule.every(1).minutes.do(self._heartbeat)
        
        print("✅ Scheduled tasks setup completed")
    
    def _run_task_wrapper(self, task_name: str):
        """Wrapper to run task and handle errors"""
        asyncio.create_task(self._execute_task(task_name))
    
    async def _execute_task(self, task_name: str):
        """Execute a scheduled task"""
        task_info = self.tasks.get(task_name)
        if not task_info or not task_info["enabled"]:
            return
        
        # Check dependencies
        dependencies = self.dependencies.get(task_name, [])
        for dep in dependencies:
            dep_info = self.tasks.get(dep)
            if dep_info and dep_info["enabled"]:
                # Check if dependency ran recently
                last_run = dep_info.get("last_run")
                if last_run:
                    last_run_time = datetime.fromisoformat(last_run)
                    if (datetime.now() - last_run_time).total_seconds() > 3600:  # 1 hour
                        print(f"⏳ Waiting for dependency: {dep}")
                        await self._execute_task(dep)
        
        # Execute task
        try:
            await task_info["function"]()
        except Exception as e:
            print(f"❌ Error executing {task_name}: {e}")
    
    def _heartbeat(self):
        """Heartbeat to show scheduler is alive"""
        now = datetime.now()
        
        # Calculate uptime
        if "start_time" in self.db.stats:
            start_time = datetime.fromisoformat(self.db.stats["start_time"])
            uptime = now - start_time
            uptime_str = str(uptime).split(".")[0]
        else:
            uptime_str = "Unknown"
        
        # Count pending tasks
        pending_tasks = len(schedule.get_jobs())
        
        # Log heartbeat (less frequent to avoid spam)
        if now.minute % 15 == 0:  # Every 15 minutes
            print(f"[{now}] 💓 Scheduler heartbeat - Uptime: {uptime_str}, "
                  f"Pending: {pending_tasks} tasks")
    
    def run(self):
        """Run the scheduler"""
        self.setup_schedule()
        self.running = True
        
        print("🚀 Starting task scheduler...")
        print(f"📅 Scheduled tasks: {len([t for t in self.tasks.values() if t['enabled']])}")
        
        # Record start time
        if "start_time" not in self.db.stats:
            self.db.stats["start_time"] = datetime.now().isoformat()
            self.db._save_data("stats", self.db.stats)
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start(self):
        """Start scheduler in background thread"""
        if not self.thread:
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            print("✅ Scheduler started in background")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        print("🛑 Scheduler stopped")
    
    async def run_task_now(self, task_name: str) -> Dict:
        """Run a task immediately"""
        if task_name not in self.tasks:
            return {
                "success": False,
                "message": f"টাস্ক খুঁজে পাওয়া যায়নি: {task_name}"
            }
        
        task_info = self.tasks[task_name]
        
        if not task_info["enabled"]:
            return {
                "success": False,
                "message": f"টাস্ক ডিজেবল করা আছে: {task_name}"
            }
        
        print(f"🚀 Running {task_name} now...")
        
        try:
            start_time = datetime.now()
            await task_info["function"]()
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "message": f"✅ {task_name} সম্পন্ন হয়েছে ({execution_time:.2f}s)",
                "execution_time": execution_time,
                "task_name": task_name
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"❌ {task_name} ব্যর্থ হয়েছে: {str(e)}",
                "error": str(e),
                "task_name": task_name
            }
    
    async def get_status(self) -> Dict:
        """Get scheduler status"""
        status = {
            "running": self.running,
            "uptime": None,
            "total_tasks": len(self.tasks),
            "enabled_tasks": len([t for t in self.tasks.values() if t["enabled"]]),
            "pending_jobs": len(schedule.get_jobs()),
            "tasks": {}
        }
        
        # Calculate uptime
        if "start_time" in self.db.stats:
            start_time = datetime.fromisoformat(self.db.stats["start_time"])
            uptime = datetime.now() - start_time
            status["uptime"] = str(uptime).split(".")[0]
        
        # Get task status
        for task_name, task_info in self.tasks.items():
            next_run = None
            if task_info["enabled"]:
                # Find scheduled job
                jobs = schedule.get_jobs(task_name)
                if jobs:
                    next_run = jobs[0].next_run
            
            status["tasks"][task_name] = {
                "enabled": task_info["enabled"],
                "last_run": task_info["last_run"],
                "next_run": next_run.isoformat() if next_run else None,
                "success_count": task_info["success_count"],
                "fail_count": task_info["fail_count"],
                "execution_time": task_info["execution_time"],
                "description": task_info["description"],
                "category": task_info["category"],
                "priority": task_info["priority"]
            }
        
        return status
    
    async def update_task_schedule(self, task_name: str, schedule_str: str, 
                                 enabled: bool = None) -> Dict:
        """Update task schedule"""
        if task_name not in self.tasks:
            return {
                "success": False,
                "message": f"টাস্ক খুঁজে পাওয়া যায়নি: {task_name}"
            }
        
        # Clear existing schedule
        schedule.clear(task_name)
        
        # Update task info
        self.tasks[task_name]["schedule"] = schedule_str
        if enabled is not None:
            self.tasks[task_name]["enabled"] = enabled
        
        # Reschedule if enabled
        if self.tasks[task_name]["enabled"]:
            try:
                if schedule_str == "*/30":
                    schedule.every(30).minutes.do(
                        self._run_task_wrapper, task_name
                    )
                else:
                    hour, minute = map(int, schedule_str.split(":"))
                    
                    if task_name == "weekly_reset":
                        schedule.every().monday.at(f"{hour:02d}:{minute:02d}").do(
                            self._run_task_wrapper, task_name
                        )
                    else:
                        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(
                            self._run_task_wrapper, task_name
                        )
                
                # Calculate next run
                now = datetime.now()
                hour, minute = map(int, schedule_str.split(":"))
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if next_run < now:
                    if task_name == "weekly_reset":
                        next_run += timedelta(days=(7 - now.weekday()))
                    else:
                        next_run += timedelta(days=1)
                
                self.tasks[task_name]["next_run"] = next_run.isoformat()
                
                return {
                    "success": True,
                    "message": f"✅ {task_name} এর শিডিউল আপডেট করা হয়েছে: {schedule_str}",
                    "next_run": next_run.isoformat()
                }
                
            except ValueError:
                return {
                    "success": False,
                    "message": f"❌ ভুল শিডিউল ফরম্যাট: {schedule_str}"
                }
        else:
            return {
                "success": True,
                "message": f"✅ {task_name} ডিজেবল করা হয়েছে"
            }
    
    async def get_task_categories(self) -> Dict:
        """Get task categories"""
        categories = {}
        
        for task_info in self.tasks.values():
            category = task_info["category"]
            if category not in categories:
                categories[category] = {
                    "name": category,
                    "task_count": 0,
                    "enabled_count": 0,
                    "tasks": []
                }
            
            categories[category]["task_count"] += 1
            if task_info["enabled"]:
                categories[category]["enabled_count"] += 1
            
            categories[category]["tasks"].append({
                "name": task_info["description"],
                "enabled": task_info["enabled"],
                "schedule": task_info["schedule"],
                "last_run": task_info["last_run"]
            })
        
        return categories
    
    async def cleanup_completed_tasks(self, days_old: int = 7):
        """Cleanup old completed task records"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0
        
        # Keep only recent completed tasks
        self.completed_tasks = [
            task for task in self.completed_tasks
            if datetime.fromisoformat(task.get("completed_at", "2000-01-01")) > cutoff_date
        ]
        
        cleaned_count = len(self.completed_tasks)  # Actually kept count
        
        print(f"🧹 Cleaned old task records, keeping {cleaned_count} recent tasks")
        return cleaned_count