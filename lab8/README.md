# Lab 8 CPI Loading

This directory contains a standalone implementation for Lab 8 using DuckDB and CPI vintages from the Philadelphia Fed.

## Files

- `cpi_lab.py`: core functions, CLI, and benchmark helpers
- `benchmark_lab8.py`: small wrapper to print benchmark output
- `test_cpi_lab.py`: automated checks for `get_latest_data` and the simplified workflow
- `notebooks/lab8_simulation.ipynb`: notebook showing initialization, updates, comparison, and benchmark output
- `data/PCPI24M1.csv`: January 2024 snapshot
- `data/PCPI25M2.csv`: February 2025 snapshot
- `lab8.duckdb`: persistent database created by the scripts

## Setup

From the repo root:

```bash
python3 -m pip install -r requirements.txt
python3 lab8/cpi_lab.py generate-snapshots
```

## Simplified workflow

Initialize the database from the January 2024 snapshot:

```bash
python3 lab8/cpi_lab.py init-simplified
python3 lab8/cpi_lab.py summary
```

Expected result after initialization:

- `cpi_append`, `cpi_trunc`, and `cpi_inc` all contain the same rows.
- Each table should start at `1947-01-01` and end at `2024-01-01`.

Update each table from the February 2025 snapshot:

```bash
python3 lab8/cpi_lab.py update-simplified --method append
python3 lab8/cpi_lab.py update-simplified --method trunc
python3 lab8/cpi_lab.py update-simplified --method inc
python3 lab8/cpi_lab.py summary
```

Expected result after the updates:

- `cpi_append` keeps old values for dates that already existed, so revisions are ignored.
- `cpi_trunc` is replaced entirely with the new snapshot, so it matches `PCPI25M2.csv`.
- `cpi_inc` updates revised rows and inserts new dates, so it also matches `PCPI25M2.csv`.

## Manual testing

1. Run `python3 lab8/cpi_lab.py init-simplified`.
2. Check the initial table counts with `python3 lab8/cpi_lab.py summary`.
3. Run one update method at a time.
4. Inspect sample rows in DuckDB:

```bash
python3 - <<'PY'
import duckdb
con = duckdb.connect("lab8/lab8.duckdb")
for table in ("cpi_append", "cpi_trunc", "cpi_inc"):
    print(f"\n{table}")
    print(con.execute(
        f"SELECT * FROM {table} WHERE dates BETWEEN DATE '2019-01-01' AND DATE '2025-02-01' ORDER BY dates DESC LIMIT 8"
    ).fetchdf())
con.close()
PY
```

What you should see:

- `cpi_append` may differ from the other two tables on historically revised dates.
- `cpi_trunc` and `cpi_inc` should agree row-for-row after the simplified update.

## Full pull-date workflow

You can also load the latest available vintage for an arbitrary `pull_date`:

```bash
python3 lab8/cpi_lab.py load-pull-date --method append --pull-date 2004-01-15
python3 lab8/cpi_lab.py load-pull-date --method trunc --pull-date 2004-01-15
python3 lab8/cpi_lab.py load-pull-date --method inc --pull-date 2004-01-15
```

For `pull_date=2004-01-15`, `get_latest_data` uses vintage `PCPI04M1`.

## Benchmark

Run the daily simulation from `2024-01-01` to `2025-02-28`:

```bash
python3 lab8/cpi_lab.py benchmark
```

Interpretation:

- `append` is fast and simple, but inconsistent when revisions happen.
- `trunc` is consistent, but it rewrites the full table every time.
- `inc` keeps consistency while updating only changed or new rows, so it is usually the best operational choice for revised time-series data.
