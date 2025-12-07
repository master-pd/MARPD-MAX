import time
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    """Advanced Rate Limiting System v15.0.00"""
    
    def __init__(self):
        self.limits = {
            'user_commands': {
                'window': 60,  # seconds
                'max_requests': 30,
                'penalty': 5  # seconds penalty
            },
            'game_requests': {
                'window': 30,
                'max_requests': 10,
                'penalty': 10
            },
            'payment_requests': {
                'window': 300,
                'max_requests': 5,
                'penalty': 30
            },
            'api_requests': {
                'window': 60,
                'max_requests': 60,
                'penalty': 60
            },
            'admin_commands': {
                'window': 10,
                'max_requests': 5,
                'penalty': 2
            },
            'spam_protection': {
                'window': 10,
                'max_requests': 5,
                'penalty': 30
            }
        }
        
        # Store request history
        self.request_history = defaultdict(list)
        self.penalties = defaultdict(dict)
        self.user_stats = defaultdict(lambda: defaultdict(int))
        
        # IP-based limiting
        self.ip_history = defaultdict(list)
        self.suspicious_ips = set()
        
        # Advanced analytics
        self.analytics = {
            'total_requests': 0,
            'blocked_requests': 0,
            'user_violations': defaultdict(int),
            'peak_hours': defaultdict(int),
            'by_type': defaultdict(int)
        }
        
        print("✅ Advanced Rate Limiter v15.0.00 Initialized")
    
    async def check_limit(self, user_id: int, limit_type: str, 
                         ip_address: str = None) -> Dict:
        """Check if request is allowed"""
        current_time = time.time()
        window = self.limits[limit_type]['window']
        max_req = self.limits[limit_type]['max_requests']
        
        # Update analytics
        self.analytics['total_requests'] += 1
        self.analytics['by_type'][limit_type] += 1
        self.analytics['peak_hours'][datetime.now().hour] += 1
        
        # Check IP restrictions
        if ip_address:
            if await self._check_ip_restrictions(ip_address, limit_type):
                return {
                    'allowed': False,
                    'message': 'আইপি ঠিকানা সন্দেহজনক!',
                    'retry_after': 3600,  # 1 hour
                    'reason': 'suspicious_ip'
                }
        
        # Check if user is in penalty
        penalty_key = f"{user_id}_{limit_type}"
        if penalty_key in self.penalties:
            penalty_end = self.penalties[penalty_key]['until']
            if current_time < penalty_end:
                remaining = penalty_end - current_time
                return {
                    'allowed': False,
                    'message': f'রেট লিমিট অতিক্রম করেছেন! {int(remaining)} সেকেন্ড পর চেষ্টা করুন।',
                    'retry_after': int(remaining),
                    'reason': 'penalty_active'
                }
        
        # Get user's recent requests
        history_key = f"{user_id}_{limit_type}"
        recent_requests = self.request_history[history_key]
        
        # Clean old requests
        cutoff_time = current_time - window
        recent_requests = [req_time for req_time in recent_requests if req_time > cutoff_time]
        
        # Check if limit exceeded
        if len(recent_requests) >= max_req:
            # Apply penalty
            penalty_duration = self.limits[limit_type]['penalty']
            penalty_end = current_time + penalty_duration
            
            self.penalties[penalty_key] = {
                'until': penalty_end,
                'applied_at': current_time,
                'violation_count': self.user_stats[user_id].get(f'{limit_type}_violations', 0) + 1
            }
            
            # Update user stats
            self.user_stats[user_id][f'{limit_type}_violations'] += 1
            self.analytics['user_violations'][user_id] += 1
            self.analytics['blocked_requests'] += 1
            
            return {
                'allowed': False,
                'message': f'রেট লিমিট অতিক্রম করেছেন! {penalty_duration} সেকেন্ডের জন্য ব্লক করা হয়েছে।',
                'retry_after': penalty_duration,
                'violations': self.user_stats[user_id][f'{limit_type}_violations'],
                'reason': 'limit_exceeded'
            }
        
        # Allow request
        recent_requests.append(current_time)
        self.request_history[history_key] = recent_requests[-max_req*2:]  # Keep some extra
        
        # Update user stats
        self.user_stats[user_id]['total_requests'] += 1
        self.user_stats[user_id][f'{limit_type}_requests'] += 1
        
        requests_in_window = len(recent_requests)
        remaining_requests = max_req - requests_in_window
        reset_time = window - (current_time - recent_requests[0]) if recent_requests else window
        
        return {
            'allowed': True,
            'remaining': remaining_requests,
            'reset_in': int(reset_time),
            'window': window,
            'limit': max_req,
            'current': requests_in_window
        }
    
    async def _check_ip_restrictions(self, ip_address: str, limit_type: str) -> bool:
        """Check IP-based restrictions"""
        current_time = time.time()
        
        # Check if IP is suspicious
        if ip_address in self.suspicious_ips:
            return True
        
        # Track IP requests
        ip_key = f"{ip_address}_{limit_type}"
        recent_requests = self.ip_history[ip_key]
        
        # Clean old requests
        cutoff_time = current_time - 3600  # 1 hour window for IP tracking
        recent_requests = [req_time for req_time in recent_requests if req_time > cutoff_time]
        
        # Check for suspicious patterns
        if len(recent_requests) > 100:  # More than 100 requests per hour
            self.suspicious_ips.add(ip_address)
            return True
        
        # Update IP history
        recent_requests.append(current_time)
        self.ip_history[ip_key] = recent_requests[-200:]  # Keep last 200 requests
        
        return False
    
    async def adjust_limits(self, user_id: int, limit_type: str, adjustment: float):
        """Dynamically adjust limits based on user behavior"""
        if user_id not in self.user_stats:
            return
        
        # Get current stats
        violations = self.user_stats[user_id].get(f'{limit_type}_violations', 0)
        total_requests = self.user_stats[user_id].get(f'{limit_type}_requests', 0)
        
        if total_requests > 100:  # Enough data to make adjustments
            violation_rate = violations / total_requests
            
            if violation_rate > 0.3:  # High violation rate
                # Reduce limit by 20%
                new_limit = int(self.limits[limit_type]['max_requests'] * 0.8)
                self.limits[limit_type]['max_requests'] = max(new_limit, 5)
            
            elif violation_rate < 0.05 and total_requests > 500:  # Good user
                # Increase limit by 10%
                new_limit = int(self.limits[limit_type]['max_requests'] * 1.1)
                self.limits[limit_type]['max_requests'] = min(new_limit, 100)
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Get user's rate limiting statistics"""
        if user_id not in self.user_stats:
            return {
                'total_requests': 0,
                'violations': 0,
                'penalties_active': 0
            }
        
        # Count active penalties
        active_penalties = 0
        current_time = time.time()
        
        for penalty_key, penalty_data in self.penalties.items():
            if f"{user_id}_" in penalty_key and penalty_data['until'] > current_time:
                active_penalties += 1
        
        return {
            'total_requests': self.user_stats[user_id].get('total_requests', 0),
            'violations': sum(1 for k in self.user_stats[user_id].keys() if 'violations' in k),
            'penalties_active': active_penalties,
            'by_type': {
                'user_commands': self.user_stats[user_id].get('user_commands_requests', 0),
                'game_requests': self.user_stats[user_id].get('game_requests_requests', 0),
                'payment_requests': self.user_stats[user_id].get('payment_requests_requests', 0)
            },
            'violation_by_type': {
                'user_commands': self.user_stats[user_id].get('user_commands_violations', 0),
                'game_requests': self.user_stats[user_id].get('game_requests_violations', 0),
                'payment_requests': self.user_stats[user_id].get('payment_requests_violations', 0)
            }
        }
    
    async def get_analytics(self) -> Dict:
        """Get rate limiting analytics"""
        # Calculate rates
        total_req = self.analytics['total_requests']
        blocked_req = self.analytics['blocked_requests']
        
        block_rate = (blocked_req / max(total_req, 1)) * 100
        
        # Find peak hour
        peak_hour = max(self.analytics['peak_hours'].items(), key=lambda x: x[1])[0] if self.analytics['peak_hours'] else 0
        
        # Get top violators
        top_violators = sorted(
            self.analytics['user_violations'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_requests': total_req,
            'blocked_requests': blocked_req,
            'block_rate_percent': block_rate,
            'peak_hour': f"{peak_hour}:00-{peak_hour+1}:00",
            'requests_by_type': dict(self.analytics['by_type']),
            'top_violators': [
                {'user_id': uid, 'violations': count}
                for uid, count in top_violators
            ],
            'suspicious_ips_count': len(self.suspicious_ips),
            'active_penalties': len([p for p in self.penalties.values() if p['until'] > time.time()])
        }
    
    async def reset_user_limits(self, user_id: int) -> Dict:
        """Reset all limits for a user"""
        # Remove from request history
        keys_to_remove = [k for k in self.request_history.keys() if str(user_id) in k]
        for key in keys_to_remove:
            del self.request_history[key]
        
        # Remove penalties
        penalties_to_remove = [k for k in self.penalties.keys() if str(user_id) in k]
        for key in penalties_to_remove:
            del self.penalties[key]
        
        # Reset user stats
        if user_id in self.user_stats:
            del self.user_stats[user_id]
        
        # Remove from violations
        if user_id in self.analytics['user_violations']:
            del self.analytics['user_violations'][user_id]
        
        return {
            'success': True,
            'message': f'ইউজার {user_id} এর সব রেট লিমিট রিসেট করা হয়েছে।',
            'user_id': user_id
        }
    
    async def cleanup_old_data(self, hours_old: int = 24):
        """Cleanup old rate limiting data"""
        current_time = time.time()
        cutoff_time = current_time - (hours_old * 3600)
        
        # Clean request history
        cleaned_count = 0
        for key, requests in list(self.request_history.items()):
            # Keep only recent requests
            recent_requests = [req_time for req_time in requests if req_time > cutoff_time]
            if recent_requests:
                self.request_history[key] = recent_requests
            else:
                del self.request_history[key]
                cleaned_count += 1
        
        # Clean expired penalties
        for key, penalty_data in list(self.penalties.items()):
            if penalty_data['until'] < cutoff_time:
                del self.penalties[key]
                cleaned_count += 1
        
        # Clean IP history
        for key, requests in list(self.ip_history.items()):
            recent_requests = [req_time for req_time in requests if req_time > cutoff_time]
            if recent_requests:
                self.ip_history[key] = recent_requests
            else:
                del self.ip_history[key]
                cleaned_count += 1
        
        print(f"🧹 Rate limiter cleanup: {cleaned_count} items removed")
        return cleaned_count
    
    async def add_exception(self, user_id: int, limit_type: str = None, duration_hours: int = 24):
        """Add exception for specific user"""
        exception_key = f"ex_{user_id}"
        
        if limit_type:
            exception_key += f"_{limit_type}"
        
        exception_until = time.time() + (duration_hours * 3600)
        
        # Store exception
        self.penalties[exception_key] = {
            'until': exception_until,
            'type': 'exception',
            'added_at': time.time(),
            'duration_hours': duration_hours
        }
        
        return {
            'success': True,
            'message': f'ইউজার {user_id} এর জন্য {duration_hours} ঘন্টার এক্সেপশন যুক্ত করা হয়েছে।',
            'exception_until': datetime.fromtimestamp(exception_until).isoformat()
        }
    
    async def remove_exception(self, user_id: int, limit_type: str = None):
        """Remove exception for user"""
        exception_key = f"ex_{user_id}"
        
        if limit_type:
            exception_key += f"_{limit_type}"
        
        if exception_key in self.penalties:
            del self.penalties[exception_key]
            return {
                'success': True,
                'message': f'ইউজার {user_id} এর এক্সেপশন রিমুভ করা হয়েছে।'
            }
        else:
            return {
                'success': False,
                'message': f'ইউজার {user_id} এর কোনো এক্সেপশন নেই!'
            }
    
    async def get_limit_config(self) -> Dict:
        """Get current limit configuration"""
        return {
            'limits': self.limits,
            'total_users_tracked': len(self.user_stats),
            'active_penalties': len([p for p in self.penalties.values() if p['until'] > time.time()]),
            'suspicious_ips': len(self.suspicious_ips),
            'data_size': {
                'request_history': sum(len(v) for v in self.request_history.values()),
                'ip_history': sum(len(v) for v in self.ip_history.values()),
                'penalties': len(self.penalties),
                'user_stats': len(self.user_stats)
            }
        }


# Decorator for easy rate limiting
def rate_limit(limit_type: str = 'user_commands'):
    """Decorator for rate limiting functions"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract user_id from args or kwargs
                user_id = None
                ip_address = None
                
                # Try to find user_id in args/kwargs
                for arg in args:
                    if isinstance(arg, int) and arg > 100000000:  # Likely Telegram ID
                        user_id = arg
                        break
                
                if not user_id and 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                
                if 'ip_address' in kwargs:
                    ip_address = kwargs['ip_address']
                
                if user_id:
                    # Create rate limiter instance
                    limiter = RateLimiter()
                    check = await limiter.check_limit(user_id, limit_type, ip_address)
                    
                    if not check['allowed']:
                        return {
                            'success': False,
                            'message': check['message'],
                            'retry_after': check['retry_after'],
                            'code': 'RATE_LIMITED'
                        }
                
                # Execute function if allowed
                return await func(*args, **kwargs)
            
            return async_wrapper
        
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Similar logic for sync functions
                user_id = None
                
                for arg in args:
                    if isinstance(arg, int) and arg > 100000000:
                        user_id = arg
                        break
                
                if not user_id and 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                
                if user_id:
                    # Note: For sync functions, you'd need to handle async differently
                    # This is simplified
                    pass
                
                return func(*args, **kwargs)
            
            return sync_wrapper
    
    return decorator