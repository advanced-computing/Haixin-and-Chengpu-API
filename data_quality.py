"""
Data quality check functions for NYC Film Permits dataset.
Each function takes a DataFrame and returns True if the check passes.
"""

import pandas as pd


def check_no_duplicate_event_ids(df):
    """Check that EventID is unique — no duplicate rows."""
    return df["EventID"].duplicated().sum() == 0


def check_borough_values_valid(df):
    """Check that Borough only contains the 5 valid NYC boroughs."""
    valid = {"Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"}
    actual = set(df["Borough"].dropna().unique())
    return actual.issubset(valid)


def check_missing_rate_below_threshold(df, threshold=0.15):
    """Check that no column has more than 15% missing values."""
    for col in df.columns:
        if df[col].isnull().mean() > threshold:
            return False
    return True
