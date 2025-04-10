from data_loader import load_data
import pandas as pd

data = load_data()
items = data["items"]
transaction_data = data["transaction_data"]
transaction_items = data["transaction_items"]

# merge items and transaction_items for next operation
merged_data = transaction_items.merge(items, on = "item_id", how = "left")

print(transaction_data.columns)  # To check if 'order_value' exists
print(transaction_data.head())  # To see the first few rows and ensure the data is correct



# return total order value and number of orders for a given date
def get_daily_sales_summary():
    # Ensure 'order_time' is a datetime object
    transaction_data["order_time"] = pd.to_datetime(transaction_data["order_time"])

    # Strip any whitespace from column names
    transaction_data.columns = transaction_data.columns.str.strip()

    # Filter the data by the date
    date_str = "2023-11-07"  # Test with a known date
    filtered = transaction_data[transaction_data["order_time"].dt.strftime("%Y-%m-%d") == date_str]

    # Check if filtered DataFrame is empty
    if filtered.empty:
        print(f"No data found for {date_str}")
        return None

    # Ensure 'order_value' column exists and has no NaN values
    if "order_value" not in filtered.columns:
        print("Column 'order_value' is missing!")
        return None

    # Drop NaN values in 'order_value' column
    filtered = filtered.dropna(subset=["order_value"])

    # Check if 'order_value' is numeric
    filtered["order_value"] = pd.to_numeric(filtered["order_value"], errors='coerce')

    # Calculate total sales
    total_sales = filtered["order_value"].sum()
    num_orders = filtered.shape[0]
    return f"You made RM{total_sales: .2f} on {date_str} from {num_orders} orders."

# Run the function and display the result
print(get_daily_sales_summary())

# return top-selling item names based on quantity sold
def get_top_selling_items(top_n = 3, date_str = "2023-11-07"):
    merged_date = merged_data.merge(transaction_data[["order_id", "order_time"]], on = "order_id")
    merged_date["order_date"] = merged_date["order_time"].dt.strftime("%Y-%m-%d")
    filtered = merged_date[merged_date["order_date"] == date_str]

    top_items = (
        filtered.groupby("item_name")["item_id"]
        .count()
        .sort_values(ascending = False)
        .head(top_n)
    )
    return [f"{item}: {count} sold" for item, count in top_items.items()]

# simulated alerts : items ordered more than threshold are considered low 
def get_low_stock_alerts(threshold = 5):
    item_counts = merged_data["item_name"].value_counts()
    alerts = [
        f"⚠️ {item} is running low (ordered {count} times)"
        for item, count in item_counts.items()
        if count >= threshold
    ]
    return alerts or ["All stock level looks great."]

# suggestion
def get_simple_suggestion():
    return [
        "Try offering bundle deals on bestsellers.",
        "Nearby cafes often do weekend promos - want to try one?",
        "Afternoon drinks sell more - consider a 2-5 PM promo!!"
    ]