import pandas as pd
import numpy as np
from pathlib import Path

def custom_date_parser(date_str):
    """Parse dates supporting multiple formats."""
    if pd.isna(date_str) or date_str == '':
        return pd.NaT
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m-%d-%Y', '%b %d, %Y']:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.to_datetime(date_str, errors='coerce')

def clean_customers(df):
    """Clean customers dataframe matching notebook logic."""
    df = df.copy()
    initial_rows = len(df)
    
    # 1.1 Remove duplicates based on customer_id, keeping most recent signup_date
    df['signup_date'] = pd.to_datetime(df['signup_date'], errors='coerce')
    df = df.sort_values(by=['customer_id', 'signup_date'], ascending=[True, False])
    df = df.drop_duplicates(subset='customer_id', keep='first')
    duplicates_removed = initial_rows - len(df)
    
    # 1.2 Standardize emails
    df['email'] = df['email'].astype(str).str.lower().str.strip()
    df.loc[df['email'].isin(['nan', 'none', '']), 'email'] = ''
    df['is_valid_email'] = df['email'].apply(lambda x: isinstance(x, str) and '@' in x and '.' in x if x else False)
    
    # 1.3 Parse signup_date (format to string for CSV consistency if needed, but keeping as datetime is fine too)
    # We already converted to datetime above for sorting
    
    # 1.4 Strip whitespace
    df['name'] = df['name'].astype(str).str.strip()
    df['region'] = df['region'].astype(str).str.strip()
    
    # 1.5 Fill missing regions
    df['region'] = df['region'].replace(['None', 'nan', ''], 'Unknown')
    
    return df, duplicates_removed

def clean_orders(df):
    """Clean orders dataframe matching notebook logic."""
    df = df.copy()
    initial_rows = len(df)
    
    # 1.1 Parse order_date
    df['order_date'] = df['order_date'].apply(custom_date_parser)
    
    # 1.2 Drop unrecoverable rows (both customer_id and order_id null)
    df = df.dropna(subset=['customer_id', 'order_id'], how='all')
    rows_dropped = initial_rows - len(df)
    
    # 1.3 Impute missing amounts with median per product
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df['amount'] = df.groupby('product')['amount'].transform(lambda x: x.fillna(x.median()))
    
    # 1.4 Normalize status
    status_mapping = {
        'shipped': 'completed',
        'delivered': 'completed',
        'done': 'completed',
        'pending': 'pending',
        'cancelled': 'cancelled',
        'canceled': 'cancelled',
        'refunded': 'refunded'
    }
    df['status'] = df['status'].str.lower().str.strip().map(status_mapping).fillna(df['status'].str.lower())
    
    # 1.5 Add order_year_month
    df['order_year_month'] = df['order_date'].dt.strftime('%Y-%m')
    
    return df, rows_dropped

def print_report(name, df_before, df_after, duplicates=0, dropped=0):
    print(f"\n--- Cleaning Report: {name} ---")
    print(f"Rows Before: {len(df_before)}")
    print(f"Rows After:  {len(df_after)}")
    if duplicates: print(f"Duplicate Rows Removed: {duplicates}")
    if dropped: print(f"Unrecoverable Rows Dropped: {dropped}")
    
    print("\nNull Counts (Before vs After):")
    all_cols = sorted(list(set(df_before.columns) | set(df_after.columns)))
    null_before = df_before.isnull().sum().reindex(all_cols, fill_value='N/A')
    null_after = df_after.isnull().sum().reindex(all_cols, fill_value='N/A')
    
    report_df = pd.DataFrame({
        'Column': all_cols,
        'Nulls Before': null_before.values,
        'Nulls After': null_after.values
    })
    print(report_df.to_string(index=False))

def main():
    # Use script location for path resolution
    base_path = Path(__file__).parent
    data_dir = base_path / "data"
    
    # Load raw data
    cust_raw = pd.read_csv(data_dir / "customers.csv")
    orders_raw = pd.read_csv(data_dir / "orders.csv")
    
    # Process
    cust_clean, cust_dupes = clean_customers(cust_raw)
    orders_clean, orders_dropped = clean_orders(orders_raw)
    
    # Save
    cust_clean.to_csv(data_dir / "customers_clean.csv", index=False)
    orders_clean.to_csv(data_dir / "orders_clean.csv", index=False)
    
    # Report
    print_report("customers.csv", cust_raw, cust_clean, duplicates=cust_dupes)
    print_report("orders.csv", orders_raw, orders_clean, dropped=orders_dropped)
    
    print(f"\nCleaned files saved to {data_dir}")

if __name__ == "__main__":
    main()
