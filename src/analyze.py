import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# CONFIGURATION - No hardcoded file paths in the logic
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG = {
    'RAW_DIR': BASE_DIR / 'data' / 'raw',
    'PROCESSED_DIR': BASE_DIR / 'data' / 'processed',
    'REQUIRED_FILES': {
        'customers': 'customers_clean.csv',
        'orders': 'orders_clean.csv',
        'products': 'products.csv'
    },
    'OUTPUT_FILES': {
        'monthly_revenue': 'monthly_revenue.csv',
        'top_customers': 'top_customers.csv',
        'category_performance': 'category_performance.csv',
        'regional_analysis': 'regional_analysis.csv'
    }
}

def load_data(file_path):
    """Load CSV data with error handling."""
    try:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        df = pd.read_csv(file_path)
        if df.empty:
            raise pd.errors.EmptyDataError(f"The file is empty: {file_path}")
        return df
    except FileNotFoundError as e:
        logging.error(f"Missing file: {e}")
        return None
    except pd.errors.EmptyDataError as e:
        logging.warning(f"Empty data: {e}")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"Unexpected error loading {file_path.name}: {e}")
        return None

def perform_analysis():
    """Main analysis pipeline."""
    # 1. Loading
    logging.info("Loading datasets...")
    cust_df = load_data(CONFIG['PROCESSED_DIR'] / CONFIG['REQUIRED_FILES']['customers'])
    orders_df = load_data(CONFIG['PROCESSED_DIR'] / CONFIG['REQUIRED_FILES']['orders'])
    products_df = load_data(CONFIG['RAW_DIR'] / CONFIG['REQUIRED_FILES']['products'])

    if cust_df is None or orders_df is None or products_df is None:
        logging.error("Failed to load required datasets. Aborting analysis.")
        return

    # Ensure dates are datetime objects
    cust_df['signup_date'] = pd.to_datetime(cust_df['signup_date'])
    orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])

    # 2. Merging
    logging.info("Merging datasets...")
    # Explicit left-join orders onto customers
    orders_with_customers = cust_df.merge(orders_df, on='customer_id', how='left')
    
    # Explicit left-join products onto orders_with_customers
    full_data = orders_with_customers.merge(products_df, left_on='product', right_on='product_id', how='left')

    # Reporting mismatches
    missing_cust_count = orders_df[~orders_df['customer_id'].isin(cust_df['customer_id'])].shape[0]
    missing_prod_count = full_data[full_data['order_id'].notna() & full_data['product_id'].isna()].shape[0]
    logging.info(f"Order rows with no matching customer: {missing_cust_count}")
    logging.info(f"Order rows with no matching product: {missing_prod_count}")

    # 3. Task 1: Monthly Revenue Trend
    logging.info("Computing Monthly Revenue Trend...")
    monthly_revenue = full_data[full_data['status'] == 'completed'] \
        .groupby('order_year_month')['amount'] \
        .sum() \
        .reset_index() \
        .rename(columns={'amount': 'total_revenue'})
    monthly_revenue.to_csv(CONFIG['PROCESSED_DIR'] / CONFIG['OUTPUT_FILES']['monthly_revenue'], index=False)

    # 4. Task 2 & 5: Top Customers and Churn Indicator
    logging.info("Identifying Top Customers and Churn status...")
    top_customers = full_data[full_data['status'] == 'completed'] \
        .groupby(['customer_id', 'name', 'region'])['amount'] \
        .sum() \
        .reset_index() \
        .rename(columns={'amount': 'total_spend'}) \
        .sort_values(by='total_spend', ascending=False) \
        .head(10)

    # Churn Flag (No completed orders in past 90 days relative to latest dataset date)
    latest_date = full_data['order_date'].max()
    churn_threshold = latest_date - timedelta(days=90)
    
    last_order_dates = full_data[full_data['status'] == 'completed'] \
        .groupby('customer_id')['order_date'] \
        .max() \
        .reset_index() \
        .rename(columns={'order_date': 'last_order_date'})
    
    last_order_dates['churned'] = last_order_dates['last_order_date'] < churn_threshold
    
    top_customers = top_customers.merge(last_order_dates[['customer_id', 'churned']], on='customer_id', how='left')
    top_customers.to_csv(CONFIG['PROCESSED_DIR'] / CONFIG['OUTPUT_FILES']['top_customers'], index=False)

    # 5. Task 3: Category Performance
    logging.info("Computing Category Performance...")
    category_perf = full_data[full_data['status'] == 'completed'] \
        .groupby('category')['amount'] \
        .agg(['sum', 'mean', 'count']) \
        .reset_index() \
        .rename(columns={'sum': 'total_revenue', 'mean': 'avg_order_value', 'count': 'order_count'})
    category_perf.to_csv(CONFIG['PROCESSED_DIR'] / CONFIG['OUTPUT_FILES']['category_performance'], index=False)

    # 6. Task 4: Regional Analysis
    logging.info("Computing Regional Analysis...")
    regional_analysis = full_data[full_data['status'] == 'completed'] \
        .groupby('region') \
        .agg({
            'customer_id': 'nunique', 
            'order_id': 'count', 
            'amount': 'sum'
        }) \
        .reset_index() \
        .rename(columns={'customer_id': 'customer_count', 'order_id': 'order_count', 'amount': 'total_revenue'})
    
    regional_analysis['revenue_per_customer'] = regional_analysis['total_revenue'] / regional_analysis['customer_count']
    regional_analysis.to_csv(CONFIG['PROCESSED_DIR'] / CONFIG['OUTPUT_FILES']['regional_analysis'], index=False)

    logging.info("Analysis complete. Results saved to the data folder.")

if __name__ == "__main__":
    perform_analysis()
