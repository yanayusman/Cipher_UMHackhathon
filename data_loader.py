import pandas as pd

def load_data():
    transaction_data = pd.read_csv("transaction_data.csv")
    transaction_items = pd.read_csv("transaction_items.csv")
    merchant = pd.read_csv("merchant.csv")
    items = pd.read_csv("items.csv")
    keywords = pd.read_csv("keywords.csv")
    return {
        "transaction_data" : transaction_data, 
        "transaction_items" : transaction_items, 
        "merchant" : merchant, 
        "items" : items, 
        "keywords" : keywords
    }
