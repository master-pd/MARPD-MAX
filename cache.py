import time
import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
import threading
from collections import OrderedDict
from logger import Logger

class CacheManager:
    """Advanced Cache Management System v15.0.00"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl  # seconds
        self.cache = OrderedDict()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0,
            'total_size': 0
        }
        self.lock = threading.RLock()
        self.logger = Logger.get_logger(__name__)
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        self.logger.info(f"🔄 Cache Manager v15.0.00 Initialized (Max size: {max_size}, TTL: {default_ttl}s)")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check if expired
                if entry['expires'] and entry['expires'] < time.time():
                    del self.cache[key]
                    self.stats['misses'] += 1
                    self.stats['deletes'] += 1
                    return None
                
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.stats['hits'] += 1
                return entry['value']
            
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        with self.lock:
            # Calculate expiration time
            expires = None
            if ttl is not None:
                expires = time.time() + ttl
            elif self.default_ttl:
                expires = time.time() + self.default_ttl
            
            # Create cache entry
            entry = {
                'value': value,
                'expires': expires,
                'created': time.time(),
                'size': self._get_size(value)
            }
            
            # Check if key exists
            if key in self.cache:
                old_size = self.cache[key]['size']
                self.cache[key] = entry
                self.stats['total_size'] += entry['size'] - old_size
            else:
                self.cache[key] = entry
                self.stats['total_size'] += entry['size']
                
                # Evict if cache is full
                if len(self.cache) > self.max_size:
                    self._evict()
            
            self.cache.move_to_end(key)
            self.stats['sets'] += 1
            return True
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        with self.lock:
            if key in self.cache:
                old_size = self.cache[key]['size']
                del self.cache[key]
                self.stats['deletes'] += 1
                self.stats['total_size'] -= old_size
                return True
            return False
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
            self.stats['total_size'] = 0
            self.stats['deletes'] += len(self.cache)
            self.logger.info("🗑️ Cache cleared")
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache (and is not expired)"""
        with self.lock:
            if key not in self.cache:
                return False
            
            entry = self.cache[key]
            if entry['expires'] and entry['expires'] < time.time():
                del self.cache[key]
                self.stats['deletes'] += 1
                return False
            
            return True
    
    def ttl(self, key: str) -> Optional[float]:
        """Get time to live for a key"""
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            if not entry['expires']:
                return None
            
            ttl = entry['expires'] - time.time()
            return max(0, ttl) if ttl > 0 else None
    
    def keys(self, pattern: str = None) -> list:
        """Get cache keys (optionally filtered by pattern)"""
        with self.lock:
            all_keys = list(self.cache.keys())
            
            if not pattern:
                return all_keys
            
            # Simple pattern matching (supports * at end)
            if pattern.endswith('*'):
                prefix = pattern[:-1]
                return [k for k in all_keys if k.startswith(prefix)]
            else:
                return [k for k in all_keys if k == pattern]
    
    def _evict(self):
        """Evict least recently used entries"""
        with self.lock:
            while len(self.cache) > self.max_size:
                key, entry = self.cache.popitem(last=False)
                self.stats['evictions'] += 1
                self.stats['total_size'] -= entry['size']
                self.logger.debug(f"Evicted cache key: {key}")
    
    def _cleanup_loop(self):
        """Background thread to cleanup expired entries"""
        while True:
            time.sleep(60)  # Run every minute
            self._cleanup_expired()
    
    def _cleanup_expired(self):
        """Cleanup expired cache entries"""
        with self.lock:
            expired_count = 0
            current_time = time.time()
            
            keys_to_delete = []
            for key, entry in self.cache.items():
                if entry['expires'] and entry['expires'] < current_time:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                old_size = self.cache[key]['size']
                del self.cache[key]
                self.stats['deletes'] += 1
                self.stats['total_size'] -= old_size
                expired_count += 1
            
            if expired_count > 0:
                self.logger.debug(f"🧹 Cleaned up {expired_count} expired cache entries")
    
    def _get_size(self, value: Any) -> int:
        """Estimate size of value in bytes"""
        try:
            if isinstance(value, (str, bytes, bytearray)):
                return len(value)
            elif isinstance(value, (int, float, bool)):
                return 8
            elif isinstance(value, (list, tuple, set)):
                return sum(self._get_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(self._get_size(k) + self._get_size(v) for k, v in value.items())
            else:
                # Try to pickle and get size
                pickled = pickle.dumps(value)
                return len(pickled)
        except:
            return 1  # Minimum size
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self.lock:
            stats = self.stats.copy()
            
            # Calculate hit rate
            total_requests = stats['hits'] + stats['misses']
            stats['hit_rate'] = (stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            # Current cache info
            stats['current_size'] = len(self.cache)
            stats['memory_usage_mb'] = stats['total_size'] / (1024 * 1024)
            
            # Expired count
            current_time = time.time()
            expired_count = sum(1 for entry in self.cache.values() 
                              if entry['expires'] and entry['expires'] < current_time)
            stats['expired_entries'] = expired_count
            
            # Most accessed keys (last 100 operations)
            # This would require tracking access counts - simplified for now
            
            return stats
    
    def get_info(self) -> Dict:
        """Get detailed cache information"""
        with self.lock:
            info = {
                'max_size': self.max_size,
                'default_ttl': self.default_ttl,
                'current_entries': len(self.cache),
                'memory_usage_bytes': self.stats['total_size'],
                'memory_usage_mb': self.stats['total_size'] / (1024 * 1024),
                'stats': self.get_stats(),
                'config': {
                    'max_size': self.max_size,
                    'default_ttl': self.default_ttl
                }
            }
            
            # Sample of keys (first 10)
            info['sample_keys'] = list(self.cache.keys())[:10]
            
            # Size distribution by key prefix
            prefix_sizes = {}
            for key, entry in self.cache.items():
                prefix = key.split('_')[0] if '_' in key else key[:10]
                prefix_sizes[prefix] = prefix_sizes.get(prefix, 0) + entry['size']
            
            info['size_by_prefix'] = prefix_sizes
            
            return info
    
    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Increment integer value in cache"""
        with self.lock:
            current = self.get(key)
            if current is None:
                new_value = amount
            elif isinstance(current, int):
                new_value = current + amount
            else:
                raise TypeError(f"Value for key {key} is not an integer")
            
            self.set(key, new_value, ttl)
            return new_value
    
    def decrement(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Decrement integer value in cache"""
        return self.increment(key, -amount, ttl)
    
    def get_or_set(self, key: str, default_value: Any, ttl: Optional[int] = None) -> Any:
        """Get value or set default if not exists"""
        value = self.get(key)
        if value is None:
            self.set(key, default_value, ttl)
            return default_value
        return value
    
    def cache_user_data(self, user_id: int, data: Dict, ttl: int = 600) -> bool:
        """Cache user data with standard key format"""
        key = f"user_{user_id}"
        return self.set(key, data, ttl)
    
    def get_user_data(self, user_id: int) -> Optional[Dict]:
        """Get cached user data"""
        key = f"user_{user_id}"
        return self.get(key)
    
    def cache_game_result(self, user_id: int, game_type: str, result: Dict, ttl: int = 300) -> bool:
        """Cache game result"""
        key = f"game_{user_id}_{game_type}_{int(time.time())}"
        return self.set(key, result, ttl)
    
    def get_recent_games(self, user_id: int, limit: int = 10) -> list:
        """Get recent cached games for user"""
        pattern = f"game_{user_id}_*"
        game_keys = self.keys(pattern)
        
        # Sort by timestamp (newest first)
        game_keys.sort(reverse=True)
        
        games = []
        for key in game_keys[:limit]:
            game = self.get(key)
            if game:
                games.append(game)
        
        return games
    
    def cache_leaderboard(self, leaderboard_type: str, data: list, ttl: int = 60) -> bool:
        """Cache leaderboard data"""
        key = f"leaderboard_{leaderboard_type}"
        return self.set(key, data, ttl)
    
    def get_leaderboard(self, leaderboard_type: str) -> Optional[list]:
        """Get cached leaderboard"""
        key = f"leaderboard_{leaderboard_type}"
        return self.get(key)
    
    def clear_user_cache(self, user_id: int):
        """Clear all cache for a specific user"""
        with self.lock:
            pattern = f"user_{user_id}"
            user_keys = self.keys(pattern)
            
            for key in user_keys:
                self.delete(key)
            
            # Also clear game cache for user
            pattern = f"game_{user_id}_*"
            game_keys = self.keys(pattern)
            
            for key in game_keys:
                self.delete(key)
            
            self.logger.info(f"Cleared cache for user {user_id}: {len(user_keys) + len(game_keys)} entries")
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all cache entries matching pattern"""
        with self.lock:
            keys_to_delete = self.keys(pattern)
            
            for key in keys_to_delete:
                self.delete(key)
            
            self.logger.info(f"Cleared cache pattern '{pattern}': {len(keys_to_delete)} entries")
            return len(keys_to_delete)
    
    def backup_cache(self) -> Dict:
        """Create backup of cache (excluding expired entries)"""
        with self.lock:
            backup = {}
            current_time = time.time()
            
            for key, entry in self.cache.items():
                # Skip expired entries
                if entry['expires'] and entry['expires'] < current_time:
                    continue
                
                backup[key] = {
                    'value': entry['value'],
                    'expires': entry['expires'],
                    'created': entry['created']
                }
            
            self.logger.info(f"Cache backup created: {len(backup)} entries")
            return backup
    
    def restore_cache(self, backup: Dict):
        """Restore cache from backup"""
        with self.lock:
            self.clear()
            
            for key, entry in backup.items():
                # Calculate remaining TTL
                ttl = None
                if entry['expires']:
                    remaining = entry['expires'] - time.time()
                    if remaining > 0:
                        ttl = int(remaining)
                    else:
                        continue  # Skip expired entries
                
                self.set(key, entry['value'], ttl)
            
            self.logger.info(f"Cache restored: {len(backup)} entries")
    
    def optimize(self):
        """Optimize cache by removing least used entries"""
        with self.lock:
            initial_size = len(self.cache)
            
            # Current implementation uses LRU, so we just need to ensure size limits
            if len(self.cache) > self.max_size:
                self._evict()
            
            # Also cleanup expired entries
            self._cleanup_expired()
            
            final_size = len(self.cache)
            self.logger.info(f"Cache optimized: {initial_size - final_size} entries removed")