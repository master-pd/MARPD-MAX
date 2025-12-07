import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re

class Utils:
    """Utility Functions v15.0.00"""
    
    # Progress bar templates
    PROGRESS_BARS = [
        ["▱", "▰"],  # Default
        ["○", "●"],  # Circle
        ["□", "■"],  # Square
        ["░", "▓"],  # Shaded
        ["-", "="],  # Dash
        ["⚪", "🔵"],  # Emoji
        ["🌑", "🌕"],  # Moon
        ["⚫", "🟢"]   # Dot
    ]
    
    # Motivational quotes in Bengali
    QUOTES = [
        "সফলতা চাইলে আগে বিশ্বাস করতে হবে!",
        "প্রতিদিন ছোট একটি পদক্ষেপ বিশাল পরিবর্তন আনে।",
        "ভালোবাসা আর বিশ্বাসে সবকিছু সম্ভব!",
        "আপনার লক্ষ্য যত বড় হবে, সাফল্য তত মিষ্টি হবে।",
        "কখনো হাল ছাড়বেন না, সাফল্য আপনার দরজায় কড়া নাড়ছে।",
        "যে পরিশ্রম করে, তার ভাগ্যেও সুযোগ আসে।",
        "বিশ্বাসই সাফল্যের প্রথম সিঁড়ি।",
        "আপনার স্বপ্ন দেখার সাহস আছে তো?",
        "ছোট থেকে শুরু করুন, বড় স্বপ্ন দেখুন।",
        "আজকের সংগ্রাম আগামীকালের সাফল্যের ভিত্তি।"
    ]
    
    # Game emojis
    EMOJIS = {
        "dice": ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"],
        "slot": ["🍒", "🍋", "⭐", "7️⃣", "🔔", "💎", "💰", "🍀"],
        "cards": ["🂡", "🂢", "🂣", "🂤", "🂥", "🂦", "🂧", "🂨", "🂩", "🂪", "🂫", "🂭", "🂮"],
        "money": ["💰", "💵", "💎", "🪙", "💸", "💳", "🏦"],
        "status": ["✅", "❌", "⚠️", "⏳", "🎯", "🔥", "🌟", "💯"]
    }
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Format currency with emoji"""
        if amount >= 1000000:
            return f"৳{amount/1000000:.2f}M"
        elif amount >= 1000:
            return f"৳{amount/1000:.1f}K"
        else:
            return f"৳{amount:,.2f}"
    
    @staticmethod
    def format_coins(coins: int) -> str:
        """Format coins with emoji"""
        if coins >= 1000000:
            return f"{coins/1000000:.2f}M 🪙"
        elif coins >= 1000:
            return f"{coins/1000:.1f}K 🪙"
        else:
            return f"{coins:,} 🪙"
    
    @staticmethod
    def format_number(number: int) -> str:
        """Format any number"""
        if number >= 1000000:
            return f"{number/1000000:.2f}M"
        elif number >= 1000:
            return f"{number/1000:.1f}K"
        else:
            return f"{number:,}"
    
    @staticmethod
    def calculate_level(xp: int) -> Dict:
        """Calculate level from XP"""
        level = 1
        xp_needed = 100
        
        while xp >= xp_needed:
            xp -= xp_needed
            level += 1
            xp_needed = int(xp_needed * 1.5)  # Each level needs 50% more XP
        
        return {
            "level": level,
            "xp": xp,
            "xp_needed": xp_needed,
            "total_xp": xp + sum(100 * (1.5 ** i) for i in range(level-1))
        }
    
    @staticmethod
    def create_progress_bar(current: int, total: int, length: int = 10, style: int = 0) -> str:
        """Create progress bar"""
        if total == 0:
            return "0%"
        
        style = min(style, len(Utils.PROGRESS_BARS) - 1)
        empty, filled = Utils.PROGRESS_BARS[style]
        
        percentage = min(current / total, 1.0)
        filled_length = int(length * percentage)
        empty_length = length - filled_length
        
        bar = filled * filled_length + empty * empty_length
        percent_text = f"{percentage*100:.1f}%"
        
        return f"{bar} {percent_text}"
    
    @staticmethod
    def get_random_quote() -> str:
        """Get random motivational quote"""
        return random.choice(Utils.QUOTES)
    
    @staticmethod
    def get_time_ago(timestamp: str) -> str:
        """Get human readable time ago"""
        try:
            past_time = datetime.fromisoformat(timestamp)
            now = datetime.now()
            diff = now - past_time
            
            if diff.days > 365:
                years = diff.days // 365
                return f"{years} বছর আগে"
            elif diff.days > 30:
                months = diff.days // 30
                return f"{months} মাস আগে"
            elif diff.days > 0:
                return f"{diff.days} দিন আগে"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} ঘন্টা আগে"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} মিনিট আগে"
            else:
                return f"{diff.seconds} সেকেন্ড আগে"
        except:
            return "অজানা সময়"
    
    @staticmethod
    def validate_phone(number: str) -> bool:
        """Validate Bangladeshi phone number"""
        pattern = r'^(?:\+88|88)?(01[3-9]\d{8})$'
        return bool(re.match(pattern, number))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def generate_referral_code(user_id: int) -> str:
        """Generate referral code"""
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        code = f"MARPD{user_id}"
        # Add random suffix
        for _ in range(4):
            code += random.choice(chars)
        return code
    
    @staticmethod
    def calculate_streak_bonus(streak: int) -> int:
        """Calculate daily streak bonus"""
        base_bonus = 100
        streak_bonus = min(streak * 20, 200)  # Max 200 extra
        return base_bonus + streak_bonus
    
    @staticmethod
    def get_emoji_progress(percentage: float) -> str:
        """Get emoji based on percentage"""
        if percentage >= 90:
            return "💯"
        elif percentage >= 80:
            return "🔥"
        elif percentage >= 70:
            return "⭐"
        elif percentage >= 60:
            return "👍"
        elif percentage >= 50:
            return "✅"
        elif percentage >= 40:
            return "🔄"
        elif percentage >= 30:
            return "⚠️"
        elif percentage >= 20:
            return "📉"
        else:
            return "📊"
    
    @staticmethod
    def format_time_duration(seconds: int) -> str:
        """Format duration in seconds to human readable"""
        if seconds < 60:
            return f"{seconds} সেকেন্ড"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} মিনিট"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} ঘন্টা {minutes} মিনিট"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days} দিন {hours} ঘন্টা"
    
    @staticmethod
    def generate_password(length: int = 8) -> str:
        """Generate random password"""
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(random.choice(chars) for _ in range(length))
    
    @staticmethod
    def get_random_emoji(category: str = None) -> str:
        """Get random emoji"""
        if category and category in Utils.EMOJIS:
            return random.choice(Utils.EMOJIS[category])
        
        # Return random emoji from all categories
        all_emojis = []
        for emoji_list in Utils.EMOJIS.values():
            all_emojis.extend(emoji_list)
        
        return random.choice(all_emojis)
    
    @staticmethod
    def calculate_win_chance(user_level: int, game_type: str) -> float:
        """Calculate win chance based on level"""
        base_chance = {
            "dice": 0.5,
            "slot": 0.3,
            "quiz": 0.7
        }.get(game_type, 0.5)
        
        # Each level adds 0.5% chance (max 10% bonus)
        level_bonus = min(user_level * 0.005, 0.1)
        
        return min(base_chance + level_bonus, 0.9)  # Max 90% chance
    
    @staticmethod
    def create_leaderboard_entry(position: int, user_data: Dict, metric: str = "coins") -> str:
        """Create leaderboard entry"""
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        medal = medals[position - 1] if position <= len(medals) else f"{position}."
        
        username = user_data.get("username", f"User_{user_data.get('id')}")
        if not username or username.startswith("User_"):
            username = user_data.get("first_name", "Anonymous")
        
        value = user_data.get(metric, 0)
        
        if metric == "coins":
            value_text = Utils.format_coins(value)
        elif metric == "balance":
            value_text = Utils.format_currency(value)
        elif metric == "level":
            value_text = f"Level {value}"
        else:
            value_text = str(value)
        
        return f"{medal} @{username} - {value_text}"