import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_loader import load_data

class BusinessAnalytics:
    def __init__(self):
        data = load_data()
        self.transaction_data = data["transaction_data"]
        self.transaction_items = data["transaction_items"]
        self.merchant = data["merchant"]
        self.items = data["items"]
        self.keywords = data["keywords"]
        
        # Convert date columns to datetime
        self.transaction_data['order_time'] = pd.to_datetime(self.transaction_data['order_time'])
        
        # Merge transaction items with items data
        self.merged_data = self.transaction_items.merge(
            self.items, 
            on='item_id', 
            how='left'
        )
    
    def get_weekly_growth_trends(self):
        """Calculate weekly growth trends from real transaction data with more detailed insights"""
        # Calculate daily sales
        daily_sales = self.transaction_data.groupby(
            self.transaction_data['order_time'].dt.date
        ).agg({
            'order_value': 'sum',
            'order_id': 'count'
        }).rename(columns={
            'order_value': 'total_sales',
            'order_id': 'order_count'
        })
        
        # Calculate daily growth rates
        daily_sales['sales_growth'] = daily_sales['total_sales'].pct_change() * 100
        daily_sales['order_growth'] = daily_sales['order_count'].pct_change() * 100
        
        # Calculate weekly metrics
        weekly_data = daily_sales.groupby(
            pd.to_datetime(daily_sales.index).isocalendar().week
        ).agg({
            'total_sales': ['sum', 'mean'],
            'order_count': ['sum', 'mean'],
            'sales_growth': 'mean',
            'order_growth': 'mean'
        })
        
        current_week = weekly_data.iloc[-1]
        previous_week = weekly_data.iloc[-2]
        
        return {
            'current_week': {
                'total_sales': current_week[('total_sales', 'sum')],
                'avg_daily_sales': current_week[('total_sales', 'mean')],
                'total_orders': current_week[('order_count', 'sum')],
                'avg_daily_orders': current_week[('order_count', 'mean')],
                'sales_growth': current_week[('sales_growth', 'mean')],
                'order_growth': current_week[('order_growth', 'mean')]
            },
            'previous_week': {
                'total_sales': previous_week[('total_sales', 'sum')],
                'avg_daily_sales': previous_week[('total_sales', 'mean')],
                'total_orders': previous_week[('order_count', 'sum')],
                'avg_daily_orders': previous_week[('order_count', 'mean')],
                'sales_growth': previous_week[('sales_growth', 'mean')],
                'order_growth': previous_week[('order_growth', 'mean')]
            },
            'trend': 'increasing' if current_week[('sales_growth', 'mean')] > previous_week[('sales_growth', 'mean')] else 'decreasing'
        }
    
    def get_top_3_items(self, days=7, metric='revenue'):
        """Get top 3 items with detailed metrics"""
        # Get recent transactions
        recent_date = self.transaction_data['order_time'].max()
        start_date = recent_date - timedelta(days=days)
        
        recent_transactions = self.transaction_data[
            self.transaction_data['order_time'] >= start_date
        ]
        
        # Merge with items and calculate metrics
        recent_items = self.merged_data[
            self.merged_data['order_id'].isin(recent_transactions['order_id'])
        ]
        
        # Calculate various metrics
        item_metrics = (
            recent_items.groupby('item_name')
            .agg({
                'quantity': ['sum', 'mean', 'count'],
                'price': 'mean'
            })
        )
        
        # Calculate derived metrics
        item_metrics['revenue'] = item_metrics[('quantity', 'sum')] * item_metrics[('price', 'mean')]
        item_metrics['avg_order_quantity'] = item_metrics[('quantity', 'sum')] / item_metrics[('quantity', 'count')]
        
        # Sort by selected metric
        if metric == 'revenue':
            sorted_items = item_metrics.sort_values('revenue', ascending=False)
        elif metric == 'quantity':
            sorted_items = item_metrics.sort_values(('quantity', 'sum'), ascending=False)
        elif metric == 'orders':
            sorted_items = item_metrics.sort_values(('quantity', 'count'), ascending=False)
        
        # Format results
        top_items = []
        for item_name in sorted_items.head(3).index:
            metrics = sorted_items.loc[item_name]
            top_items.append({
                'item_name': item_name,
                'total_quantity': int(metrics[('quantity', 'sum')]),
                'avg_quantity_per_order': round(metrics['avg_order_quantity'], 2),
                'price': round(metrics[('price', 'mean')], 2),
                'revenue': round(metrics['revenue'], 2),
                'order_count': int(metrics[('quantity', 'count')])
            })
        
        return top_items
    
    def get_low_stock_alerts(self, threshold_days=3):
        """Get low stock alerts with advanced predictive analysis"""
        # Calculate sales velocity (items sold per day)
        daily_sales = (
            self.merged_data.groupby(['item_name', 'order_date'])
            .agg({
                'quantity': 'sum',
                'price': 'mean'
            })
            .reset_index()
        )
        
        # Calculate average daily sales and price trends
        item_metrics = (
            daily_sales.groupby('item_name')
            .agg({
                'quantity': ['mean', 'std', 'count'],
                'price': 'mean'
            })
        )
        
        # Get current stock levels
        current_stock = self.items.set_index('item_name')['stock_level']
        
        # Calculate days until stockout with confidence intervals
        alerts = []
        for item in current_stock.index:
            avg_daily_sales = item_metrics.loc[item, ('quantity', 'mean')]
            std_daily_sales = item_metrics.loc[item, ('quantity', 'std')]
            current_level = current_stock[item]
            
            if avg_daily_sales > 0:  # Only process items with sales history
                # Calculate optimistic and pessimistic scenarios
                optimistic_days = current_level / (avg_daily_sales + std_daily_sales)
                pessimistic_days = current_level / max(1, avg_daily_sales - std_daily_sales)
                
                # Generate alert based on risk level
                if pessimistic_days <= threshold_days:
                    risk_level = "URGENT" if pessimistic_days <= 1 else "HIGH"
                    alerts.append({
                        'item': item,
                        'current_stock': int(current_level),
                        'avg_daily_sales': round(avg_daily_sales, 1),
                        'days_until_stockout': {
                            'optimistic': round(optimistic_days, 1),
                            'pessimistic': round(pessimistic_days, 1)
                        },
                        'risk_level': risk_level,
                        'suggestion': self._generate_stock_suggestion(
                            item, current_level, avg_daily_sales
                        )
                    })
        
        return alerts if alerts else [{'status': 'healthy', 'message': 'All stock levels are healthy'}]
    
    def _generate_stock_suggestion(self, item, current_stock, avg_daily_sales):
        """Generate specific suggestions for stock management"""
        days_worth = current_stock / avg_daily_sales if avg_daily_sales > 0 else float('inf')
        
        if days_worth <= 1:
            return f"Immediate restock needed for {item}. Consider emergency order."
        elif days_worth <= 3:
            return f"Schedule restock for {item} within 24 hours."
        elif days_worth <= 7:
            return f"Plan restock for {item} in the next few days."
        else:
            return f"Monitor {item} stock levels. Current levels are sufficient."
    
    def get_personalized_suggestions(self, merchant_type, business_size):
        """Generate personalized business suggestions with data-driven insights"""
        suggestions = []
        
        # Get sales patterns and metrics
        daily_sales = (
            self.transaction_data.groupby(
                self.transaction_data['order_time'].dt.day_name()
            ).agg({
                'order_value': ['sum', 'count'],
                'order_id': 'nunique'
            })
        )
        
        hourly_sales = (
            self.transaction_data.groupby(
                self.transaction_data['order_time'].dt.hour
            )['order_value'].sum()
        )
        
        # Get top and bottom performing items
        top_items = self.get_top_3_items(metric='revenue')
        bottom_items = self.get_top_3_items(metric='revenue', ascending=True)
        
        # Generate data-driven suggestions
        best_day = daily_sales[('order_value', 'sum')].idxmax()
        worst_day = daily_sales[('order_value', 'sum')].idxmin()
        peak_hour = hourly_sales.idxmax()
        
        # Base suggestions from data analysis
        suggestions.extend([
            f"Your best-selling item is {top_items[0]['item_name']} with RM{top_items[0]['revenue']:.2f} revenue. Consider promoting it more!",
            f"Sales peak on {best_day}s (RM{daily_sales.loc[best_day, ('order_value', 'sum')]:.2f}). Consider special promotions on {worst_day}s to boost sales.",
            f"Busiest hour is {peak_hour}:00. Consider staffing adjustments during peak times.",
            f"Bundle {top_items[0]['item_name']} with {bottom_items[0]['item_name']} to increase sales of slower-moving items."
        ])
        
        # Merchant type specific suggestions
        if merchant_type == "Restaurant":
            suggestions.extend([
                "Lunch specials (12-2 PM) could increase weekday sales",
                "Weekend family bundles are popular in your area",
                "Consider adding a kids' menu to attract family customers"
            ])
        elif merchant_type == "Cafe":
            suggestions.extend([
                "Afternoon tea sets (2-5 PM) are trending in your area",
                "Consider adding seasonal drinks to your menu",
                "Loyalty program for regular coffee drinkers could increase retention"
            ])
        
        # Business size specific suggestions
        if business_size == "Small":
            suggestions.extend([
                "Focus on your top 3 bestsellers to maximize profits",
                "Consider offering takeaway specials to increase orders",
                "Limited-time offers could help test new menu items"
            ])
        elif business_size == "Large":
            suggestions.extend([
                "Implement a tiered loyalty program for different customer segments",
                "Bulk purchase discounts could attract more customers",
                "Consider adding a catering menu for corporate clients"
            ])
        
        # Add inventory-specific suggestions
        stock_alerts = self.get_low_stock_alerts()
        if isinstance(stock_alerts, list) and len(stock_alerts) > 0:
            for alert in stock_alerts:
                if isinstance(alert, dict) and 'suggestion' in alert:
                    suggestions.append(alert['suggestion'])
        
        return suggestions
    
    def get_yearly_sales(self, year=None):
        """Calculate total sales and metrics for a specific year"""
        try:
            # If no year provided, use the most recent year with data
            if year is None:
                year = self.transaction_data['order_time'].dt.year.max()
            
            # Filter data for the specified year
            yearly_data = self.transaction_data[
                self.transaction_data['order_time'].dt.year == year
            ]
            
            if yearly_data.empty:
                return f"No sales data available for {year}"
            
            # Calculate yearly metrics
            total_sales = yearly_data['order_value'].sum()
            total_orders = len(yearly_data)
            avg_order_value = total_sales / total_orders if total_orders > 0 else 0
            
            # Calculate monthly breakdown
            monthly_sales = yearly_data.groupby(
                yearly_data['order_time'].dt.month
            ).agg({
                'order_value': ['sum', 'count'],
                'order_id': 'nunique'
            })
            
            # Calculate growth compared to previous year
            prev_year = year - 1
            prev_year_data = self.transaction_data[
                self.transaction_data['order_time'].dt.year == prev_year
            ]
            prev_year_sales = prev_year_data['order_value'].sum() if not prev_year_data.empty else 0
            year_over_year_growth = ((total_sales - prev_year_sales) / prev_year_sales * 100) if prev_year_sales > 0 else 0
            
            return {
                'year': year,
                'total_sales': total_sales,
                'total_orders': total_orders,
                'average_order_value': avg_order_value,
                'monthly_breakdown': monthly_sales,
                'year_over_year_growth': year_over_year_growth,
                'best_month': monthly_sales[('order_value', 'sum')].idxmax(),
                'worst_month': monthly_sales[('order_value', 'sum')].idxmin()
            }
            
        except Exception as e:
            return f"Error calculating yearly sales: {str(e)}"

    def get_sales_insights(self):
        """Get comprehensive sales insights and trends"""
        growth_trends = self.get_weekly_growth_trends()
        top_items = self.get_top_3_items()
        
        # Get daily sales patterns
        daily_sales = (
            self.transaction_data.groupby(
                self.transaction_data['order_time'].dt.day_name()
            )['order_value'].sum()
        )
        
        # Get yearly sales data
        current_year = self.transaction_data['order_time'].dt.year.max()
        yearly_data = self.get_yearly_sales(current_year)
        
        insights = {
            'growth': {
                'current': growth_trends['current_week']['sales_growth'],
                'trend': growth_trends['trend']
            },
            'top_items': top_items,
            'best_day': daily_sales.idxmax(),
            'worst_day': daily_sales.idxmin(),
            'avg_order_value': self.transaction_data['order_value'].mean(),
            'yearly_data': yearly_data
        }
        
        return insights

    def get_customer_behavior_insights(self):
        """Analyze customer behavior patterns and preferences"""
        # Merge transaction data with items to get complete order information
        customer_data = self.transaction_data.merge(
            self.merged_data,
            on='order_id',
            how='left'
        )
        
        # Calculate customer metrics
        customer_metrics = {
            'average_order_value': customer_data.groupby('order_id')['order_value'].sum().mean(),
            'average_items_per_order': customer_data.groupby('order_id')['quantity'].sum().mean(),
            'peak_hours': customer_data.groupby(customer_data['order_time'].dt.hour)['order_id'].count().sort_values(ascending=False).head(3),
            'popular_cuisines': customer_data.groupby('cuisine_tag')['order_id'].count().sort_values(ascending=False).head(3)
        }
        
        return customer_metrics

    def get_seasonal_trends(self):
        """Analyze seasonal patterns in sales and customer behavior"""
        # Extract month and day of week from order time
        seasonal_data = self.transaction_data.copy()
        seasonal_data['month'] = seasonal_data['order_time'].dt.month
        seasonal_data['day_of_week'] = seasonal_data['order_time'].dt.day_name()
        
        # Calculate monthly trends
        monthly_trends = seasonal_data.groupby('month').agg({
            'order_value': ['sum', 'count'],
            'order_id': 'nunique'
        })
        
        # Calculate day of week trends
        weekday_trends = seasonal_data.groupby('day_of_week').agg({
            'order_value': ['sum', 'mean'],
            'order_id': 'count'
        })
        
        return {
            'monthly_trends': monthly_trends,
            'weekday_trends': weekday_trends
        }

    def get_profitability_analysis(self):
        """Analyze profitability of different items and categories"""
        # Merge transaction data with items to get cost information
        profitability_data = self.merged_data.merge(
            self.transaction_data[['order_id', 'order_value']],
            on='order_id',
            how='left'
        )
        
        # Calculate item-level profitability
        item_profitability = profitability_data.groupby('item_name').agg({
            'quantity': 'sum',
            'price': 'mean',
            'order_value': 'sum'
        })
        
        # Calculate category-level profitability
        category_profitability = profitability_data.groupby('cuisine_tag').agg({
            'quantity': 'sum',
            'price': 'mean',
            'order_value': 'sum'
        })
        
        return {
            'item_profitability': item_profitability,
            'category_profitability': category_profitability
        }

    def get_inventory_optimization_suggestions(self):
        """Generate data-driven suggestions for inventory optimization"""
        # Get current stock levels and sales velocity
        stock_data = self.items.merge(
            self.merged_data.groupby('item_id').agg({
                'quantity': 'sum',
                'order_id': 'count'
            }),
            on='item_id',
            how='left'
        )
        
        # Calculate inventory turnover and days of supply
        stock_data['inventory_turnover'] = stock_data['quantity'] / stock_data['stock_level']
        stock_data['days_of_supply'] = stock_data['stock_level'] / (stock_data['quantity'] / 30)  # Assuming 30 days
        
        # Generate optimization suggestions
        suggestions = []
        for _, row in stock_data.iterrows():
            if row['days_of_supply'] < 7:
                suggestions.append(f"⚠️ {row['item_name']} is running low (only {row['days_of_supply']:.1f} days of supply)")
            elif row['days_of_supply'] > 30:
                suggestions.append(f"ℹ️ {row['item_name']} has excess stock ({row['days_of_supply']:.1f} days of supply)")
        
        return suggestions

    def get_promotion_effectiveness(self):
        """Analyze the effectiveness of past promotions"""
        # Get promotion data from transaction data
        promotion_data = self.transaction_data[
            self.transaction_data['promotion_id'].notna()
        ]
        
        if promotion_data.empty:
            return "No promotion data available for analysis"
        
        # Calculate promotion metrics
        promotion_metrics = {
            'total_promotions': len(promotion_data['promotion_id'].unique()),
            'average_discount': promotion_data['discount_amount'].mean(),
            'promotion_sales': promotion_data['order_value'].sum(),
            'promotion_orders': len(promotion_data)
        }
        
        # Compare with non-promotion periods
        non_promotion_data = self.transaction_data[
            self.transaction_data['promotion_id'].isna()
        ]
        
        promotion_metrics['lift_in_sales'] = (
            (promotion_metrics['promotion_sales'] / promotion_metrics['promotion_orders']) /
            (non_promotion_data['order_value'].sum() / len(non_promotion_data))
        ) - 1
        
        return promotion_metrics

# Example usage
if __name__ == "__main__":
    analytics = BusinessAnalytics()
    
    # Test the functions
    print("\nWeekly Growth Trends:")
    print(analytics.get_weekly_growth_trends())
    
    print("\nTop 3 Items:")
    print(analytics.get_top_3_items())
    
    print("\nLow Stock Alerts:")
    print(analytics.get_low_stock_alerts())
    
    print("\nPersonalized Suggestions:")
    print(analytics.get_personalized_suggestions("Cafe", "Small"))
    
    print("\nSales Insights:")
    print(analytics.get_sales_insights())
