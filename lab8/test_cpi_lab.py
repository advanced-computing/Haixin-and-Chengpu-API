from pathlib import Path

import duckdb
import pandas as pd

from cpi_lab import (
    INITIAL_SNAPSHOT_PATH,
    UPDATE_SNAPSHOT_PATH,
    ensure_snapshots,
    get_latest_data,
    initialize_from_snapshot,
    update_from_snapshot,
)


def test_get_latest_data_returns_two_columns():
    frame = get_latest_data("2024-01-15")
    assert list(frame.columns) == ["dates", "cpi"]
    assert len(frame) > 0


def test_get_latest_data_uses_latest_available_vintage():
    january = get_latest_data("2024-01-15")
    expected = pd.read_csv(INITIAL_SNAPSHOT_PATH, parse_dates=["dates"])
    pd.testing.assert_frame_equal(january.reset_index(drop=True), expected.reset_index(drop=True))


def test_simplified_update_produces_distinct_results(tmp_path: Path):
    ensure_snapshots()
    db_path = tmp_path / "lab8_test.duckdb"
    initialize_from_snapshot(db_path)

    update_from_snapshot("append", db_path)
    update_from_snapshot("trunc", db_path)
    update_from_snapshot("inc", db_path)

    con = duckdb.connect(str(db_path))
    append_df = con.execute("SELECT * FROM cpi_append ORDER BY dates").fetchdf()
    trunc_df = con.execute("SELECT * FROM cpi_trunc ORDER BY dates").fetchdf()
    inc_df = con.execute("SELECT * FROM cpi_inc ORDER BY dates").fetchdf()
    con.close()

    update_df = pd.read_csv(UPDATE_SNAPSHOT_PATH, parse_dates=["dates"])

    assert len(append_df) <= len(update_df)
    assert len(trunc_df) == len(update_df)
    assert len(inc_df) == len(update_df)
    assert not append_df.equals(update_df)
    pd.testing.assert_frame_equal(trunc_df.reset_index(drop=True), update_df.reset_index(drop=True))
    pd.testing.assert_frame_equal(inc_df.reset_index(drop=True), update_df.reset_index(drop=True))
