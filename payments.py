from datetime import datetime
from typing import Dict, List, Optional, Tuple
import random
import json
from config import Config
from db import Database
from utils import Utils
import asyncio

class PaymentManager:
    """Advanced Payment Management System v15.0.00"""
    
    def __init__(self, db: Database):
        self.db = db
        self.config = Config()
        self.pending_payments = {}
        self.payment_webhooks = {}
        
        # Payment methods configuration
        self.payment_methods = {
            "nagod": {
                "name": "নগদ",
                "number": self.config.NAGOD_NUMBER,
                "emoji": "💳",
                "min_amount": 10,
                "max_amount": 50000,
                "fee_percent": 0,
                "processing_time": "Instant",
                "supported": True
            },
            "bikash": {
                "name": "বিকাশ",
                "number": self.config.BIKASH_NUMBER,
                "emoji": "📱",
                "min_amount": 10,
                "max_amount": 50000,
                "fee_percent": 1.5,
                "processing_time": "2-5 minutes",
                "supported": True
            },
            "rocket": {
                "name": "রকেট",
                "number": self.config.NAGOD_NUMBER,  # Same as Nagod for now
                "emoji": "🚀",
                "min_amount": 10,
                "max_amount": 50000,
                "fee_percent": 1.0,
                "processing_time": "5-10 minutes",
                "supported": True
            },
            "upay": {
                "name": "উপায়",
                "number": self.config.NAGOD_NUMBER,  # Same as Nagod for now
                "emoji": "⚡",
                "min_amount": 10,
                "max_amount": 50000,
                "fee_percent": 0.5,
                "processing_time": "Instant",
                "supported": True
            }
        }
    
    async def request_deposit(self, user_id: int, amount: float, method: str, trx_id: str = None) -> Dict:
        """Request deposit with advanced validation"""
        # Validate amount
        if amount < self.config.MIN_DEPOSIT:
            return {
                "success": False,
                "message": f"ন্যূনতম ডিপোজিট {self.config.MIN_DEPOSIT} টাকা"
            }
        
        if amount > 50000:  # Max deposit limit
            return {
                "success": False,
                "message": "সর্বোচ্চ ডিপোজিট ৫০,০০০ টাকা"
            }
        
        # Validate payment method
        method_lower = method.lower()
        if method_lower not in self.payment_methods:
            return {
                "success": False,
                "message": f"সাপোর্টেড পেমেন্ট মেথড: {', '.join([m['name'] for m in self.payment_methods.values()])}"
            }
        
        payment_method = self.payment_methods[method_lower]
        
        # Check if method is supported
        if not payment_method["supported"]:
            return {
                "success": False,
                "message": f"{payment_method['name']} বর্তমানে সাপোর্ট করছে না"
            }
        
        # Calculate fees
        fee = amount * (payment_method["fee_percent"] / 100)
        net_amount = amount - fee
        
        # Create payment data
        payment_data = {
            "user_id": user_id,
            "type": "DEPOSIT",
            "method": payment_method["name"],
            "method_code": method_lower,
            "amount": amount,
            "net_amount": net_amount,
            "fee": fee,
            "fee_percent": payment_method["fee_percent"],
            "status": "PENDING",
            "trx_id": trx_id,
            "reference": self._generate_reference(),
            "requested_at": datetime.now().isoformat(),
            "instructions": self._get_deposit_instructions(payment_method, amount, net_amount, fee),
            "metadata": {
                "user_ip": "N/A",
                "user_agent": "Telegram Bot",
                "payment_gateway": method_lower
            }
        }
        
        # Add payment to database
        payment_id = self.db.add_payment(payment_data)
        
        # Store in pending payments
        self.pending_payments[payment_id] = {
            "user_id": user_id,
            "amount": amount,
            "method": method_lower,
            "timestamp": datetime.now().timestamp()
        }
        
        # Log the payment request
        self.db.add_log(
            "payment_request",
            f"Deposit request: {amount} via {method_lower}",
            user_id,
            {"payment_id": payment_id, "amount": amount, "method": method_lower}
        )
        
        return {
            "success": True,
            "payment_id": payment_id,
            "instructions": payment_data["instructions"],
            "message": f"💰 {Utils.format_currency(amount)} ডিপোজিট রিকোয়েস্ট তৈরি হয়েছে!",
            "reference": payment_data["reference"],
            "payment_method": payment_method,
            "estimated_time": payment_method["processing_time"]
        }
    
    def _get_deposit_instructions(self, method: Dict, amount: float, net_amount: float, fee: float) -> str:
        """Generate deposit instructions"""
        instructions = f"""
💰 **{method['name']} ডিপোজিট ইনস্ট্রাকশন**

{method['emoji']} **পেমেন্ট নম্বর:** `{method['number']}`
💵 **পরিমাণ:** {Utils.format_currency(amount)}
📌 **রেফারেন্স:** MARPD-{datetime.now().strftime('%H%M')}

📊 **বিস্তারিত:**
• Gross Amount: {Utils.format_currency(amount)}
• Fee ({method['fee_percent']}%): {Utils.format_currency(fee)}
• Net Amount: {Utils.format_currency(net_amount)}
• Processing Time: {method['processing_time']}

✅ **পেমেন্ট করার নিয়ম:**
1. উপরের নম্বরে টাকা সেন্ড করুন
2. লেনদেন আইডি (TrxID) নোট করুন
3. এই ফরম্যাটে মেসেজ দিন:
   `/confirm_deposit [amount] [trx_id]`

📞 **সাপোর্ট:** @{self.config.OWNER_USERNAME}
⚠️ **দ্রষ্টব্য:** ভুল রেফারেন্স দিলে পেমেন্ট ডিলে হতে পারে
        """
        
        return instructions
    
    async def confirm_deposit(self, payment_id: str, trx_id: str, admin_id: int = None) -> Dict:
        """Confirm deposit (can be auto or manual)"""
        payment = self.db.payments.get(payment_id)
        
        if not payment:
            return {
                "success": False,
                "message": "পেমেন্ট খুঁজে পাওয়া যায়নি!"
            }
        
        if payment["status"] != "PENDING":
            current_status = payment["status"]
            return {
                "success": False,
                "message": f"পেমেন্ট ইতিমধ্যে {current_status}!"
            }
        
        # Auto-confirmation logic (for trusted payments)
        is_auto_confirm = admin_id is None
        
        if is_auto_confirm:
            # Auto-confirmation rules
            amount = payment["amount"]
            method = payment["method_code"]
            
            # Small amounts can be auto-confirmed
            if amount <= 500 and method in ["nagod", "bikash"]:
                admin_id = 0  # System auto-confirm
            else:
                return {
                    "success": False,
                    "message": "এই পেমেন্ট ম্যানুয়াল কনফার্মেশন প্রয়োজন!"
                }
        
        # Update payment status
        payment["status"] = "COMPLETED"
        payment["confirmed_by"] = admin_id
        payment["confirmed_at"] = datetime.now().isoformat()
        payment["trx_id"] = trx_id
        
        # Add bonus for first deposit
        user = self.db.get_user(payment["user_id"])
        is_first_deposit = len(self.db.get_user_payments(payment["user_id"])) == 0
        
        deposit_bonus = 0
        if is_first_deposit:
            deposit_bonus = min(payment["amount"] * 0.10, 500)  # 10% bonus, max 500
            payment["first_deposit_bonus"] = deposit_bonus
        
        # Update user balance
        total_added = payment["net_amount"] + deposit_bonus
        
        if user:
            user["balance"] = user.get("balance", 0) + total_added
            user["total_earned"] = user.get("total_earned", 0) + total_added
            
            # Update user level based on deposits
            deposit_xp = int(payment["amount"] * 0.5)  # 0.5 XP per taka
            current_level = Utils.calculate_level(user.get("xp", 0))
            user["xp"] = current_level["xp"] + deposit_xp
            user["total_xp"] = current_level["total_xp"] + deposit_xp
            
            self.db.update_user(payment["user_id"], {
                "balance": user["balance"],
                "total_earned": user["total_earned"],
                "xp": user["xp"],
                "total_xp": user["total_xp"]
            })
        
        # Save payment
        self.db.payments[payment_id] = payment
        self.db._save_data("payments", self.db.payments)
        
        # Remove from pending
        if payment_id in self.pending_payments:
            del self.pending_payments[payment_id]
        
        # Log the confirmation
        self.db.add_log(
            "payment_confirmed",
            f"Deposit confirmed: {payment['amount']} via {payment['method']}",
            payment["user_id"],
            {"payment_id": payment_id, "amount": payment["amount"], "bonus": deposit_bonus}
        )
        
        # Prepare response message
        bonus_text = f"\n🎁 প্রথম ডিপোজিট বোনাস: +{Utils.format_currency(deposit_bonus)}" if is_first_deposit else ""
        
        return {
            "success": True,
            "message": f"✅ ডিপোজিট কনফার্ম হয়েছে!{bonus_text}\n💰 যোগ হয়েছে: {Utils.format_currency(total_added)}",
            "amount_added": total_added,
            "bonus": deposit_bonus,
            "new_balance": user["balance"] if user else 0,
            "payment_id": payment_id,
            "confirmed_by": "সিস্টেম" if admin_id == 0 else f"অ্যাডমিন {admin_id}"
        }
    
    async def request_withdraw(self, user_id: int, amount: float, method: str, account_number: str) -> Dict:
        """Request withdrawal with validation"""
        user = self.db.get_user(user_id)
        
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        # Validate amount
        if amount < self.config.MIN_WITHDRAW:
            return {
                "success": False,
                "message": f"ন্যূনতম উইথড্র {self.config.MIN_WITHDRAW} টাকা"
            }
        
        if amount > self.config.MAX_WITHDRAW_DAILY:
            return {
                "success": False,
                "message": f"সর্বোচ্চ উইথড্র {Utils.format_currency(self.config.MAX_WITHDRAW_DAILY)} প্রতি দিন"
            }
        
        # Check daily withdrawal limit
        today_withdrawals = await self._get_today_withdrawals(user_id)
        total_today = sum(w["amount"] for w in today_withdrawals)
        
        if total_today + amount > self.config.MAX_WITHDRAW_DAILY:
            remaining = self.config.MAX_WITHDRAW_DAILY - total_today
            return {
                "success": False,
                "message": f"আজকের উইথড্র লিমিট শেষ! বাকি আছে: {Utils.format_currency(remaining)}"
            }
        
        # Check balance
        if user["balance"] < amount:
            return {
                "success": False,
                "message": f"পর্যাপ্ত ব্যালেন্স নেই! আপনার ব্যালেন্স: {Utils.format_currency(user['balance'])}"
            }
        
        # Validate payment method
        method_lower = method.lower()
        if method_lower not in self.payment_methods:
            return {
                "success": False,
                "message": f"সাপোর্টেড পেমেন্ট মেথড: {', '.join([m['name'] for m in self.payment_methods.values()])}"
            }
        
        # Validate account number
        if not Utils.validate_phone(account_number):
            return {
                "success": False,
                "message": "সঠিক মোবাইল নম্বর দিন (11 ডিজিট)"
            }
        
        payment_method = self.payment_methods[method_lower]
        
        # Calculate fees
        fee = amount * (payment_method["fee_percent"] / 100)
        net_amount = amount - fee
        
        # Create withdrawal data
        payment_data = {
            "user_id": user_id,
            "type": "WITHDRAW",
            "method": payment_method["name"],
            "method_code": method_lower,
            "amount": amount,
            "net_amount": net_amount,
            "fee": fee,
            "fee_percent": payment_method["fee_percent"],
            "status": "PENDING",
            "account_number": account_number,
            "reference": self._generate_reference(),
            "requested_at": datetime.now().isoformat(),
            "metadata": {
                "daily_withdrawal": total_today + amount,
                "user_level": user.get("level", 1),
                "processing_priority": "normal"
            }
        }
        
        # Deduct balance immediately
        user["balance"] -= amount
        user["total_spent"] = user.get("total_spent", 0) + amount
        
        self.db.update_user(user_id, {
            "balance": user["balance"],
            "total_spent": user["total_spent"]
        })
        
        # Add payment to database
        payment_id = self.db.add_payment(payment_data)
        
        # Send notification to admin
        admin_notification = self._create_admin_notification(payment_id, user, payment_data)
        
        # Log the withdrawal request
        self.db.add_log(
            "withdrawal_request",
            f"Withdrawal request: {amount} to {account_number}",
            user_id,
            {"payment_id": payment_id, "amount": amount, "account": account_number}
        )
        
        return {
            "success": True,
            "payment_id": payment_id,
            "message": f"🏧 {Utils.format_currency(amount)} উইথড্র রিকোয়েস্ট তৈরি হয়েছে!",
            "net_amount": net_amount,
            "fee": fee,
            "new_balance": user["balance"],
            "admin_notification": admin_notification,
            "estimated_time": "২৪ ঘন্টার মধ্যে"
        }
    
    def _create_admin_notification(self, payment_id: str, user: Dict, payment_data: Dict) -> str:
        """Create admin notification for withdrawal"""
        return f"""
🚨 **নতুন উইথড্র রিকোয়েস্ট!**

👤 **ইউজার:**
• ID: {user['id']}
• নাম: {user.get('first_name', 'N/A')}
• লেভেল: {user.get('level', 1)}

💰 **বিস্তারিত:**
• পরিমাণ: {Utils.format_currency(payment_data['amount'])}
• মেথড: {payment_data['method']}
• একাউন্ট: {payment_data['account_number']}
• Net Amount: {Utils.format_currency(payment_data['net_amount'])}
• Fee: {Utils.format_currency(payment_data['fee'])}
• রেফারেন্স: {payment_data['reference']}

🆔 **পেমেন্ট আইডি:** `{payment_id}`

✅ **অ্যাডমিন কমান্ড:**
• `/confirm_withdraw {payment_id}` - কনফার্ম করুন
• `/reject_withdraw {payment_id} [reason]` - রিজেক্ট করুন

📊 **ইউজার স্ট্যাটাস:**
• ব্যালেন্স: {Utils.format_currency(user.get('balance', 0))}
• লেভেল: {user.get('level', 1)}
• সতর্কতা: {user.get('warnings', 0)}/3
        """
    
    async def confirm_withdraw(self, payment_id: str, admin_id: int) -> Dict:
        """Confirm withdrawal (admin only)"""
        payment = self.db.payments.get(payment_id)
        
        if not payment:
            return {
                "success": False,
                "message": "পেমেন্ট খুঁজে পাওয়া যায়নি!"
            }
        
        if payment["status"] != "PENDING":
            return {
                "success": False,
                "message": f"পেমেন্ট ইতিমধ্যে {payment['status']}!"
            }
        
        if payment["type"] != "WITHDRAW":
            return {
                "success": False,
                "message": "শুধুমাত্র উইথড্র পেমেন্ট কনফার্ম করা যায়!"
            }
        
        # Update payment status
        payment["status"] = "COMPLETED"
        payment["confirmed_by"] = admin_id
        payment["confirmed_at"] = datetime.now().isoformat()
        payment["processed_at"] = datetime.now().isoformat()
        
        # Save payment
        self.db.payments[payment_id] = payment
        self.db._save_data("payments", self.db.payments)
        
        # Get user
        user = self.db.get_user(payment["user_id"])
        
        # Log the confirmation
        self.db.add_log(
            "withdrawal_confirmed",
            f"Withdrawal confirmed: {payment['amount']} to {payment['account_number']}",
            payment["user_id"],
            {"payment_id": payment_id, "amount": payment["amount"], "admin_id": admin_id}
        )
        
        return {
            "success": True,
            "message": f"✅ উইথড্র কনফার্ম হয়েছে! {Utils.format_currency(payment['net_amount'])} পাঠানো হয়েছে।",
            "amount_sent": payment["net_amount"],
            "account": payment["account_number"],
            "user_id": payment["user_id"],
            "user_name": user.get("first_name", "User") if user else "Unknown"
        }
    
    async def reject_payment(self, payment_id: str, admin_id: int, reason: str = "No reason provided") -> Dict:
        """Reject payment (admin only)"""
        payment = self.db.payments.get(payment_id)
        
        if not payment:
            return {
                "success": False,
                "message": "পেমেন্ট খুঁজে পাওয়া যায়নি!"
            }
        
        if payment["status"] != "PENDING":
            return {
                "success": False,
                "message": f"পেমেন্ট ইতিমধ্যে {payment['status']}!"
            }
        
        # Refund balance if it's a withdrawal
        if payment["type"] == "WITHDRAW":
            user = self.db.get_user(payment["user_id"])
            if user:
                user["balance"] += payment["amount"]
                self.db.update_user(payment["user_id"], {"balance": user["balance"]})
        
        # Update payment status
        payment["status"] = "REJECTED"
        payment["rejected_by"] = admin_id
        payment["rejected_at"] = datetime.now().isoformat()
        payment["rejection_reason"] = reason
        
        # Save payment
        self.db.payments[payment_id] = payment
        self.db._save_data("payments", self.db.payments)
        
        # Log the rejection
        self.db.add_log(
            "payment_rejected",
            f"Payment rejected: {payment['amount']} - Reason: {reason}",
            payment["user_id"],
            {"payment_id": payment_id, "reason": reason, "admin_id": admin_id}
        )
        
        return {
            "success": True,
            "message": f"❌ পেমেন্ট রিজেক্ট হয়েছে। কারণ: {reason}",
            "payment_id": payment_id,
            "refunded": payment["type"] == "WITHDRAW"
        }
    
    async def get_payment_history(self, user_id: int, limit: int = 10, page: int = 1) -> Dict:
        """Get user's payment history with pagination"""
        all_payments = self.db.get_user_payments(user_id)
        
        # Sort by date (newest first)
        all_payments.sort(key=lambda x: x.get("requested_at", ""), reverse=True)
        
        # Pagination
        total_payments = len(all_payments)
        total_pages = (total_payments + limit - 1) // limit
        page = min(max(page, 1), total_pages)
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        payments = all_payments[start_idx:end_idx]
        
        # Format payments for display
        formatted_payments = []
        total_deposits = 0
        total_withdrawals = 0
        
        for payment in payments:
            status_icon = {
                "PENDING": "⏳",
                "COMPLETED": "✅",
                "REJECTED": "❌",
                "FAILED": "❌"
            }.get(payment.get("status", "PENDING"), "❓")
            
            type_icon = "💰" if payment["type"] == "DEPOSIT" else "🏧"
            
            formatted_payments.append({
                "id": payment.get("id", "N/A"),
                "type": payment["type"],
                "type_icon": type_icon,
                "method": payment.get("method", "N/A"),
                "amount": payment.get("amount", 0),
                "status": payment.get("status", "UNKNOWN"),
                "status_icon": status_icon,
                "time": payment.get("requested_at", "N/A")[:16],
                "reference": payment.get("reference", "N/A")
            })
            
            if payment["type"] == "DEPOSIT" and payment.get("status") == "COMPLETED":
                total_deposits += payment.get("amount", 0)
            elif payment["type"] == "WITHDRAW" and payment.get("status") == "COMPLETED":
                total_withdrawals += payment.get("amount", 0)
        
        # Create summary
        summary = {
            "total_payments": total_payments,
            "total_deposits": total_deposits,
            "total_withdrawals": total_withdrawals,
            "net_flow": total_deposits - total_withdrawals,
            "success_rate": (len([p for p in all_payments if p.get("status") == "COMPLETED"]) / max(total_payments, 1)) * 100
        }
        
        return {
            "payments": formatted_payments,
            "summary": summary,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "total_items": total_payments,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    async def _get_today_withdrawals(self, user_id: int) -> List[Dict]:
        """Get today's withdrawals for a user"""
        today = datetime.now().strftime("%Y-%m-%d")
        withdrawals = []
        
        for payment in self.db.payments.values():
            if (payment.get("user_id") == user_id and 
                payment.get("type") == "WITHDRAW" and
                payment.get("requested_at", "").startswith(today)):
                withdrawals.append(payment)
        
        return withdrawals
    
    def _generate_reference(self) -> str:
        """Generate unique payment reference"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=6))
        return f"MARPD-{timestamp}-{random_part}"
    
    async def get_payment_methods(self) -> List[Dict]:
        """Get available payment methods"""
        methods = []
        
        for code, method in self.payment_methods.items():
            if method["supported"]:
                methods.append({
                    "code": code,
                    "name": method["name"],
                    "emoji": method["emoji"],
                    "number": method["number"],
                    "min_amount": method["min_amount"],
                    "max_amount": method["max_amount"],
                    "fee_percent": method["fee_percent"],
                    "processing_time": method["processing_time"],
                    "description": f"{method['emoji']} {method['name']} - {method['processing_time']}"
                })
        
        return methods
    
    async def get_payment_stats(self, user_id: int = None) -> Dict:
        """Get payment statistics"""
        total_deposits = 0
        total_withdrawals = 0
        pending_deposits = 0
        pending_withdrawals = 0
        successful_transactions = 0
        failed_transactions = 0
        
        for payment in self.db.payments.values():
            if user_id and payment.get("user_id") != user_id:
                continue
            
            amount = payment.get("amount", 0)
            status = payment.get("status", "PENDING")
            
            if payment["type"] == "DEPOSIT":
                total_deposits += amount
                if status == "PENDING":
                    pending_deposits += amount
            elif payment["type"] == "WITHDRAW":
                total_withdrawals += amount
                if status == "PENDING":
                    pending_withdrawals += amount
            
            if status == "COMPLETED":
                successful_transactions += 1
            elif status in ["REJECTED", "FAILED"]:
                failed_transactions += 1
        
        total_transactions = len([p for p in self.db.payments.values() 
                                 if not user_id or p.get("user_id") == user_id])
        
        success_rate = (successful_transactions / max(total_transactions, 1)) * 100
        
        return {
            "total_deposits": total_deposits,
            "total_withdrawals": total_withdrawals,
            "pending_deposits": pending_deposits,
            "pending_withdrawals": pending_withdrawals,
            "net_flow": total_deposits - total_withdrawals,
            "total_transactions": total_transactions,
            "successful_transactions": successful_transactions,
            "failed_transactions": failed_transactions,
            "success_rate": success_rate,
            "avg_deposit": total_deposits / max(len([p for p in self.db.payments.values() 
                                                    if p["type"] == "DEPOSIT"]), 1),
            "avg_withdrawal": total_withdrawals / max(len([p for p in self.db.payments.values() 
                                                          if p["type"] == "WITHDRAW"]), 1)
        }