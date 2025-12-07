import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import math

class AIRecommender:
    """Advanced AI Recommendation System v15.0.00"""
    
    def __init__(self, db):
        self.db = db
        self.user_profiles = {}
        self.game_recommendations = {}
        self.shop_recommendations = {}
        self.analytics = {
            'total_recommendations': 0,
            'successful_recommendations': 0,
            'user_engagement': defaultdict(float),
            'popular_items': defaultdict(int)
        }
        
        # Game categories and weights
        self.game_categories = {
            'dice': {'risk': 'low', 'reward': 'medium', 'time': 'short'},
            'slot': {'risk': 'medium', 'reward': 'high', 'time': 'short'},
            'quiz': {'risk': 'low', 'reward': 'low', 'time': 'medium'},
            'coin_flip': {'risk': 'high', 'reward': 'medium', 'time': 'short'},
            'number_guess': {'risk': 'high', 'reward': 'high', 'time': 'medium'}
        }
        
        # User behavior patterns
        self.behavior_patterns = {
            'aggressive': {'risk_tolerance': 'high', 'preferred_games': ['slot', 'number_guess']},
            'conservative': {'risk_tolerance': 'low', 'preferred_games': ['dice', 'quiz']},
            'balanced': {'risk_tolerance': 'medium', 'preferred_games': ['dice', 'slot', 'quiz']},
            'explorer': {'risk_tolerance': 'medium', 'preferred_games': 'all'}
        }
        
        print("🤖 AI Recommender System v15.0.00 Initialized")
    
    async def analyze_user_behavior(self, user_id: int) -> Dict:
        """Analyze user behavior and create profile"""
        user = self.db.get_user(user_id)
        if not user:
            return {'behavior': 'unknown', 'confidence': 0}
        
        # Get user game stats
        game_stats = {}
        if 'stats' in user:
            game_stats = user['stats']
        
        # Calculate behavior metrics
        total_games = sum(game_stats.values()) if game_stats else 0
        if total_games < 10:
            return {'behavior': 'new_user', 'confidence': 0.3}
        
        # Calculate win rate
        win_rate = await self._calculate_win_rate(user_id)
        
        # Calculate risk appetite
        risk_appetite = await self._calculate_risk_appetite(user_id)
        
        # Calculate playing patterns
        playing_patterns = await self._analyze_playing_patterns(user_id)
        
        # Determine behavior type
        behavior_type = self._determine_behavior_type(win_rate, risk_appetite, playing_patterns)
        
        # Create user profile
        user_profile = {
            'user_id': user_id,
            'behavior_type': behavior_type,
            'win_rate': win_rate,
            'risk_appetite': risk_appetite,
            'playing_patterns': playing_patterns,
            'total_games': total_games,
            'preferred_games': await self._get_preferred_games(user_id),
            'spending_habits': await self._analyze_spending_habits(user_id),
            'activity_level': await self._calculate_activity_level(user_id),
            'last_analyzed': datetime.now().isoformat(),
            'profile_version': '2.0',
            'confidence_score': self._calculate_confidence_score(total_games, playing_patterns)
        }
        
        # Store profile
        self.user_profiles[user_id] = user_profile
        
        return user_profile
    
    async def _calculate_win_rate(self, user_id: int) -> float:
        """Calculate user's win rate"""
        user = self.db.get_user(user_id)
        if not user or 'stats' not in user:
            return 0.5  # Default
        
        stats = user['stats']
        total_played = 0
        total_won = 0
        
        for game_type in ['dice', 'slot', 'quiz']:
            played_key = f"{game_type}_played"
            won_key = f"{game_type}_won"
            
            if played_key in stats and won_key in stats:
                total_played += stats[played_key]
                total_won += stats[won_key]
        
        return total_won / max(total_played, 1)
    
    async def _calculate_risk_appetite(self, user_id: int) -> float:
        """Calculate user's risk appetite (0-1)"""
        # Analyze bet sizes relative to balance
        user = self.db.get_user(user_id)
        if not user:
            return 0.5
        
        balance = user.get('coins', 0)
        total_games = user.get('total_games', 0)
        
        if total_games < 5 or balance == 0:
            return 0.5
        
        # Get recent game history
        recent_bets = []
        for game_id, game_data in self.db.game_history.items():
            if game_data.get('user_id') == user_id:
                bet = game_data.get('bet', 0)
                if bet > 0:
                    recent_bets.append(bet)
        
        if not recent_bets:
            return 0.5
        
        # Calculate average bet as percentage of balance
        avg_bet = sum(recent_bets) / len(recent_bets)
        risk_score = min(avg_bet / max(balance, 1), 1.0)
        
        return risk_score
    
    async def _analyze_playing_patterns(self, user_id: int) -> Dict:
        """Analyze user's playing patterns"""
        patterns = {
            'preferred_time': None,
            'session_length': 0,
            'games_per_session': 0,
            'break_frequency': 'medium',
            'streak_behavior': 'normal'
        }
        
        # Get recent games
        recent_games = []
        for game_id, game_data in self.db.game_history.items():
            if game_data.get('user_id') == user_id:
                recent_games.append(game_data)
        
        if len(recent_games) < 5:
            return patterns
        
        # Analyze time patterns
        hour_counts = defaultdict(int)
        for game in recent_games:
            timestamp = game.get('timestamp')
            if timestamp:
                try:
                    hour = datetime.fromisoformat(timestamp).hour
                    hour_counts[hour] += 1
                except:
                    pass
        
        if hour_counts:
            preferred_hour = max(hour_counts.items(), key=lambda x: x[1])[0]
            time_of_day = self._categorize_time(preferred_hour)
            patterns['preferred_time'] = time_of_day
        
        # Analyze session behavior
        sessions = self._group_into_sessions(recent_games)
        if sessions:
            avg_session_length = sum(len(s) for s in sessions) / len(sessions)
            patterns['games_per_session'] = avg_session_length
            patterns['session_length'] = avg_session_length * 2  # Assuming 2 minutes per game
        
        return patterns
    
    def _categorize_time(self, hour: int) -> str:
        """Categorize hour into time of day"""
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 22:
            return 'evening'
        else:
            return 'night'
    
    def _group_into_sessions(self, games: List[Dict]) -> List[List[Dict]]:
        """Group games into sessions"""
        if not games:
            return []
        
        # Sort games by timestamp
        games.sort(key=lambda x: x.get('timestamp', ''))
        
        sessions = []
        current_session = [games[0]]
        
        for i in range(1, len(games)):
            current_time = datetime.fromisoformat(games[i]['timestamp'])
            prev_time = datetime.fromisoformat(games[i-1]['timestamp'])
            time_diff = (current_time - prev_time).total_seconds() / 60  # minutes
            
            if time_diff < 30:  # Same session if within 30 minutes
                current_session.append(games[i])
            else:
                sessions.append(current_session)
                current_session = [games[i]]
        
        if current_session:
            sessions.append(current_session)
        
        return sessions
    
    def _determine_behavior_type(self, win_rate: float, risk_appetite: float, patterns: Dict) -> str:
        """Determine user behavior type"""
        if win_rate > 0.7 and risk_appetite > 0.7:
            return 'aggressive'
        elif win_rate < 0.4 and risk_appetite < 0.3:
            return 'conservative'
        elif 0.4 <= win_rate <= 0.7 and 0.3 <= risk_appetite <= 0.7:
            return 'balanced'
        else:
            return 'explorer'
    
    async def _get_preferred_games(self, user_id: int) -> List[str]:
        """Get user's preferred games"""
        user = self.db.get_user(user_id)
        if not user or 'stats' not in user:
            return ['dice', 'quiz']  # Default
        
        stats = user['stats']
        game_counts = {}
        
        for game_type in ['dice', 'slot', 'quiz']:
            played_key = f"{game_type}_played"
            if played_key in stats:
                game_counts[game_type] = stats[played_key]
        
        if not game_counts:
            return ['dice', 'quiz']
        
        # Sort by play count
        sorted_games = sorted(game_counts.items(), key=lambda x: x[1], reverse=True)
        return [game[0] for game in sorted_games[:3]]
    
    async def _analyze_spending_habits(self, user_id: int) -> Dict:
        """Analyze user's spending habits"""
        habits = {
            'deposit_frequency': 'low',
            'avg_deposit': 0,
            'withdrawal_frequency': 'low',
            'shop_spending': 0
        }
        
        # Get payment history
        payments = self.db.get_user_payments(user_id, limit=50)
        
        deposit_count = 0
        deposit_total = 0
        withdrawal_count = 0
        
        for payment in payments:
            if payment.get('type') == 'DEPOSIT' and payment.get('status') == 'COMPLETED':
                deposit_count += 1
                deposit_total += payment.get('amount', 0)
            elif payment.get('type') == 'WITHDRAW' and payment.get('status') == 'COMPLETED':
                withdrawal_count += 1
        
        # Calculate frequencies
        habits['deposit_frequency'] = self._categorize_frequency(deposit_count)
        habits['withdrawal_frequency'] = self._categorize_frequency(withdrawal_count)
        
        if deposit_count > 0:
            habits['avg_deposit'] = deposit_total / deposit_count
        
        # Analyze shop spending
        user = self.db.get_user(user_id)
        if user and 'inventory' in user:
            habits['shop_spending'] = sum(item.get('price_paid', 0) for item in user['inventory'])
        
        return habits
    
    def _categorize_frequency(self, count: int) -> str:
        """Categorize frequency based on count"""
        if count == 0:
            return 'none'
        elif count <= 2:
            return 'low'
        elif count <= 5:
            return 'medium'
        elif count <= 10:
            return 'high'
        else:
            return 'very_high'
    
    async def _calculate_activity_level(self, user_id: int) -> float:
        """Calculate user activity level (0-1)"""
        user = self.db.get_user(user_id)
        if not user:
            return 0
        
        last_active = datetime.fromisoformat(user.get('last_active', '2000-01-01'))
        days_since_active = (datetime.now() - last_active).days
        
        if days_since_active == 0:
            return 1.0
        elif days_since_active <= 3:
            return 0.7
        elif days_since_active <= 7:
            return 0.4
        elif days_since_active <= 14:
            return 0.2
        else:
            return 0.1
    
    def _calculate_confidence_score(self, total_games: int, patterns: Dict) -> float:
        """Calculate confidence score for profile (0-1)"""
        if total_games < 5:
            return 0.3
        elif total_games < 20:
            return 0.6
        elif total_games < 50:
            return 0.8
        else:
            return 0.95
    
    async def recommend_game(self, user_id: int) -> Dict:
        """Recommend a game to user based on profile"""
        # Get or create user profile
        if user_id not in self.user_profiles:
            profile = await self.analyze_user_behavior(user_id)
        else:
            profile = self.user_profiles[user_id]
        
        behavior_type = profile['behavior_type']
        confidence = profile['confidence_score']
        
        # Get recommendation based on behavior
        if behavior_type in self.behavior_patterns:
            pattern = self.behavior_patterns[behavior_type]
            preferred_games = pattern['preferred_games']
            
            if preferred_games == 'all':
                available_games = list(self.game_categories.keys())
            else:
                available_games = preferred_games
            
            # Filter by user's recent games (avoid repetition)
            recent_games = await self._get_recent_games(user_id, limit=5)
            recent_game_types = [game.get('game') for game in recent_games if game.get('game')]
            
            # Remove recently played games
            recommended_games = [g for g in available_games if g not in recent_game_types]
            
            if not recommended_games:
                recommended_games = available_games
            
            # Select game
            recommended_game = random.choice(recommended_games)
            
            # Create recommendation message
            game_info = self.game_categories.get(recommended_game, {})
            message = self._create_recommendation_message(recommended_game, game_info, behavior_type)
            
            # Store recommendation
            rec_id = f"rec_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.game_recommendations[rec_id] = {
                'user_id': user_id,
                'game': recommended_game,
                'behavior_type': behavior_type,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'presented': False,
                'accepted': False
            }
            
            # Update analytics
            self.analytics['total_recommendations'] += 1
            
            return {
                'success': True,
                'game': recommended_game,
                'message': message,
                'confidence': f"{confidence*100:.1f}%",
                'reason': f'আপনার {behavior_type} প্লেয়িং স্টাইল অনুযায়ী',
                'recommendation_id': rec_id,
                'game_info': game_info
            }
        
        else:
            # Default recommendation
            return {
                'success': True,
                'game': 'dice',
                'message': 'নতুন শুরু করার জন্য ডাইস গেম উপযুক্ত!',
                'confidence': '50%',
                'reason': 'নতুন ইউজারদের জন্য',
                'recommendation_id': None
            }
    
    async def _get_recent_games(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get user's recent games"""
        recent_games = []
        
        for game_id, game_data in self.db.game_history.items():
            if game_data.get('user_id') == user_id:
                recent_games.append(game_data)
        
        # Sort by timestamp (newest first)
        recent_games.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return recent_games[:limit]
    
    def _create_recommendation_message(self, game: str, game_info: Dict, behavior_type: str) -> str:
        """Create personalized recommendation message"""
        game_names = {
            'dice': '🎲 ডাইস গেম',
            'slot': '🎰 স্লট মেশিন',
            'quiz': '🧠 কুইজ গেম',
            'coin_flip': '🪙 কয়েন ফ্লিপ',
            'number_guess': '🎯 নাম্বার গেস'
        }
        
        behavior_messages = {
            'aggressive': 'আপনার উচ্চ রিস্ক টোলারেন্সের জন্য উপযুক্ত!',
            'conservative': 'নিরাপদ ও ধারাবাহিক জয়ের সুযোগ!',
            'balanced': 'রিস্ক ও রিওয়ার্ডের পারফেক্ট ব্যালেন্স!',
            'explorer': 'নতুন চ্যালেঞ্জের জন্য উত্তম!',
            'new_user': 'শুরু করার জন্য সহজ গেম!'
        }
        
        game_name = game_names.get(game, game)
        behavior_msg = behavior_messages.get(behavior_type, 'আপনার প্লেয়িং স্টাইল অনুযায়ী')
        
        return f"""
🤖 **AI রিকমেন্ডেশন**

🎮 **গেম:** {game_name}
📊 **রিস্ক লেভেল:** {game_info.get('risk', 'Medium').upper()}
💰 **রিওয়ার্ড:** {game_info.get('reward', 'Medium').upper()}
⏱️ **সময়:** {game_info.get('time', 'Short')}

💡 **কারণ:** {behavior_msg}

🔥 **বিশেষ সুবিধা:** প্রথম খেলায় ১০% এক্সট্রা এক্সপি!
        """
    
    async def recommend_shop_item(self, user_id: int) -> Dict:
        """Recommend shop item based on user profile"""
        user = self.db.get_user(user_id)
        if not user:
            return {'success': False, 'message': 'ইউজার খুঁজে পাওয়া যায়নি!'}
        
        # Get user profile
        if user_id not in self.user_profiles:
            profile = await self.analyze_user_behavior(user_id)
        else:
            profile = self.user_profiles[user_id]
        
        # Get available shop items
        shop_items = self.db.get_shop_items()
        
        if not shop_items:
            return {'success': False, 'message': 'কোনো শপ আইটেম নেই!'}
        
        # Filter items based on user profile
        recommended_items = []
        
        for item in shop_items:
            score = self._calculate_item_score(item, profile, user)
            if score > 0.5:  # Minimum score threshold
                recommended_items.append((item, score))
        
        if not recommended_items:
            # Fallback: recommend popular or affordable items
            for item in shop_items:
                if item.get('price', 0) <= user.get('coins', 0):
                    recommended_items.append((item, 0.5))
        
        if not recommended_items:
            return {'success': False, 'message': 'উপযুক্ত আইটেম নেই!'}
        
        # Sort by score
        recommended_items.sort(key=lambda x: x[1], reverse=True)
        recommended_item = recommended_items[0][0]
        
        # Create recommendation
        message = self._create_shop_recommendation_message(recommended_item, profile)
        
        # Store recommendation
        rec_id = f"shop_rec_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.shop_recommendations[rec_id] = {
            'user_id': user_id,
            'item_id': recommended_item.get('id'),
            'item_name': recommended_item.get('name'),
            'price': recommended_item.get('price'),
            'score': recommended_items[0][1],
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'item': recommended_item,
            'message': message,
            'reason': 'আপনার প্লেয়িং প্যাটার্ন অনুযায়ী',
            'affordable': recommended_item.get('price', 0) <= user.get('coins', 0),
            'recommendation_id': rec_id
        }
    
    def _calculate_item_score(self, item: Dict, profile: Dict, user: Dict) -> float:
        """Calculate score for shop item (0-1)"""
        score = 0.0
        
        # Price affordability (30% weight)
        item_price = item.get('price', 0)
        user_coins = user.get('coins', 0)
        
        if user_coins >= item_price:
            affordability = 1.0
        elif user_coins > 0:
            affordability = user_coins / item_price
        else:
            affordability = 0.0
        
        score += affordability * 0.3
        
        # Item category match (30% weight)
        item_category = item.get('category', '')
        behavior_type = profile.get('behavior_type', '')
        
        category_scores = {
            'aggressive': {'booster': 0.9, 'charm': 0.7, 'cosmetic': 0.3, 'badge': 0.5},
            'conservative': {'booster': 0.6, 'charm': 0.8, 'cosmetic': 0.7, 'badge': 0.9},
            'balanced': {'booster': 0.8, 'charm': 0.8, 'cosmetic': 0.6, 'badge': 0.7},
            'explorer': {'booster': 0.7, 'charm': 0.6, 'cosmetic': 0.9, 'badge': 0.8}
        }
        
        category_score = category_scores.get(behavior_type, {}).get(item_category, 0.5)
        score += category_score * 0.3
        
        # User needs (20% weight)
        user_needs_score = self._calculate_user_needs_score(item, user, profile)
        score += user_needs_score * 0.2
        
        # Popularity (10% weight)
        popularity_score = self.analytics['popular_items'].get(item.get('id'), 0) / 100
        score += min(popularity_score, 1.0) * 0.1
        
        # Rarity bonus (10% weight)
        rarity = item.get('rarity', 'common')
        rarity_scores = {'common': 0.1, 'uncommon': 0.3, 'rare': 0.6, 'epic': 0.8, 'legendary': 1.0}
        rarity_score = rarity_scores.get(rarity, 0.5)
        score += rarity_score * 0.1
        
        return min(score, 1.0)
    
    def _calculate_user_needs_score(self, item: Dict, user: Dict, profile: Dict) -> float:
        """Calculate score based on user's needs"""
        score = 0.0
        
        # Check if user already has the item
        inventory = user.get('inventory', [])
        for inv_item in inventory:
            if inv_item.get('id') == item.get('id'):
                return 0.0  # Already have it
        
        # Analyze user's weaknesses
        win_rate = profile.get('win_rate', 0.5)
        risk_appetite = profile.get('risk_appetite', 0.5)
        
        # Boosters for low win rate
        if win_rate < 0.4 and item.get('category') == 'booster':
            score += 0.5
        
        # Charms for high risk appetite
        if risk_appetite > 0.7 and item.get('category') == 'charm':
            score += 0.5
        
        # Cosmetics for explorers
        if profile.get('behavior_type') == 'explorer' and item.get('category') == 'cosmetic':
            score += 0.3
        
        # Badges for conservative players
        if profile.get('behavior_type') == 'conservative' and item.get('category') == 'badge':
            score += 0.4
        
        return min(score, 1.0)
    
    def _create_shop_recommendation_message(self, item: Dict, profile: Dict) -> str:
        """Create shop recommendation message"""
        behavior_messages = {
            'aggressive': 'আপনার অ্যাগ্রেসিভ স্টাইলের জন্য পারফেক্ট!',
            'conservative': 'আপনার কনজারভেটিভ অ্যাপ্রোচের সাথে মিলে যায়!',
            'balanced': 'আপনার ব্যালেন্সড গেমপ্লের জন্য আদর্শ!',
            'explorer': 'আপনার এক্সপ্লোরার মেন্টালিটির জন্য উপযুক্ত!',
            'new_user': 'শুরু করার জন্য উত্তম আইটেম!'
        }
        
        behavior = profile.get('behavior_type', 'balanced')
        behavior_msg = behavior_messages.get(behavior, 'আপনার গেমিং স্টাইলের জন্য')
        
        benefits = item.get('bonus', {})
        benefit_text = ""
        
        if benefits:
            benefit_list = []
            for key, value in benefits.items():
                if key == 'daily_extra':
                    benefit_list.append(f'প্রতিদিন +{value} অতিরিক্ত কয়েন')
                elif key == 'xp_boost':
                    benefit_list.append(f'{value}% অতিরিক্ত XP')
                elif key == 'duration_days':
                    benefit_list.append(f'{value} দিনের জন্য')
                elif key == 'duration_hours':
                    benefit_list.append(f'{value} ঘন্টার জন্য')
            
            if benefit_list:
                benefit_text = "\n✨ **বিশেষ সুবিধা:**\n" + "\n".join([f"• {b}" for b in benefit_list])
        
        return f"""
🛍️ **AI শপ রিকমেন্ডেশন**

{item.get('icon', '🎁')} **আইটেম:** {item.get('name', 'Unknown')}
💰 **দাম:** {item.get('price', 0):,} কয়েন
📝 **বর্ণনা:** {item.get('description', '')}
🏷️ **ক্যাটাগরি:** {item.get('category', 'general').upper()}
⭐ **দুর্লভতা:** {item.get('rarity', 'common').upper()}

💡 **কারণ:** {behavior_msg}{benefit_text}

🎯 **স্মার্ট টিপ:** এই আইটেম আপনার {behavior} প্লেয়িং স্টাইলের সাথে ৮৫% ম্যাচ করে!
        """
    
    async def track_recommendation_feedback(self, recommendation_id: str, accepted: bool):
        """Track user feedback on recommendations"""
        if recommendation_id.startswith('rec_') and recommendation_id in self.game_recommendations:
            self.game_recommendations[recommendation_id]['accepted'] = accepted
            self.game_recommendations[recommendation_id]['presented'] = True
            
            if accepted:
                self.analytics['successful_recommendations'] += 1
        
        elif recommendation_id.startswith('shop_rec_') and recommendation_id in self.shop_recommendations:
            item_id = self.shop_recommendations[recommendation_id].get('item_id')
            if item_id and accepted:
                self.analytics['popular_items'][item_id] += 1
    
    async def get_recommendation_stats(self, user_id: int = None) -> Dict:
        """Get recommendation statistics"""
        if user_id:
            # User-specific stats
            user_recs = [r for r in self.game_recommendations.values() if r['user_id'] == user_id]
            shop_recs = [r for r in self.shop_recommendations.values() if r['user_id'] == user_id]
            
            accepted_count = sum(1 for r in user_recs if r.get('accepted', False))
            presented_count = sum(1 for r in user_recs if r.get('presented', False))
            
            acceptance_rate = (accepted_count / max(presented_count, 1)) * 100
            
            return {
                'user_id': user_id,
                'total_recommendations': len(user_recs) + len(shop_recs),
                'game_recommendations': len(user_recs),
                'shop_recommendations': len(shop_recs),
                'accepted_count': accepted_count,
                'acceptance_rate': f"{acceptance_rate:.1f}%",
                'last_recommendation': user_recs[-1]['timestamp'] if user_recs else None,
                'profile': self.user_profiles.get(user_id, {})
            }
        else:
            # Global stats
            total_recs = len(self.game_recommendations) + len(self.shop_recommendations)
            successful_recs = sum(1 for r in self.game_recommendations.values() if r.get('accepted', False))
            
            success_rate = (successful_recs / max(len(self.game_recommendations), 1)) * 100
            
            # Most recommended games
            game_counts = defaultdict(int)
            for rec in self.game_recommendations.values():
                game_counts[rec.get('game')] += 1
            
            most_recommended_game = max(game_counts.items(), key=lambda x: x[1])[0] if game_counts else 'None'
            
            # Most successful behavior type
            behavior_success = defaultdict(int)
            for rec in self.game_recommendations.values():
                if rec.get('accepted', False):
                    behavior_success[rec.get('behavior_type')] += 1
            
            most_successful_behavior = max(behavior_success.items(), key=lambda x: x[1])[0] if behavior_success else 'None'
            
            return {
                'total_recommendations': total_recs,
                'game_recommendations': len(self.game_recommendations),
                'shop_recommendations': len(self.shop_recommendations),
                'successful_recommendations': successful_recs,
                'success_rate': f"{success_rate:.1f}%",
                'most_recommended_game': most_recommended_game,
                'most_successful_behavior': most_successful_behavior,
                'user_profiles_created': len(self.user_profiles),
                'analytics': self.analytics
            }
    
    async def improve_recommendations(self):
        """Improve recommendation algorithms based on feedback"""
        print("🔄 Improving recommendation algorithms...")
        
        # Analyze successful recommendations
        successful_recs = [r for r in self.game_recommendations.values() if r.get('accepted', False)]
        
        if len(successful_recs) < 10:
            print("⚠️ Not enough data for improvement")
            return
        
        # Find patterns in successful recommendations
        successful_games_by_behavior = defaultdict(list)
        for rec in successful_recs:
            behavior = rec.get('behavior_type')
            game = rec.get('game')
            if behavior and game:
                successful_games_by_behavior[behavior].append(game)
        
        # Update behavior patterns
        for behavior, games in successful_games_by_behavior.items():
            if games and behavior in self.behavior_patterns:
                # Find most successful game for this behavior
                from collections import Counter
                game_counts = Counter(games)
                most_successful = game_counts.most_common(1)[0][0]
                
                # Update preferred games
                if most_successful not in self.behavior_patterns[behavior]['preferred_games']:
                    print(f"📊 Updated {behavior} pattern: Added {most_successful} to preferred games")
                    if isinstance(self.behavior_patterns[behavior]['preferred_games'], list):
                        self.behavior_patterns[behavior]['preferred_games'].append(most_successful)
        
        print("✅ Recommendation algorithms improved!")
    
    async def cleanup_old_data(self, days_old: int = 30):
        """Cleanup old recommendation data"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cutoff_str = cutoff_date.isoformat()
        
        # Clean game recommendations
        old_game_recs = [
            rid for rid, rec in self.game_recommendations.items()
            if rec['timestamp'] < cutoff_str
        ]
        
        for rid in old_game_recs:
            del self.game_recommendations[rid]
        
        # Clean shop recommendations
        old_shop_recs = [
            rid for rid, rec in self.shop_recommendations.items()
            if rec['timestamp'] < cutoff_str
        ]
        
        for rid in old_shop_recs:
            del self.shop_recommendations[rid]
        
        # Clean old user profiles (inactive users)
        inactive_users = []
        for user_id, profile in self.user_profiles.items():
            last_analyzed = datetime.fromisoformat(profile.get('last_analyzed', '2000-01-01'))
            if last_analyzed < cutoff_date:
                # Check if user is active
                user = self.db.get_user(user_id)
                if user:
                    last_active = datetime.fromisoformat(user.get('last_active', '2000-01-01'))
                    if last_active < cutoff_date:
                        inactive_users.append(user_id)
        
        for user_id in inactive_users:
            del self.user_profiles[user_id]
        
        cleaned_count = len(old_game_recs) + len(old_shop_recs) + len(inactive_users)
        print(f"🧹 AI Recommender cleanup: {cleaned_count} items removed")
        return cleaned_count