import hashlib
import hmac
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import re
from logger import Logger
from db import Database
from config import Config

class SecurityManager:
    """Advanced Security Management System v15.0.00"""
    
    def __init__(self, db: Database):
        self.db = db
        self.config = Config()
        self.logger = Logger.get_logger(__name__)
        
        # Security settings
        self.security_config = {
            'password_min_length': 8,
            'password_require_special': True,
            'password_require_numbers': True,
            'password_require_uppercase': True,
            'max_login_attempts': 5,
            'lockout_duration_minutes': 30,
            'session_timeout_minutes': 60,
            'require_2fa': False,
            'ip_whitelist': [],
            'ip_blacklist': [],
            'rate_limiting': True,
            'encryption_enabled': True
        }
        
        # Active sessions
        self.active_sessions = {}
        
        # Failed login attempts tracking
        self.failed_attempts = {}
        
        # Security events log
        self.security_events = []
        
        # API keys management
        self.api_keys = {}
        
        # Encryption keys (in production, these should be stored securely)
        self.encryption_keys = {
            'current': self._generate_encryption_key(),
            'previous': None,
            'rotation_date': datetime.now().isoformat()
        }
        
        self.logger.info("🔒 Security Manager v15.0.00 Initialized")
    
    # Password Security
    def hash_password(self, password: str) -> str:
        """Hash password using secure algorithm"""
        try:
            # Generate salt
            salt = secrets.token_bytes(32)
            
            # Hash password with salt using PBKDF2
            hashed = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000,  # Number of iterations
                dklen=64
            )
            
            # Combine salt and hash for storage
            combined = salt + hashed
            
            # Return as hex string
            return combined.hex()
            
        except Exception as e:
            self.logger.error(f"Password hashing error: {e}")
            raise
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            # Convert hex string back to bytes
            combined = bytes.fromhex(hashed_password)
            
            # Extract salt and hash
            salt = combined[:32]
            original_hash = combined[32:]
            
            # Hash the provided password with the same salt
            test_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000,
                dklen=64
            )
            
            # Compare hashes
            return hmac.compare_digest(original_hash, test_hash)
            
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            return False
    
    def validate_password_strength(self, password: str) -> Dict:
        """Validate password strength"""
        errors = []
        warnings = []
        
        # Check minimum length
        if len(password) < self.security_config['password_min_length']:
            errors.append(f"পাসওয়ার্ড খুব ছোট! ন্যূনতম {self.security_config['password_min_length']} অক্ষর প্রয়োজন")
        
        # Check for uppercase letters
        if self.security_config['password_require_uppercase'] and not any(c.isupper() for c in password):
            errors.append("পাসওয়ার্ডে অন্তত একটি বড় হাতের বর্ণ (A-Z) থাকতে হবে")
        
        # Check for numbers
        if self.security_config['password_require_numbers'] and not any(c.isdigit() for c in password):
            errors.append("পাসওয়ার্ডে অন্তত একটি সংখ্যা (0-9) থাকতে হবে")
        
        # Check for special characters
        if self.security_config['password_require_special'] and not any(c in string.punctuation for c in password):
            errors.append("পাসওয়ার্ডে অন্তত একটি বিশেষ অক্ষর (!@#$% ইত্যাদি) থাকতে হবে")
        
        # Check for common patterns
        common_patterns = [
            '123456', 'password', 'qwerty', 'admin', 'welcome',
            '12345678', '123456789', '1234567890'
        ]
        
        for pattern in common_patterns:
            if pattern in password.lower():
                warnings.append(f"পাসওয়ার্ডে সাধারণ প্যাটার্ন ({pattern}) পাওয়া গেছে")
                break
        
        # Check for sequential characters
        if self._has_sequential_chars(password):
            warnings.append("পাসওয়ার্ডে অনুক্রমিক অক্ষর আছে")
        
        # Check for repeated characters
        if self._has_repeated_chars(password):
            warnings.append("পাসওয়ার্ডে বারবার ব্যবহৃত অক্ষর আছে")
        
        # Calculate password strength score
        strength_score = self._calculate_password_strength(password)
        
        # Determine strength level
        if strength_score >= 80:
            strength_level = "শক্তিশালী"
        elif strength_score >= 60:
            strength_level = "মধ্যম"
        elif strength_score >= 40:
            strength_level = "দুর্বল"
        else:
            strength_level = "খুব দুর্বল"
        
        return {
            'valid': len(errors) == 0,
            'strength_score': strength_score,
            'strength_level': strength_level,
            'errors': errors,
            'warnings': warnings,
            'suggestions': self._generate_password_suggestions(errors, warnings)
        }
    
    def generate_secure_password(self, length: int = 12) -> str:
        """Generate secure random password"""
        try:
            # Define character sets
            lowercase = string.ascii_lowercase
            uppercase = string.ascii_uppercase
            digits = string.digits
            special = string.punctuation
            
            # Ensure at least one of each required type
            password_chars = [
                secrets.choice(lowercase),
                secrets.choice(uppercase),
                secrets.choice(digits),
                secrets.choice(special)
            ]
            
            # Fill remaining length with random characters from all sets
            all_chars = lowercase + uppercase + digits + special
            remaining_length = length - len(password_chars)
            
            for _ in range(remaining_length):
                password_chars.append(secrets.choice(all_chars))
            
            # Shuffle the characters
            secrets.SystemRandom().shuffle(password_chars)
            
            return ''.join(password_chars)
            
        except Exception as e:
            self.logger.error(f"Password generation error: {e}")
            # Fallback to simple random string
            return secrets.token_urlsafe(length)
    
    # Session Management
    def create_session(self, user_id: int, ip_address: str = None, 
                      user_agent: str = None) -> str:
        """Create secure session for user"""
        try:
            # Generate session token
            session_token = secrets.token_urlsafe(64)
            
            # Calculate expiration time
            expiration = datetime.now() + timedelta(
                minutes=self.security_config['session_timeout_minutes']
            )
            
            # Create session data
            session_data = {
                'user_id': user_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'expires_at': expiration.isoformat(),
                'is_valid': True
            }
            
            # Store session
            self.active_sessions[session_token] = session_data
            
            # Log session creation
            self._log_security_event(
                'session_created',
                f"Session created for user {user_id}",
                user_id,
                {'ip': ip_address, 'user_agent': user_agent[:50] if user_agent else None}
            )
            
            return session_token
            
        except Exception as e:
            self.logger.error(f"Session creation error: {e}")
            raise
    
    def validate_session(self, session_token: str, ip_address: str = None) -> Dict:
        """Validate session token"""
        try:
            # Check if session exists
            if session_token not in self.active_sessions:
                return {
                    'valid': False,
                    'reason': 'SESSION_NOT_FOUND',
                    'message': 'সেশন খুঁজে পাওয়া যায়নি'
                }
            
            session_data = self.active_sessions[session_token]
            
            # Check if session is still valid
            if not session_data['is_valid']:
                return {
                    'valid': False,
                    'reason': 'SESSION_INVALID',
                    'message': 'সেশন অবৈধ'
                }
            
            # Check expiration
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                # Session expired
                del self.active_sessions[session_token]
                return {
                    'valid': False,
                    'reason': 'SESSION_EXPIRED',
                    'message': 'সেশনের মেয়াদ শেষ'
                }
            
            # Check IP address if provided
            if ip_address and session_data['ip_address']:
                if ip_address != session_data['ip_address']:
                    # IP mismatch - potential session hijacking
                    self._log_security_event(
                        'session_ip_mismatch',
                        f"IP mismatch for session {session_token[:10]}...",
                        session_data['user_id'],
                        {'expected_ip': session_data['ip_address'], 'actual_ip': ip_address}
                    )
                    
                    # Optionally invalidate session
                    # self.invalidate_session(session_token)
                    
                    return {
                        'valid': False,
                        'reason': 'IP_MISMATCH',
                        'message': 'সেশন নিরাপত্তা ইস্যু'
                    }
            
            # Update last activity
            session_data['last_activity'] = datetime.now().isoformat()
            
            # Extend session if nearing expiration
            time_remaining = (expires_at - datetime.now()).total_seconds()
            if time_remaining < 300:  # 5 minutes remaining
                # Extend session
                new_expiration = datetime.now() + timedelta(
                    minutes=self.security_config['session_timeout_minutes']
                )
                session_data['expires_at'] = new_expiration.isoformat()
            
            return {
                'valid': True,
                'user_id': session_data['user_id'],
                'session_data': session_data
            }
            
        except Exception as e:
            self.logger.error(f"Session validation error: {e}")
            return {
                'valid': False,
                'reason': 'VALIDATION_ERROR',
                'message': 'সেশন ভ্যালিডেশন ত্রুটি'
            }
    
    def invalidate_session(self, session_token: str, reason: str = "User logout"):
        """Invalidate session"""
        try:
            if session_token in self.active_sessions:
                user_id = self.active_sessions[session_token]['user_id']
                
                # Log session invalidation
                self._log_security_event(
                    'session_invalidated',
                    f"Session invalidated: {reason}",
                    user_id,
                    {'session_token': session_token[:10] + '...'}
                )
                
                # Remove session
                del self.active_sessions[session_token]
                
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Session invalidation error: {e}")
            return False
    
    def invalidate_all_user_sessions(self, user_id: int, reason: str = "Security measure"):
        """Invalidate all sessions for a user"""
        try:
            sessions_invalidated = 0
            
            for session_token, session_data in list(self.active_sessions.items()):
                if session_data['user_id'] == user_id:
                    self.invalidate_session(session_token, reason)
                    sessions_invalidated += 1
            
            self._log_security_event(
                'all_sessions_invalidated',
                f"All sessions invalidated for user {user_id}: {reason}",
                user_id,
                {'sessions_invalidated': sessions_invalidated}
            )
            
            return sessions_invalidated
            
        except Exception as e:
            self.logger.error(f"Error invalidating all sessions: {e}")
            return 0
    
    # Login Security
    def track_login_attempt(self, user_id: int, ip_address: str, success: bool):
        """Track login attempts for rate limiting"""
        try:
            key = f"{user_id}:{ip_address}"
            
            if success:
                # Reset failed attempts on successful login
                if key in self.failed_attempts:
                    del self.failed_attempts[key]
            else:
                # Increment failed attempts
                if key not in self.failed_attempts:
                    self.failed_attempts[key] = {
                        'count': 0,
                        'first_attempt': datetime.now().isoformat(),
                        'last_attempt': datetime.now().isoformat(),
                        'ip_address': ip_address,
                        'user_id': user_id
                    }
                
                self.failed_attempts[key]['count'] += 1
                self.failed_attempts[key]['last_attempt'] = datetime.now().isoformat()
                
                # Check if lockout threshold reached
                if self.failed_attempts[key]['count'] >= self.security_config['max_login_attempts']:
                    lockout_duration = self.security_config['lockout_duration_minutes']
                    lockout_until = datetime.now() + timedelta(minutes=lockout_duration)
                    
                    self.failed_attempts[key]['locked_until'] = lockout_until.isoformat()
                    
                    self._log_security_event(
                        'account_locked',
                        f"Account locked due to {self.failed_attempts[key]['count']} failed login attempts",
                        user_id,
                        {
                            'ip_address': ip_address,
                            'lockout_until': lockout_until.isoformat(),
                            'failed_attempts': self.failed_attempts[key]['count']
                        }
                    )
            
            # Log the attempt
            self._log_security_event(
                'login_attempt',
                f"Login attempt {'successful' if success else 'failed'}",
                user_id,
                {'ip_address': ip_address, 'success': success}
            )
            
        except Exception as e:
            self.logger.error(f"Login tracking error: {e}")
    
    def check_login_allowed(self, user_id: int, ip_address: str) -> Dict:
        """Check if login is allowed (rate limiting)"""
        try:
            key = f"{user_id}:{ip_address}"
            
            if key not in self.failed_attempts:
                return {
                    'allowed': True,
                    'remaining_attempts': self.security_config['max_login_attempts']
                }
            
            attempts = self.failed_attempts[key]
            
            # Check if account is locked
            if 'locked_until' in attempts:
                locked_until = datetime.fromisoformat(attempts['locked_until'])
                
                if datetime.now() < locked_until:
                    # Still locked
                    time_remaining = (locked_until - datetime.now()).total_seconds()
                    
                    return {
                        'allowed': False,
                        'reason': 'ACCOUNT_LOCKED',
                        'message': f'অ্যাকাউন্ট লক করা হয়েছে। {int(time_remaining // 60)} মিনিট অপেক্ষা করুন',
                        'locked_until': attempts['locked_until'],
                        'failed_attempts': attempts['count']
                    }
                else:
                    # Lock expired, reset
                    del self.failed_attempts[key]
                    return {
                        'allowed': True,
                        'remaining_attempts': self.security_config['max_login_attempts']
                    }
            
            # Check remaining attempts
            remaining = self.security_config['max_login_attempts'] - attempts['count']
            
            if remaining <= 0:
                # Should have been locked, but handle edge case
                return {
                    'allowed': False,
                    'reason': 'MAX_ATTEMPTS_EXCEEDED',
                    'message': 'সর্বোচ্চ লগইন চেষ্টা শেষ',
                    'failed_attempts': attempts['count']
                }
            
            return {
                'allowed': True,
                'remaining_attempts': remaining,
                'failed_attempts': attempts['count']
            }
            
        except Exception as e:
            self.logger.error(f"Login check error: {e}")
            return {
                'allowed': True,  # Allow on error to prevent blocking legitimate users
                'reason': 'CHECK_ERROR'
            }
    
    def unlock_account(self, user_id: int, ip_address: str = None) -> bool:
        """Unlock user account"""
        try:
            if ip_address:
                # Unlock specific IP
                key = f"{user_id}:{ip_address}"
                if key in self.failed_attempts:
                    del self.failed_attempts[key]
                    
                    self._log_security_event(
                        'account_unlocked',
                        f"Account unlocked for IP {ip_address}",
                        user_id,
                        {'ip_address': ip_address}
                    )
                    
                    return True
            else:
                # Unlock all IPs for user
                keys_to_remove = []
                for key in self.failed_attempts.keys():
                    if key.startswith(f"{user_id}:"):
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.failed_attempts[key]
                
                if keys_to_remove:
                    self._log_security_event(
                        'account_unlocked',
                        f"Account unlocked for all IPs",
                        user_id,
                        {'ips_unlocked': len(keys_to_remove)}
                    )
                    
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Account unlock error: {e}")
            return False
    
    # Encryption
    def encrypt_data(self, data: str, key_id: str = 'current') -> str:
        """Encrypt sensitive data"""
        try:
            if not self.security_config['encryption_enabled']:
                return data
            
            # Get encryption key
            key = self.encryption_keys.get(key_id)
            if not key:
                raise ValueError(f"Encryption key not found: {key_id}")
            
            # Generate random IV
            iv = secrets.token_bytes(16)
            
            # Create cipher
            from cryptography.fernet import Fernet
            cipher = Fernet(key)
            
            # Encrypt data
            encrypted = cipher.encrypt(data.encode('utf-8'))
            
            # Combine IV and encrypted data
            result = iv + encrypted
            
            # Return as base64
            import base64
            return base64.b64encode(result).decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Data encryption error: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str, key_id: str = 'current') -> str:
        """Decrypt sensitive data"""
        try:
            if not self.security_config['encryption_enabled']:
                return encrypted_data
            
            # Get encryption key
            key = self.encryption_keys.get(key_id)
            if not key:
                # Try previous key for backward compatibility
                key = self.encryption_keys.get('previous')
                if not key:
                    raise ValueError("Encryption key not found")
            
            import base64
            from cryptography.fernet import Fernet
            
            # Decode base64
            data = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extract IV and encrypted data
            iv = data[:16]
            encrypted = data[16:]
            
            # Decrypt
            cipher = Fernet(key)
            decrypted = cipher.decrypt(encrypted)
            
            return decrypted.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Data decryption error: {e}")
            raise
    
    def rotate_encryption_keys(self):
        """Rotate encryption keys"""
        try:
            self.logger.info("Rotating encryption keys...")
            
            # Move current key to previous
            self.encryption_keys['previous'] = self.encryption_keys['current']
            
            # Generate new current key
            self.encryption_keys['current'] = self._generate_encryption_key()
            self.encryption_keys['rotation_date'] = datetime.now().isoformat()
            
            self._log_security_event(
                'encryption_keys_rotated',
                "Encryption keys rotated",
                None,
                {'rotation_date': self.encryption_keys['rotation_date']}
            )
            
            self.logger.info("Encryption keys rotated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Key rotation error: {e}")
            return False
    
    # API Key Management
    def generate_api_key(self, user_id: int, name: str, permissions: List[str]) -> Dict:
        """Generate API key for user"""
        try:
            # Generate key
            api_key = secrets.token_urlsafe(32)
            
            # Generate key ID
            key_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            
            # Create key data
            key_data = {
                'key_id': key_id,
                'user_id': user_id,
                'name': name,
                'permissions': permissions,
                'created_at': datetime.now().isoformat(),
                'last_used': None,
                'is_active': True,
                'usage_count': 0
            }
            
            # Store key (in production, hash the key before storing)
            self.api_keys[key_id] = key_data
            
            # Log key generation
            self._log_security_event(
                'api_key_generated',
                f"API key generated: {name}",
                user_id,
                {'key_id': key_id, 'permissions': permissions}
            )
            
            return {
                'api_key': api_key,
                'key_id': key_id,
                'key_data': key_data,
                'warning': 'এই API কী সেভ করে রাখুন! এটি শুধু একবার দেখানো হবে।'
            }
            
        except Exception as e:
            self.logger.error(f"API key generation error: {e}")
            raise
    
    def validate_api_key(self, api_key: str, required_permissions: List[str] = None) -> Dict:
        """Validate API key"""
        try:
            # Calculate key ID
            key_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            
            # Check if key exists
            if key_id not in self.api_keys:
                return {
                    'valid': False,
                    'reason': 'KEY_NOT_FOUND',
                    'message': 'API কী খুঁজে পাওয়া যায়নি'
                }
            
            key_data = self.api_keys[key_id]
            
            # Check if key is active
            if not key_data['is_active']:
                return {
                    'valid': False,
                    'reason': 'KEY_INACTIVE',
                    'message': 'API কী নিষ্ক্রিয়'
                }
            
            # Check permissions if required
            if required_permissions:
                user_permissions = set(key_data['permissions'])
                required_permissions_set = set(required_permissions)
                
                if not required_permissions_set.issubset(user_permissions):
                    return {
                        'valid': False,
                        'reason': 'INSUFFICIENT_PERMISSIONS',
                        'message': 'পর্যাপ্ত অনুমতি নেই',
                        'required': required_permissions,
                        'has': key_data['permissions']
                    }
            
            # Update last used and usage count
            key_data['last_used'] = datetime.now().isoformat()
            key_data['usage_count'] += 1
            
            return {
                'valid': True,
                'key_data': key_data,
                'user_id': key_data['user_id']
            }
            
        except Exception as e:
            self.logger.error(f"API key validation error: {e}")
            return {
                'valid': False,
                'reason': 'VALIDATION_ERROR',
                'message': 'API কী ভ্যালিডেশন ত্রুটি'
            }
    
    def revoke_api_key(self, key_id: str, user_id: int = None, reason: str = "Revoked by admin") -> bool:
        """Revoke API key"""
        try:
            if key_id not in self.api_keys:
                return False
            
            # Check user authorization if user_id provided
            if user_id and self.api_keys[key_id]['user_id'] != user_id:
                return False
            
            # Revoke key
            self.api_keys[key_id]['is_active'] = False
            self.api_keys[key_id]['revoked_at'] = datetime.now().isoformat()
            self.api_keys[key_id]['revoke_reason'] = reason
            
            self._log_security_event(
                'api_key_revoked',
                f"API key revoked: {reason}",
                user_id or self.api_keys[key_id]['user_id'],
                {'key_id': key_id, 'reason': reason}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"API key revocation error: {e}")
            return False
    
    # Input Validation and Sanitization
    def sanitize_input(self, input_str: str, input_type: str = 'text') -> str:
        """Sanitize user input"""
        try:
            if not input_str:
                return ""
            
            # Trim whitespace
            sanitized = input_str.strip()
            
            # Type-specific sanitization
            if input_type == 'email':
                sanitized = sanitized.lower()
                # Basic email validation
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', sanitized):
                    raise ValueError("Invalid email format")
            
            elif input_type == 'phone':
                # Remove all non-digit characters
                sanitized = re.sub(r'\D', '', sanitized)
            
            elif input_type == 'username':
                # Allow only alphanumeric, underscore, and dot
                sanitized = re.sub(r'[^\w\.]', '', sanitized)
                if len(sanitized) < 3:
                    raise ValueError("Username too short")
                if len(sanitized) > 20:
                    sanitized = sanitized[:20]
            
            elif input_type == 'name':
                # Allow letters, spaces, and basic punctuation
                sanitized = re.sub(r'[^\w\s\.\-]', '', sanitized)
                if len(sanitized) > 50:
                    sanitized = sanitized[:50]
            
            elif input_type == 'text':
                # General text - remove potentially dangerous characters
                # Remove script tags
                sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.IGNORECASE)
                # Remove event handlers
                sanitized = re.sub(r'on\w+=".*?"', '', sanitized, flags=re.IGNORECASE)
                # Remove JavaScript protocol
                sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
                # Limit length
                if len(sanitized) > 1000:
                    sanitized = sanitized[:1000]
            
            elif input_type == 'password':
                # Don't modify passwords, they'll be hashed anyway
                pass
            
            else:
                # Default sanitization
                if len(sanitized) > 500:
                    sanitized = sanitized[:500]
            
            return sanitized
            
        except Exception as e:
            self.logger.error(f"Input sanitization error: {e}")
            raise
    
    def validate_csrf_token(self, token: str, session_token: str) -> bool:
        """Validate CSRF token"""
        try:
            # In production, this would validate against session-specific token
            # For now, simple implementation
            if not token or not session_token:
                return False
            
            # Check if session exists
            if session_token not in self.active_sessions:
                return False
            
            # Generate expected token from session data
            session_data = self.active_sessions[session_token]
            expected_token = self._generate_csrf_token(session_data)
            
            # Compare tokens
            return hmac.compare_digest(token, expected_token)
            
        except Exception as e:
            self.logger.error(f"CSRF validation error: {e}")
            return False
    
    def generate_csrf_token(self, session_token: str) -> str:
        """Generate CSRF token for session"""
        try:
            if session_token not in self.active_sessions:
                raise ValueError("Session not found")
            
            session_data = self.active_sessions[session_token]
            return self._generate_csrf_token(session_data)
            
        except Exception as e:
            self.logger.error(f"CSRF token generation error: {e}")
            raise
    
    # Security Monitoring
    def check_security_health(self) -> Dict:
        """Check security system health"""
        try:
            health = {
                'overall': 'healthy',
                'checks': [],
                'issues': [],
                'statistics': {}
            }
            
            # Check active sessions
            active_sessions = len(self.active_sessions)
            health['statistics']['active_sessions'] = active_sessions
            
            if active_sessions > 1000:
                health['checks'].append({
                    'check': 'active_sessions',
                    'status': 'warning',
                    'message': f'অনেক বেশি অ্যাকটিভ সেশন: {active_sessions}'
                })
            
            # Check failed login attempts
            failed_attempts = len(self.failed_attempts)
            health['statistics']['failed_attempts'] = failed_attempts
            
            # Check locked accounts
            locked_accounts = sum(1 for attempt in self.failed_attempts.values() 
                                 if 'locked_until' in attempt)
            health['statistics']['locked_accounts'] = locked_accounts
            
            if locked_accounts > 10:
                health['checks'].append({
                    'check': 'locked_accounts',
                    'status': 'warning',
                    'message': f'অনেক বেশি লক করা অ্যাকাউন্ট: {locked_accounts}'
                })
            
            # Check encryption key age
            rotation_date = datetime.fromisoformat(self.encryption_keys['rotation_date'])
            days_since_rotation = (datetime.now() - rotation_date).days
            health['statistics']['days_since_key_rotation'] = days_since_rotation
            
            if days_since_rotation > 90:
                health['checks'].append({
                    'check': 'encryption_keys',
                    'status': 'warning',
                    'message': f'এনক্রিপশন কী পুরনো: {days_since_rotation} দিন'
                })
            
            # Check security events
            recent_events = [e for e in self.security_events 
                           if datetime.fromisoformat(e['timestamp']) > 
                           datetime.now() - timedelta(hours=24)]
            health['statistics']['recent_security_events'] = len(recent_events)
            
            # Check for critical events
            critical_events = [e for e in recent_events 
                             if e.get('level') == 'critical']
            
            if critical_events:
                health['checks'].append({
                    'check': 'critical_events',
                    'status': 'critical',
                    'message': f'গুরুত্বপূর্ণ সিকিউরিটি ইভেন্ট: {len(critical_events)}টি'
                })
                health['overall'] = 'critical'
            
            # Determine overall status
            if any(check['status'] == 'critical' for check in health['checks']):
                health['overall'] = 'critical'
            elif any(check['status'] == 'warning' for check in health['checks']):
                health['overall'] = 'warning'
            else:
                health['overall'] = 'healthy'
            
            return health
            
        except Exception as e:
            self.logger.error(f"Security health check error: {e}")
            return {
                'overall': 'error',
                'error': str(e)
            }
    
    def get_security_report(self, period: str = '24h') -> Dict:
        """Generate security report"""
        try:
            # Calculate time range
            if period == '24h':
                start_time = datetime.now() - timedelta(hours=24)
            elif period == '7d':
                start_time = datetime.now() - timedelta(days=7)
            elif period == '30d':
                start_time = datetime.now() - timedelta(days=30)
            else:
                start_time = datetime.now() - timedelta(hours=24)
            
            # Filter events
            events = [e for e in self.security_events 
                     if datetime.fromisoformat(e['timestamp']) > start_time]
            
            # Categorize events
            categories = defaultdict(int)
            for event in events:
                categories[event.get('event_type', 'unknown')] += 1
            
            # Count by severity
            severity_counts = defaultdict(int)
            for event in events:
                severity_counts[event.get('level', 'info')] += 1
            
            # Get top IPs with failed attempts
            suspicious_ips = defaultdict(int)
            for attempt in self.failed_attempts.values():
                if datetime.fromisoformat(attempt.get('last_attempt', start_time.isoformat())) > start_time:
                    suspicious_ips[attempt['ip_address']] += attempt['count']
            
            top_suspicious_ips = sorted(suspicious_ips.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'period': period,
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'summary': {
                    'total_events': len(events),
                    'event_categories': dict(categories),
                    'severity_counts': dict(severity_counts),
                    'active_sessions': len(self.active_sessions),
                    'locked_accounts': sum(1 for a in self.failed_attempts.values() 
                                          if 'locked_until' in a),
                    'api_keys': len(self.api_keys)
                },
                'top_suspicious_ips': [{'ip': ip, 'attempts': count} 
                                      for ip, count in top_suspicious_ips],
                'recent_critical_events': [e for e in events[-10:] 
                                          if e.get('level') in ['critical', 'high']]
            }
            
        except Exception as e:
            self.logger.error(f"Security report error: {e}")
            return {'error': str(e)}
    
    # Helper methods
    def _generate_encryption_key(self):
        """Generate encryption key"""
        from cryptography.fernet import Fernet
        return Fernet.generate_key()
    
    def _calculate_password_strength(self, password: str) -> int:
        """Calculate password strength score (0-100)"""
        score = 0
        
        # Length contribution
        length = len(password)
        score += min(length * 4, 40)  # Up to 40 points for length
        
        # Character variety
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in string.punctuation for c in password)
        
        variety_score = (has_upper + has_lower + has_digit + has_special) * 10
        score += variety_score
        
        # Deductions for patterns
        if self._has_sequential_chars(password):
            score -= 10
        
        if self._has_repeated_chars(password):
            score -= 5
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))
    
    def _has_sequential_chars(self, password: str) -> bool:
        """Check for sequential characters"""
        sequences = ['123', '234', '345', '456', '567', '678', '789', '890',
                    'abc', 'bcd', 'cde', 'def', 'efg', 'fgh', 'ghi', 'hij',
                    'ijk', 'jkl', 'klm', 'lmn', 'mno', 'nop', 'opq', 'pqr',
                    'qrs', 'rst', 'stu', 'tuv', 'uvw', 'vwx', 'wxy', 'xyz']
        
        password_lower = password.lower()
        for seq in sequences:
            if seq in password_lower:
                return True
        
        return False
    
    def _has_repeated_chars(self, password: str) -> bool:
        """Check for repeated characters"""
       