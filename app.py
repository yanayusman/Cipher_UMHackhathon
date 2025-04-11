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

# Initialize BusinessAnalytics
analytics = BusinessAnalytics()

# Load data once at startup
data = load_data()

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
        date_str = datetime.now().date()
    else:
        date_str = None
with col2:
    if st.button("Yesterday"):
        date_str = (datetime.now() - timedelta(days=1)).date()
    else:
        date_str = None

# Add date input
selected_date = st.sidebar.date_input(
    "Select Date",
    value=date_str if date_str else None,
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
    
    ### Inventory/Stock
    - "What items are running low?"
    - "Show me inventory alerts"
    - "Which items need restocking?"
    - "Check my stock levels"
    
    ### Business Tips
    - "Give me some business tips"
    - "What suggestions do you have?"
    - "How can I improve my business?"
    - "What promotions should I run?"
    """)

query = st.text_input("Ask me something:")

if query:
    query = query.lower()
    
    # Convert date to string if selected
    date_param = selected_date.strftime("%Y-%m-%d") if selected_date else None

    # Check for sales-related queries
    sales_keywords = [
        "sales", "how much", "revenue", "earnings", "income",
        "top selling", "best selling", "popular items", "most sold",
        "what's selling", "what sells", "selling well", "trends"
    ]
    
    if any(keyword in query for keyword in sales_keywords):
        # Handle year-specific queries
        if "2023" in query or "year" in query:
            st.markdown("**Yearly Sales Summary (2023):**")
            yearly_data = analytics.get_yearly_sales(2023)
            
            if isinstance(yearly_data, dict):
                st.markdown(f"""
                • Total Sales: RM{yearly_data['total_sales']:,.2f}
                • Total Orders: {yearly_data['total_orders']:,}
                • Average Order Value: RM{yearly_data['average_order_value']:,.2f}
                • Year-over-Year Growth: {yearly_data['year_over_year_growth']:+.1f}%
                • Best Month: {yearly_data['best_month']}
                • Worst Month: {yearly_data['worst_month']}
                """)
                
                # Display monthly breakdown
                st.markdown("**Monthly Breakdown:**")
                monthly_data = yearly_data['monthly_breakdown']
                for month, data in monthly_data.iterrows():
                    st.write(f"Month {month}: RM{data[('order_value', 'sum')]:,.2f} ({data[('order_id', 'nunique')]} orders)")
            else:
                st.warning(yearly_data)
        
        # Handle "yesterday" in query
        elif "yesterday" in query and not date_param:
            date_param = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
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
        else:
            # For general sales queries
            st.success(get_daily_sales_summary(date_param))
            top_items = get_top_selling_items(date_str=date_param)
            st.markdown("**Top Selling Items:**")
            for item in top_items:
                st.info(item)
            
            # Show sales trends
            trends = get_sales_trends()
            st.markdown("**Sales Trends:**")
            st.write(f"Growth Rate: {trends['growth_rate']:.2f}%")
            st.write(f"Best Day: {trends['best_day']}")
            st.write(f"Worst Day: {trends['worst_day']}")

    elif any(word in query for word in ["stock", "inventory", "low", "running out", "restock"]):
        st.markdown("**Low Stock Alerts:**")
        alerts = get_low_stock_alerts(data, merchant_id=merchant_id)
        if alerts:
            # Sort alerts by how far below average they are
            alerts.sort(key=lambda x: x['below_avg'], reverse=True)
            
            # Display summary
            st.warning(f"⚠️ Found {len(alerts)} items with low sales frequency")
            
            # Display each alert
            for alert in alerts:
                st.markdown(f"""
                **{alert['item_name']}**  
                • Sales Count: {alert['sales_count']}  
                • {alert['below_avg']:.1f}% below average  
                • Item ID: {alert['item_id']}
                """)
            
            # Add suggestion
            st.info("💡 Consider reviewing these items for potential restocking or promotional opportunities")
        else:
            st.success("✅ No low stock alerts at this time. All items are selling well!")

    elif any(word in query for word in ["tip", "suggest", "advice", "help", "improve", "promotion"]):
        # Get merchant type and business size from merchant data
        merchant_info = data["merchant"][data["merchant"]["merchant_id"] == merchant_id].iloc[0]
        merchant_type = merchant_info.get("merchant_type", "General")
        business_size = merchant_info.get("business_size", "Medium")
        
        tips = get_simple_suggestion(merchant_type, business_size)
        st.markdown("**Here are some tips for you:**")
        for tip in tips:
            st.info(tip)

    else:
        st.write("I can help you with:")
        st.markdown("""
        - Sales information and trends
        - Inventory and stock levels
        - Business tips and suggestions
        
        Try asking about any of these topics!
        """)