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
        try:
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
                    'order_id': 'count',  # Number of times item was ordered
                    'item_price': 'mean'  # Average price of the item
                })
            )
            
            # Calculate revenue
            item_metrics['revenue'] = item_metrics['order_id'] * item_metrics['item_price']
            
            # Sort by selected metric
            if metric == 'revenue':
                sorted_items = item_metrics.sort_values('revenue', ascending=False)
            elif metric == 'orders':
                sorted_items = item_metrics.sort_values('order_id', ascending=False)
            
            # Format results
            top_items = []
            for item_name in sorted_items.head(3).index:
                metrics = sorted_items.loc[item_name]
                top_items.append({
                    'item_name': item_name,
                    'total_orders': int(metrics['order_id']),
                    'price': round(metrics['item_price'], 2),
                    'revenue': round(metrics['revenue'], 2)
                })
            
            return top_items
        except Exception as e:
            print(f"Error in get_top_3_items: {str(e)}")
            return []
    
    def get_low_stock_alerts(self, threshold_days=3):
        """Get low stock alerts with advanced predictive analysis"""
        # Calculate sales frequency (number of times each item is ordered per day)
        daily_sales = (
            self.merged_data.groupby([
                'item_name', 
                self.transaction_data['order_time'].dt.date
            ])
            .agg({
                'order_id': 'count',  # Count number of orders per item per day
                'item_price': 'mean'  # Average price of the item
            })
            .reset_index()
        )
        
        # Calculate average daily sales and price trends
        item_metrics = (
            daily_sales.groupby('item_name')
            .agg({
                'order_id': ['mean', 'std', 'count'],  # Daily order frequency metrics
                'item_price': 'mean'  # Average price
            })
        )
        
        # Calculate total sales for each item
        total_sales = (
            self.merged_data.groupby('item_name')
            .agg({
                'order_id': 'count',  # Total number of orders
                'item_price': 'mean'  # Average price
            })
        )
        
        # Calculate alerts based on sales frequency
        alerts = []
        for item in item_metrics.index:
            avg_daily_orders = item_metrics.loc[item, ('order_id', 'mean')]
            std_daily_orders = item_metrics.loc[item, ('order_id', 'std')]
            total_orders = total_sales.loc[item, 'order_id']
            
            if avg_daily_orders > 0:  # Only process items with sales history
                # Calculate sales velocity (orders per day)
                sales_velocity = avg_daily_orders
                
                # Calculate risk based on sales frequency and standard deviation
                risk_score = (std_daily_orders / avg_daily_orders) if avg_daily_orders > 0 else 0
                
                # Generate alert based on risk level
                if risk_score > 0.5 or sales_velocity > avg_daily_orders * 1.5:  # High risk if high variability or increasing sales
                    risk_level = "URGENT" if risk_score > 1.0 else "HIGH"
                    alerts.append({
                        'item': item,
                        'current_sales': int(total_orders),
                        'avg_daily_sales': round(avg_daily_orders, 1),
                        'days_until_stockout': {
                            'optimistic': round(30 / (sales_velocity + std_daily_orders), 1),  # Assuming 30 days of stock
                            'pessimistic': round(30 / max(1, sales_velocity - std_daily_orders), 1)
                        },
                        'risk_level': risk_level,
                        'suggestion': self._generate_stock_suggestion(
                            item, total_orders, avg_daily_orders
                        )
                    })
        
        return alerts if alerts else [{'status': 'healthy', 'message': 'All stock levels are healthy'}]
    
    def _generate_stock_suggestion(self, item, total_orders, avg_daily_orders):
        """Generate specific suggestions for stock management"""
        if avg_daily_orders > 0:
            days_worth = total_orders / avg_daily_orders
            
            if days_worth <= 1:
                return f"Immediate restock needed for {item}. Consider emergency order."
            elif days_worth <= 3:
                return f"Schedule restock for {item} within 24 hours."
            elif days_worth <= 7:
                return f"Plan restock for {item} in the next few days."
            else:
                return f"Monitor {item} stock levels. Current sales patterns suggest stable demand."
        else:
            return f"Review {item} performance. No recent sales activity detected."
    
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
        bottom_items = self.get_top_3_items(metric='orders')
        
        # Generate data-driven suggestions
        best_day = daily_sales[('order_value', 'sum')].idxmax()
        worst_day = daily_sales[('order_value', 'sum')].idxmin()
        peak_hour = hourly_sales.idxmax()
        
        # Base suggestions from data analysis
        if top_items:
            suggestions.extend([
                f"Your best-selling item is {top_items[0]['item_name']} with RM{top_items[0]['revenue']:.2f} revenue. Consider promoting it more!",
                f"Sales peak on {best_day}s (RM{daily_sales.loc[best_day, ('order_value', 'sum')]:.2f}). Consider special promotions on {worst_day}s to boost sales.",
                f"Busiest hour is {peak_hour}:00. Consider staffing adjustments during peak times.",
            ])
            if bottom_items:
                suggestions.append(f"Bundle {top_items[0]['item_name']} with {bottom_items[-1]['item_name']} to increase sales of slower-moving items.")
        
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
            
            # Format monthly data for display
            monthly_breakdown = {}
            for month in range(1, 13):
                if month in monthly_sales.index:
                    data = monthly_sales.loc[month]
                    monthly_breakdown[month] = {
                        'sales': data[('order_value', 'sum')],
                        'orders': data[('order_id', 'nunique')]
                    }
                else:
                    monthly_breakdown[month] = {
                        'sales': 0,
                        'orders': 0
                    }
            
            return {
                'year': year,
                'total_sales': total_sales,
                'total_orders': total_orders,
                'average_order_value': avg_order_value,
                'monthly_breakdown': monthly_breakdown,
                'year_over_year_growth': year_over_year_growth,
                'best_month': monthly_sales[('order_value', 'sum')].idxmax() if not monthly_sales.empty else None,
                'worst_month': monthly_sales[('order_value', 'sum')].idxmin() if not monthly_sales.empty else None
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
        try:
            # Get unique orders by hour
            hourly_orders = (
                self.transaction_data
                .groupby(self.transaction_data['order_time'].dt.hour)['order_id']
                .nunique()  # Count unique orders per hour
                .sort_values(ascending=False)
            )
            
            # Get top 3 hours with most unique orders
            peak_hours = hourly_orders.head(3).to_dict()
            
            # Calculate total unique orders for percentage calculation
            total_unique_orders = self.transaction_data['order_id'].nunique()
            
            # Calculate customer metrics
            customer_metrics = {
                'average_order_value': self.transaction_data.groupby('order_id')['order_value'].sum().mean(),
                'average_items_per_order': self.merged_data.groupby('order_id')['item_id'].count().mean(),
                'peak_hours': peak_hours,
                'total_orders': total_unique_orders,
                'popular_cuisines': self.merged_data.groupby('cuisine_tag')['order_id'].count().sort_values(ascending=False).head(3).to_dict()
            }
            
            return customer_metrics
        except Exception as e:
            print(f"Error in get_customer_behavior_insights: {str(e)}")
            return {
                'average_order_value': 0,
                'average_items_per_order': 0,
                'peak_hours': {},
                'total_orders': 0,
                'popular_cuisines': {}
            }

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
        # Merge transaction data with items to get complete order information
        profitability_data = self.merged_data.merge(
            self.transaction_data[['order_id', 'order_value']],
            on='order_id',
            how='left'
        )
        
        # Calculate item-level profitability
        item_profitability = profitability_data.groupby('item_name').agg({
            'order_id': 'count',  # Number of times item was ordered
            'item_price': 'mean',  # Average price of the item
            'order_value': 'sum'   # Total revenue from the item
        }).rename(columns={
            'order_id': 'total_orders',
            'item_price': 'average_price',
            'order_value': 'total_revenue'
        })
        
        # Calculate category-level profitability
        category_profitability = profitability_data.groupby('cuisine_tag').agg({
            'order_id': 'count',  # Number of orders in category
            'item_price': 'mean',  # Average price in category
            'order_value': 'sum'   # Total revenue in category
        }).rename(columns={
            'order_id': 'total_orders',
            'item_price': 'average_price',
            'order_value': 'total_revenue'
        })
        
        return {
            'item_profitability': item_profitability,
            'category_profitability': category_profitability
        }

    def get_inventory_optimization_suggestions(self):
        """Generate data-driven suggestions for inventory optimization"""
        try:
            # Calculate sales frequency and average price for each item
            item_metrics = self.merged_data.groupby('item_id').agg({
                'order_id': 'count',  # Number of times item was ordered
                'item_price': 'mean'  # Average price of the item
            }).reset_index()
            
            # Merge with items data to get item names
            item_metrics = item_metrics.merge(
                self.items[['item_id', 'item_name']],
                on='item_id',
                how='left'
            )
            
            # Calculate average daily sales (assuming 30 days period)
            item_metrics['avg_daily_sales'] = item_metrics['order_id'] / 30
            
            # Generate optimization suggestions
            suggestions = []
            
            # Sort items by sales frequency
            item_metrics = item_metrics.sort_values('order_id', ascending=False)
            
            # Top selling items
            top_items = item_metrics.head(3)
            suggestions.append("**Top Selling Items:**")
            for _, item in top_items.iterrows():
                suggestions.append(f"• {item['item_name']}: {item['order_id']} orders (RM{item['item_price']:.2f} avg price)")
            
            # Slow moving items
            slow_items = item_metrics.tail(3)
            suggestions.append("\n**Slow Moving Items:**")
            for _, item in slow_items.iterrows():
                suggestions.append(f"• {item['item_name']}: {item['order_id']} orders (RM{item['item_price']:.2f} avg price)")
            
            # General inventory suggestions
            suggestions.append("\n**Inventory Management Tips:**")
            suggestions.append("1. Consider bundling slow-moving items with popular items")
            suggestions.append("2. Review pricing strategy for items with low sales")
            suggestions.append("3. Monitor sales patterns to optimize stock levels")
            suggestions.append("4. Consider seasonal variations in demand")
            
            return suggestions
            
        except Exception as e:
            return [f"Error generating inventory suggestions: {str(e)}"]

    def get_promotion_effectiveness(self):
        """Analyze the effectiveness of promotions based on order patterns"""
        try:
            # Get the most recent 30 days of data for analysis
            recent_date = self.transaction_data['order_time'].max()
            start_date = recent_date - pd.Timedelta(days=30)
            
            recent_data = self.transaction_data[
                self.transaction_data['order_time'] >= start_date
            ]
            
            # Calculate daily metrics
            daily_metrics = recent_data.groupby(recent_data['order_time'].dt.date).agg({
                'order_value': ['sum', 'count'],
                'order_id': 'nunique'
            }).reset_index()
            
            daily_metrics.columns = ['date', 'total_sales', 'order_count', 'unique_orders']
            
            # Calculate baseline metrics
            avg_daily_sales = daily_metrics['total_sales'].mean()
            std_daily_sales = daily_metrics['total_sales'].std()
            
            # Identify promotional days (1 standard deviation above mean)
            promotional_days = daily_metrics[daily_metrics['total_sales'] > (avg_daily_sales + std_daily_sales)]
            non_promotional_days = daily_metrics[daily_metrics['total_sales'] <= (avg_daily_sales + std_daily_sales)]
            
            if len(promotional_days) == 0:
                return {
                    'status': 'no_promotions',
                    'message': 'No significant promotional activity detected in the last 30 days',
                    'baseline_metrics': {
                        'average_daily_sales': round(avg_daily_sales, 2),
                        'average_orders_per_day': round(daily_metrics['order_count'].mean(), 1),
                        'average_unique_orders': round(daily_metrics['unique_orders'].mean(), 1)
                    }
                }
            
            # Calculate promotional metrics
            promo_metrics = {
                'total_promotional_days': len(promotional_days),
                'average_sales_on_promo': round(promotional_days['total_sales'].mean(), 2),
                'average_orders_on_promo': round(promotional_days['order_count'].mean(), 1),
                'average_unique_orders_on_promo': round(promotional_days['unique_orders'].mean(), 1),
                'highest_sales_day': {
                    'date': promotional_days.loc[promotional_days['total_sales'].idxmax(), 'date'].strftime("%Y-%m-%d"),
                    'sales': round(promotional_days['total_sales'].max(), 2),
                    'orders': int(promotional_days['order_count'].max())
                },
                'lift_in_sales': round(((promotional_days['total_sales'].mean() - avg_daily_sales) / avg_daily_sales * 100), 1),
                'baseline_metrics': {
                    'average_daily_sales': round(avg_daily_sales, 2),
                    'average_orders_per_day': round(daily_metrics['order_count'].mean(), 1),
                    'average_unique_orders': round(daily_metrics['unique_orders'].mean(), 1)
                }
            }
            
            return promo_metrics
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error analyzing promotion effectiveness: {str(e)}"
            }

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
