import re
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import phonenumbers
from email_validator import validate_email, EmailNotValidError

class Validator:
    """Advanced Validation System v15.0.00"""
    
    def __init__(self):
        # Regex patterns
        self.patterns = {
            'username': r'^[a-zA-Z0-9_]{3,20}$',
            'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
            'telegram_username': r'^@?[a-zA-Z0-9_]{5,32}$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^\+?[1-9]\d{1,14}$',
            'bangladeshi_phone': r'^01[3-9]\d{8}$',
            'trx_id': r'^[A-Z0-9]{8,20}$',
            'numeric': r'^[0-9]+$',
            'decimal': r'^[0-9]+(\.[0-9]{1,2})?$',
            'date_yyyy_mm_dd': r'^\d{4}-\d{2}-\d{2}$',
            'time_hh_mm': r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$',
            'url': r'^https?://[^\s]+$',
            'hashtag': r'^#[a-zA-Z0-9_]+$',
            'emoji': r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+'
        }
        
        # Validation rules
        self.rules = {
            'username': {
                'min_length': 3,
                'max_length': 20,
                'allowed_chars': 'letters, numbers, underscore',
                'blacklist': ['admin', 'root', 'system', 'bot', 'null', 'undefined']
            },
            'password': {
                'min_length': 8,
                'requirements': ['lowercase', 'uppercase', 'digit', 'special_char'],
                'common_passwords': ['password', '123456', 'qwerty', 'admin', 'letmein']
            },
            'amount': {
                'min': 0.01,
                'max': 1000000,
                'precision': 2
            },
            'text': {
                'min_length': 1,
                'max_length': 5000,
                'disallowed_patterns': [
                    r'<script.*?>.*?</script>',  # Script tags
                    r'on\w+=".*?"',  # Event handlers
                    r'javascript:',  # JavaScript protocol
                    r'data:'  # Data URLs
                ]
            }
        }
        
        # Country-specific validation rules
        self.country_rules = {
            'BD': {  # Bangladesh
                'phone_length': 11,
                'phone_prefix': '880',
                'currency': 'BDT',
                'min_age': 18
            },
            'US': {
                'phone_length': 10,
                'phone_prefix': '1',
                'currency': 'USD',
                'min_age': 13
            },
            'IN': {
                'phone_length': 10,
                'phone_prefix': '91',
                'currency': 'INR',
                'min_age': 18
            }
        }
        
        print("✅ Advanced Validator v15.0.00 Initialized")
    
    def validate_telegram_id(self, user_id: Union[int, str]) -> Dict:
        """Validate Telegram user ID"""
        try:
            user_id_int = int(user_id)
            
            if user_id_int <= 0:
                return {
                    'valid': False,
                    'message': 'ইউজার আইডি শূন্য বা নেগেটিভ হতে পারে না!',
                    'code': 'INVALID_ID'
                }
            
            # Telegram user IDs are typically 9-10 digits
            if not (100000000 <= user_id_int <= 9999999999):
                return {
                    'valid': False,
                    'message': 'ইউজার আইডি ভুল ফরম্যাট!',
                    'code': 'INVALID_FORMAT'
                }
            
            return {
                'valid': True,
                'message': 'ইউজার আইডি বৈধ',
                'normalized_id': user_id_int
            }
        
        except ValueError:
            return {
                'valid': False,
                'message': 'ইউজার আইডি সংখ্যা হতে হবে!',
                'code': 'NOT_NUMERIC'
            }
    
    def validate_username(self, username: str, check_blacklist: bool = True) -> Dict:
        """Validate username"""
        if not username:
            return {
                'valid': False,
                'message': 'ইউজারনেম খালি হতে পারে না!',
                'code': 'EMPTY'
            }
        
        # Check length
        min_len = self.rules['username']['min_length']
        max_len = self.rules['username']['max_length']
        
        if len(username) < min_len:
            return {
                'valid': False,
                'message': f'ইউজারনেম খুব ছোট! ন্যূনতম {min_len} অক্ষর প্রয়োজন।',
                'code': 'TOO_SHORT'
            }
        
        if len(username) > max_len:
            return {
                'valid': False,
                'message': f'ইউজারনেম খুব বড়! সর্বোচ্চ {max_len} অক্ষর হতে পারে।',
                'code': 'TOO_LONG'
            }
        
        # Check pattern
        if not re.match(self.patterns['username'], username):
            return {
                'valid': False,
                'message': f'ইউজারনেমে শুধুমাত্র ইংরেজি অক্ষর, সংখ্যা ও আন্ডারস্কোর (_) থাকতে পারে।',
                'code': 'INVALID_CHARS'
            }
        
        # Check blacklist
        if check_blacklist:
            username_lower = username.lower()
            for banned in self.rules['username']['blacklist']:
                if banned in username_lower:
                    return {
                        'valid': False,
                        'message': 'এই ইউজারনেম ব্যবহার করা যাবে না!',
                        'code': 'BLACKLISTED'
                    }
        
        # Check for offensive words
        offensive_patterns = [
            r'(?i)admin',
            r'(?i)root',
            r'(?i)moderator',
            r'(?i)owner',
            r'(?i)system'
        ]
        
        for pattern in offensive_patterns:
            if re.search(pattern, username):
                return {
                    'valid': False,
                    'message': 'ইউজারনেমে বিশেষ টাইটেল ব্যবহার করা যাবে না!',
                    'code': 'OFFENSIVE'
                }
        
        return {
            'valid': True,
            'message': 'ইউজারনেম বৈধ',
            'normalized': username,
            'suggestions': self._generate_username_suggestions(username) if len(username) < 5 else []
        }
    
    def _generate_username_suggestions(self, username: str) -> List[str]:
        """Generate username suggestions"""
        suggestions = []
        
        if len(username) < 5:
            # Add random numbers
            import random
            for _ in range(3):
                suggestion = f"{username}{random.randint(100, 999)}"
                if self.validate_username(suggestion, check_blacklist=False)['valid']:
                    suggestions.append(suggestion)
        
        return suggestions[:3]
    
    def validate_password(self, password: str) -> Dict:
        """Validate password strength"""
        if not password:
            return {
                'valid': False,
                'message': 'পাসওয়ার্ড খালি হতে পারে না!',
                'code': 'EMPTY'
            }
        
        # Check length
        min_len = self.rules['password']['min_length']
        
        if len(password) < min_len:
            return {
                'valid': False,
                'message': f'পাসওয়ার্ড খুব ছোট! ন্যূনতম {min_len} অক্ষর প্রয়োজন।',
                'code': 'TOO_SHORT'
            }
        
        # Check for common passwords
        password_lower = password.lower()
        for common in self.rules['password']['common_passwords']:
            if common in password_lower or password_lower == common:
                return {
                    'valid': False,
                    'message': 'এই পাসওয়ার্ড খুবই সাধারণ, অন্য পাসওয়ার্ড ব্যবহার করুন!',
                    'code': 'COMMON_PASSWORD'
                }
        
        # Check requirements
        requirements = self.rules['password']['requirements']
        issues = []
        
        if 'lowercase' in requirements and not re.search(r'[a-z]', password):
            issues.append('ছোট হাতের অক্ষর')
        
        if 'uppercase' in requirements and not re.search(r'[A-Z]', password):
            issues.append('বড় হাতের অক্ষর')
        
        if 'digit' in requirements and not re.search(r'\d', password):
            issues.append('সংখ্যা')
        
        if 'special_char' in requirements and not re.search(r'[@$!%*?&]', password):
            issues.append('বিশেষ অক্ষর (@, $, !, %, *, ?, &)')
        
        if issues:
            return {
                'valid': False,
                'message': f'পাসওয়ার্ডে অবশ্যই থাকতে হবে: {", ".join(issues)}',
                'code': 'REQUIREMENTS_NOT_MET',
                'missing': issues
            }
        
        # Check for sequential characters
        if self._has_sequential_chars(password):
            return {
                'valid': False,
                'message': 'পাসওয়ার্ডে ধারাবাহিক অক্ষর ব্যবহার করবেন না!',
                'code': 'SEQUENTIAL_CHARS'
            }
        
        # Check for repeated characters
        if self._has_repeated_chars(password):
            return {
                'valid': False,
                'message': 'পাসওয়ার্ডে একই অক্ষর বারবার ব্যবহার করবেন না!',
                'code': 'REPEATED_CHARS'
            }
        
        # Calculate password strength
        strength = self._calculate_password_strength(password)
        
        return {
            'valid': True,
            'message': 'পাসওয়ার্ড বৈধ',
            'strength': strength,
            'strength_text': self._get_strength_text(strength),
            'suggestions': self._generate_password_suggestions() if strength < 80 else []
        }
    
    def _has_sequential_chars(self, text: str, length: int = 3) -> bool:
        """Check for sequential characters"""
        for i in range(len(text) - length + 1):
            substring = text[i:i+length].lower()
            
            # Check numeric sequence
            if substring.isdigit():
                if self._is_sequential_numeric(substring):
                    return True
            
            # Check alphabetical sequence
            if substring.isalpha():
                if self._is_sequential_alpha(substring):
                    return True
        
        return False
    
    def _is_sequential_numeric(self, text: str) -> bool:
        """Check if text is sequential numbers"""
        for i in range(len(text) - 1):
            if ord(text[i+1]) - ord(text[i]) != 1:
                return False
        return True
    
    def _is_sequential_alpha(self, text: str) -> bool:
        """Check if text is sequential letters"""
        text = text.lower()
        for i in range(len(text) - 1):
            if ord(text[i+1]) - ord(text[i]) != 1:
                return False
        return True
    
    def _has_repeated_chars(self, text: str, max_repeat: int = 3) -> bool:
        """Check for repeated characters"""
        import itertools
        for char, group in itertools.groupby(text):
            if len(list(group)) > max_repeat:
                return True
        return False
    
    def _calculate_password_strength(self, password: str) -> int:
        """Calculate password strength (0-100)"""
        score = 0
        
        # Length score (max 30)
        length = len(password)
        if length >= 8:
            score += 10
        if length >= 12:
            score += 10
        if length >= 16:
            score += 10
        
        # Character variety score (max 40)
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[@$!%*?&]', password))
        
        score += (has_lower + has_upper + has_digit + has_special) * 10
        
        # Entropy score (max 30)
        import math
        char_set_size = 0
        if has_lower:
            char_set_size += 26
        if has_upper:
            char_set_size += 26
        if has_digit:
            char_set_size += 10
        if has_special:
            char_set_size += 8  # 8 special characters in our pattern
        
        if char_set_size > 0:
            entropy = length * math.log2(char_set_size)
            if entropy > 50:
                score += 30
            elif entropy > 40:
                score += 20
            elif entropy > 30:
                score += 10
        
        # Penalties
        if self._has_sequential_chars(password):
            score -= 10
        
        if self._has_repeated_chars(password):
            score -= 10
        
        # Check for personal info patterns (simplified)
        common_patterns = [
            r'password', r'admin', r'123456', r'qwerty',
            r'asdfgh', r'zxcvbn', r'iloveyou', r'letmein'
        ]
        
        for pattern in common_patterns:
            if pattern in password.lower():
                score -= 20
                break
        
        return max(0, min(100, score))
    
    def _get_strength_text(self, strength: int) -> str:
        """Get strength description"""
        if strength >= 80:
            return 'অত্যন্ত শক্তিশালী 💪'
        elif strength >= 60:
            return 'শক্তিশালী 👍'
        elif strength >= 40:
            return 'মাঝারি 📊'
        elif strength >= 20:
            return 'দুর্বল ⚠️'
        else:
            return 'অত্যন্ত দুর্বল ❌'
    
    def _generate_password_suggestions(self) -> List[str]:
        """Generate password suggestions"""
        import random
        import string
        
        suggestions = []
        
        for _ in range(3):
            # Generate random password
            length = random.randint(12, 16)
            lowercase = string.ascii_lowercase
            uppercase = string.ascii_uppercase
            digits = string.digits
            special = '@$!%*?&'
            
            # Ensure at least one of each type
            password = [
                random.choice(lowercase),
                random.choice(uppercase),
                random.choice(digits),
                random.choice(special)
            ]
            
            # Fill remaining
            all_chars = lowercase + uppercase + digits + special
            password.extend(random.choice(all_chars) for _ in range(length - 4))
            
            # Shuffle
            random.shuffle(password)
            suggestions.append(''.join(password))
        
        return suggestions
    
    def validate_email(self, email: str) -> Dict:
        """Validate email address"""
        if not email:
            return {
                'valid': False,
                'message': 'ইমেইল খালি হতে পারে না!',
                'code': 'EMPTY'
            }
        
        # Basic regex validation
        if not re.match(self.patterns['email'], email):
            return {
                'valid': False,
                'message': 'ইমেইল ভুল ফরম্যাট!',
                'code': 'INVALID_FORMAT'
            }
        
        try:
            # Advanced validation using email-validator
            valid = validate_email(email, check_deliverability=False)
            normalized_email = valid.email
            
            # Check for disposable email domains
            disposable_domains = [
                'tempmail.com', 'mailinator.com', '10minutemail.com',
                'guerrillamail.com', 'yopmail.com', 'trashmail.com'
            ]
            
            domain = normalized_email.split('@')[1].lower()
            if any(disposable in domain for disposable in disposable_domains):
                return {
                    'valid': False,
                    'message': 'ডিসপোজেবল ইমেইল ব্যবহার করা যাবে না!',
                    'code': 'DISPOSABLE_EMAIL'
                }
            
            return {
                'valid': True,
                'message': 'ইমেইল বৈধ',
                'normalized': normalized_email,
                'domain': domain
            }
        
        except EmailNotValidError as e:
            return {
                'valid': False,
                'message': f'ইমেইল ভ্যালিডেশন ব্যর্থ: {str(e)}',
                'code': 'VALIDATION_FAILED'
            }
    
    def validate_phone(self, phone: str, country_code: str = 'BD') -> Dict:
        """Validate phone number"""
        if not phone:
            return {
                'valid': False,
                'message': 'ফোন নম্বর খালি হতে পারে না!',
                'code': 'EMPTY'
            }
        
        # Clean phone number
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        
        if not cleaned_phone:
            return {
                'valid': False,
                'message': 'ফোন নম্বরে শুধুমাত্র সংখ্যা ও + চিহ্ন থাকতে পারে!',
                'code': 'INVALID_CHARS'
            }
        
        # Country-specific validation
        if country_code == 'BD':
            # Bangladeshi phone validation
            if not re.match(self.patterns['bangladeshi_phone'], cleaned_phone):
                return {
                    'valid': False,
                    'message': 'বাংলাদেশী ফোন নম্বর ভুল ফরম্যাট! (01XXXXXXXXX)',
                    'code': 'INVALID_BD_PHONE'
                }
            
            # Check operator prefix
            operator_prefix = cleaned_phone[0:3]
            valid_prefixes = ['013', '014', '015', '016', '017', '018', '019']
            
            if operator_prefix not in valid_prefixes:
                return {
                    'valid': False,
                    'message': 'ফোন নম্বরের অপারেটর কোড ভুল!',
                    'code': 'INVALID_OPERATOR'
                }
            
            return {
                'valid': True,
                'message': 'ফোন নম্বর বৈধ',
                'normalized': f'+880{cleaned_phone[1:]}' if cleaned_phone.startswith('0') else f'+880{cleaned_phone}',
                'operator': self._get_operator_name(operator_prefix),
                'country': 'Bangladesh'
            }
        
        else:
            # International validation using phonenumbers
            try:
                import phonenumbers
                parsed_number = phonenumbers.parse(cleaned_phone, country_code)
                
                if not phonenumbers.is_valid_number(parsed_number):
                    return {
                        'valid': False,
                        'message': 'ফোন নম্বর ভুল!',
                        'code': 'INVALID_NUMBER'
                    }
                
                formatted = phonenumbers.format_number(
                    parsed_number, 
                    phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                
                return {
                    'valid': True,
                    'message': 'ফোন নম্বর বৈধ',
                    'normalized': formatted,
                    'country': phonenumbers.region_code_for_number(parsed_number)
                }
            
            except phonenumbers.NumberParseException:
                return {
                    'valid': False,
                    'message': 'ফোন নম্বর পার্স করতে ব্যর্থ!',
                    'code': 'PARSE_ERROR'
                }
    
    def _get_operator_name(self, prefix: str) -> str:
        """Get mobile operator name from prefix"""
        operators = {
            '013': 'গ্রামীণফোন',
            '014': 'বাংলালিংক',
            '015': 'টেলিটক',
            '016': 'এয়ারটেল',
            '017': 'জিপি',
            '018': 'রবি',
            '019': 'বাংলালিংক'
        }
        return operators.get(prefix, 'অজানা')
    
    def validate_amount(self, amount: Union[int, float, str], 
                       min_amount: float = None, 
                       max_amount: float = None) -> Dict:
        """Validate monetary amount"""
        try:
            # Convert to float
            if isinstance(amount, str):
                amount_str = amount.strip()
                if not amount_str:
                    return {
                        'valid': False,
                        'message': 'পরিমাণ খালি হতে পারে না!',
                        'code': 'EMPTY'
                    }
                
                # Check decimal format
                if not re.match(self.patterns['decimal'], amount_str):
                    return {
                        'valid': False,
                        'message': 'পরিমাণ ভুল ফরম্যাট!',
                        'code': 'INVALID_FORMAT'
                    }
                
                amount_float = float(amount_str)
            else:
                amount_float = float(amount)
            
            # Check if positive
            if amount_float <= 0:
                return {
                    'valid': False,
                    'message': 'পরিমাণ শূন্য বা নেগেটিভ হতে পারে না!',
                    'code': 'NON_POSITIVE'
                }
            
            # Check against default limits
            default_min = self.rules['amount']['min']
            default_max = self.rules['amount']['max']
            
            if amount_float < default_min:
                return {
                    'valid': False,
                    'message': f'ন্যূনতম পরিমাণ {default_min}!',
                    'code': 'BELOW_MIN'
                }
            
            if amount_float > default_max:
                return {
                    'valid': False,
                    'message': f'সর্বোচ্চ পরিমাণ {default_max}!',
                    'code': 'ABOVE_MAX'
                }
            
            # Check custom limits
            if min_amount is not None and amount_float < min_amount:
                return {
                    'valid': False,
                    'message': f'ন্যূনতম পরিমাণ {min_amount}!',
                    'code': 'BELOW_CUSTOM_MIN'
                }
            
            if max_amount is not None and amount_float > max_amount:
                return {
                    'valid': False,
                    'message': f'সর্বোচ্চ পরিমাণ {max_amount}!',
                    'code': 'ABOVE_CUSTOM_MAX'
                }
            
            # Check precision
            precision = self.rules['amount']['precision']
            rounded = round(amount_float, precision)
            
            if abs(amount_float - rounded) > 0.0001:
                return {
                    'valid': False,
                    'message': f'পরিমাণ সর্বোচ্চ {precision} দশমিক পর্যন্ত হতে পারে!',
                    'code': 'INVALID_PRECISION'
                }
            
            return {
                'valid': True,
                'message': 'পরিমাণ বৈধ',
                'normalized': rounded,
                'precision': precision
            }
        
        except ValueError:
            return {
                'valid': False,
                'message': 'পরিমাণ সংখ্যা হতে হবে!',
                'code': 'NOT_NUMERIC'
            }
    
    def validate_date(self, date_str: str, date_format: str = '%Y-%m-%d') -> Dict:
        """Validate date string"""
        if not date_str:
            return {
                'valid': False,
                'message': 'তারিখ খালি হতে পারে না!',
                'code': 'EMPTY'
            }
        
        try:
            # Parse date
            date_obj = datetime.strptime(date_str, date_format)
            
            # Check if date is not in future (for certain validations)
            current_date = datetime.now().date()
            
            if date_obj.date() > current_date:
                return {
                    'valid': False,
                    'message': 'ভবিষ্যতের তারিখ ব্যবহার করা যাবে না!',
                    'code': 'FUTURE_DATE'
                }
            
            # Check if date is too old
            min_date = datetime(1900, 1, 1).date()
            if date_obj.date() < min_date:
                return {
                    'valid': False,
                    'message': 'তারিখ খুব পুরনো!',
                    'code': 'TOO_OLD'
                }
            
            # Calculate age if needed
            age = self._calculate_age(date_obj.date())
            
            return {
                'valid': True,
                'message': 'তারিখ বৈধ',
                'date': date_obj.isoformat(),
                'age': age,
                'is_adult': age >= 18
            }
        
        except ValueError:
            return {
                'valid': False,
                'message': f'তারিখ ভুল ফরম্যাট! সঠিক ফরম্যাট: {date_format}',
                'code': 'INVALID_FORMAT'
            }
    
    def _calculate_age(self, birth_date) -> int:
        """Calculate age from birth date"""
        today = datetime.now().date()
        age = today.year - birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        return age
    
    def validate_text(self, text: str, field_name: str = 'টেক্সট', 
                     max_length: int = None) -> Dict:
        """Validate text content"""
        if not text:
            return {
                'valid': False,
                'message': f'{field_name} খালি হতে পারে না!',
                'code': 'EMPTY'
            }
        
        # Check length
        text_length = len(text)
        default_max = self.rules['text']['max_length']
        
        if max_length is None:
            max_length = default_max
        
        if text_length > max_length:
            return {
                'valid': False,
                'message': f'{field_name} খুব বড়! সর্বোচ্চ {max_length} অক্ষর হতে পারে।',
                'code': 'TOO_LONG',
                'current_length': text_length,
                'max_length': max_length
            }
        
        # Check for disallowed patterns
        disallowed_patterns = self.rules['text']['disallowed_patterns']
        
        for pattern in disallowed_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    'valid': False,
                    'message': f'{field_name} এ অনুমোদনহীন কনটেন্ট পাওয়া গেছে!',
                    'code': 'DISALLOWED_CONTENT'
                }
        
        # Check for excessive whitespace
        if re.search(r'\s{5,}', text):
            return {
                'valid': False,
                'message': f'{field_name} এ অত্যধিক স্পেস ব্যবহার করা হয়েছে!',
                'code': 'EXCESSIVE_WHITESPACE'
            }
        
        # Check for excessive newlines
        if text.count('\n') > 20:
            return {
                'valid': False,
                'message': f'{field_name} এ অত্যধিক নতুন লাইন ব্যবহার করা হয়েছে!',
                'code': 'EXCESSIVE_NEWLINES'
            }
        
        # Check for repeated characters
        if self._has_repeated_chars(text, 10):
            return {
                'valid': False,
                'message': f'{field_name} এ একই অক্ষর বারবার ব্যবহার করা হয়েছে!',
                'code': 'REPEATED_CHARS'
            }
        
        return {
            'valid': True,
            'message': f'{field_name} বৈধ',
            'length': text_length,
            'word_count': len(text.split()),
            'line_count': text.count('\n') + 1
        }
    
    def validate_url(self, url: str) -> Dict:
        """Validate URL"""
        if not url:
            return {
                'valid': False,
                'message': 'URL খালি হতে পারে না!',
                'code': 'EMPTY'
            }
        
        # Basic regex validation
        if not re.match(self.patterns['url'], url):
            return {
                'valid': False,
                'message': 'URL ভুল ফরম্যাট!',
                'code': 'INVALID_FORMAT'
            }
        
        # Check for allowed domains
        allowed_domains = [
            'telegram.org', 'github.com', 'google.com', 'youtube.com',
            'facebook.com', 'twitter.com', 'instagram.com'
        ]
        
        domain_match = re.search(r'https?://([^/]+)', url)
        if not domain_match:
            return {
                'valid': False,
                'message': 'URL থেকে ডোমেইন খুঁজে পাওয়া যায়নি!',
                'code': 'NO_DOMAIN'
            }
        
        domain = domain_match.group(1).lower()
        
        # Check if domain is in allowed list
        domain_allowed = False
        for allowed in allowed_domains:
            if domain.endswith(allowed):
                domain_allowed = True
                break
        
        if not domain_allowed:
            return {
                'valid': False,
                'message': 'এই ডোমেইনের লিংক অনুমোদন করা হয়নি!',
                'code': 'DOMAIN_NOT_ALLOWED'
            }
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'bit\.ly/', r'tinyurl\.com/', r'shorturl\.',
            r'redirect', r'phishing', r'malware'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return {
                    'valid': False,
                    'message': 'সন্দেহজনক URL পাওয়া গেছে!',
                    'code': 'SUSPICIOUS_URL'
                }
        
        return {
            'valid': True,
            'message': 'URL বৈধ',
            'domain': domain,
            'is_secure': url.startswith('https://')
        }
    
    def validate_transaction_id(self, trx_id: str, method: str = None) -> Dict:
        """Validate transaction ID"""
        if not trx_id:
            return {
                'valid': False,
                'message': 'লেনদেন আইডি খালি হতে পারে না!',
                'code': 'EMPTY'
            }
        
        # Clean transaction ID
        cleaned_trx = trx_id.strip().upper()
        
        # Check length
        if len(cleaned_trx) < 8:
            return {
                'valid': False,
                'message': 'লেনদেন আইডি খুব ছোট! ন্যূনতম ৮ অক্ষর প্রয়োজন।',
                'code': 'TOO_SHORT'
            }
        
        if len(cleaned_trx) > 20:
            return {
                'valid': False,
                'message': 'লেনদেন আইডি খুব বড়! সর্বোচ্চ ২০ অক্ষর হতে পারে।',
                'code': 'TOO_LONG'
            }
        
        # Check pattern
        if not re.match(self.patterns['trx_id'], cleaned_trx):
            return {
                'valid': False,
                'message': 'লেনদেন আইডিতে শুধুমাত্র বড় হাতের অক্ষর ও সংখ্যা থাকতে পারে!',
                'code': 'INVALID_CHARS'
            }
        
        # Method-specific validation
        if method:
            method = method.lower()
            
            if method == 'nagod':
                # Nagod transaction IDs are typically 10-12 characters
                if not (10 <= len(cleaned_trx) <= 12):
                    return {
                        'valid': False,
                        'message': 'নগদ লেনদেন আইডি ১০-১২ অক্ষরের হতে হবে!',
                        'code': 'INVALID_LENGTH_FOR_METHOD'
                    }
            
            elif method == 'bikash':
                # Bikash transaction IDs are typically 10 characters
                if len(cleaned_trx) != 10:
                    return {
                        'valid': False,
                        'message': 'বিকাশ লেনদেন আইডি ১০ অক্ষরের হতে হবে!',
                        'code': 'INVALID_LENGTH_FOR_METHOD'
                    }
        
        return {
            'valid': True,
            'message': 'লেনদেন আইডি বৈধ',
            'normalized': cleaned_trx,
            'method_compatible': True if method else None
        }
    
    def validate_json(self, json_str: str) -> Dict:
        """Validate JSON string"""
        if not json_str:
            return {
                'valid': False,
                'message': 'JSON খালি হতে পারে না!',
                'code': 'EMPTY'
            }
        
        try:
            import json
            parsed = json.loads(json_str)
            
            # Check for deep nesting
            def check_depth(obj, current_depth=0, max_depth=10):
                if current_depth > max_depth:
                    return False
                
                if isinstance(obj, dict):
                    for value in obj.values():
                        if not check_depth(value, current_depth + 1, max_depth):
                            return False
                elif isinstance(obj, list):
                    for item in obj:
                        if not check_depth(item, current_depth + 1, max_depth):
                            return False
                
                return True
            
            if not check_depth(parsed):
                return {
                    'valid': False,
                    'message': 'JSON খুব গভীর নেস্টিং আছে!',
                    'code': 'TOO_DEEP'
                }
            
            return {
                'valid': True,
                'message': 'JSON বৈধ',
                'size': len(json_str),
                'type': type(parsed).__name__,
                'depth': self._calculate_json_depth(parsed)
            }
        
        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'message': f'JSON পার্স করতে ব্যর্থ: {str(e)}',
                'code': 'INVALID_JSON',
                'position': e.pos
            }
    
    def _calculate_json_depth(self, obj, current_depth=1) -> int:
        """Calculate depth of JSON object"""
        if isinstance(obj, dict):
            if obj:
                return max(
                    self._calculate_json_depth(v, current_depth + 1)
                    for v in obj.values()
                )
            else:
                return current_depth
        elif isinstance(obj, list):
            if obj:
                return max(
                    self._calculate_json_depth(item, current_depth + 1)
                    for item in obj
                )
            else:
                return current_depth
        else:
            return current_depth
    
    def batch_validate(self, validations: List[Dict]) -> Dict:
        """Batch validate multiple fields"""
        results = {
            'all_valid': True,
            'valid_count': 0,
            'invalid_count': 0,
            'results': [],
            'errors': []
        }
        
        for validation in validations:
            field_name = validation.get('field_name', 'Unknown')
            field_value = validation.get('value')
            validation_type = validation.get('type', 'text')
            validation_params = validation.get('params', {})
            
            # Perform validation based on type
            if validation_type == 'username':
                result = self.validate_username(field_value)
            elif validation_type == 'email':
                result = self.validate_email(field_value)
            elif validation_type == 'phone':
                country = validation_params.get('country', 'BD')
                result = self.validate_phone(field_value, country)
            elif validation_type == 'amount':
                min_amount = validation_params.get('min')
                max_amount = validation_params.get('max')
                result = self.validate_amount(field_value, min_amount, max_amount)
            elif validation_type == 'password':
                result = self.validate_password(field_value)
            elif validation_type == 'date':
                date_format = validation_params.get('format', '%Y-%m-%d')
                result = self.validate_date(field_value, date_format)
            elif validation_type == 'url':
                result = self.validate_url(field_value)
            elif validation_type == 'trx_id':
                method = validation_params.get('method')
                result = self.validate_transaction_id(field_value, method)
            elif validation_type == 'json':
                result = self.validate_json(field_value)
            else:  # Default to text validation
                max_length = validation_params.get('max_length')
                result = self.validate_text(field_value, field_name, max_length)
            
            # Add field info to result
            result['field_name'] = field_name
            result['field_value'] = field_value
            
            results['results'].append(result)
            
            if result['valid']:
                results['valid_count'] += 1
            else:
                results['all_valid'] = False
                results['invalid_count'] += 1
                results['errors'].append({
                    'field': field_name,
                    'error': result.get('message', 'Unknown error'),
                    'code': result.get('code', 'UNKNOWN')
                })
        
        return results
    
    def get_validation_rules(self, validation_type: str = None) -> Dict:
        """Get validation rules for a specific type or all"""
        if validation_type:
            if validation_type in self.rules:
                return {
                    'type': validation_type,
                    'rules': self.rules[validation_type],
                    'pattern': self.patterns.get(validation_type)
                }
            else:
                return {
                    'type': validation_type,
                    'rules': {},
                    'pattern': None,
                    'error': 'Validation type not found'
                }
        else:
            return {
                'patterns': self.patterns,
                'rules': self.rules,
                'country_rules': self.country_rules,
                'total_patterns': len(self.patterns),
                'total_rules': len(self.rules)
            }