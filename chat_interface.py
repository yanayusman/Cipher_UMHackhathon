 import streamlit as st
from logic import (
    get_daily_sales_summary,
    get_top_selling_items,
    get_low_stock_alerts,
    get_simple_suggestion
)
import pandas as pd
from datetime import datetime
from helper import BusinessAnalytics

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Initialize BusinessAnalytics
analytics = BusinessAnalytics()

# Language selection
LANGUAGES = {
    'English': 'en',
    'Bahasa Melayu': 'ms',
    '中文': 'zh',
    'Tiếng Việt': 'vi',
    'ภาษาไทย': 'th'
}

# Set page config
st.set_page_config(
    page_title="MEX Assistant",
    page_icon="🤖",
    layout="wide"
)

# Sidebar for settings
with st.sidebar:
    st.title("Settings")
    selected_language = st.selectbox(
        "Select Language",
        options=list(LANGUAGES.keys()),
        index=0
    )
    
    # Merchant profile
    st.title("Merchant Profile")
    merchant_type = st.selectbox(
        "Business Type",
        options=["Restaurant", "Cafe", "Retail", "Service"]
    )
    business_size = st.selectbox(
        "Business Size",
        options=["Small", "Medium", "Large"]
    )

# Main chat interface
st.title("MEX Assistant - AI Business Assistant")
st.write("Hi there! I'm your AI business assistant. Ask me about your sales, stock, or tips to improve your business.")

# Chat history display
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask me something..."):
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    # Process the query
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get response based on query
    with st.chat_message("assistant"):
        response = process_query(prompt)
        st.write(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})

def process_query(query):
    query = query.lower()
    
    # Sales related queries
    if any(word in query for word in ["sales", "revenue", "earnings", "income", "how much"]):
        if any(word in query for word in ["week", "weekly", "trend", "growth"]):
            growth_data = analytics.get_weekly_growth_trends()
            response = f"""📈 Weekly Growth Analysis:
• Current Week Sales: RM{growth_data['current_week']['total_sales']:,.2f}
• Average Daily Sales: RM{growth_data['current_week']['avg_daily_sales']:,.2f}
• Sales Growth: {growth_data['current_week']['sales_growth']:+.1f}%
• Order Growth: {growth_data['current_week']['order_growth']:+.1f}%
• Trend: {growth_data['trend'].capitalize()}

Compared to last week:
• Sales Change: {growth_data['current_week']['total_sales'] - growth_data['previous_week']['total_sales']:+,.2f}
• Growth Rate Change: {growth_data['current_week']['sales_growth'] - growth_data['previous_week']['sales_growth']:+.1f}%"""
        else:
            sales_summary = get_daily_sales_summary()
            top_items = get_top_selling_items()
            response = f"{sales_summary}\n\n**Top Selling Items Today:**\n"
            for item in top_items:
                response += f"- {item}\n"
        return response
    
    # Inventory related queries
    elif any(word in query for word in ["stock", "inventory", "items", "running low"]):
        alerts = analytics.get_low_stock_alerts()
        response = "**Inventory Status:**\n"
        for alert in alerts:
            if isinstance(alert, dict):
                if 'status' in alert:
                    response += f"✅ {alert['message']}\n"
                else:
                    response += f"{alert['suggestion']}\n"
            else:
                response += f"{alert}\n"
        return response
    
    # Tips and suggestions
    elif any(word in query for word in ["tip", "suggest", "advice", "help", "improve"]):
        suggestions = analytics.get_personalized_suggestions(merchant_type, business_size)
        response = "**Here are some personalized tips for your business:**\n"
        for suggestion in suggestions:
            response += f"- {suggestion}\n"
        return response
    
    # Top items queries
    elif any(word in query for word in ["top", "best", "selling", "popular"]):
        top_items = analytics.get_top_3_items()
        response = "**Top 3 Items by Revenue:**\n"
        for item in top_items:
            response += f"- {item['item_name']}: {item['total_quantity']} sold (RM{item['revenue']:,.2f} revenue)\n"
        return response
    
    # Default response
    else:
        return """I can help you with:
• Sales and revenue (including weekly trends)
• Inventory and stock levels
• Top selling items
• Business tips and suggestions
• Growth analysis

Try asking something like:
- "How are my sales this week?"
- "What are my top selling items?"
- "Do I need to restock anything?"
- "Any tips to improve my business?" """ 