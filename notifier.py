import asyncio
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from config import Config
from db import Database
from utils import Utils
from logger import Logger

class Notifier:
    """Advanced Notification System v15.0.00"""
    
    def __init__(self, db: Database):
        self.db = db
        self.config = Config()
        self.logger = Logger.get_logger(__name__)
        
        # Notification settings
        self.settings = {
            'enabled': True,
            'max_notifications_per_hour': 3,
            'notification_cooldown_minutes': 30,
            'default_language': 'bn',
            'notification_channels': ['telegram', 'in_app'],
            'emergency_contacts': [self.config.BOT_OWNER_ID],
            'auto_cleanup_days': 7
        }
        
        # Notification templates
        self.templates = {
            'welcome': {
                'bn': '🎉 স্বাগতম {name}! আপনি এখন আমাদের কমিউনিটির অংশ।',
                'en': '🎉 Welcome {name}! You are now part of our community.'
            },
            'deposit_success': {
                'bn': '💰 {amount} ডিপোজিট সফল হয়েছে! আপনার নতুন ব্যালেন্স: {balance}',
                'en': '💰 {amount} deposit successful! Your new balance: {balance}'
            },
            'withdrawal_success': {
                'bn': '🏧 {amount} উইথড্র সফল হয়েছে! ট্রানজেকশন আইডি: {trx_id}',
                'en': '🏧 {amount} withdrawal successful! Transaction ID: {trx_id}'
            },
            'level_up': {
                'bn': '🎯 অভিনন্দন! আপনি লেভেল {level} এ পৌঁছেছেন!',
                'en': '🎯 Congratulations! You reached level {level}!'
            },
            'daily_bonus': {
                'bn': '🎁 আপনার ডেইলি বোনাস প্রস্তুত! /daily কমান্ড দিন।',
                'en': '🎁 Your daily bonus is ready! Use /daily command.'
            },
            'streak_milestone': {
                'bn': '🔥 অসাধারণ! আপনি {days} দিন ধরে স্ট্রীক রাখছেন!',
                'en': '🔥 Amazing! You have maintained a {days} day streak!'
            },
            'security_alert': {
                'bn': '⚠️ সতর্কতা: আপনার অ্যাকাউন্টে সন্দেহজনক কার্যকলাপ ধরা পড়েছে।',
                'en': '⚠️ Security Alert: Suspicious activity detected on your account.'
            },
            'system_maintenance': {
                'bn': '🔧 সিস্টেম রক্ষণাবেক্ষণ: {start_time} থেকে {end_time} পর্যন্ত',
                'en': '🔧 System Maintenance: From {start_time} to {end_time}'
            },
            'new_feature': {
                'bn': '✨ নতুন ফিচার: {feature_name} এখন লাইভ!',
                'en': '✨ New Feature: {feature_name} is now live!'
            }
        }
        
        # Notification queue
        self.notification_queue = []
        self.sent_notifications = []
        self.user_notification_history = {}
        
        self.logger.info("🔔 Notifier v15.0.00 Initialized")
    
    async def send_notification(self, user_id: int, notification_type: str, 
                               data: Dict = None, priority: str = 'normal') -> Dict:
        """Send notification to user"""
        try:
            # Check if notifications are enabled
            if not self.settings['enabled']:
                return {'success': False, 'message': 'Notifications are disabled'}
            
            # Get user
            user = self.db.get_user(user_id)
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            # Check user notification preferences
            user_settings = user.get('settings', {})
            if not user_settings.get('notifications', True):
                return {'success': False, 'message': 'User has disabled notifications'}
            
            # Check notification cooldown
            if not await self._check_cooldown(user_id, notification_type):
                return {'success': False, 'message': 'Notification cooldown active'}
            
            # Check hourly limit
            if not await self._check_hourly_limit(user_id):
                return {'success': False, 'message': 'Hourly notification limit reached'}
            
            # Get user language
            language = user_settings.get('language', self.settings['default_language'])
            if language not in ['bn', 'en']:
                language = self.settings['default_language']
            
            # Prepare notification data
            notification_data = data or {}
            notification_data['name'] = user.get('first_name', 'User')
            
            # Get template
            template = self.templates.get(notification_type, {}).get(language)
            if not template:
                # Fallback to English or default
                template = self.templates.get(notification_type, {}).get('en')
                if not template:
                    template = 'Notification: {type}'
            
            # Format message
            try:
                message = template.format(**notification_data)
            except KeyError as e:
                message = f"Notification: {notification_type}"
                self.logger.warning(f"Missing key in notification template: {e}")
            
            # Create notification object
            notification_id = f"notif_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user_id}"
            notification = {
                'id': notification_id,
                'user_id': user_id,
                'type': notification_type,
                'message': message,
                'priority': priority,
                'timestamp': datetime.now().isoformat(),
                'status': 'PENDING',
                'data': notification_data,
                'language': language,
                'channels': self.settings['notification_channels']
            }
            
            # Add to queue
            self.notification_queue.append(notification)
            
            # Log notification
            self.logger.info(f"Notification queued: {notification_type} for user {user_id}")
            
            # Process notification (in real implementation, this would send via Telegram)
            await self._process_notification(notification)
            
            # Update user notification history
            self._update_user_history(user_id, notification)
            
            return {
                'success': True,
                'message': 'Notification sent successfully',
                'notification_id': notification_id,
                'notification': notification
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return {'success': False, 'message': f'Notification failed: {str(e)}'}
    
    async def _process_notification(self, notification: Dict):
        """Process and send notification"""
        try:
            # Mark as sending
            notification['status'] = 'SENDING'
            notification['sent_at'] = datetime.now().isoformat()
            
            # In a real implementation, this would send via Telegram API
            # For now, we'll simulate sending
            
            user_id = notification['user_id']
            message = notification['message']
            
            # Simulate sending delay
            await asyncio.sleep(0.1)
            
            # Mark as sent
            notification['status'] = 'SENT'
            notification['delivered_at'] = datetime.now().isoformat()
            
            # Add to sent notifications
            self.sent_notifications.append(notification)
            
            # Keep only last 1000 sent notifications
            if len(self.sent_notifications) > 1000:
                self.sent_notifications = self.sent_notifications[-1000:]
            
            self.logger.debug(f"Notification sent: {notification['id']} to user {user_id}")
            
            # Log in database
            self.db.add_log(
                'notification_sent',
                f"Notification sent: {notification['type']}",
                user_id,
                {
                    'notification_id': notification['id'],
                    'type': notification['type'],
                    'message_preview': message[:50]
                }
            )
            
        except Exception as e:
            notification['status'] = 'FAILED'
            notification['error'] = str(e)
            self.logger.error(f"Failed to process notification {notification['id']}: {e}")
    
    async def _check_cooldown(self, user_id: int, notification_type: str) -> bool:
        """Check if user has notification cooldown"""
        cooldown_minutes = self.settings['notification_cooldown_minutes']
        
        # Get user's recent notifications
        recent_notifications = []
        for notif in self.sent_notifications:
            if notif['user_id'] == user_id and notif['type'] == notification_type:
                recent_notifications.append(notif)
        
        if not recent_notifications:
            return True
        
        # Check most recent notification
        latest_notif = max(recent_notifications, key=lambda x: x.get('timestamp', ''))
        sent_time = datetime.fromisoformat(latest_notif.get('timestamp', '2000-01-01'))
        time_diff = datetime.now() - sent_time
        
        return time_diff.total_seconds() >= (cooldown_minutes * 60)
    
    async def _check_hourly_limit(self, user_id: int) -> bool:
        """Check hourly notification limit"""
        max_per_hour = self.settings['max_notifications_per_hour']
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        # Count notifications in last hour
        recent_count = 0
        for notif in self.sent_notifications:
            if notif['user_id'] == user_id:
                sent_time = datetime.fromisoformat(notif.get('timestamp', '2000-01-01'))
                if sent_time > one_hour_ago:
                    recent_count += 1
        
        return recent_count < max_per_hour
    
    def _update_user_history(self, user_id: int, notification: Dict):
        """Update user notification history"""
        if user_id not in self.user_notification_history:
            self.user_notification_history[user_id] = []
        
        self.user_notification_history[user_id].append({
            'id': notification['id'],
            'type': notification['type'],
            'timestamp': notification['timestamp'],
            'status': notification['status']
        })
        
        # Keep only last 100 notifications per user
        if len(self.user_notification_history[user_id]) > 100:
            self.user_notification_history[user_id] = self.user_notification_history[user_id][-100:]
    
    async def send_bulk_notification(self, user_ids: List[int], notification_type: str, 
                                   data: Dict = None, priority: str = 'normal') -> Dict:
        """Send notification to multiple users"""
        try:
            results = {
                'total': len(user_ids),
                'successful': 0,
                'failed': 0,
                'details': []
            }
            
            for user_id in user_ids:
                result = await self.send_notification(user_id, notification_type, data, priority)
                
                if result['success']:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                
                results['details'].append({
                    'user_id': user_id,
                    'success': result['success'],
                    'message': result.get('message', '')
                })
            
            # Log bulk notification
            self.logger.info(f"Bulk notification sent: {notification_type} - {results['successful']}/{results['total']} successful")
            
            return {
                'success': True,
                'message': f"Bulk notification sent to {results['successful']} users",
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"Bulk notification failed: {e}")
            return {'success': False, 'message': f'Bulk notification failed: {str(e)}'}
    
    async def send_admin_notification(self, notification_type: str, data: Dict = None) -> Dict:
        """Send notification to admins"""
        try:
            admin_ids = self.config.ADMINS.copy()
            
            if self.config.BOT_OWNER_ID not in admin_ids:
                admin_ids.append(self.config.BOT_OWNER_ID)
            
            # Add emergency contacts
            for contact in self.settings['emergency_contacts']:
                if contact not in admin_ids:
                    admin_ids.append(contact)
            
            # Send to all admins
            result = await self.send_bulk_notification(
                admin_ids, 
                notification_type, 
                data, 
                priority='high'
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Admin notification failed: {e}")
            return {'success': False, 'message': f'Admin notification failed: {str(e)}'}
    
    async def send_welcome_notification(self, user_id: int) -> Dict:
        """Send welcome notification to new user"""
        user = self.db.get_user(user_id)
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        data = {
            'name': user.get('first_name', 'User'),
            'bonus': self.config.WELCOME_BONUS,
            'bot_name': self.config.BOT_NAME
        }
        
        return await self.send_notification(user_id, 'welcome', data, priority='high')
    
    async def send_deposit_notification(self, user_id: int, amount: float, new_balance: float) -> Dict:
        """Send deposit success notification"""
        data = {
            'amount': Utils.format_currency(amount),
            'balance': Utils.format_currency(new_balance)
        }
        
        return await self.send_notification(user_id, 'deposit_success', data)
    
    async def send_withdrawal_notification(self, user_id: int, amount: float, trx_id: str) -> Dict:
        """Send withdrawal success notification"""
        data = {
            'amount': Utils.format_currency(amount),
            'trx_id': trx_id
        }
        
        return await self.send_notification(user_id, 'withdrawal_success', data)
    
    async def send_level_up_notification(self, user_id: int, level: int) -> Dict:
        """Send level up notification"""
        data = {
            'level': level
        }
        
        return await self.send_notification(user_id, 'level_up', data, priority='high')
    
    async def send_security_alert(self, user_id: int, activity: str) -> Dict:
        """Send security alert notification"""
        data = {
            'activity': activity
        }
        
        return await self.send_notification(user_id, 'security_alert', data, priority='critical')
    
    async def send_system_maintenance_notification(self, start_time: str, end_time: str, 
                                                  user_ids: List[int] = None) -> Dict:
        """Send system maintenance notification"""
        if user_ids is None:
            # Send to all active users
            active_users = []
            cutoff = datetime.now() - timedelta(days=7)
            
            for user in self.db.users.values():
                last_active = datetime.fromisoformat(user.get("last_active", "2000-01-01"))
                if last_active > cutoff:
                    active_users.append(user['id'])
            
            user_ids = active_users
        
        data = {
            'start_time': start_time,
            'end_time': end_time
        }
        
        return await self.send_bulk_notification(user_ids, 'system_maintenance', data, priority='high')
    
    def get_notification_stats(self) -> Dict:
        """Get notification statistics"""
        total_sent = len(self.sent_notifications)
        total_queued = len(self.notification_queue)
        
        # Sent notifications by type
        sent_by_type = {}
        for notif in self.sent_notifications:
            notif_type = notif.get('type', 'unknown')
            sent_by_type[notif_type] = sent_by_type.get(notif_type, 0) + 1
        
        # Sent notifications by status
        sent_by_status = {}
        for notif in self.sent_notifications:
            status = notif.get('status', 'unknown')
            sent_by_status[status] = sent_by_status.get(status, 0) + 1
        
        # Recent notifications (last 24 hours)
        one_day_ago = datetime.now() - timedelta(days=1)
        recent_notifications = [
            notif for notif in self.sent_notifications
            if datetime.fromisoformat(notif.get('timestamp', '2000-01-01')) > one_day_ago
        ]
        
        return {
            'total_sent': total_sent,
            'total_queued': total_queued,
            'sent_by_type': sent_by_type,
            'sent_by_status': sent_by_status,
            'recent_24h': len(recent_notifications),
            'unique_users': len(self.user_notification_history),
            'settings': self.settings
        }
    
    def get_user_notification_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's notification history"""
        user_history = self.user_notification_history.get(user_id, [])
        
        # Sort by timestamp (newest first)
        user_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return user_history[:limit]
    
    async def cleanup_old_notifications(self, days_to_keep: int = None):
        """Cleanup old notifications"""
        if days_to_keep is None:
            days_to_keep = self.settings['auto_cleanup_days']
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Cleanup sent notifications
        initial_count = len(self.sent_notifications)
        self.sent_notifications = [
            notif for notif in self.sent_notifications
            if datetime.fromisoformat(notif.get('timestamp', '2000-01-01')) > cutoff_date
        ]
        removed_sent = initial_count - len(self.sent_notifications)
        
        # Cleanup user history
        removed_user_history = 0
        for user_id in list(self.user_notification_history.keys()):
            initial_user_count = len(self.user_notification_history[user_id])
            self.user_notification_history[user_id] = [
                notif for notif in self.user_notification_history[user_id]
                if datetime.fromisoformat(notif.get('timestamp', '2000-01-01')) > cutoff_date
            ]
            removed_user_history += initial_user_count - len(self.user_notification_history[user_id])
            
            # Remove empty user history
            if not self.user_notification_history[user_id]:
                del self.user_notification_history[user_id]
        
        self.logger.info(f"🧹 Cleaned up notifications: {removed_sent} sent, {removed_user_history} user history entries")
        
        return {
            'removed_sent': removed_sent,
            'removed_user_history': removed_user_history,
            'remaining_sent': len(self.sent_notifications),
            'remaining_users': len(self.user_notification_history)
        }
    
    def setup_scheduled_notifications(self):
        """Setup scheduled notifications"""
        # Daily bonus reminder at 9 AM
        schedule.every().day.at("09:00").do(self._daily_bonus_reminder)
        
        # Inactive user reminder at 6 PM
        schedule.every().day.at("18:00").do(self._inactive_user_reminder)
        
        # Weekly summary on Monday at 10 AM
        schedule.every().monday.at("10:00").do(self._weekly_summary)
        
        # System health check every 4 hours
        schedule.every(4).hours.do(self._system_health_check)
        
        self.logger.info("⏰ Scheduled notifications setup completed")
    
    async def _daily_bonus_reminder(self):
        """Send daily bonus reminder"""
        self.logger.info("⏰ Sending daily bonus reminders...")
        
        # Get users who haven't claimed daily bonus today
        today = datetime.now().strftime('%Y-%m-%d')
        users_to_notify = []
        
        for user in self.db.users.values():
            last_daily = user.get('last_daily')
            if last_daily != today:
                users_to_notify.append(user['id'])
        
        if users_to_notify:
            await self.send_bulk_notification(
                users_to_notify[:100],  # Limit to 100 users at a time
                'daily_bonus',
                priority='normal'
            )
    
    async def _inactive_user_reminder(self):
        """Send reminders to inactive users"""
        self.logger.info("⏰ Sending inactive user reminders...")
        
        cutoff_date = datetime.now() - timedelta(days=3)
        users_to_notify = []
        
        for user in self.db.users.values():
            last_active = datetime.fromisoformat(user.get('last_active', '2000-01-01'))
            if last_active < cutoff_date:
                users_to_notify.append(user['id'])
        
        if users_to_notify:
            await self.send_bulk_notification(
                users_to_notify[:50],  # Limit to 50 users
                'streak_milestone',
                {'days': '৩'},
                priority='low'
            )
    
    async def _weekly_summary(self):
        """Send weekly summary to active users"""
        self.logger.info("⏰ Sending weekly summaries...")
        
        # Get active users (active in last week)
        cutoff_date = datetime.now() - timedelta(days=7)
        active_users = []
        
        for user in self.db.users.values():
            last_active = datetime.fromisoformat(user.get('last_active', '2000-01-01'))
            if last_active > cutoff_date:
                active_users.append(user['id'])
        
        if active_users:
            await self.send_bulk_notification(
                active_users[:200],  # Limit to 200 users
                'new_feature',
                {'feature_name': 'সাপ্তাহিক রিফ্রেশ'},
                priority='normal'
            )
    
    async def _system_health_check(self):
        """Send system health check notification to admin"""
        try:
            import psutil
            
            # Check system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            if cpu_percent > 80 or memory.percent > 80:
                data = {
                    'cpu_usage': f"{cpu_percent:.1f}%",
                    'memory_usage': f"{memory.percent:.1f}%"
                }
                
                await self.send_admin_notification(
                    'security_alert',
                    {'activity': f"সিস্টেম লোড বেশি: CPU {cpu_percent}%, Memory {memory.percent}%"}
                )
                
        except Exception as e:
            self.logger.error(f"System health check failed: {e}")
    
    def run_scheduler(self):
        """Run notification scheduler in background"""
        self.logger.info("🚀 Starting notification scheduler...")
        
        self.setup_scheduled_notifications()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start(self):
        """Start notification scheduler in background thread"""
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        self.logger.info("✅ Notification scheduler started")