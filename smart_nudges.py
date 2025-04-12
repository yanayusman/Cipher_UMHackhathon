import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

class SmartNudges:
    def __init__(self, transaction_data: pd.DataFrame, merchant_id: str, items_data: pd.DataFrame, transaction_items: pd.DataFrame):
        self.transaction_data = transaction_data
        self.merchant_id = merchant_id
        self.items_data = items_data
        self.transaction_items = transaction_items
        self.merchant_data = self._filter_merchant_data()
        
    def _filter_merchant_data(self) -> pd.DataFrame:
        """Filter transaction data for the specific merchant"""
        return self.transaction_data[self.transaction_data['merchant_id'] == self.merchant_id]
    
    def _analyze_weekly_patterns(self) -> Dict[str, Any]:
        """Analyze sales patterns by day of week"""
        # Group by day of week and calculate metrics
        daily_patterns = self.merchant_data.groupby(
            self.merchant_data['order_time'].dt.day_name()
        ).agg({
            'order_value': ['sum', 'count', 'mean'],
            'order_id': 'nunique'
        })
        
        # Calculate growth compared to average
        avg_sales = daily_patterns[('order_value', 'sum')].mean()
        daily_patterns['growth_vs_avg'] = (
            (daily_patterns[('order_value', 'sum')] - avg_sales) / avg_sales * 100
        )
        
        return daily_patterns
    
    def _analyze_hourly_patterns(self) -> Dict[str, Any]:
        """Analyze sales patterns by hour of day"""
        hourly_patterns = self.merchant_data.groupby(
            self.merchant_data['order_time'].dt.hour
        ).agg({
            'order_value': ['sum', 'count', 'mean'],
            'order_id': 'nunique'
        })
        
        return hourly_patterns
    
    def _analyze_item_performance(self) -> Dict[str, Any]:
        """Analyze item performance patterns"""
        # First merge merchant transactions with transaction_items
        merchant_transactions = self.merchant_data.merge(
            self.transaction_items,
            on='order_id',
            how='left'
        )
        
        # Then merge with items data to get item names
        merged_data = merchant_transactions.merge(
            self.items_data[['item_id', 'item_name']],
            on='item_id',
            how='left'
        )
        
        # Group by item name and calculate metrics
        item_performance = merged_data.groupby('item_name').agg({
            'order_value': ['sum', 'count', 'mean'],
            'order_id': 'nunique'
        })
        
        # Calculate growth compared to average
        avg_item_sales = item_performance[('order_value', 'sum')].mean()
        item_performance['growth_vs_avg'] = (
            (item_performance[('order_value', 'sum')] - avg_item_sales) / avg_item_sales * 100
        )
        
        return item_performance
    
    def generate_nudges(self) -> List[Dict[str, Any]]:
        """Generate personalized nudges based on merchant data"""
        nudges = []
        
        # Analyze patterns
        daily_patterns = self._analyze_weekly_patterns()
        hourly_patterns = self._analyze_hourly_patterns()
        item_performance = self._analyze_item_performance()
        
        # Generate daily pattern nudges
        for day, data in daily_patterns.iterrows():
            growth = data['growth_vs_avg']
            if isinstance(growth, (int, float)) and abs(growth) > 20:  # Significant deviation from average
                nudge = {
                    'type': 'daily_pattern',
                    'day': day,
                    'growth': growth,
                    'message': (
                        f"Your sales are {abs(growth):.0f}% {'higher' if growth > 0 else 'lower'} "
                        f"than average on {day}s. Consider {'scheduling promotions' if growth > 0 else 'offering special discounts'} "
                        f"on {day}s to {'maximize revenue' if growth > 0 else 'boost sales'}."
                    )
                }
                nudges.append(nudge)
        
        # Generate hourly pattern nudges
        peak_hour = hourly_patterns[('order_value', 'sum')].idxmax()
        if isinstance(peak_hour, (int, float)) and peak_hour >= 11 and peak_hour <= 14:  # Lunch hours
            nudge = {
                'type': 'hourly_pattern',
                'hour': peak_hour,
                'message': (
                    f"Your busiest time is during lunch hours ({peak_hour}:00). "
                    "Consider offering lunch specials or quick meal deals to attract more customers."
                )
            }
            nudges.append(nudge)
        elif isinstance(peak_hour, (int, float)) and peak_hour >= 17 and peak_hour <= 20:  # Dinner hours
            nudge = {
                'type': 'hourly_pattern',
                'hour': peak_hour,
                'message': (
                    f"Your peak sales occur during dinner hours ({peak_hour}:00). "
                    "Consider introducing family meal deals or dinner specials to increase order value."
                )
            }
            nudges.append(nudge)
        
        # Generate item performance nudges
        for item, data in item_performance.iterrows():
            growth = data['growth_vs_avg']
            if isinstance(growth, (int, float)) and abs(growth) > 30:  # Significant deviation from average
                nudge = {
                    'type': 'item_performance',
                    'item': item,
                    'growth': growth,
                    'message': (
                        f"Your {item} sales are {abs(growth):.0f}% {'above' if growth > 0 else 'below'} average. "
                        f"Consider {'creating a special combo meal' if growth > 0 else 'bundling with popular items'} "
                        f"to {'maximize revenue' if growth > 0 else 'boost sales'}."
                    )
                }
                nudges.append(nudge)
        
        return nudges
    
    def get_personalized_nudges(self, merchant_name: str) -> List[str]:
        """Get formatted nudges for display"""
        nudges = self.generate_nudges()
        formatted_nudges = []
        
        for nudge in nudges:
            if nudge['type'] == 'daily_pattern':
                formatted_nudges.append(
                    f"📅 Hey {merchant_name}, {nudge['message']}"
                )
            elif nudge['type'] == 'hourly_pattern':
                formatted_nudges.append(
                    f"⏰ Hey {merchant_name}, {nudge['message']}"
                )
            elif nudge['type'] == 'item_performance':
                formatted_nudges.append(
                    f"🍽️ Hey {merchant_name}, {nudge['message']}"
                )
        
        return formatted_nudges 