"""
Tests for data quality check functions (data_quality.py)
"""
import pytest
import pandas as pd
import os

from data_quality import (
    check_no_duplicate_event_ids,
    check_borough_values_valid,
    check_missing_rate_below_threshold,
)

DATA_PATH = os.path.join(os.path.dirname(__file__), "data.csv")


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(DATA_PATH)


# ── Test check_no_duplicate_event_ids ─────────────────────────────────────────

def test_no_duplicate_event_ids_passes(df):
    """Real data should have unique EventIDs."""
    assert check_no_duplicate_event_ids(df) is True


def test_no_duplicate_event_ids_fails_on_dupes():
    """Function should return False when duplicates exist."""
    bad_df = pd.DataFrame({"EventID": [1, 1, 2]})
    assert check_no_duplicate_event_ids(bad_df) is False


# ── Test check_borough_values_valid ───────────────────────────────────────────

def test_borough_values_valid_passes(df):
    """Real data should only contain valid NYC boroughs."""
    assert check_borough_values_valid(df) is True


def test_borough_values_valid_fails_on_bad_data():
    """Function should return False when invalid borough appears."""
    bad_df = pd.DataFrame({"Borough": ["Manhattan", "Narnia"]})
    assert check_borough_values_valid(bad_df) is False


# ── Test check_missing_rate_below_threshold ───────────────────────────────────

def test_missing_rate_passes(df):
    """No column in real data should exceed 15% missing."""
    assert check_missing_rate_below_threshold(df) is True


def test_missing_rate_fails_on_high_nulls():
    """Function should return False when a column is mostly null."""
    bad_df = pd.DataFrame({"A": [1, None, None, None, None]})
    assert check_missing_rate_below_threshold(bad_df, threshold=0.15) is False
