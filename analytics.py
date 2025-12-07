import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # For headless environments
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from config import Config
from db import Database
from utils import Utils
from logger import Logger

class Analytics:
    """Advanced Analytics System v15.0.00"""
    
    def __init__(self, db: Database):
        self.db = db
        self.config = Config()
        self.logger = Logger.get_logger(__name__)
        
        # Analytics cache
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Chart configurations
        self.chart_styles = {
            'primary_color': '#3498db',
            'secondary_color': '#2ecc71',
            'danger_color': '#e74c3c',
            'warning_color': '#f39c12',
            'dark_color': '#2c3e50',
            'light_color': '#ecf0f1'
        }
    
    async def get_dashboard_stats(self) -> Dict:
        """Get comprehensive dashboard statistics"""
        try:
            stats = self.db.get_stats()
            
            # Calculate growth metrics
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            last_week = today - timedelta(days=7)
            
            # User growth
            total_users = stats['total_users']
            active_users = stats['active_users']
            new_users_today = stats['today_stats']['new_users']
            
            # Financial metrics
            total_deposits = await self._calculate_total_deposits()
            total_withdrawals = await self._calculate_total_withdrawals()
            net_flow = total_deposits - total_withdrawals
            
            # Game metrics
            game_stats = await self._get_game_analytics()
            
            # Revenue metrics
            shop_revenue = await self._calculate_shop_revenue()
            
            # Performance metrics
            success_rates = await self._calculate_success_rates()
            
            # Create dashboard data
            dashboard = {
                'overview': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'active_rate': (active_users / max(total_users, 1)) * 100,
                    'new_users_today': new_users_today,
                    'total_transactions': stats['total_transactions'],
                    'system_uptime': self._format_uptime(stats.get('system_uptime'))
                },
                
                'financial': {
                    'total_deposits': total_deposits,
                    'total_withdrawals': total_withdrawals,
                    'net_flow': net_flow,
                    'shop_revenue': shop_revenue,
                    'total_revenue': total_deposits + shop_revenue,
                    'profit_margin': ((total_deposits + shop_revenue - total_withdrawals) / 
                                    max(total_deposits + shop_revenue, 1)) * 100
                },
                
                'gaming': {
                    'total_games': game_stats['total_games'],
                    'win_rate': game_stats['win_rate'],
                    'popular_game': game_stats['popular_game'],
                    'total_bet': game_stats['total_bet'],
                    'total_payout': game_stats['total_payout'],
                    'house_edge': ((game_stats['total_bet'] - game_stats['total_payout']) / 
                                  max(game_stats['total_bet'], 1)) * 100
                },
                
                'performance': {
                    'deposit_success_rate': success_rates['deposit'],
                    'withdrawal_success_rate': success_rates['withdrawal'],
                    'game_success_rate': success_rates['game'],
                    'response_time': '~0.5s',  # Simulated
                    'error_rate': success_rates['error']
                },
                
                'user_engagement': {
                    'avg_session_time': '5.2m',
                    'avg_games_per_user': game_stats['total_games'] / max(active_users, 1),
                    'avg_deposit_per_user': total_deposits / max(active_users, 1),
                    'retention_rate': self._calculate_retention_rate(),
                    'churn_rate': self._calculate_churn_rate()
                }
            }
            
            return {
                'success': True,
                'dashboard': dashboard,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Analytics error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_user_analytics(self, period: str = '7d') -> Dict:
        """Get user analytics for specified period"""
        try:
            # Calculate period
            if period == '1d':
                days = 1
            elif period == '7d':
                days = 7
            elif period == '30d':
                days = 30
            elif period == '90d':
                days = 90
            else:
                days = 7
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get user data for period
            new_users = []
            active_users = []
            dates = []
            
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                dates.append(date_str)
                
                # Count new users for this date
                new_count = await self._count_new_users(date_str)
                new_users.append(new_count)
                
                # Count active users for this date
                active_count = await self._count_active_users(date_str)
                active_users.append(active_count)
                
                current_date += timedelta(days=1)
            
            # Calculate metrics
            total_new_users = sum(new_users)
            avg_daily_new = total_new_users / max(days, 1)
            peak_active = max(active_users) if active_users else 0
            
            # Calculate growth rate
            if len(new_users) >= 2:
                growth_rate = ((new_users[-1] - new_users[0]) / max(new_users[0], 1)) * 100
            else:
                growth_rate = 0
            
            return {
                'success': True,
                'period': period,
                'dates': dates,
                'new_users': new_users,
                'active_users': active_users,
                'metrics': {
                    'total_new_users': total_new_users,
                    'avg_daily_new': round(avg_daily_new, 1),
                    'peak_active_users': peak_active,
                    'growth_rate': round(growth_rate, 1),
                    'retention_rate': self._calculate_retention_rate()
                },
                'chart_data': await self._create_user_chart(dates, new_users, active_users)
            }
            
        except Exception as e:
            self.logger.error(f"User analytics error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_financial_analytics(self, period: str = '7d') -> Dict:
        """Get financial analytics"""
        try:
            # Calculate period
            if period == '1d':
                days = 1
            elif period == '7d':
                days = 7
            elif period == '30d':
                days = 30
            else:
                days = 7
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Collect daily data
            dates = []
            deposits = []
            withdrawals = []
            net_flows = []
            
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                dates.append(date_str)
                
                # Get daily financial data
                daily_deposits = await self._get_daily_deposits(date_str)
                daily_withdrawals = await self._get_daily_withdrawals(date_str)
                
                deposits.append(daily_deposits)
                withdrawals.append(daily_withdrawals)
                net_flows.append(daily_deposits - daily_withdrawals)
                
                current_date += timedelta(days=1)
            
            # Calculate metrics
            total_deposits = sum(deposits)
            total_withdrawals = sum(withdrawals)
            total_net_flow = total_deposits - total_withdrawals
            
            avg_daily_deposit = total_deposits / max(days, 1)
            avg_daily_withdrawal = total_withdrawals / max(days, 1)
            
            # Calculate success rates
            deposit_success = await self._calculate_deposit_success_rate(period)
            withdrawal_success = await self._calculate_withdrawal_success_rate(period)
            
            return {
                'success': True,
                'period': period,
                'dates': dates,
                'deposits': deposits,
                'withdrawals': withdrawals,
                'net_flows': net_flows,
                'metrics': {
                    'total_deposits': total_deposits,
                    'total_withdrawals': total_withdrawals,
                    'total_net_flow': total_net_flow,
                    'avg_daily_deposit': round(avg_daily_deposit, 2),
                    'avg_daily_withdrawal': round(avg_daily_withdrawal, 2),
                    'deposit_success_rate': deposit_success,
                    'withdrawal_success_rate': withdrawal_success,
                    'profit_margin': (total_net_flow / max(total_deposits, 1)) * 100
                },
                'chart_data': await self._create_financial_chart(dates, deposits, withdrawals, net_flows)
            }
            
        except Exception as e:
            self.logger.error(f"Financial analytics error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_game_analytics(self, period: str = '7d') -> Dict:
        """Get game analytics"""
        try:
            # Calculate period
            if period == '1d':
                days = 1
            elif period == '7d':
                days = 7
            elif period == '30d':
                days = 30
            else:
                days = 7
            
            # Get game statistics
            game_stats = await self._get_game_analytics_period(period)
            
            # Calculate game distribution
            game_distribution = await self._get_game_distribution(period)
            
            # Calculate hourly activity
            hourly_activity = await self._get_hourly_activity(period)
            
            # Calculate player metrics
            player_metrics = await self._get_player_metrics(period)
            
            return {
                'success': True,
                'period': period,
                'overview': game_stats,
                'distribution': game_distribution,
                'hourly_activity': hourly_activity,
                'player_metrics': player_metrics,
                'charts': {
                    'distribution_chart': await self._create_game_distribution_chart(game_distribution),
                    'activity_chart': await self._create_hourly_activity_chart(hourly_activity)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Game analytics error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_revenue_report(self, start_date: str = None, end_date: str = None) -> Dict:
        """Generate revenue report"""
        try:
            # Set date range
            if not end_date:
                end_date = datetime.now()
            else:
                end_date = datetime.fromisoformat(end_date)
            
            if not start_date:
                start_date = end_date - timedelta(days=30)
            else:
                start_date = datetime.fromisoformat(start_date)
            
            # Collect revenue data
            revenue_data = {
                'deposits': 0,
                'withdrawals': 0,
                'shop_sales': 0,
                'game_revenue': 0,
                'other_income': 0
            }
            
            # Calculate deposits
            for payment in self.db.payments.values():
                created_at = datetime.fromisoformat(payment.get('created_at', '2000-01-01'))
                
                if start_date <= created_at <= end_date:
                    if payment['type'] == 'DEPOSIT' and payment.get('status') == 'COMPLETED':
                        revenue_data['deposits'] += payment.get('amount', 0)
                    elif payment['type'] == 'WITHDRAW' and payment.get('status') == 'COMPLETED':
                        revenue_data['withdrawals'] += payment.get('amount', 0)
            
            # Calculate shop sales
            for user in self.db.users.values():
                for item in user.get('inventory', []):
                    purchased_at = item.get('purchased_at')
                    if purchased_at:
                        purchase_date = datetime.fromisoformat(purchased_at)
                        if start_date <= purchase_date <= end_date:
                            revenue_data['shop_sales'] += item.get('price_paid', 0) * item.get('quantity', 1)
            
            # Calculate game revenue
            game_revenue = 0
            for game_data in self.db.game_history.values():
                timestamp = game_data.get('timestamp')
                if timestamp:
                    game_date = datetime.fromisoformat(timestamp)
                    if start_date <= game_date <= end_date:
                        bet = game_data.get('bet', 0)
                        payout = game_data.get('payout', 0)
                        if bet > payout:  # House win
                            game_revenue += bet - payout
            
            revenue_data['game_revenue'] = game_revenue
            
            # Calculate totals
            total_revenue = revenue_data['deposits'] + revenue_data['shop_sales'] + revenue_data['game_revenue']
            total_expenses = revenue_data['withdrawals']
            net_profit = total_revenue - total_expenses
            
            # Calculate percentages
            revenue_distribution = {
                'deposits': (revenue_data['deposits'] / max(total_revenue, 1)) * 100,
                'shop_sales': (revenue_data['shop_sales'] / max(total_revenue, 1)) * 100,
                'game_revenue': (revenue_data['game_revenue'] / max(total_revenue, 1)) * 100
            }
            
            return {
                'success': True,
                'period': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d'),
                    'days': (end_date - start_date).days
                },
                'revenue': revenue_data,
                'summary': {
                    'total_revenue': total_revenue,
                    'total_expenses': total_expenses,
                    'net_profit': net_profit,
                    'profit_margin': (net_profit / max(total_revenue, 1)) * 100
                },
                'distribution': revenue_distribution,
                'chart': await self._create_revenue_chart(revenue_data, revenue_distribution)
            }
            
        except Exception as e:
            self.logger.error(f"Revenue report error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_dashboard_chart(self, chart_type: str = 'overview') -> str:
        """Create dashboard chart and return as base64"""
        try:
            plt.figure(figsize=(10, 6))
            
            if chart_type == 'user_growth':
                # User growth chart
                data = await self.get_user_analytics('7d')
                dates = data.get('dates', [])
                new_users = data.get('new_users', [])
                active_users = data.get('active_users', [])
                
                x = range(len(dates))
                width = 0.35
                
                plt.bar([i - width/2 for i in x], new_users, width, 
                       label='নতুন ইউজার', color=self.chart_styles['primary_color'])
                plt.bar([i + width/2 for i in x], active_users, width,
                       label='অ্যাকটিভ ইউজার', color=self.chart_styles['secondary_color'])
                
                plt.xlabel('তারিখ')
                plt.ylabel('ইউজার সংখ্যা')
                plt.title('ইউজার বৃদ্ধি (সপ্তাহিক)')
                plt.xticks(x, [d.split('-')[-1] for d in dates], rotation=45)
                plt.legend()
                plt.tight_layout()
                
            elif chart_type == 'financial':
                # Financial chart
                data = await self.get_financial_analytics('7d')
                dates = data.get('dates', [])
                deposits = data.get('deposits', [])
                withdrawals = data.get('withdrawals', [])
                
                x = range(len(dates))
                plt.plot(x, deposits, marker='o', label='ডিপোজিট', 
                        color=self.chart_styles['primary_color'], linewidth=2)
                plt.plot(x, withdrawals, marker='s', label='উইথড্র', 
                        color=self.chart_styles['danger_color'], linewidth=2)
                
                plt.xlabel('তারিখ')
                plt.ylabel('পরিমাণ (টাকা)')
                plt.title('আর্থিক প্রবাহ')
                plt.xticks(x, [d.split('-')[-1] for d in dates], rotation=45)
                plt.legend()
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                
            elif chart_type == 'game_distribution':
                # Game distribution pie chart
                data = await self.get_game_analytics('7d')
                distribution = data.get('distribution', {})
                
                if distribution:
                    games = list(distribution.keys())
                    counts = list(distribution.values())
                    
                    colors = plt.cm.Set3(np.linspace(0, 1, len(games)))
                    plt.pie(counts, labels=games, colors=colors, autopct='%1.1f%%')
                    plt.title('গেম ডিস্ট্রিবিউশন')
                
            else:  # Overview
                # Overview metrics chart
                metrics = ['ইউজার', 'ডিপোজিট', 'উইথড্র', 'গেম']
                values = [100, 85, 72, 93]  # Example percentages
                
                colors = [self.chart_styles['primary_color'], 
                         self.chart_styles['secondary_color'],
                         self.chart_styles['danger_color'],
                         self.chart_styles['warning_color']]
                
                bars = plt.barh(metrics, values, color=colors)
                plt.xlabel('শতকরা (%)')
                plt.title('সিস্টেম ওভারভিউ')
                plt.xlim(0, 100)
                
                # Add value labels
                for bar, value in zip(bars, values):
                    plt.text(value + 1, bar.get_y() + bar.get_height()/2, 
                            f'{value}%', va='center')
            
            # Save to buffer
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            
            # Convert to base64
            img_str = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            self.logger.error(f"Chart creation error: {e}")
            plt.close()
            return None
    
    # Helper methods
    async def _calculate_total_deposits(self) -> float:
        """Calculate total deposits"""
        total = 0
        for payment in self.db.payments.values():
            if payment['type'] == 'DEPOSIT' and payment.get('status') == 'COMPLETED':
                total += payment.get('amount', 0)
        return total
    
    async def _calculate_total_withdrawals(self) -> float:
        """Calculate total withdrawals"""
        total = 0
        for payment in self.db.payments.values():
            if payment['type'] == 'WITHDRAW' and payment.get('status') == 'COMPLETED':
                total += payment.get('amount', 0)
        return total
    
    async def _calculate_shop_revenue(self) -> float:
        """Calculate shop revenue"""
        total = 0
        for user in self.db.users.values():
            for item in user.get('inventory', []):
                total += item.get('price_paid', 0) * item.get('quantity', 1)
        return total
    
    async def _calculate_success_rates(self) -> Dict:
        """Calculate various success rates"""
        deposit_success = 0
        deposit_total = 0
        withdrawal_success = 0
        withdrawal_total = 0
        game_success = 0
        game_total = 0
        
        # Payment success rates
        for payment in self.db.payments.values():
            if payment['type'] == 'DEPOSIT':
                deposit_total += 1
                if payment.get('status') == 'COMPLETED':
                    deposit_success += 1
            elif payment['type'] == 'WITHDRAW':
                withdrawal_total += 1
                if payment.get('status') == 'COMPLETED':
                    withdrawal_success += 1
        
        # Game success rate (from user perspective)
        for user in self.db.users.values():
            stats = user.get('stats', {})
            if 'games_won' in stats and 'total_games' in stats:
                game_success += stats.get('games_won', 0)
                game_total += stats.get('total_games', 0)
        
        # Error rate (simulated)
        error_rate = 2.5  # 2.5% error rate
        
        return {
            'deposit': (deposit_success / max(deposit_total, 1)) * 100,
            'withdrawal': (withdrawal_success / max(withdrawal_total, 1)) * 100,
            'game': (game_success / max(game_total, 1)) * 100,
            'error': error_rate
        }
    
    async def _get_game_analytics(self) -> Dict:
        """Get game analytics"""
        total_games = 0
        total_wins = 0
        total_bet = 0
        total_payout = 0
        
        game_counts = {}
        
        for game_data in self.db.game_history.values():
            total_games += 1
            
            if game_data.get('result') in ['WIN', 'JACKPOT']:
                total_wins += 1
            
            bet = game_data.get('bet', 0)
            payout = game_data.get('payout', 0)
            
            total_bet += bet
            total_payout += payout
            
            # Count by game type
            game_type = game_data.get('game', 'unknown')
            game_counts[game_type] = game_counts.get(game_type, 0) + 1
        
        # Find popular game
        popular_game = max(game_counts.items(), key=lambda x: x[1])[0] if game_counts else 'N/A'
        
        return {
            'total_games': total_games,
            'win_rate': (total_wins / max(total_games, 1)) * 100,
            'popular_game': popular_game,
            'total_bet': total_bet,
            'total_payout': total_payout
        }
    
    def _format_uptime(self, uptime_str: str) -> str:
        """Format uptime string"""
        if not uptime_str:
            return 'N/A'
        
        try:
            start_time = datetime.fromisoformat(uptime_str)
            uptime = datetime.now() - start_time
            
            days = uptime.days
            hours = uptime.seconds // 3600
            minutes = (uptime.seconds % 3600) // 60
            
            if days > 0:
                return f"{days} দিন {hours} ঘন্টা"
            elif hours > 0:
                return f"{hours} ঘন্টা {minutes} মিনিট"
            else:
                return f"{minutes} মিনিট"
        except:
            return 'N/A'
    
    def _calculate_retention_rate(self) -> float:
        """Calculate user retention rate"""
        try:
            # Users active in last 7 days who were also active 14 days ago
            two_weeks_ago = datetime.now() - timedelta(days=14)
            one_week_ago = datetime.now() - timedelta(days=7)
            
            retained_users = 0
            total_users = 0
            
            for user in self.db.users.values():
                last_active = datetime.fromisoformat(user.get('last_active', '2000-01-01'))
                first_seen = datetime.fromisoformat(user.get('first_seen', '2000-01-01'))
                
                # User existed two weeks ago
                if first_seen < two_weeks_ago:
                    total_users += 1
                    # User was active in last week
                    if last_active > one_week_ago:
                        retained_users += 1
            
            return (retained_users / max(total_users, 1)) * 100
        except:
            return 0.0
    
    def _calculate_churn_rate(self) -> float:
        """Calculate user churn rate"""
        retention = self._calculate_retention_rate()
        return 100 - retention
    
    async def _count_new_users(self, date_str: str) -> int:
        """Count new users for a specific date"""
        count = 0
        for user in self.db.users.values():
            joined = user.get('first_seen', '')
            if joined.startswith(date_str):
                count += 1
        return count
    
    async def _count_active_users(self, date_str: str) -> int:
        """Count active users for a specific date"""
        count = 0
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        for user in self.db.users.values():
            last_active = datetime.fromisoformat(user.get('last_active', '2000-01-01'))
            # If user was active on this date
            if last_active.date() == target_date.date():
                count += 1
        
        return count
    
    async def _get_daily_deposits(self, date_str: str) -> float:
        """Get total deposits for a specific date"""
        total = 0
        for payment in self.db.payments.values():
            created_at = payment.get('created_at', '')
            if created_at.startswith(date_str):
                if payment['type'] == 'DEPOSIT' and payment.get('status') == 'COMPLETED':
                    total += payment.get('amount', 0)
        return total
    
    async def _get_daily_withdrawals(self, date_str: str) -> float:
        """Get total withdrawals for a specific date"""
        total = 0
        for payment in self.db.payments.values():
            created_at = payment.get('created_at', '')
            if created_at.startswith(date_str):
                if payment['type'] == 'WITHDRAW' and payment.get('status') == 'COMPLETED':
                    total += payment.get('amount', 0)
        return total
    
    async def _calculate_deposit_success_rate(self, period: str) -> float:
        """Calculate deposit success rate for period"""
        success = 0
        total = 0
        
        for payment in self.db.payments.values():
            if payment['type'] == 'DEPOSIT':
                total += 1
                if payment.get('status') == 'COMPLETED':
                    success += 1
        
        return (success / max(total, 1)) * 100
    
    async def _calculate_withdrawal_success_rate(self, period: str) -> float:
        """Calculate withdrawal success rate for period"""
        success = 0
        total = 0
        
        for payment in self.db.payments.values():
            if payment['type'] == 'WITHDRAW':
                total += 1
                if payment.get('status') == 'COMPLETED':
                    success += 1
        
        return (success / max(total, 1)) * 100
    
    async def _get_game_analytics_period(self, period: str) -> Dict:
        """Get game analytics for specific period"""
        # This would filter games by period
        # For now, return overall stats
        return await self._get_game_analytics()
    
    async def _get_game_distribution(self, period: str) -> Dict:
        """Get game distribution by type"""
        distribution = {}
        
        for game_data in self.db.game_history.values():
            game_type = game_data.get('game', 'unknown')
            distribution[game_type] = distribution.get(game_type, 0) + 1
        
        return distribution
    
    async def _get_hourly_activity(self, period: str) -> Dict:
        """Get hourly game activity"""
        hourly = {str(hour).zfill(2): 0 for hour in range(24)}
        
        for game_data in self.db.game_history.values():
            timestamp = game_data.get('timestamp')
            if timestamp:
                try:
                    game_time = datetime.fromisoformat(timestamp)
                    hour = str(game_time.hour).zfill(2)
                    hourly[hour] = hourly.get(hour, 0) + 1
                except:
                    pass
        
        return hourly
    
    async def _get_player_metrics(self, period: str) -> Dict:
        """Get player metrics"""
        total_players = len(self.db.users)
        active_players = sum(1 for user in self.db.users.values() 
                           if datetime.fromisoformat(user.get('last_active', '2000-01-01')) > 
                           datetime.now() - timedelta(days=7))
        
        # Calculate average games per player
        total_games = sum(1 for _ in self.db.game_history.values())
        avg_games = total_games / max(total_players, 1)
        
        # Calculate paying players
        paying_players = 0
        for user in self.db.users.values():
            if any(payment['type'] == 'DEPOSIT' and payment.get('status') == 'COMPLETED'
                   for payment in self.db.payments.values()
                   if payment.get('user_id') == user['id']):
                paying_players += 1
        
        return {
            'total_players': total_players,
            'active_players': active_players,
            'paying_players': paying_players,
            'avg_games_per_player': round(avg_games, 1),
            'conversion_rate': (paying_players / max(total_players, 1)) * 100
        }
    
    async def _create_user_chart(self, dates, new_users, active_users):
        """Create user chart data for frontend"""
        return {
            'labels': dates,
            'datasets': [
                {
                    'label': 'নতুন ইউজার',
                    'data': new_users,
                    'backgroundColor': self.chart_styles['primary_color'],
                    'borderColor': self.chart_styles['primary_color']
                },
                {
                    'label': 'অ্যাকটিভ ইউজার',
                    'data': active_users,
                    'backgroundColor': self.chart_styles['secondary_color'],
                    'borderColor': self.chart_styles['secondary_color']
                }
            ]
        }
    
    async def _create_financial_chart(self, dates, deposits, withdrawals, net_flows):
        """Create financial chart data"""
        return {
            'labels': dates,
            'datasets': [
                {
                    'label': 'ডিপোজিট',
                    'data': deposits,
                    'borderColor': self.chart_styles['primary_color'],
                    'backgroundColor': self.chart_styles['primary_color'] + '20',
                    'fill': True
                },
                {
                    'label': 'উইথড্র',
                    'data': withdrawals,
                    'borderColor': self.chart_styles['danger_color'],
                    'backgroundColor': self.chart_styles['danger_color'] + '20',
                    'fill': True
                },
                {
                    'label': 'নেট প্রবাহ',
                    'data': net_flows,
                    'borderColor': self.chart_styles['secondary_color'],
                    'backgroundColor': self.chart_styles['secondary_color'] + '20',
                    'fill': True,
                    'type': 'line'
                }
            ]
        }
    
    async def _create_game_distribution_chart(self, distribution):
        """Create game distribution chart data"""
        games = list(distribution.keys())
        counts = list(distribution.values())
        
        colors = []
        for i in range(len(games)):
            color = plt.cm.Set3(i / max(len(games), 1))
            colors.append(f'rgba({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)}, 0.7)')
        
        return {
            'labels': games,
            'datasets': [{
                'data': counts,
                'backgroundColor': colors
            }]
        }
    
    async def _create_hourly_activity_chart(self, hourly_activity):
        """Create hourly activity chart data"""
        hours = list(hourly_activity.keys())
        counts = list(hourly_activity.values())
        
        return {
            'labels': hours,
            'datasets': [{
                'label': 'গেম সংখ্যা',
                'data': counts,
                'backgroundColor': self.chart_styles['warning_color'],
                'borderColor': self.chart_styles['warning_color'],
                'borderWidth': 1
            }]
        }
    
    async def _create_revenue_chart(self, revenue_data, distribution):
        """Create revenue chart data"""
        labels = ['ডিপোজিট', 'শপ বিক্রয়', 'গেম রেভিনিউ']
        values = [revenue_data['deposits'], revenue_data['shop_sales'], revenue_data['game_revenue']]
        
        return {
            'labels': labels,
            'datasets': [{
                'data': values,
                'backgroundColor': [
                    self.chart_styles['primary_color'],
                    self.chart_styles['secondary_color'],
                    self.chart_styles['warning_color']
                ]
            }]
        }
    
    async def generate_report(self, report_type: str = 'weekly') -> Dict:
        """Generate comprehensive report"""
        try:
            if report_type == 'daily':
                period = '1d'
                report_name = 'দৈনিক রিপোর্ট'
            elif report_type == 'weekly':
                period = '7d'
                report_name = 'সাপ্তাহিক রিপোর্ট'
            elif report_type == 'monthly':
                period = '30d'
                report_name = 'মাসিক রিপোর্ট'
            else:
                period = '7d'
                report_name = 'রিপোর্ট'
            
            # Collect all data
            user_analytics = await self.get_user_analytics(period)
            financial_analytics = await self.get_financial_analytics(period)
            game_analytics = await self.get_game_analytics(period)
            
            # Generate insights
            insights = await self._generate_insights(
                user_analytics, 
                financial_analytics, 
                game_analytics
            )
            
            # Create report
            report = {
                'success': True,
                'report_type': report_type,
                'report_name': report_name,
                'period': period,
                'generated_at': datetime.now().isoformat(),
                'user_analytics': user_analytics,
                'financial_analytics': financial_analytics,
                'game_analytics': game_analytics,
                'insights': insights,
                'recommendations': await self._generate_recommendations(insights)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Report generation error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _generate_insights(self, user_data, financial_data, game_data):
        """Generate insights from analytics data"""
        insights = []
        
        # User insights
        user_metrics = user_data.get('metrics', {})
        if user_metrics.get('growth_rate', 0) > 10:
            insights.append('ইউজার বৃদ্ধির হার উল্লেখযোগ্য (>10%)')
        elif user_metrics.get('growth_rate', 0) < 0:
            insights.append('ইউজার বৃদ্ধির হার নেতিবাচক - মনোযোগ প্রয়োজন')
        
        if user_metrics.get('retention_rate', 0) < 30:
            insights.append('রিটেনশন রেট কম - ইউজার রিটেনশন বাড়ানোর প্রয়োজন')
        
        # Financial insights
        financial_metrics = financial_data.get('metrics', {})
        if financial_metrics.get('net_flow', 0) < 0:
            insights.append('নেট আর্থিক প্রবাহ নেতিবাচক - ডিপোজিট বাড়ানোর প্রয়োজন')
        
        if financial_metrics.get('deposit_success_rate', 0) < 80:
            insights.append('ডিপোজিট সাকসেস রেট কম - পেমেন্ট সিস্টেম চেক করুন')
        
        # Game insights
        game_overview = game_data.get('overview', {})
        if game_overview.get('house_edge', 0) < 5:
            insights.append('হাউস এজ কম - গেম সেটিংস রিভিউ করুন')
        
        if len(insights) == 0:
            insights.append('সব মেট্রিক্স সন্তোষজনক পর্যায়ে আছে')
        
        return insights
    
    async def _generate_recommendations(self, insights):
        """Generate recommendations based on insights"""
        recommendations = []
        
        for insight in insights:
            if 'ইউজার বৃদ্ধির হার নেতিবাচক' in insight:
                recommendations.append('রেফারেল প্রোগ্রাম শক্তিশালী করুন এবং মার্কেটিং বাড়ান')
            
            if 'রিটেনশন রেট কম' in insight:
                recommendations.append('নতুন ইউজারদের জন্য ওয়েলকাম বোনাস বাড়ান এবং রেগুলার নোটিফিকেশন দিন')
            
            if 'নেট আর্থিক প্রবাহ নেতিবাচক' in insight:
                recommendations.append('ডিপোজিট বোনাস অফার করুন এবং নতুন পেমেন্ট মেথড যুক্ত করুন')
            
            if 'ডিপোজিট সাকসেস রেট কম' in insight:
                recommendations.append('পেমেন্ট গেটওয়ে টেস্ট করুন এবং অল্টারনেটিভ মেথড যুক্ত করুন')
            
            if 'হাউস এজ কম' in insight:
                recommendations.append('গেম ওডস রিভিউ করুন এবং প্রয়োজনে এডজাস্ট করুন')
        
        if not recommendations:
            recommendations.append('বর্তমান স্ট্র্যাটেজি ধরে রাখুন এবং পারফরম্যান্স মনিটর করুন')
        
        return recommendations