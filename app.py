import streamlit as st
from logic import(
    get_daily_sales_summary,
    get_top_selling_items,
    get_low_stock_alerts,
    get_simple_suggestion
)

st.set_page_config(page_title = "MEX Assistant", page_icon = "=")
st.title("MEX Assistant - AI Business Assistant")
st.write("Hi there!! Ask me about your sales, stock or tips to improve your business.")

query = st.text_input("Ask me something:")

if query:
    query = query.lower()

    if "sales" in query or "how much" in query:
        st.success(get_daily_sales_summary())
        top_items = get_top_selling_items()
        st.markdown("**Top Selling Items Today: **")
        for item in top_items:
            st.info(item)

    elif "stock" in query or "inventory" in query:
        st.markdown("**Low Stock Alerts:**")
        alerts = get_low_stock_alerts()
        for alert in alerts:
            st.warning(alert)

    elif "tip" in query or "suggest" in query:
        tips = get_simple_suggestion()
        st.markdown("**Here are some tips for you:**")
        for tip in tips:
            st.info(tip)

    else:
        st.write("I'm still learning. Try asking about 'sales', 'stock' or 'tips'.")