import traceback
import logging
from typing import Callable, Any, Union
from functools import wraps
import asyncio
from datetime import datetime

class ErrorHandler:
    """Advanced Error Handling System v15.0.00"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.error_stats = {
            'total_errors': 0,
            'error_by_type': {},
            'recent_errors': [],
            'last_error_time': None
        }
        
    def handle_exception(self, func: Callable) -> Callable:
        """Decorator for handling exceptions in sync functions"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self._process_exception(e, func.__name__, args, kwargs)
                return self._create_error_response(e, func.__name__)
        return wrapper
    
    def async_handle_exception(self, func: Callable) -> Callable:
        """Decorator for handling exceptions in async functions"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                self._process_exception(e, func.__name__, args, kwargs)
                return self._create_error_response(e, func.__name__)
        return wrapper
    
    def _process_exception(self, error: Exception, func_name: str, args: tuple, kwargs: dict):
        """Process and log exception"""
        error_time = datetime.now()
        error_type = type(error).__name__
        error_message = str(error)
        
        # Update statistics
        self.error_stats['total_errors'] += 1
        self.error_stats['error_by_type'][error_type] = self.error_stats['error_by_type'].get(error_type, 0) + 1
        self.error_stats['last_error_time'] = error_time.isoformat()
        
        # Add to recent errors (keep last 100)
        error_entry = {
            'timestamp': error_time.isoformat(),
            'function': func_name,
            'type': error_type,
            'message': error_message,
            'traceback': traceback.format_exc()
        }
        self.error_stats['recent_errors'].append(error_entry)
        if len(self.error_stats['recent_errors']) > 100:
            self.error_stats['recent_errors'] = self.error_stats['recent_errors'][-100:]
        
        # Log the error
        self.logger.error(f"Error in {func_name}: {error_type} - {error_message}")
        self.logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Log context information
        context_info = self._get_context_info(args, kwargs)
        if context_info:
            self.logger.info(f"Error Context: {context_info}")
    
    def _get_context_info(self, args: tuple, kwargs: dict) -> dict:
        """Extract context information from function arguments"""
        context = {}
        
        try:
            # Extract user_id if present in args
            for i, arg in enumerate(args):
                if isinstance(arg, int) and arg > 100000000:  # Likely Telegram user ID
                    context['user_id'] = arg
                    break
            
            # Extract from kwargs
            if 'user_id' in kwargs:
                context['user_id'] = kwargs['user_id']
            if 'chat_id' in kwargs:
                context['chat_id'] = kwargs['chat_id']
            if 'message' in kwargs:
                msg = kwargs['message']
                if hasattr(msg, 'text'):
                    context['message_preview'] = msg.text[:50] + '...' if len(msg.text) > 50 else msg.text
                
        except:
            pass
        
        return context
    
    def _create_error_response(self, error: Exception, func_name: str) -> dict:
        """Create user-friendly error response"""
        error_type = type(error).__name__
        
        # Define user-friendly messages for common errors
        error_messages = {
            'ConnectionError': '⚠️ নেটওয়ার্ক সমস্যা! দয়া করে আবার চেষ্টা করুন।',
            'TimeoutError': '⏰ সময় শেষ! দয়া করে আবার চেষ্টা করুন।',
            'KeyError': '🔑 তথ্য পাওয়া যায়নি!',
            'ValueError': '❌ ভুল মান! দয়া করে আবার চেষ্টা করুন।',
            'FileNotFoundError': '📄 ফাইল পাওয়া যায়নি!',
            'PermissionError': '🚫 অনুমতি নেই!',
            'TypeError': '❓ ভুল ধরনের তথ্য!',
            'IndexError': '📊 তথ্যের অবস্থান ভুল!',
            'AttributeError': '⚙️ বৈশিষ্ট্য নেই!',
            'RuntimeError': '⚡ রানটাইম সমস্যা!',
            'DatabaseError': '🗄️ ডাটাবেস সমস্যা! দয়া করে আবার চেষ্টা করুন।'
        }
        
        user_message = error_messages.get(error_type, '❌ একটি ত্রুটি হয়েছে! দয়া করে আবার চেষ্টা করুন।')
        
        # For development/debugging, include more details
        debug_info = {
            'error': error_type,
            'message': str(error),
            'function': func_name,
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'success': False,
            'message': user_message,
            'error_type': error_type,
            'debug_info': debug_info if self.logger.level <= logging.DEBUG else None
        }
    
    def get_error_stats(self) -> dict:
        """Get error statistics"""
        stats = self.error_stats.copy()
        
        # Calculate error rates
        if stats['recent_errors']:
            # Errors in last hour
            one_hour_ago = datetime.now().timestamp() - 3600
            recent_errors = [e for e in stats['recent_errors'] 
                           if datetime.fromisoformat(e['timestamp']).timestamp() > one_hour_ago]
            stats['errors_last_hour'] = len(recent_errors)
        
        # Most common error types
        if stats['error_by_type']:
            stats['most_common_error'] = max(stats['error_by_type'].items(), key=lambda x: x[1])
        
        return stats
    
    def clear_errors(self):
        """Clear error statistics"""
        self.error_stats = {
            'total_errors': 0,
            'error_by_type': {},
            'recent_errors': [],
            'last_error_time': None
        }
    
    def retry_on_failure(self, max_attempts: int = 3, delay: float = 1.0):
        """Decorator for retrying failed operations"""
        def decorator(func: Callable):
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    last_error = None
                    for attempt in range(1, max_attempts + 1):
                        try:
                            return await func(*args, **kwargs)
                        except Exception as e:
                            last_error = e
                            if attempt < max_attempts:
                                wait_time = delay * attempt
                                self.logger.warning(f"Attempt {attempt} failed for {func.__name__}. Retrying in {wait_time}s...")
                                await asyncio.sleep(wait_time)
                            else:
                                self.logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                                raise last_error
                    return None
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    last_error = None
                    for attempt in range(1, max_attempts + 1):
                        try:
                            return func(*args, **kwargs)
                        except Exception as e:
                            last_error = e
                            if attempt < max_attempts:
                                wait_time = delay * attempt
                                self.logger.warning(f"Attempt {attempt} failed for {func.__name__}. Retrying in {wait_time}s...")
                                import time
                                time.sleep(wait_time)
                            else:
                                self.logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                                raise last_error
                    return None
                return sync_wrapper
        return decorator
    
    def create_error_report(self) -> str:
        """Create comprehensive error report"""
        stats = self.get_error_stats()
        
        report = f"""
❌ **ত্রুটি রিপোর্ট** - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **পরিসংখ্যান:**
• মোট ত্রুটি: {stats['total_errors']}
• শেষ ত্রুটি: {stats['last_error_time'] or 'কোনোটি নয়'}
• শেষ ১ ঘন্টায়: {stats.get('errors_last_hour', 0)}টি

📈 **ত্রুটি ধরণ অনুযায়ী:**
"""
        
        for error_type, count in sorted(stats['error_by_type'].items(), key=lambda x: x[1], reverse=True)[:10]:
            report += f"• {error_type}: {count} বার\n"
        
        report += f"""
🔍 **সাম্প্রতিক ত্রুটি ({len(stats['recent_errors'])}টি):**
"""
        
        for error in stats['recent_errors'][-5:]:  # Last 5 errors
            error_time = datetime.fromisoformat(error['timestamp']).strftime('%H:%M:%S')
            report += f"• [{error_time}] {error['function']}: {error['type']}\n"
        
        report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 **সমাধানের পরামর্শ:**
"""
        
        if stats.get('errors_last_hour', 0) > 10:
            report += "• ত্রুটির হার বেশি! সিস্টেম চেক করুন।\n"
        if 'ConnectionError' in stats['error_by_type']:
            report += "• নেটওয়ার্ক সংযোগ চেক করুন।\n"
        if 'DatabaseError' in stats['error_by_type']:
            report += "• ডাটাবেস সংযোগ ভেরিফাই করুন।\n"
        
        report += "• লগ ফাইল চেক করুন বিস্তারিত তথ্যের জন্য।"
        
        return report
    
    def send_error_alert(self, error: Exception, context: dict = None):
        """Send error alert for critical issues"""
        try:
            error_type = type(error).__name__
            error_message = str(error)
            
            # Check if this is a critical error
            critical_errors = [
                'DatabaseError', 'ConnectionError', 
                'MemoryError', 'KeyboardInterrupt',
                'SystemExit'
            ]
            
            if error_type in critical_errors or 'critical' in error_message.lower():
                alert_message = f"""
🚨 **গুরুত্বপূর্ণ ত্রুটি সতর্কতা!**

⚠️ **ত্রুটি ধরণ:** {error_type}
📝 **বার্তা:** {error_message}
🕒 **সময়:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                if context:
                    alert_message += f"\n📋 **কনটেক্সট:** {context}"
                
                # Log as critical
                self.logger.critical(alert_message)
                
                # Here you could add code to send alert via:
                # - Telegram message to admin
                # - Email
                # - Discord webhook
                # etc.
                
                return True
        
        except Exception as alert_error:
            self.logger.error(f"Failed to send error alert: {alert_error}")
        
        return False