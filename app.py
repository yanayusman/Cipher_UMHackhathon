import streamlit as st
from logic import(
    get_daily_sales_summary,
    get_top_selling_items,
    get_low_stock_alerts,
    get_simple_suggestion,
    get_sales_trends
)
from data_loader import load_data
from datetime import datetime, timedelta
from helper import BusinessAnalytics
import pandas as pd

# Initialize BusinessAnalytics
analytics = BusinessAnalytics()

# Load data once at startup
data = load_data()

def process_query(query, merchant_id=None, date_param=None):
    """Process user queries and return appropriate responses"""
    # Check for sales-related queries
    sales_keywords = [
        "sales", "how much", "revenue", "earnings", "income",
        "top selling", "best selling", "popular items", "most sold",
        "what's selling", "what sells", "selling well", "trends",
        "compare", "versus", "vs", "difference", "average", "mean",
        "median", "total", "sum", "amount", "value"
    ]
    
    if any(keyword in query for keyword in sales_keywords):
        # Handle comparative queries
        if any(word in query for word in ["compare", "vs", "versus", "difference"]):
            if "today" in query and "yesterday" in query:
                today_sales = get_daily_sales_summary()
                yesterday_sales = get_daily_sales_summary((datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"))
                st.markdown("**Comparison: Today vs Yesterday**")
                st.write(f"Today: {today_sales}")
                st.write(f"Yesterday: {yesterday_sales}")
                return
        
        # Handle specific metric queries
        if any(word in query for word in ["average", "mean", "median", "total", "sum"]):
            if "order" in query and "value" in query:
                avg_order_value = analytics.transaction_data['order_value'].mean()
                st.success(f"Average Order Value: RM{avg_order_value:,.2f}")
                return
            elif "revenue" in query or "total" in query:
                total_revenue = analytics.transaction_data['order_value'].sum()
                total_orders = len(analytics.transaction_data)
                avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
                
                st.markdown("**💰 Total Revenue Summary:**")
                st.write(f"• Total Revenue: RM{total_revenue:,.2f}")
                st.write(f"• Total Orders: {total_orders:,}")
                st.write(f"• Average Order Value: RM{avg_order_value:,.2f}")
                
                # Get yearly breakdown
                yearly_data = analytics.transaction_data.groupby(
                    analytics.transaction_data['order_time'].dt.year
                )['order_value'].agg(['sum', 'count']).rename(columns={'sum': 'revenue', 'count': 'orders'})
                
                st.markdown("**📊 Yearly Breakdown:**")
                for year, data in yearly_data.iterrows():
                    st.write(f"• {year}: RM{data['revenue']:,.2f} ({data['orders']:,} orders)")
                return
        
        # Handle year-specific queries
        if any(str(year) in query for year in range(2000, 2100)):
            year = int(next((str(year) for year in range(2000, 2100) if str(year) in query), None))
            st.markdown(f"**Yearly Sales Summary ({year}):**")
            yearly_data = analytics.get_yearly_sales(year)
            
            if isinstance(yearly_data, dict):
                st.markdown(f"""
                • Total Sales: RM{yearly_data['total_sales']:,.2f}
                • Total Orders: {yearly_data['total_orders']:,}
                • Average Order Value: RM{yearly_data['average_order_value']:,.2f}
                • Year-over-Year Growth: {yearly_data['year_over_year_growth']:+.1f}%
                • Best Month: {yearly_data['best_month'] if yearly_data['best_month'] else 'N/A'}
                • Worst Month: {yearly_data['worst_month'] if yearly_data['worst_month'] else 'N/A'}
                """)
                
                # Display monthly breakdown
                st.markdown("**Monthly Breakdown:**")
                for month, data in yearly_data['monthly_breakdown'].items():
                    st.write(f"Month {month}: RM{data['sales']:,.2f} ({data['orders']:,} orders)")
            else:
                st.warning(yearly_data)
        
        # Handle "today" in query
        elif "today" in query:
            st.markdown("**Today's Sales Summary:**")
            today_summary = get_daily_sales_summary()
            if "No sales data available" in today_summary:
                st.warning(today_summary)
            else:
                st.success(today_summary)
        
        # Handle "yesterday" in query
        elif "yesterday" in query and not date_param:
            date_param = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            st.markdown("**Yesterday's Sales Summary:**")
            yesterday_summary = get_daily_sales_summary(date_param)
            if "No sales data available" in yesterday_summary:
                st.warning(yesterday_summary)
            else:
                st.success(yesterday_summary)
        
        # For queries specifically about trends
        elif "trend" in query:
            st.markdown("**Sales Trends (Last 7 Days):**")
            trends = get_sales_trends()
            
            if not trends['daily_sales'].empty:
                # Display daily sales
                st.write("Daily Sales:")
                for date, sales in trends['daily_sales'].items():
                    # Highlight outliers
                    if date in trends['outliers']:
                        st.warning(f"{date.strftime('%A, %Y-%m-%d')}: RM{sales:,.2f} ⚠️ Unusual activity")
                    else:
                        st.write(f"{date.strftime('%A, %Y-%m-%d')}: RM{sales:,.2f}")
                
                # Display summary statistics
                st.markdown("**Summary Statistics:**")
                st.write(f"Total Sales: RM{trends['total_sales']:,.2f}")
                st.write(f"Average Daily Sales: RM{trends['avg_daily_sales']:,.2f}")
                st.write(f"Growth Rate: {trends['growth_rate']:.2f}%")
                st.write(f"Best Day: {trends['best_day']}")
                st.write(f"Worst Day: {trends['worst_day']}")
                
                if trends['outliers']:
                    st.warning("⚠️ Note: Some days show unusual sales activity and were excluded from trend calculations")
            else:
                st.warning("No sales data available for trend analysis")
        
        # For queries specifically about top/best selling items
        elif any(phrase in query for phrase in ["top selling", "best selling", "popular items", "most sold"]):
            st.markdown("**Top Selling Items:**")
            top_items = get_top_selling_items(date_str=date_param)
            for item in top_items:
                st.info(item)
        
        # Handle monthly sales queries
        elif any(phrase in query for phrase in ["monthly sales", "sales by month", "monthly revenue"]):
            # Get the most recent year with data
            current_year = analytics.transaction_data['order_time'].dt.year.max()
            yearly_data = analytics.get_yearly_sales(current_year)
            
            if isinstance(yearly_data, dict):
                st.markdown(f"**Monthly Sales Summary ({current_year}):**")
                
                # Create a table for monthly data
                monthly_data = []
                for month, data in yearly_data['monthly_breakdown'].items():
                    monthly_data.append({
                        'Month': month,
                        'Sales': f"RM{data['sales']:,.2f}",
                        'Orders': f"{data['orders']:,}",
                        'Average Order Value': f"RM{data['sales']/data['orders']:,.2f}" if data['orders'] > 0 else "RM0.00"
                    })
                
                # Convert to DataFrame and display
                df = pd.DataFrame(monthly_data)
                st.table(df)
                
                # Add summary statistics
                st.markdown("**Summary Statistics:**")
                total_sales = sum(data['sales'] for data in yearly_data['monthly_breakdown'].values())
                total_orders = sum(data['orders'] for data in yearly_data['monthly_breakdown'].values())
                avg_monthly_sales = total_sales / 12
                avg_monthly_orders = total_orders / 12
                
                st.write(f"• Total Annual Sales: RM{total_sales:,.2f}")
                st.write(f"• Average Monthly Sales: RM{avg_monthly_sales:,.2f}")
                st.write(f"• Total Annual Orders: {total_orders:,}")
                st.write(f"• Average Monthly Orders: {avg_monthly_orders:,.0f}")
                
                # Show best and worst months
                best_month = max(yearly_data['monthly_breakdown'].items(), key=lambda x: x[1]['sales'])
                worst_month = min(yearly_data['monthly_breakdown'].items(), key=lambda x: x[1]['sales'])
                
                st.write(f"• Best Month: Month {best_month[0]} (RM{best_month[1]['sales']:,.2f})")
                st.write(f"• Worst Month: Month {worst_month[0]} (RM{worst_month[1]['sales']:,.2f})")
            else:
                st.warning(yearly_data)
        else:
            # For general sales queries, just show the daily summary
            st.markdown("**Sales Summary:**")
            summary = get_daily_sales_summary(date_param)
            if "No sales data available" in summary:
                st.warning(summary)
            else:
                st.success(summary)
    
    # Handle customer behavior queries
    elif any(word in query for word in ["customer", "behavior", "pattern", "preference"]):
        customer_insights = analytics.get_customer_behavior_insights()
        st.markdown("**Customer Behavior Insights:**")
        st.write(f"Average Order Value: RM{customer_insights['average_order_value']:,.2f}")
        st.write(f"Average Items per Order: {customer_insights['average_items_per_order']:.1f}")
        st.write("Peak Hours:")
        for hour, count in customer_insights['peak_hours'].items():
            st.write(f"• {hour}:00 - {count} orders")
        st.write("Popular Cuisines:")
        for cuisine, count in customer_insights['popular_cuisines'].items():
            st.write(f"• {cuisine}: {count} orders")
    
    # Handle profitability queries
    elif any(word in query for word in ["profit", "revenue", "income", "earnings"]):
        profitability = analytics.get_profitability_analysis()
        st.markdown("**Profitability Analysis:**")
        
        st.markdown("**Item-Level Profitability:**")
        for item, metrics in profitability['item_profitability'].head(5).iterrows():
            st.write(f"• {item}:")
            st.write(f"  - Total Revenue: RM{metrics['total_revenue']:,.2f}")
            st.write(f"  - Average Price: RM{metrics['average_price']:,.2f}")
            st.write(f"  - Total Orders: {metrics['total_orders']}")
        
        st.markdown("**Category-Level Profitability:**")
        for category, metrics in profitability['category_profitability'].iterrows():
            st.write(f"• {category}:")
            st.write(f"  - Total Revenue: RM{metrics['total_revenue']:,.2f}")
            st.write(f"  - Average Price: RM{metrics['average_price']:,.2f}")
            st.write(f"  - Total Orders: {metrics['total_orders']}")
    
    # Handle seasonal trend queries
    elif any(word in query for word in ["seasonal", "trend", "pattern", "monthly"]):
        trends = analytics.get_seasonal_trends()
        st.markdown("**Seasonal Trends:**")
        
        st.markdown("**Monthly Trends:**")
        for month, data in trends['monthly_trends'].iterrows():
            st.write(f"Month {month}: RM{data[('order_value', 'sum')]:,.2f} sales")
        
        st.markdown("**Weekday Trends:**")
        for day, data in trends['weekday_trends'].iterrows():
            st.write(f"{day}: RM{data[('order_value', 'sum')]:,.2f} sales")
    
    # Handle inventory queries
    elif any(word in query for word in ["inventory", "stock", "supply", "restock"]):
        suggestions = analytics.get_inventory_optimization_suggestions()
        if suggestions:
            st.markdown("**Inventory Optimization Suggestions:**")
            for suggestion in suggestions:
                st.write(suggestion)
        else:
            st.success("All inventory levels are optimal at this time.")
    
    # Handle promotion queries
    elif any(word in query for word in ["promotion", "discount", "offer", "deal"]):
        promotion_metrics = analytics.get_promotion_effectiveness()
        if isinstance(promotion_metrics, dict):
            st.markdown("**Promotion Effectiveness (Last 30 Days):**")
            st.write(f"• Total Promotional Days: {promotion_metrics['total_promotional_days']}")
            st.write(f"• Average Sales on Promotional Days: RM{promotion_metrics['average_sales_on_promo']:,.2f}")
            st.write(f"• Highest Sales Day: RM{promotion_metrics['highest_sales_day']:,.2f}")
            st.write(f"• Sales Lift: {promotion_metrics['lift_in_sales']:+.1f}%")
            st.write(f"• Best Promotional Day: {promotion_metrics['best_promo_day']}")
        else:
            st.warning(promotion_metrics)
    
    # Handle help and greeting queries
    elif any(word in query for word in ["hi", "hello", "hey", "greetings"]):
        st.success("Hello! How can I help you today? You can ask me about sales, inventory, or business insights.")
    
    elif any(word in query for word in ["help", "what can you do", "capabilities"]):
        st.markdown("""
        I can help you with:
        
        **Sales Information**
        - Daily, weekly, monthly, and yearly sales
        - Sales trends and growth rates
        - Top selling items
        - Best and worst performing days
        
        **Inventory Management**
        - Low stock alerts
        - Inventory optimization suggestions
        - Stock levels and turnover
        
        **Business Insights**
        - Customer behavior patterns
        - Seasonal trends
        - Profitability analysis
        - Promotion effectiveness
        
        **Business Tips**
        - Personalized suggestions
        - Improvement recommendations
        - Marketing strategies
        
        Try asking me about any of these topics!
        """)
    
    # Handle business tips queries
    elif any(phrase in query for phrase in ["business tips", "suggestions", "improve", "advice", "recommendations"]):
        # Get personalized suggestions based on business type and size
        suggestions = analytics.get_personalized_suggestions("Restaurant", "Small")
        
        st.markdown("**📈 Data-Driven Business Tips:**")
        
        # Display suggestions in a more organized way
        st.markdown("### 🍽️ Menu & Product Optimization")
        st.write("• " + suggestions[0])  # Best-selling item tip
        st.write("• " + suggestions[3])  # Bundle suggestion
        
        st.markdown("### ⏰ Timing & Operations")
        st.write("• " + suggestions[1])  # Peak day suggestion
        st.write("• " + suggestions[2])  # Staffing suggestion
        
        # Get inventory suggestions
        inventory_suggestions = analytics.get_inventory_optimization_suggestions()
        if inventory_suggestions:
            st.markdown("### 📦 Inventory Management")
            for suggestion in inventory_suggestions:
                st.write("• " + suggestion)
        
        # Get promotion effectiveness
        promo_metrics = analytics.get_promotion_effectiveness()
        if isinstance(promo_metrics, dict):
            st.markdown("### 🎯 Promotions & Marketing")
            st.write(f"• Your best promotional day was {promo_metrics['best_promo_day']} with RM{promo_metrics['highest_sales_day']:,.2f} in sales")
            st.write(f"• Promotions typically increase sales by {promo_metrics['lift_in_sales']:.1f}%")
        
        # Get customer behavior insights
        customer_insights = analytics.get_customer_behavior_insights()
        st.markdown("### 👥 Customer Insights")
        st.write(f"• Average order value: RM{customer_insights['average_order_value']:,.2f}")
        st.write(f"• Average items per order: {customer_insights['average_items_per_order']:.1f}")
        st.write("• Peak hours:")
        for hour, count in customer_insights['peak_hours'].items():
            st.write(f"  - {hour}:00: {count} orders")
        st.write("• Popular cuisines:")
        for cuisine, count in customer_insights['popular_cuisines'].items():
            st.write(f"  - {cuisine}: {count} orders")
        
        # Get profitability analysis
        profitability = analytics.get_profitability_analysis()
        st.markdown("### 💰 Profitability Insights")
        st.write("• Most profitable items:")
        for item, metrics in profitability['item_profitability'].head(3).iterrows():
            st.write(f"  - {item}: RM{metrics['total_revenue']:,.2f} revenue")
        st.write("• Most profitable categories:")
        for category, metrics in profitability['category_profitability'].head(3).iterrows():
            st.write(f"  - {category}: RM{metrics['total_revenue']:,.2f} revenue")
    
    # Handle day performance queries
    elif any(phrase in query for phrase in ["best day", "worst day", "best performing", "worst performing", "best and worst"]):
        # Get daily sales patterns
        daily_sales = (
            analytics.transaction_data.groupby(
                analytics.transaction_data['order_time'].dt.day_name()
            )['order_value'].agg(['sum', 'count']).rename(columns={'sum': 'revenue', 'count': 'orders'})
        )
        
        # Sort by revenue to get best and worst days
        daily_sales = daily_sales.sort_values('revenue', ascending=False)
        
        st.markdown("**📊 Day Performance Analysis:**")
        
        # Show best performing day
        best_day = daily_sales.index[0]
        st.markdown(f"### 🏆 Best Performing Day: {best_day}")
        st.write(f"• Total Revenue: RM{daily_sales.loc[best_day, 'revenue']:,.2f}")
        st.write(f"• Number of Orders: {daily_sales.loc[best_day, 'orders']:,}")
        st.write(f"• Average Order Value: RM{daily_sales.loc[best_day, 'revenue']/daily_sales.loc[best_day, 'orders']:,.2f}")
        
        # Show worst performing day
        worst_day = daily_sales.index[-1]
        st.markdown(f"### 📉 Worst Performing Day: {worst_day}")
        st.write(f"• Total Revenue: RM{daily_sales.loc[worst_day, 'revenue']:,.2f}")
        st.write(f"• Number of Orders: {daily_sales.loc[worst_day, 'orders']:,}")
        st.write(f"• Average Order Value: RM{daily_sales.loc[worst_day, 'revenue']/daily_sales.loc[worst_day, 'orders']:,.2f}")
        
        # Show day-by-day breakdown
        st.markdown("### 📈 Daily Performance Breakdown")
        for day in daily_sales.index:
            revenue = daily_sales.loc[day, 'revenue']
            orders = daily_sales.loc[day, 'orders']
            avg_order = revenue / orders if orders > 0 else 0
            st.write(f"• {day}: RM{revenue:,.2f} ({orders:,} orders, avg: RM{avg_order:,.2f})")
        
        return
    
    # Handle customer behavior queries
    elif any(phrase in query for phrase in ["peak hours", "busiest hours", "busy times", "rush hours"]):
        customer_insights = analytics.get_customer_behavior_insights()
        
        st.markdown("**⏰ Peak Hours Analysis:**")
        
        # Get peak hours data
        peak_hours = customer_insights['peak_hours']
        total_orders = customer_insights['total_orders']
        
        if not peak_hours:
            st.warning("No peak hours data available")
            return
        
        # Format hours for display
        st.markdown("### 🏆 Top 3 Busiest Hours")
        for hour, count in peak_hours.items():
            # Convert 24-hour format to 12-hour format with AM/PM
            hour_12 = hour % 12
            if hour_12 == 0:
                hour_12 = 12
            period = "AM" if hour < 12 else "PM"
            percentage = (count / total_orders * 100) if total_orders > 0 else 0
            st.write(f"• {hour_12}:00 {period}: {count:,} orders ({percentage:.1f}% of total orders)")
        
        # Add recommendations based on peak hours
        st.markdown("### 💡 Recommendations")
        busiest_hour = max(peak_hours.items(), key=lambda x: x[1])[0]
        hour_12 = busiest_hour % 12
        if hour_12 == 0:
            hour_12 = 12
        period = "AM" if busiest_hour < 12 else "PM"
        
        st.write(f"• Consider increasing staff during {hour_12}:00 {period} to handle peak demand")
        st.write("• Schedule promotions during off-peak hours to boost sales")
        st.write("• Review inventory levels before peak hours to ensure stock availability")
        
        return
    
    # Handle cuisine-related queries
    elif any(phrase in query for phrase in ["popular cuisines", "most popular cuisines", "cuisine preferences", "favorite cuisines"]):
        customer_insights = analytics.get_customer_behavior_insights()
        
        st.markdown("**🍽️ Popular Cuisines Analysis:**")
        
        # Get popular cuisines data
        popular_cuisines = customer_insights['popular_cuisines']
        total_orders = customer_insights['total_orders']
        
        if not popular_cuisines:
            st.warning("No cuisine data available")
            return
        
        # Format cuisines for display
        st.markdown("### 🏆 Top 3 Popular Cuisines")
        for cuisine, count in popular_cuisines.items():
            percentage = (count / total_orders * 100) if total_orders > 0 else 0
            st.write(f"• {cuisine}: {count:,} orders ({percentage:.1f}% of total orders)")
        
        # Add recommendations based on popular cuisines
        st.markdown("### 💡 Recommendations")
        st.write("• Consider promoting your most popular cuisine items during peak hours")
        st.write("• Create special bundles or combos featuring your top cuisines")
        st.write("• Use popular cuisines as a basis for seasonal menu planning")
        
        return
    
    else:
        st.write("I can help you with:")
        st.markdown("""
        - Sales information and trends
        - Inventory and stock levels
        - Business tips and suggestions
        
        Try asking about any of these topics!
        """)

# Streamlit UI
st.set_page_config(page_title="MEX Assistant", page_icon="=")
st.title("MEX Assistant - AI Business Assistant")
st.write("Hi there!! Ask me about your sales, stock or tips to improve your business.")

# Add sidebar for merchant selection
merchant_id = st.sidebar.selectbox(
    "Select Merchant",
    options=data["merchant"]["merchant_id"].unique(),
    format_func=lambda x: f"Merchant {x}"
)

# Add date selection with quick buttons
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Today"):
        date_param = datetime.now().strftime("%Y-%m-%d")
    else:
        date_param = None
with col2:
    if st.button("Yesterday"):
        date_param = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        date_param = None

# Add date input
selected_date = st.sidebar.date_input(
    "Select Date",
    value=date_param if date_param else None,
    min_value=None,
    max_value=None,
    key=None
)

# Add help section
with st.expander("💡 What can I ask?"):
    st.markdown("""
    ### Sales Information
    - "Show me today's sales"
    - "What were the sales yesterday?"
    - "How much did we make this week?"
    - "What are our top selling items?"
    - "Show me sales trends"
    - "What were the sales for 2023?"
    - "Compare today's sales with yesterday"
    - "What's our average order value?"
    - "What's our total revenue?"
    - "Show me our best and worst performing days"
    
    ### Customer Behavior
    - "What are our customer behavior patterns?"
    - "What are our peak hours?"
    - "What are our most popular cuisines?"
    - "What's our average order value?"
    - "How many items do customers typically order?"
    
    ### Profitability Analysis
    - "Which items are most profitable?"
    - "What are our most profitable categories?"
    - "Show me item profitability"
    - "Show me category profitability"
    - "What's our revenue by item?"
    
    ### Inventory Management
    - "What items are running low?"
    - "Show me inventory alerts"
    - "Which items need restocking?"
    - "Check my stock levels"
    - "What are our inventory optimization suggestions?"
    
    ### Promotions & Marketing
    - "How effective are our promotions?"
    - "What's our promotion performance?"
    - "Show me our best promotional days"
    - "What's our sales lift from promotions?"
    
    ### Seasonal Trends
    - "What are our seasonal trends?"
    - "Show me monthly trends"
    - "What are our weekday patterns?"
    - "What's our best performing month?"
    
    ### Business Tips
    - "Give me some business tips"
    - "What suggestions do you have?"
    - "How can I improve my business?"
    - "What promotions should I run?"
    
    ### General
    - "Hello" / "Hi" - Get a greeting
    - "Help" - Show this help menu
    - "What can you do?" - List capabilities
    
    You can also combine these queries, for example:
    - "Show me today's sales and top items"
    - "What are our best selling items and their profitability?"
    """)

# Get user query
query = st.text_input("Ask me something:")

if query:
    # Convert date to string if selected
    date_param = selected_date.strftime("%Y-%m-%d") if selected_date else None
    
    # Process the query
    process_query(query.lower().strip(), merchant_id, date_param)