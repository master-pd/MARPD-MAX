import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import math
from config import Config
from db import Database
from utils import Utils

class GamesManager:
    """Advanced Game Management System v15.0.00"""
    
    def __init__(self, db: Database):
        self.db = db
        self.config = Config()
        self.active_games = {}
        self.game_history = {}
        
        # Game configurations
        self.game_configs = {
            "dice": {
                "name": "🎲 ডাইস গেম",
                "min_bet": 10,
                "max_bet": 10000,
                "win_multiplier": 2.0,
                "house_edge": 0.05,
                "description": "বটের চেয়ে বেশি ডাইস রোল করুন",
                "emoji": "🎲",
                "rules": "• 1-6 পর্যন্ত ডাইস রোল হয়\n• বটের চেয়ে বেশি পেলে জিতবেন\n• সমান হলে ড্র"
            },
            "slot": {
                "name": "🎰 স্লট মেশিন",
                "min_bet": 20,
                "max_bet": 5000,
                "jackpot_multiplier": 10.0,
                "win_multiplier": 2.0,
                "house_edge": 0.10,
                "description": "৩টি মিললে জ্যাকপট পান!",
                "emoji": "🎰",
                "symbols": ["🍒", "🍋", "⭐", "7️⃣", "🔔", "💎", "💰", "🍀"],
                "rules": "• ৩টি রিলে স্পিন হয়\n• ২টি মিললে ২x\n• ৩টি মিললে জ্যাকপট\n• হারলে বেট হারাবেন"
            },
            "quiz": {
                "name": "🧠 কুইজ গেম",
                "entry_fee": 10,
                "reward": 50,
                "time_limit": 60,
                "description": "জ্ঞান পরীক্ষা করুন",
                "emoji": "🧠",
                "rules": "• ৬০ সেকেন্ডে উত্তর দিন\n• সঠিক উত্তরে ৫০ কয়েন\n• ভুল উত্তরে হারাবেন"
            },
            "coin_flip": {
                "name": "🪙 কয়েন ফ্লিপ",
                "min_bet": 5,
                "max_bet": 2000,
                "win_multiplier": 1.95,
                "house_edge": 0.025,
                "description": "হেড নাকি টেল?",
                "emoji": "🪙",
                "rules": "• হেড বা টেল সিলেক্ট করুন\n• সঠিক অনুমানে জিতবেন\n• হারলে বেট হারাবেন"
            },
            "number_guess": {
                "name": "🎯 নাম্বার গেস",
                "min_bet": 10,
                "max_bet": 1000,
                "win_multiplier": 5.0,
                "house_edge": 0.20,
                "description": "১-১০০ এর মধ্যে নাম্বার অনুমান করুন",
                "emoji": "🎯",
                "rules": "• ১-১০০ এর মধ্যে নাম্বার অনুমান\n• ৩টি সুযোগ আছে\n• সঠিক অনুমানে জ্যাকপট"
            }
        }
        
        # Quiz questions database
        self.quiz_questions = {
            "bangladesh": [
                {
                    "question": "বাংলাদেশের স্বাধীনতা দিবস কবে?",
                    "options": ["২৬ মার্চ", "১৬ ডিসেম্বর", "২১ ফেব্রুয়ারি", "৭ মার্চ"],
                    "answer": 0,
                    "category": "ইতিহাস",
                    "difficulty": "easy"
                },
                {
                    "question": "বাংলাদেশের জাতীয় পাখি কি?",
                    "options": ["দোয়েল", "ময়ূর", "কাক", "শালিক"],
                    "answer": 0,
                    "category": "প্রকৃতি",
                    "difficulty": "easy"
                },
                {
                    "question": "বাংলাদেশের জাতীয় ফুল কি?",
                    "options": ["গোলাপ", "শাপলা", "জবা", "বেলি"],
                    "answer": 1,
                    "category": "প্রকৃতি",
                    "difficulty": "easy"
                },
                {
                    "question": "পদ্মা সেতুর দৈর্ঘ্য কত কিমি?",
                    "options": ["৬.১৫ কিমি", "৫.৮ কিমি", "৭.২ কিমি", "৬.৫ কিমি"],
                    "answer": 0,
                    "category": "স্থাপত্য",
                    "difficulty": "medium"
                },
                {
                    "question": "বাংলাদেশের প্রথম প্রধানমন্ত্রী কে?",
                    "options": ["শেখ মুজিবুর রহমান", "তাজউদ্দিন আহমেদ", "খন্দকার মোশতাক আহমেদ", "জিয়াউর রহমান"],
                    "answer": 1,
                    "category": "ইতিহাস",
                    "difficulty": "medium"
                }
            ],
            "general": [
                {
                    "question": "সূর্য থেকে পৃথিবীতে আলো আসতে কত সময় লাগে?",
                    "options": ["৮ মিনিট ২০ সেকেন্ড", "১২ মিনিট", "৬ মিনিট", "১০ মিনিট"],
                    "answer": 0,
                    "category": "বিজ্ঞান",
                    "difficulty": "medium"
                },
                {
                    "question": "টেলিগ্রামে সর্বোচ্চ কত এমবি ফাইল সেন্ড করা যায়?",
                    "options": ["২ জিবি", "১.৫ জিবি", "২.৫ জিবি", "৫০০ এমবি"],
                    "answer": 0,
                    "category": "টেকনোলজি",
                    "difficulty": "easy"
                }
            ]
        }
    
    async def play_dice(self, user_id: int, bet: int, auto_roll: bool = False) -> Dict:
        """Play dice game with advanced features"""
        # Validate bet
        config = self.game_configs["dice"]
        
        if bet < config["min_bet"]:
            return {
                "success": False,
                "message": f"ন্যূনতম বেট {config['min_bet']} কয়েন"
            }
        
        if bet > config["max_bet"]:
            return {
                "success": False,
                "message": f"সর্বোচ্চ বেট {config['max_bet']} কয়েন"
            }
        
        # Check user coins
        user = self.db.get_user(user_id)
        if not user or user["coins"] < bet:
            return {
                "success": False,
                "message": f"পর্যাপ্ত কয়েন নেই! আপনার কয়েন: {Utils.format_coins(user['coins'] if user else 0)}"
            }
        
        # Get user win chance based on level
        win_chance = Utils.calculate_win_chance(user.get("level", 1), "dice")
        
        # Calculate house edge
        house_edge = config["house_edge"]
        actual_multiplier = config["win_multiplier"] * (1 - house_edge)
        
        # Roll dice with weighted chance
        user_roll = random.randint(1, 6)
        
        # Bot roll with house edge consideration
        if random.random() < win_chance:
            # User should win
            bot_roll = random.randint(1, user_roll - 1) if user_roll > 1 else 1
        else:
            # Bot should win (house edge)
            bot_roll = random.randint(user_roll + 1, 6) if user_roll < 6 else 6
        
        # Handle auto-roll (1 always loses, 6 always wins for bot)
        if auto_roll:
            bot_roll = 6 if random.random() < 0.7 else 1
        
        # Determine result
        if user_roll > bot_roll:
            result = "WIN"
            win_amount = int(bet * actual_multiplier)
            payout = win_amount
            net_profit = win_amount - bet
            
            # Update user coins
            user["coins"] += net_profit
            user["total_earned"] = user.get("total_earned", 0) + net_profit
            
            # Add XP for win
            xp_gain = bet // 10 + 5
            user["xp"] = user.get("xp", 0) + xp_gain
            
            message = f"🎲 আপনি পেলেন: {user_roll}\n🤖 বট পেলো: {bot_roll}\n🎉 আপনি জিতেছেন! +{win_amount} কয়েন (+{xp_gain} XP)"
        
        elif user_roll < bot_roll:
            result = "LOSE"
            win_amount = 0
            payout = 0
            net_profit = -bet
            
            # Update user coins
            user["coins"] -= bet
            user["total_spent"] = user.get("total_spent", 0) + bet
            
            # Small XP for participation
            xp_gain = bet // 20
            user["xp"] = user.get("xp", 0) + xp_gain
            
            message = f"🎲 আপনি পেলেন: {user_roll}\n🤖 বট পেলো: {bot_roll}\n😢 আপনি হারলেন! -{bet} কয়েন (+{xp_gain} XP)"
        
        else:  # Draw
            result = "DRAW"
            win_amount = 0
            payout = 0
            net_profit = 0
            xp_gain = bet // 15
            
            user["xp"] = user.get("xp", 0) + xp_gain
            
            message = f"🎲 আপনি পেলেন: {user_roll}\n🤖 বট পেলো: {bot_roll}\n🤝 ড্র হয়েছে! (+{xp_gain} XP)"
        
        # Update user
        self.db.update_user(user_id, {
            "coins": user["coins"],
            "total_earned": user.get("total_earned", 0),
            "total_spent": user.get("total_spent", 0),
            "xp": user["xp"],
            "total_xp": user.get("total_xp", 0) + xp_gain
        })
        
        # Update game stats
        game_result = {
            "game": "dice",
            "bet": bet,
            "won": result == "WIN",
            "payout": payout,
            "profit": net_profit,
            "user_roll": user_roll,
            "bot_roll": bot_roll,
            "xp_gained": xp_gain
        }
        
        self.db.update_game_stats(user_id, "dice", game_result)
        
        # Add to game history
        history_key = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.game_history[history_key] = {
            "user_id": user_id,
            "game": "dice",
            "result": result,
            "bet": bet,
            "payout": payout,
            "timestamp": datetime.now().isoformat(),
            "details": {
                "user_roll": user_roll,
                "bot_roll": bot_roll,
                "win_chance": win_chance,
                "house_edge": house_edge
            }
        }
        
        return {
            "success": True,
            "result": result,
            "message": message,
            "user_roll": user_roll,
            "bot_roll": bot_roll,
            "coins": user["coins"],
            "win_amount": win_amount,
            "net_profit": net_profit,
            "xp_gained": xp_gain,
            "new_level": Utils.calculate_level(user["xp"])["level"],
            "game_id": history_key
        }
    
    async def play_slot(self, user_id: int, bet: int) -> Dict:
        """Play slot machine game"""
        config = self.game_configs["slot"]
        
        if bet < config["min_bet"]:
            return {
                "success": False,
                "message": f"ন্যূনতম বেট {config['min_bet']} কয়েন"
            }
        
        if bet > config["max_bet"]:
            return {
                "success": False,
                "message": f"সর্বোচ্চ বেট {config['max_bet']} কয়েন"
            }
        
        user = self.db.get_user(user_id)
        if not user or user["coins"] < bet:
            return {
                "success": False,
                "message": f"পর্যাপ্ত কয়েন নেই! আপনার কয়েন: {Utils.format_coins(user['coins'] if user else 0)}"
            }
        
        # Calculate win chance with level bonus
        win_chance = Utils.calculate_win_chance(user.get("level", 1), "slot")
        jackpot_chance = 0.01 + (user.get("level", 1) * 0.001)  # 1% base + 0.1% per level
        
        # Generate slots with weighted randomness
        symbols = config["symbols"]
        
        if random.random() < jackpot_chance:
            # Force jackpot (rare)
            slot_result = [symbols[3], symbols[3], symbols[3]]  # 7️⃣ for jackpot
            result_type = "JACKPOT"
            multiplier = config["jackpot_multiplier"]
        
        elif random.random() < win_chance:
            # Force win
            winning_symbol = random.choice(symbols)
            slot_result = [winning_symbol, winning_symbol, random.choice(symbols)]
            result_type = "WIN"
            multiplier = config["win_multiplier"]
        
        else:
            # Random result
            slot_result = [random.choice(symbols) for _ in range(3)]
            
            # Check for matches
            if slot_result[0] == slot_result[1] == slot_result[2]:
                result_type = "JACKPOT"
                multiplier = config["jackpot_multiplier"]
            elif slot_result[0] == slot_result[1] or slot_result[1] == slot_result[2] or slot_result[0] == slot_result[2]:
                result_type = "WIN"
                multiplier = config["win_multiplier"]
            else:
                result_type = "LOSE"
                multiplier = 0
        
        # Calculate house edge
        house_edge = config["house_edge"]
        actual_multiplier = multiplier * (1 - house_edge) if multiplier > 0 else 0
        
        # Calculate payout
        if result_type != "LOSE":
            payout = int(bet * actual_multiplier)
            net_profit = payout - bet
            
            # Update user coins
            user["coins"] += net_profit
            user["total_earned"] = user.get("total_earned", 0) + net_profit
            
            # XP based on win type
            xp_gain = (bet // 10) * (3 if result_type == "JACKPOT" else 1)
            user["xp"] = user.get("xp", 0) + xp_gain
            
            message = f"{'🎰' * 3}\n[ {slot_result[0]} | {slot_result[1]} | {slot_result[2]} ]\n🎉 {result_type}! +{payout} কয়েন (+{xp_gain} XP)"
        
        else:
            payout = 0
            net_profit = -bet
            
            # Update user coins
            user["coins"] -= bet
            user["total_spent"] = user.get("total_spent", 0) + bet
            
            # Small XP for participation
            xp_gain = bet // 25
            user["xp"] = user.get("xp", 0) + xp_gain
            
            message = f"{'🎰' * 3}\n[ {slot_result[0]} | {slot_result[1]} | {slot_result[2]} ]\n😢 হারলেন! -{bet} কয়েন (+{xp_gain} XP)"
        
        # Update user
        self.db.update_user(user_id, {
            "coins": user["coins"],
            "total_earned": user.get("total_earned", 0),
            "total_spent": user.get("total_spent", 0),
            "xp": user["xp"],
            "total_xp": user.get("total_xp", 0) + xp_gain
        })
        
        # Update game stats
        game_result = {
            "game": "slot",
            "bet": bet,
            "won": result_type != "LOSE",
            "payout": payout,
            "profit": net_profit,
            "slots": slot_result,
            "result_type": result_type,
            "xp_gained": xp_gain
        }
        
        self.db.update_game_stats(user_id, "slot", game_result)
        
        # Add to history
        history_key = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.game_history[history_key] = {
            "user_id": user_id,
            "game": "slot",
            "result": result_type,
            "bet": bet,
            "payout": payout,
            "timestamp": datetime.now().isoformat(),
            "details": {
                "slots": slot_result,
                "win_chance": win_chance,
                "jackpot_chance": jackpot_chance,
                "house_edge": house_edge
            }
        }
        
        return {
            "success": True,
            "result": result_type,
            "message": message,
            "slots": slot_result,
            "coins": user["coins"],
            "payout": payout,
            "net_profit": net_profit,
            "xp_gained": xp_gain,
            "new_level": Utils.calculate_level(user["xp"])["level"],
            "game_id": history_key
        }
    
    async def start_quiz(self, user_id: int, category: str = None) -> Dict:
        """Start a quiz game"""
        config = self.game_configs["quiz"]
        
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        # Check entry fee
        if user["coins"] < config["entry_fee"]:
            return {
                "success": False,
                "message": f"কুইজ খেলার জন্য {config['entry_fee']} কয়েন প্রয়োজন!"
            }
        
        # Deduct entry fee
        user["coins"] -= config["entry_fee"]
        self.db.update_user(user_id, {"coins": user["coins"]})
        
        # Select category
        if category and category in self.quiz_questions:
            selected_category = category
        else:
            selected_category = random.choice(list(self.quiz_questions.keys()))
        
        # Select question based on user level
        user_level = user.get("level", 1)
        
        if user_level <= 5:
            difficulty_filter = "easy"
        elif user_level <= 10:
            difficulty_filter = "medium"
        else:
            difficulty_filter = random.choice(["easy", "medium", "hard"])
        
        # Filter questions by difficulty
        available_questions = [
            q for q in self.quiz_questions[selected_category]
            if q.get("difficulty", "easy") == difficulty_filter
        ]
        
        if not available_questions:
            available_questions = self.quiz_questions[selected_category]
        
        question = random.choice(available_questions)
        
        # Store active quiz
        quiz_id = f"quiz_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.active_games[quiz_id] = {
            "user_id": user_id,
            "question": question["question"],
            "options": question["options"],
            "correct_answer": question["answer"],
            "category": question.get("category", "general"),
            "difficulty": question.get("difficulty", "easy"),
            "start_time": datetime.now().isoformat(),
            "time_limit": config["time_limit"],
            "reward": config["reward"],
            "entry_fee": config["entry_fee"]
        }
        
        # Shuffle options but remember correct index
        options_with_index = list(enumerate(question["options"]))
        random.shuffle(options_with_index)
        
        shuffled_indices = [item[0] for item in options_with_index]
        shuffled_options = [item[1] for item in options_with_index]
        
        # Find new correct index
        new_correct_index = shuffled_indices.index(question["answer"])
        
        # Update with shuffled options
        self.active_games[quiz_id]["shuffled_options"] = shuffled_options
        self.active_games[quiz_id]["shuffled_indices"] = shuffled_indices
        self.active_games[quiz_id]["correct_shuffled_index"] = new_correct_index
        
        # Format question text
        options_text = "\n".join([
            f"{i+1}. {option}" for i, option in enumerate(shuffled_options)
        ])
        
        message = f"""
🧠 **কুইজ গেম** ({question.get('category', 'জেনারেল')})

❓ **প্রশ্ন:** {question['question']}

{options_text}

💰 **পুরস্কার:** {Utils.format_coins(config['reward'])}
⏱️ **সময়:** {config['time_limit']} সেকেন্ড
🎯 **ক্যাটাগরি:** {question.get('category', 'জেনারেল')}
📊 **কঠিনতা:** {question.get('difficulty', 'সহজ').upper()}

📝 **উত্তর দিন:** 1, 2, 3 বা 4 লিখুন
        """
        
        return {
            "success": True,
            "quiz_id": quiz_id,
            "message": message,
            "question": question["question"],
            "options": shuffled_options,
            "time_limit": config["time_limit"],
            "reward": config["reward"],
            "entry_fee_paid": config["entry_fee"],
            "remaining_coins": user["coins"]
        }
    
    async def submit_quiz_answer(self, user_id: int, answer_number: int) -> Dict:
        """Submit answer for active quiz"""
        # Find active quiz for user
        quiz_id = None
        quiz_data = None
        
        for qid, data in self.active_games.items():
            if data["user_id"] == user_id and data.get("question"):
                quiz_id = qid
                quiz_data = data
                break
        
        if not quiz_id or not quiz_data:
            return {
                "success": False,
                "message": "কোনো অ্যাকটিভ কুইজ খুঁজে পাওয়া যায়নি!"
            }
        
        # Check time limit
        start_time = datetime.fromisoformat(quiz_data["start_time"])
        time_passed = (datetime.now() - start_time).seconds
        
        if time_passed > quiz_data["time_limit"]:
            # Time's up
            del self.active_games[quiz_id]
            
            return {
                "success": False,
                "message": f"⏰ সময় শেষ! সঠিক উত্তর ছিল: {quiz_data['options'][quiz_data['correct_answer']]}",
                "correct_answer": quiz_data["options"][quiz_data["correct_answer"]],
                "time_taken": time_passed,
                "time_limit": quiz_data["time_limit"]
            }
        
        # Validate answer number
        if answer_number < 1 or answer_number > 4:
            return {
                "success": False,
                "message": "সঠিক উত্তর নম্বর দিন (1-4)"
            }
        
        # Check if answer is correct (using shuffled index)
        is_correct = (answer_number - 1) == quiz_data["correct_shuffled_index"]
        
        # Get user
        user = self.db.get_user(user_id)
        
        # Calculate reward
        if is_correct:
            reward = quiz_data["reward"]
            
            # Bonus for quick answer
            if time_passed < 10:  # Answered within 10 seconds
                time_bonus = int(reward * 0.2)  # 20% bonus
                reward += time_bonus
                bonus_text = f" (+{time_bonus} কুইক বোনাস)"
            else:
                time_bonus = 0
                bonus_text = ""
            
            # Level bonus
            level_bonus = user.get("level", 1) * 2
            reward += level_bonus
            
            # Update user coins
            user["coins"] += reward
            user["total_earned"] = user.get("total_earned", 0) + reward
            
            # XP gain
            xp_gain = 15 + (user.get("level", 1) * 2)
            user["xp"] = user.get("xp", 0) + xp_gain
            
            message = f"✅ সঠিক উত্তর! 🎉 +{Utils.format_coins(reward)}{bonus_text} (+{xp_gain} XP)"
            result = "WIN"
        
        else:
            reward = 0
            time_bonus = 0
            level_bonus = 0
            xp_gain = 5  # Small XP for participation
            
            user["xp"] = user.get("xp", 0) + xp_gain
            
            # Get correct answer text (original index)
            correct_answer_idx = quiz_data["correct_shuffled_index"]
            correct_answer = quiz_data["shuffled_options"][correct_answer_idx]
            
            message = f"❌ ভুল উত্তর! সঠিক উত্তর: {correct_answer} (+{xp_gain} XP)"
            result = "LOSE"
        
        # Update user
        self.db.update_user(user_id, {
            "coins": user["coins"],
            "total_earned": user.get("total_earned", 0),
            "xp": user["xp"],
            "total_xp": user.get("total_xp", 0) + xp_gain
        })
        
        # Update game stats
        game_result = {
            "game": "quiz",
            "bet": quiz_data["entry_fee"],
            "won": is_correct,
            "payout": reward,
            "profit": reward - quiz_data["entry_fee"],
            "time_taken": time_passed,
            "correct": is_correct,
            "xp_gained": xp_gain
        }
        
        self.db.update_game_stats(user_id, "quiz", game_result)
        
        # Remove from active games
        del self.active_games[quiz_id]
        
        # Add to history
        history_key = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.game_history[history_key] = {
            "user_id": user_id,
            "game": "quiz",
            "result": result,
            "entry_fee": quiz_data["entry_fee"],
            "payout": reward,
            "timestamp": datetime.now().isoformat(),
            "details": {
                "question": quiz_data["question"],
                "user_answer": answer_number - 1,
                "correct_answer": quiz_data["correct_shuffled_index"],
                "time_taken": time_passed,
                "category": quiz_data["category"],
                "difficulty": quiz_data["difficulty"]
            }
        }
        
        return {
            "success": True,
            "correct": is_correct,
            "message": message,
            "reward": reward,
            "coins": user["coins"],
            "xp_gained": xp_gain,
            "new_level": Utils.calculate_level(user["xp"])["level"],
            "time_taken": time_passed,
            "game_id": history_key
        }
    
    async def daily_bonus(self, user_id: int) -> Dict:
        """Claim daily bonus with streak system"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        today = datetime.now().strftime("%Y-%m-%d")
        last_daily = user.get("last_daily")
        
        # Check if already claimed today
        if last_daily == today:
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
            return {
                "success": False,
                "message": f"আজকের বোনাস ইতিমধ্যে নিয়েছেন! আগামীকাল আবার চেষ্টা করুন।\n⏰ {tomorrow}"
            }
        
        # Calculate streak
        streak = user.get("daily_streak", 0)
        
        if last_daily:
            last_date = datetime.fromisoformat(last_daily)
            days_diff = (datetime.now() - last_date).days
            
            if days_diff == 1:
                # Consecutive day
                streak += 1
                streak_message = f"🔥 {streak} দিন স্ট্রীক!"
            elif days_diff == 0:
                # Already claimed today (shouldn't happen due to earlier check)
                streak_message = "আজকের বোনাস নিয়েছেন!"
            else:
                # Streak broken
                streak = 1
                streak_message = "🔄 নতুন স্ট্রীক শুরু!"
        else:
            # First time
            streak = 1
            streak_message = "🎯 প্রথম দিন!"
        
        # Calculate bonus
        base_bonus = self.config.DAILY_BONUS
        streak_bonus = min(streak * 20, 200)  # 20 per day, max 200
        level_bonus = user.get("level", 1) * 5
        vip_bonus = 50 if user.get("is_vip", False) else 0
        
        total_bonus = base_bonus + streak_bonus + level_bonus + vip_bonus
        
        # Random lucky bonus (10% chance)
        lucky_bonus = 0
        if random.random() < 0.1:  # 10% chance
            lucky_bonus = random.randint(50, 200)
            total_bonus += lucky_bonus
        
        # Update user
        user["coins"] += total_bonus
        user["daily_streak"] = streak
        user["last_daily"] = today
        user["total_earned"] = user.get("total_earned", 0) + total_bonus
        
        # XP for claiming bonus
        xp_gain = 10 + (streak * 2)
        user["xp"] = user.get("xp", 0) + xp_gain
        
        # Update max streak
        if streak > user.get("max_streak", 0):
            user["max_streak"] = streak
        
        self.db.update_user(user_id, {
            "coins": user["coins"],
            "daily_streak": streak,
            "max_streak": user.get("max_streak", streak),
            "last_daily": today,
            "total_earned": user["total_earned"],
            "xp": user["xp"],
            "total_xp": user.get("total_xp", 0) + xp_gain
        })
        
        # Format bonus breakdown
        breakdown = f"""
💰 **ডেইলি বোনাস ব্রেকডাউন:**
• বেস বোনাস: {Utils.format_coins(base_bonus)}
• স্ট্রীক বোনাস ({streak} দিন): {Utils.format_coins(streak_bonus)}
• লেভেল বোনাস (লেভেল {user.get('level', 1)}): {Utils.format_coins(level_bonus)}
• VIP বোনাস: {Utils.format_coins(vip_bonus)}
"""
        
        if lucky_bonus > 0:
            breakdown += f"• 🍀 লাকি বোনাস: {Utils.format_coins(lucky_bonus)}\n"
        
        breakdown += f"• 📈 এক্সপিরিয়েন্স: +{xp_gain} XP\n"
        breakdown += f"• 🎯 **মোট বোনাস: {Utils.format_coins(total_bonus)}**"
        
        # Special rewards for milestone streaks
        milestone_rewards = ""
        if streak == 7:
            milestone_rewards = "\n🎖️ **১ সপ্তাহ স্ট্রীক অ্যাচিভমেন্ট!** +৫০০ কয়েন"
            user["coins"] += 500
            self.db.update_user(user_id, {"coins": user["coins"]})
        elif streak == 30:
            milestone_rewards = "\n🏆 **১ মাস স্ট্রীক অ্যাচিভমেন্ট!** +২০০০ কয়েন + VIP ৭ দিন"
            user["coins"] += 2000
            user["is_vip"] = True
            user["vip_until"] = (datetime.now() + timedelta(days=7)).isoformat()
            self.db.update_user(user_id, {
                "coins": user["coins"],
                "is_vip": True,
                "vip_until": user["vip_until"]
            })
        
        message = f"""
🎁 **ডেইলি বোনাস!** {streak_message}

{breakdown}{milestone_rewards}

💰 **মোট কয়েন:** {Utils.format_coins(user['coins'])}
🏆 **লেভেল:** {Utils.calculate_level(user['xp'])['level']}

⏰ **পরবর্তী বোনাস:** আগামীকাল
        """
        
        # Log the bonus claim
        self.db.add_log(
            "daily_bonus",
            f"Daily bonus claimed: {total_bonus} coins (streak: {streak})",
            user_id,
            {"bonus": total_bonus, "streak": streak, "xp_gained": xp_gain}
        )
        
        return {
            "success": True,
            "bonus": total_bonus,
            "streak": streak,
            "message": message,
            "coins": user["coins"],
            "xp_gained": xp_gain,
            "new_level": Utils.calculate_level(user["xp"])["level"],
            "breakdown": {
                "base": base_bonus,
                "streak": streak_bonus,
                "level": level_bonus,
                "vip": vip_bonus,
                "lucky": lucky_bonus,
                "xp": xp_gain
            }
        }
    
    async def get_game_stats(self, user_id: int = None, game_type: str = None) -> Dict:
        """Get game statistics"""
        stats = {
            "total_games": 0,
            "total_wins": 0,
            "total_losses": 0,
            "total_bet": 0,
            "total_payout": 0,
            "net_profit": 0,
            "win_rate": 0,
            "favorite_game": None,
            "game_breakdown": {}
        }
        
        # Filter game history
        user_games = []
        for game_id, game_data in self.game_history.items():
            if user_id and game_data["user_id"] != user_id:
                continue
            if game_type and game_data["game"] != game_type:
                continue
            user_games.append(game_data)
        
        stats["total_games"] = len(user_games)
        
        # Calculate stats
        for game in user_games:
            game_type = game["game"]
            
            if game_type not in stats["game_breakdown"]:
                stats["game_breakdown"][game_type] = {
                    "plays": 0,
                    "wins": 0,
                    "losses": 0,
                    "total_bet": 0,
                    "total_payout": 0
                }
            
            game_stats = stats["game_breakdown"][game_type]
            game_stats["plays"] += 1
            
            bet = game.get("bet", 0) or game.get("entry_fee", 0)
            payout = game.get("payout", 0)
            
            game_stats["total_bet"] += bet
            game_stats["total_payout"] += payout
            
            if game.get("result") in ["WIN", "JACKPOT"]:
                game_stats["wins"] += 1
                stats["total_wins"] += 1
            else:
                game_stats["losses"] += 1
                stats["total_losses"] += 1
            
            stats["total_bet"] += bet
            stats["total_payout"] += payout
        
        # Calculate overall stats
        if stats["total_games"] > 0:
            stats["win_rate"] = (stats["total_wins"] / stats["total_games"]) * 100
            stats["net_profit"] = stats["total_payout"] - stats["total_bet"]
            
            # Find favorite game
            if stats["game_breakdown"]:
                stats["favorite_game"] = max(
                    stats["game_breakdown"].items(),
                    key=lambda x: x[1]["plays"]
                )[0]
        
        # Calculate game-specific win rates
        for game_type, game_stats in stats["game_breakdown"].items():
            if game_stats["plays"] > 0:
                game_stats["win_rate"] = (game_stats["wins"] / game_stats["plays"]) * 100
                game_stats["net_profit"] = game_stats["total_payout"] - game_stats["total_bet"]
                game_stats["roi"] = ((game_stats["net_profit"] / max(game_stats["total_bet"], 1)) * 100)
        
        return stats
    
    async def get_available_games(self) -> List[Dict]:
        """Get list of available games"""
        games = []
        
        for game_id, config in self.game_configs.items():
            games.append({
                "id": game_id,
                "name": config["name"],
                "emoji": config["emoji"],
                "min_bet": config.get("min_bet", 0),
                "max_bet": config.get("max_bet", 0),
                "description": config["description"],
                "rules": config.get("rules", ""),
                "popularity": random.randint(50, 100)  # Simulated popularity
            })
        
        return games
    
    async def get_user_achievements(self, user_id: int) -> Dict:
        """Get user gaming achievements"""
        user = self.db.get_user(user_id)
        if not user:
            return {"achievements": []}
        
        stats = await self.get_game_stats(user_id)
        achievements = []
        
        # Gaming achievements
        if stats["total_games"] >= 10:
            achievements.append({
                "name": "🎮 গেমার শুরু",
                "description": "১০টি গেম খেলেছেন",
                "icon": "🎮",
                "unlocked": True
            })
        
        if stats["total_games"] >= 100:
            achievements.append({
                "name": "🏆 প্রো গেমার",
                "description": "১০০টি গেম খেলেছেন",
                "icon": "🏆",
                "unlocked": True
            })
        
        if stats["win_rate"] >= 60:
            achievements.append({
                "name": "⭐ উইনিং স্ট্রীক",
                "description": "৬০%+ উইন রেট",
                "icon": "⭐",
                "unlocked": True
            })
        
        if user.get("daily_streak", 0) >= 7:
            achievements.append({
                "name": "🔥 সপ্তাহিক চ্যাম্পিয়ন",
                "description": "৭ দিন স্ট্রীক",
                "icon": "🔥",
                "unlocked": True
            })
        
        if user.get("daily_streak", 0) >= 30:
            achievements.append({
                "name": "👑 মাস্টার প্লেয়ার",
                "description": "৩০ দিন স্ট্রীক",
                "icon": "👑",
                "unlocked": True
            })
        
        # Game-specific achievements
        for game_type, game_stats in stats["game_breakdown"].items():
            if game_stats["plays"] >= 50:
                achievements.append({
                    "name": f"🎯 {game_type.upper()} মাস্টার",
                    "description": f"৫০ বার {game_type} খেলেছেন",
                    "icon": "🎯",
                    "unlocked": True
                })
        
        return {
            "total_achievements": len(achievements),
            "achievements": achievements,
            "unlocked": len([a for a in achievements if a["unlocked"]]),
            "locked": 0  # Could calculate potential achievements
        }