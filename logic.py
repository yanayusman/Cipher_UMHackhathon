from data_loader import load_data
import pandas as pd
from datetime import datetime, timedelta
from helper import BusinessAnalytics

# Initialize BusinessAnalytics
analytics = BusinessAnalytics()

data = load_data()
items = data["items"]
transaction_data = data["transaction_data"]
transaction_items = data["transaction_items"]

# merge items and transaction_items for next operation
merged_data = transaction_items.merge(items, on = "item_id", how = "left")

print(transaction_data.columns)  # To check if 'order_value' exists
print(transaction_data.head())  # To see the first few rows and ensure the data is correct

def get_merged_data(data):
    """Helper function to merge transaction items with items data"""
    return data["transaction_items"].merge(
        data["items"],
        on="item_id",
        how="left"
    )

def get_daily_sales_summary(date_str=None):
    """Get daily sales summary with detailed metrics"""
    try:
        # Get current date if none provided
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Convert date string to datetime for calculations
        current_date = datetime.strptime(date_str, "%Y-%m-%d")
        yesterday = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Get sales data for the specified date
        daily_data = analytics.transaction_data[
            analytics.transaction_data['order_time'].dt.strftime('%Y-%m-%d') == date_str
        ]
        
        if daily_data.empty:
            return f"No sales data available for {date_str}"
        
        # Calculate metrics
        total_sales = daily_data['order_value'].sum()
        num_orders = len(daily_data)
        avg_order_value = total_sales / num_orders if num_orders > 0 else 0
        
        # Get yesterday's data for comparison
        yesterday_data = analytics.transaction_data[
            analytics.transaction_data['order_time'].dt.strftime('%Y-%m-%d') == yesterday
        ]
        yesterday_sales = yesterday_data['order_value'].sum() if not yesterday_data.empty else 0
        
        # Calculate growth
        growth = ((total_sales - yesterday_sales) / yesterday_sales * 100) if yesterday_sales > 0 else 0
        
        return f"""📊 Sales Summary for {date_str}:
• Total Sales: RM{total_sales:,.2f}
• Number of Orders: {num_orders}
• Average Order Value: RM{avg_order_value:,.2f}
• Growth vs Yesterday: {growth:+.1f}%"""
    
    except Exception as e:
        return f"Error calculating daily sales summary: {str(e)}"

def get_top_selling_items(top_n=3, date_str=None):
    """Get top selling items with detailed metrics"""
    try:
        # If no date provided, use the most recent date with data
        if date_str is None:
            # Get the most recent date from transaction data
            most_recent_date = analytics.transaction_data['order_time'].max().strftime('%Y-%m-%d')
            date_str = most_recent_date
            print(f"Using most recent date with data: {date_str}")
        
        # Merge transaction items with transaction data to get order_time
        merged_with_time = analytics.merged_data.merge(
            analytics.transaction_data[['order_id', 'order_time']],
            on='order_id',
            how='left'
        )
        
        # Convert order_time to datetime if it's not already
        merged_with_time['order_time'] = pd.to_datetime(merged_with_time['order_time'])
        
        # Get items data for the specified date
        daily_items = merged_with_time[
            merged_with_time['order_time'].dt.strftime('%Y-%m-%d') == date_str
        ]
        
        if daily_items.empty:
            return [f"No sales data available for {date_str}"]
        
        # Calculate top items
        top_items = (
            daily_items.groupby('item_name')
            .agg({
                'order_id': 'count',
                'item_price': 'mean'
            })
            .sort_values('order_id', ascending=False)
            .head(top_n)
        )
        
        return [
            f"{item}: {count} sold (RM{price:,.2f} avg price)"
            for item, (count, price) in top_items.iterrows()
        ]
    
    except Exception as e:
        print(f"Error in get_top_selling_items: {str(e)}")
        return [f"Error getting top selling items: {str(e)}"]

def get_low_stock_alerts(data, merchant_id=None, threshold=5):
    """
    Get alerts for items that are running low on stock.
    Since we don't have direct stock level data, we'll use sales frequency as a proxy.
    
    Args:
        data (dict): Dictionary containing DataFrames
        merchant_id (str, optional): Filter by merchant ID
        threshold (int, optional): Alert threshold for low stock
        
    Returns:
        list: List of dictionaries containing low stock alerts
    """
    try:
        # Get the merged data
        merged_data = get_merged_data(data)
        
        # Filter by merchant if specified
        if merchant_id:
            merged_data = merged_data[merged_data['merchant_id'] == merchant_id]
        
        # Calculate sales frequency per item
        sales_frequency = merged_data.groupby(['merchant_id', 'item_id', 'item_name'])['order_id'].count().reset_index()
        sales_frequency.columns = ['merchant_id', 'item_id', 'item_name', 'sales_count']
        
        # Calculate average sales per item
        avg_sales = sales_frequency['sales_count'].mean()
        
        # Adjust threshold based on average sales
        dynamic_threshold = max(threshold, avg_sales * 0.3)  # At least 30% below average
        
        # Sort by sales frequency
        sales_frequency = sales_frequency.sort_values('sales_count', ascending=True)
        
        # Get items with low sales frequency (proxy for low stock)
        low_stock_items = sales_frequency[sales_frequency['sales_count'] <= dynamic_threshold]
        
        # Format alerts
        alerts = []
        for _, row in low_stock_items.iterrows():
            # Calculate how far below average the sales are
            below_avg = ((avg_sales - row['sales_count']) / avg_sales * 100) if avg_sales > 0 else 0
            
            alerts.append({
                'merchant_id': row['merchant_id'],
                'item_id': row['item_id'],
                'item_name': row['item_name'],
                'sales_count': row['sales_count'],
                'below_avg': below_avg,
                'message': f"⚠️ {row['item_name']} (ID: {row['item_id']}) has low sales frequency - only {row['sales_count']} sales ({below_avg:.1f}% below average)"
            })
        
        return alerts
    
    except Exception as e:
        print(f"Error in get_low_stock_alerts: {str(e)}")
        return []

def get_sales_trends(days=7):
    """Get sales trends over the specified number of days"""
    try:
        # Get the most recent date with data
        most_recent_date = analytics.transaction_data['order_time'].max()
        end_date = most_recent_date
        start_date = end_date - timedelta(days=days)
        
        print(f"Analyzing trends from {start_date.date()} to {end_date.date()}")
        
        # Filter data for the specified date range
        filtered = analytics.transaction_data[
            (analytics.transaction_data['order_time'] >= start_date) &
            (analytics.transaction_data['order_time'] <= end_date)
        ]
        
        if filtered.empty:
            return {
                'daily_sales': pd.Series(),
                'growth_rate': 0,
                'best_day': 'No data available',
                'worst_day': 'No data available',
                'avg_daily_sales': 0,
                'total_sales': 0
            }
        
        # Calculate daily sales
        daily_sales = filtered.groupby(filtered['order_time'].dt.date)['order_value'].sum()
        
        # Calculate basic statistics
        avg_daily_sales = daily_sales.mean()
        std_daily_sales = daily_sales.std()
        
        # Identify and handle outliers (more than 2 standard deviations from mean)
        lower_bound = avg_daily_sales - (2 * std_daily_sales)
        upper_bound = avg_daily_sales + (2 * std_daily_sales)
        
        # Remove outliers for trend calculation
        clean_daily_sales = daily_sales[
            (daily_sales >= lower_bound) & 
            (daily_sales <= upper_bound)
        ]
        
        # Calculate growth rate using clean data
        if len(clean_daily_sales) > 1:
            growth_rate = ((clean_daily_sales.iloc[-1] - clean_daily_sales.iloc[0]) / 
                         clean_daily_sales.iloc[0] * 100)
        else:
            growth_rate = 0
        
        # Get best and worst days from clean data
        if not clean_daily_sales.empty:
            best_day = clean_daily_sales.idxmax().strftime("%A")
            worst_day = clean_daily_sales.idxmin().strftime("%A")
        else:
            best_day = "No valid data"
            worst_day = "No valid data"
        
        return {
            'daily_sales': daily_sales,
            'growth_rate': growth_rate,
            'best_day': best_day,
            'worst_day': worst_day,
            'avg_daily_sales': avg_daily_sales,
            'total_sales': daily_sales.sum(),
            'outliers': daily_sales[
                (daily_sales < lower_bound) | 
                (daily_sales > upper_bound)
            ].index.tolist()
        }
    
    except Exception as e:
        print(f"Error in get_sales_trends: {str(e)}")
        return {
            'daily_sales': pd.Series(),
            'growth_rate': 0,
            'best_day': 'Error calculating',
            'worst_day': 'Error calculating',
            'avg_daily_sales': 0,
            'total_sales': 0,
            'outliers': []
        }

def get_simple_suggestion(merchant_type=None, business_size=None):
    """Get personalized business suggestions"""
    try:
        return analytics.get_personalized_suggestions(merchant_type, business_size)
    except Exception as e:
        print(f"Error in get_simple_suggestion: {str(e)}")
        return ["Unable to generate suggestions at this time."]