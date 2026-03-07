import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add src to the python path so we can cleanly import from it
sys.path.append(str(Path(__file__).parent.parent))

from src.clean_data import custom_date_parser, clean_customers, clean_orders

def test_custom_date_parser():
    """Test the custom date parser with various formats."""
    # Standard format
    assert custom_date_parser("2023-10-15") == pd.Timestamp("2023-10-15")
    # DD/MM/YYYY
    assert custom_date_parser("15/10/2023") == pd.Timestamp("2023-10-15")
    # MM-DD-YYYY
    assert custom_date_parser("10-15-2023") == pd.Timestamp("2023-10-15")
    # Text format
    assert custom_date_parser("Oct 15, 2023") == pd.Timestamp("2023-10-15")
    
    # Missing / empty values
    assert pd.isna(custom_date_parser(""))
    assert pd.isna(custom_date_parser(np.nan))
    
    # Invalid format should coerce to NaT
    assert pd.isna(custom_date_parser("invalid-date"))

def test_clean_customers():
    """Test customer data cleaning (deduplication, email validation, missing regions)."""
    data = {
        'customer_id': [1, 1, 2, 3],
        'signup_date': ['2023-01-01', '2023-06-01', '2023-02-01', '2023-03-01'],
        'email': ['John@example.com', 'john@example.com', 'invalid-email', None],
        'name': [' John ', 'John', 'Jane', 'Bob'],
        'region': ['East', 'East', 'None', 'West']
    }
    df = pd.DataFrame(data)
    
    cleaned_df, dupes_removed = clean_customers(df)
    
    # Deduplication test
    assert len(cleaned_df) == 3
    assert dupes_removed == 1
    
    # Most recent signup kept
    john_record = cleaned_df[cleaned_df['customer_id'] == 1].iloc[0]
    assert john_record['signup_date'] == pd.Timestamp('2023-06-01')
    
    # Email standardization and validation
    assert john_record['email'] == 'john@example.com'
    assert john_record['is_valid_email'] == True
    assert cleaned_df[cleaned_df['customer_id'] == 2].iloc[0]['is_valid_email'] == False
    
    # Whitespace stripping
    assert john_record['name'] == 'John'
    
    # Missing region imputation
    assert cleaned_df[cleaned_df['customer_id'] == 2].iloc[0]['region'] == 'Unknown'

def test_clean_orders():
    """Test order data cleaning (amount imputation, row dropping, status normalization)."""
    data = {
        'order_id': [101, 102, None, 104, 105],
        'customer_id': [1, 2, None, 1, 3],
        'order_date': ['2023-01-15', '15/02/2023', '2023-03-01', '2023-04-10', '2023-05-20'],
        'amount': [100.0, np.nan, 50.0, 100.0, np.nan],
        'product': ['Widget A', 'Widget A', 'Widget B', 'Widget A', 'Widget B'],
        'status': ['shipped', 'PENDING', 'Done', 'canceled', 'unknown_status']
    }
    df = pd.DataFrame(data)
    
    cleaned_df, rows_dropped = clean_orders(df)
    
    # Unrecoverable row dropping
    assert len(cleaned_df) == 4
    assert rows_dropped == 1
    
    # Amount imputation (median of Widget A is 100.0)
    assert cleaned_df[cleaned_df['order_id'] == 102].iloc[0]['amount'] == 100.0
    
    # Status normalization
    assert cleaned_df[cleaned_df['order_id'] == 101].iloc[0]['status'] == 'completed'
    assert cleaned_df[cleaned_df['order_id'] == 102].iloc[0]['status'] == 'pending'
    assert cleaned_df[cleaned_df['order_id'] == 104].iloc[0]['status'] == 'cancelled'
    assert cleaned_df[cleaned_df['order_id'] == 105].iloc[0]['status'] == 'unknown_status'  # Unmapped keeps original lowercase
    
    # Year month derivation
    assert cleaned_df[cleaned_df['order_id'] == 101].iloc[0]['order_year_month'] == '2023-01'
