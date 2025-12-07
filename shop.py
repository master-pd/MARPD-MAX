import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from config import Config
from db import Database
from utils import Utils

class ShopManager:
    """Advanced Shop Management System v15.0.00"""
    
    def __init__(self, db: Database):
        self.db = db
        self.config = Config()
        self.daily_deals = {}
        self.featured_items = []
        self.cart_system = {}
        
        # Initialize shop if empty
        if not self.db.shop.get("items"):
            self.db.shop = self.db._default_shop()
    
    async def get_shop_items(self, category: str = None, filter_type: str = None) -> List[Dict]:
        """Get shop items with filtering and sorting"""
        items = self.db.get_shop_items(category)
        
        # Apply filters
        if filter_type:
            if filter_type == "popular":
                items = sorted(items, key=lambda x: x.get("popularity", 0), reverse=True)
            elif filter_type == "new":
                items = sorted(items, key=lambda x: x.get("added_date", ""), reverse=True)
            elif filter_type == "cheap":
                items = sorted(items, key=lambda x: x.get("price", 0))
            elif filter_type == "expensive":
                items = sorted(items, key=lambda x: x.get("price", 0), reverse=True)
            elif filter_type == "discount":
                items = [item for item in items if item.get("discount", 0) > 0]
                items = sorted(items, key=lambda x: x.get("discount", 0), reverse=True)
        
        # Add daily deals
        await self._update_daily_deals()
        for item in items:
            if item["id"] in self.daily_deals:
                deal = self.daily_deals[item["id"]]
                item["original_price"] = item["price"]
                item["price"] = deal["discounted_price"]
                item["discount"] = deal["discount_percent"]
                item["deal_expires"] = deal["expires_at"]
                item["is_daily_deal"] = True
        
        return items
    
    async def _update_daily_deals(self):
        """Update daily deals"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if "last_updated" not in self.daily_deals or self.daily_deals["last_updated"] != today:
            # Generate new daily deals
            all_items = self.db.get_shop_items()
            
            # Select 2-3 random items for daily deals
            deal_items = random.sample(all_items, min(3, len(all_items)))
            
            self.daily_deals = {
                "last_updated": today,
                "deals": {}
            }
            
            for item in deal_items:
                discount = random.choice([10, 15, 20, 25, 30])
                discounted_price = int(item["price"] * (100 - discount) / 100)
                
                self.daily_deals["deals"][item["id"]] = {
                    "item_id": item["id"],
                    "original_price": item["price"],
                    "discounted_price": discounted_price,
                    "discount_percent": discount,
                    "expires_at": (datetime.now() + timedelta(days=1)).isoformat()
                }
    
    async def buy_item(self, user_id: int, item_id: str, quantity: int = 1) -> Dict:
        """Buy an item from shop"""
        # Get item
        item = self.db.get_item(item_id)
        if not item:
            return {
                "success": False,
                "message": "এই আইটেমটি শপে নেই!"
            }
        
        # Check daily deal
        final_price = item["price"]
        is_daily_deal = False
        
        if item_id in self.daily_deals.get("deals", {}):
            deal = self.daily_deals["deals"][item_id]
            final_price = deal["discounted_price"]
            is_daily_deal = True
        
        total_price = final_price * quantity
        
        # Get user
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        # Check user coins
        if user["coins"] < total_price:
            return {
                "success": False,
                "message": f"পর্যাপ্ত কয়েন নেই! দরকার: {Utils.format_coins(total_price)}, আপনার আছে: {Utils.format_coins(user['coins'])}"
            }
        
        # Check item requirements
        requirements = item.get("requirements", {})
        
        if "min_level" in requirements and user.get("level", 1) < requirements["min_level"]:
            return {
                "success": False,
                "message": f"এই আইটেম কেনার জন্য লেভেল {requirements['min_level']} প্রয়োজন!"
            }
        
        if "vip_only" in requirements and requirements["vip_only"] and not user.get("is_vip", False):
            return {
                "success": False,
                "message": "এই আইটেম শুধুমাত্র VIP ইউজারদের জন্য!"
            }
        
        # Check if item is limited stock
        stock = item.get("stock", -1)  # -1 means unlimited
        if stock >= 0:
            if stock < quantity:
                return {
                    "success": False,
                    "message": f"স্টক শেষ! মাত্র {stock}টি আছে।"
                }
            # Update stock
            item["stock"] = stock - quantity
        
        # Deduct coins
        user["coins"] -= total_price
        user["total_spent"] = user.get("total_spent", 0) + total_price
        
        # Add to inventory
        inventory_item = {
            "item_id": item_id,
            "name": item["name"],
            "purchased_at": datetime.now().isoformat(),
            "price_paid": final_price,
            "quantity": quantity,
            "is_daily_deal": is_daily_deal,
            "expires_at": None
        }
        
        # Set expiration for timed items
        if item.get("duration_days"):
            inventory_item["expires_at"] = (datetime.now() + timedelta(days=item["duration_days"])).isoformat()
        elif item.get("duration_hours"):
            inventory_item["expires_at"] = (datetime.now() + timedelta(hours=item["duration_hours"])).isoformat()
        
        # Add to user inventory
        if "inventory" not in user:
            user["inventory"] = []
        
        # Check if already have this item
        found = False
        for inv_item in user["inventory"]:
            if inv_item["item_id"] == item_id:
                inv_item["quantity"] += quantity
                inv_item["last_purchased"] = datetime.now().isoformat()
                found = True
                break
        
        if not found:
            inventory_item["first_purchased"] = datetime.now().isoformat()
            user["inventory"].append(inventory_item)
        
        # Apply item effects
        bonuses = await self._apply_item_effects(user_id, item)
        
        # Update user
        self.db.update_user(user_id, {
            "coins": user["coins"],
            "total_spent": user["total_spent"],
            "inventory": user["inventory"]
        })
        
        # Update shop stock
        if stock >= 0:
            self._update_shop_item_stock(item_id, stock - quantity)
        
        # Log the purchase
        self.db.add_log(
            "shop_purchase",
            f"Purchased {item['name']} for {total_price} coins",
            user_id,
            {"item_id": item_id, "price": total_price, "quantity": quantity}
        )
        
        # Format response message
        deal_text = f" (Daily Deal -{item.get('discount', 0)}%!)" if is_daily_deal else ""
        
        message = f"""
✅ **ক্রয় সফল!** {deal_text}

🛍️ **আইটেম:** {item['icon']} {item['name']}
💰 **দাম:** {Utils.format_coins(total_price)} ({quantity}টি)
📦 **স্টক:** {item.get('stock', '∞')}

🎁 **বোনাস:**
{bonuses.get('message', 'কোনো বোনাস নেই')}

💰 **বাকি কয়েন:** {Utils.format_coins(user['coins'])}
📊 **মোট খরচ:** {Utils.format_coins(user['total_spent'])}
"""
        
        if inventory_item.get("expires_at"):
            expires = datetime.fromisoformat(inventory_item["expires_at"]).strftime("%d/%m/%Y %H:%M")
            message += f"\n⏰ **মেয়াদ:** {expires} পর্যন্ত"
        
        return {
            "success": True,
            "message": message,
            "item": item,
            "total_price": total_price,
            "coins": user["coins"],
            "inventory_count": len(user["inventory"]),
            "bonuses": bonuses,
            "daily_deal": is_daily_deal,
            "expires_at": inventory_item.get("expires_at")
        }
    
    async def _apply_item_effects(self, user_id: int, item: Dict) -> Dict:
        """Apply item effects to user"""
        bonuses = {
            "coins_added": 0,
            "xp_added": 0,
            "message": ""
        }
        
        user = self.db.get_user(user_id)
        
        # Apply bonuses based on item type
        item_bonus = item.get("bonus", {})
        
        if "daily_extra" in item_bonus:
            # This will be applied when claiming daily bonus
            bonuses["message"] += f"• ডেইলি বোনাস: +{item_bonus['daily_extra']} কয়েন\n"
        
        if "xp_boost" in item_bonus:
            bonuses["message"] += f"• XP বুস্ট: +{item_bonus['xp_boost']}%\n"
        
        if "coin_multiplier" in item_bonus:
            bonuses["message"] += f"• কয়েন মাল্টিপ্লায়ার: {item_bonus['coin_multiplier']}x\n"
        
        # Special effects based on item category
        if item.get("category") == "booster":
            # Add temporary boost to user
            if "boosts" not in user:
                user["boosts"] = []
            
            user["boosts"].append({
                "type": item["id"],
                "start_time": datetime.now().isoformat(),
                "duration": item.get("duration_days", 1) * 86400,  # Convert to seconds
                "effect": item_bonus
            })
            
            bonuses["message"] += f"• বুস্টার সক্রিয়: {item['name']}\n"
        
        elif item.get("category") == "badge":
            # Equip badge
            if "equipped_items" not in user:
                user["equipped_items"] = {}
            
            user["equipped_items"]["badge"] = item["id"]
            bonuses["message"] += f"• ব্যাজ ইকুইপ করা হয়েছে: {item['icon']}\n"
        
        # Save user updates
        self.db.update_user(user_id, {
            "boosts": user.get("boosts", []),
            "equipped_items": user.get("equipped_items", {})
        })
        
        if not bonuses["message"]:
            bonuses["message"] = "কোনো বোনাস নেই"
        
        return bonuses
    
    def _update_shop_item_stock(self, item_id: str, new_stock: int):
        """Update shop item stock"""
        for i, item in enumerate(self.db.shop.get("items", [])):
            if item["id"] == item_id:
                self.db.shop["items"][i]["stock"] = new_stock
                self.db._save_data("shop", self.db.shop)
                break
    
    async def get_user_inventory(self, user_id: int, show_expired: bool = False) -> Dict:
        """Get user's inventory with details"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!",
                "inventory": []
            }
        
        inventory = user.get("inventory", [])
        
        # Check for expired items
        now = datetime.now()
        active_items = []
        expired_items = []
        
        for item in inventory:
            expires_at = item.get("expires_at")
            
            if expires_at:
                try:
                    expiry_date = datetime.fromisoformat(expires_at)
                    if expiry_date < now:
                        expired_items.append(item)
                        continue
                except:
                    pass
            
            # Get item details
            item_details = self.db.get_item(item["item_id"])
            if item_details:
                item["details"] = item_details
            
            active_items.append(item)
        
        # Remove expired items if not showing
        if not show_expired and expired_items:
            user["inventory"] = active_items
            self.db.update_user(user_id, {"inventory": user["inventory"]})
        
        # Calculate total value
        total_value = 0
        for item in active_items:
            price = item.get("price_paid", 0) or item.get("details", {}).get("price", 0)
            total_value += price * item.get("quantity", 1)
        
        # Get equipped items
        equipped = user.get("equipped_items", {})
        
        return {
            "success": True,
            "inventory": active_items,
            "expired_items": expired_items,
            "total_items": len(active_items),
            "total_value": total_value,
            "equipped_items": equipped,
            "storage_used": f"{len(active_items)}/∞"
        }
    
    async def use_item(self, user_id: int, item_id: str, quantity: int = 1) -> Dict:
        """Use an item from inventory"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        # Find item in inventory
        inventory = user.get("inventory", [])
        item_index = -1
        item_data = None
        
        for i, item in enumerate(inventory):
            if item["item_id"] == item_id:
                item_index = i
                item_data = item
                break
        
        if item_index == -1:
            return {
                "success": False,
                "message": "এই আইটেমটি আপনার ইনভেন্টরিতে নেই!"
            }
        
        # Check quantity
        if item_data["quantity"] < quantity:
            return {
                "success": False,
                "message": f"মাত্র {item_data['quantity']}টি আছে, {quantity}টি ব্যবহার করা যাবে না!"
            }
        
        # Get item details
        item_details = self.db.get_item(item_id)
        
        # Apply item effects
        result = await self._use_item_effect(user_id, item_details, quantity)
        
        if not result["success"]:
            return result
        
        # Update inventory
        if item_data["quantity"] == quantity:
            # Remove item
            del inventory[item_index]
        else:
            # Reduce quantity
            inventory[item_index]["quantity"] -= quantity
        
        # Update user
        self.db.update_user(user_id, {
            "inventory": inventory
        })
        
        # Log item usage
        self.db.add_log(
            "item_used",
            f"Used {item_details['name']} x{quantity}",
            user_id,
            {"item_id": item_id, "quantity": quantity, "effect": result}
        )
        
        return {
            "success": True,
            "message": f"✅ {item_details['icon']} {item_details['name']} x{quantity} ব্যবহার করা হয়েছে!\n{result.get('message', '')}",
            "item": item_details,
            "quantity_used": quantity,
            "remaining": item_data["quantity"] - quantity,
            "effect": result
        }
    
    async def _use_item_effect(self, user_id: int, item: Dict, quantity: int) -> Dict:
        """Apply effect when using an item"""
        user = self.db.get_user(user_id)
        effects = []
        
        # Based on item category
        category = item.get("category")
        
        if category == "consumable":
            if "coins" in item.get("effects", {}):
                coin_gain = item["effects"]["coins"] * quantity
                user["coins"] += coin_gain
                effects.append(f"+{coin_gain} কয়েন")
            
            if "xp" in item.get("effects", {}):
                xp_gain = item["effects"]["xp"] * quantity
                user["xp"] += xp_gain
                effects.append(f"+{xp_gain} XP")
        
        elif category == "booster":
            # Activate booster
            if "boosts" not in user:
                user["boosts"] = []
            
            duration = item.get("duration_hours", 24) * 3600  # Convert to seconds
            
            user["boosts"].append({
                "type": item["id"],
                "start_time": datetime.now().isoformat(),
                "duration": duration,
                "effect": item.get("effects", {})
            })
            
            effects.append(f"{item['name']} বুস্টার সক্রিয়")
        
        # Update user
        update_data = {}
        if "coins" in user:
            update_data["coins"] = user["coins"]
        if "xp" in user:
            update_data["xp"] = user["xp"]
        if "boosts" in user:
            update_data["boosts"] = user["boosts"]
        
        if update_data:
            self.db.update_user(user_id, update_data)
        
        return {
            "success": True,
            "message": ", ".join(effects) if effects else "আইটেম ব্যবহার করা হয়েছে",
            "effects": effects
        }
    
    async def equip_item(self, user_id: int, item_id: str, slot: str = "badge") -> Dict:
        """Equip an item"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        # Check if item exists in inventory
        inventory = user.get("inventory", [])
        has_item = any(item["item_id"] == item_id for item in inventory)
        
        if not has_item:
            return {
                "success": False,
                "message": "এই আইটেমটি আপনার ইনভেন্টরিতে নেই!"
            }
        
        # Get item details
        item_details = self.db.get_item(item_id)
        if not item_details:
            return {
                "success": False,
                "message": "আইটেম ডিটেইলস পাওয়া যায়নি!"
            }
        
        # Check if item can be equipped in this slot
        category = item_details.get("category")
        valid_slots = {
            "badge": ["badge"],
            "cosmetic": ["title", "frame", "effect"],
            "tool": ["tool"]
        }
        
        valid_for_slot = False
        for slot_type, categories in valid_slots.items():
            if category in categories and slot == slot_type:
                valid_for_slot = True
                break
        
        if not valid_for_slot:
            return {
                "success": False,
                "message": f"এই আইটেমটি {slot} স্লটে ইকুইপ করা যায় না!"
            }
        
        # Equip item
        if "equipped_items" not in user:
            user["equipped_items"] = {}
        
        # Unequip previous item in same slot if any
        previous_item = user["equipped_items"].get(slot)
        
        user["equipped_items"][slot] = item_id
        
        self.db.update_user(user_id, {
            "equipped_items": user["equipped_items"]
        })
        
        message = f"✅ {item_details['icon']} {item_details['name']} ইকুইপ করা হয়েছে!"
        
        if previous_item:
            prev_details = self.db.get_item(previous_item)
            if prev_details:
                message += f"\n❌ {prev_details['icon']} {prev_details['name']} আনইকুইপ করা হয়েছে।"
        
        return {
            "success": True,
            "message": message,
            "slot": slot,
            "item": item_details,
            "previous_item": previous_item
        }
    
    async def unequip_item(self, user_id: int, slot: str) -> Dict:
        """Unequip an item"""
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        equipped = user.get("equipped_items", {})
        
        if slot not in equipped:
            return {
                "success": False,
                "message": f"{slot} স্লটে কোনো আইটেম ইকুইপ নেই!"
            }
        
        item_id = equipped[slot]
        item_details = self.db.get_item(item_id)
        
        # Remove from equipped
        del equipped[slot]
        
        self.db.update_user(user_id, {
            "equipped_items": equipped
        })
        
        message = f"❌ {item_details['icon']} {item_details['name']} আনইকুইপ করা হয়েছে।"
        
        return {
            "success": True,
            "message": message,
            "slot": slot,
            "item": item_details
        }
    
    async def get_shop_stats(self) -> Dict:
        """Get shop statistics"""
        items = self.db.get_shop_items()
        
        total_items = len(items)
        total_value = sum(item.get("price", 0) for item in items)
        
        # Count by category
        categories = {}
        for item in items:
            category = item.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        
        # Daily deals info
        daily_deals_count = len(self.daily_deals.get("deals", {}))
        
        # Most expensive item
        most_expensive = max(items, key=lambda x: x.get("price", 0), default=None)
        
        # Cheapest item
        cheapest = min(items, key=lambda x: x.get("price", 0), default=None)
        
        # Most popular (by simulated popularity)
        most_popular = max(items, key=lambda x: x.get("popularity", 0), default=None)
        
        return {
            "total_items": total_items,
            "total_value": total_value,
            "categories": categories,
            "daily_deals": daily_deals_count,
            "most_expensive": {
                "name": most_expensive["name"] if most_expensive else "N/A",
                "price": most_expensive.get("price", 0) if most_expensive else 0,
                "icon": most_expensive.get("icon", "📦") if most_expensive else "📦"
            },
            "cheapest": {
                "name": cheapest["name"] if cheapest else "N/A",
                "price": cheapest.get("price", 0) if cheapest else 0,
                "icon": cheapest.get("icon", "📦") if cheapest else "📦"
            },
            "most_popular": {
                "name": most_popular["name"] if most_popular else "N/A",
                "popularity": most_popular.get("popularity", 0) if most_popular else 0,
                "icon": most_popular.get("icon", "📦") if most_popular else "📦"
            }
        }
    
    async def add_to_cart(self, user_id: int, item_id: str, quantity: int = 1) -> Dict:
        """Add item to shopping cart"""
        item = self.db.get_item(item_id)
        if not item:
            return {
                "success": False,
                "message": "এই আইটেমটি শপে নেই!"
            }
        
        if user_id not in self.cart_system:
            self.cart_system[user_id] = {}
        
        cart = self.cart_system[user_id]
        
        if item_id in cart:
            cart[item_id]["quantity"] += quantity
        else:
            cart[item_id] = {
                "item_id": item_id,
                "name": item["name"],
                "price": item["price"],
                "quantity": quantity,
                "icon": item.get("icon", "📦")
            }
        
        total_price = cart[item_id]["price"] * cart[item_id]["quantity"]
        
        return {
            "success": True,
            "message": f"✅ {item['icon']} {item['name']} x{quantity} কার্টে যোগ করা হয়েছে!",
            "cart_total": self._calculate_cart_total(user_id),
            "item_total": total_price,
            "cart_items": len(cart)
        }
    
    def _calculate_cart_total(self, user_id: int) -> int:
        """Calculate total price of items in cart"""
        if user_id not in self.cart_system:
            return 0
        
        total = 0
        for item in self.cart_system[user_id].values():
            total += item["price"] * item["quantity"]
        
        return total
    
    async def checkout_cart(self, user_id: int) -> Dict:
        """Checkout all items in cart"""
        if user_id not in self.cart_system or not self.cart_system[user_id]:
            return {
                "success": False,
                "message": "কার্ট খালি!"
            }
        
        cart = self.cart_system[user_id]
        total_price = self._calculate_cart_total(user_id)
        
        # Get user
        user = self.db.get_user(user_id)
        if not user:
            return {
                "success": False,
                "message": "ইউজার খুঁজে পাওয়া যায়নি!"
            }
        
        # Check if user has enough coins
        if user["coins"] < total_price:
            return {
                "success": False,
                "message": f"পর্যাপ্ত কয়েন নেই! দরকার: {Utils.format_coins(total_price)}, আপনার আছে: {Utils.format_coins(user['coins'])}"
            }
        
        # Process each item
        successful_items = []
        failed_items = []
        
        for item_id, cart_item in cart.items():
            result = await self.buy_item(user_id, item_id, cart_item["quantity"])
            
            if result["success"]:
                successful_items.append(cart_item)
            else:
                failed_items.append({
                    "item": cart_item,
                    "error": result["message"]
                })
        
        # Clear cart
        self.cart_system[user_id] = {}
        
        # Prepare response
        if successful_items:
            message = f"""
🛒 **চেকআউট সম্পন্ন!**

✅ **সফল ক্রয় ({len(successful_items)}টি):**
"""
            for item in successful_items:
                message += f"• {item['icon']} {item['name']} x{item['quantity']}\n"
            
            if failed_items:
                message += f"\n❌ **ব্যর্থ ({len(failed_items)}টি):**"
                for fail in failed_items:
                    message += f"\n• {fail['item']['name']}: {fail['error']}"
            
            message += f"\n\n💰 **মোট খরচ:** {Utils.format_coins(total_price)}"
            message += f"\n💰 **বাকি কয়েন:** {Utils.format_coins(user['coins'])}"
        else:
            message = "❌ কোনো আইটেম ক্রয় করা যায়নি!"
        
        return {
            "success": len(successful_items) > 0,
            "message": message,
            "successful_items": successful_items,
            "failed_items": failed_items,
            "total_price": total_price,
            "remaining_coins": user["coins"]
        }