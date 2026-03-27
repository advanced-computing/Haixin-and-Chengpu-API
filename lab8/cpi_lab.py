from __future__ import annotations

import argparse
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = ROOT / "lab8.duckdb"
WORKBOOK_URL = (
    "https://www.philadelphiafed.org/-/media/FRBP/Assets/Surveys-And-Data/"
    "real-time-data/data-files/xlsx/pcpiMvMd.xlsx?sc_lang=en&hash=E41A743DC6423F950B10C3DE7A4F674D"
)
WORKBOOK_PATH = DATA_DIR / "pcpiMvMd.xlsx"
INITIAL_SNAPSHOT_PATH = DATA_DIR / "PCPI24M1.csv"
UPDATE_SNAPSHOT_PATH = DATA_DIR / "PCPI25M2.csv"


def ensure_workbook(workbook_path: Path = WORKBOOK_PATH) -> Path:
    workbook_path.parent.mkdir(parents=True, exist_ok=True)
    if workbook_path.exists():
        return workbook_path

    subprocess.run(
        ["curl", "-L", WORKBOOK_URL, "-o", str(workbook_path)],
        check=True,
    )
    return workbook_path


def load_source_frame(workbook_path: Path = WORKBOOK_PATH) -> pd.DataFrame:
    workbook_path = ensure_workbook(workbook_path)
    frame = pd.read_excel(workbook_path)
    frame["DATE"] = frame["DATE"].astype(str)
    return frame


def normalize_snapshot(frame: pd.DataFrame, vintage_col: str) -> pd.DataFrame:
    snapshot = frame[["DATE", vintage_col]].copy()
    snapshot.columns = ["dates", "cpi"]
    snapshot["dates"] = pd.to_datetime(snapshot["dates"].str.replace(":", "-", regex=False) + "-01")
    snapshot["cpi"] = pd.to_numeric(snapshot["cpi"], errors="coerce")
    snapshot = snapshot.dropna(subset=["cpi"]).sort_values("dates").reset_index(drop=True)
    return snapshot


def get_latest_vintage_column(pull_date: str | pd.Timestamp, columns: list[str]) -> str:
    pull_ts = pd.Timestamp(pull_date)
    vintage_map: list[tuple[pd.Timestamp, str]] = []

    for column in columns:
        if column == "DATE":
            continue

        suffix = column.removeprefix("PCPI")
        year_part, month_part = suffix.split("M")
        year = 1900 + int(year_part) if int(year_part) >= 98 else 2000 + int(year_part)
        month = int(month_part)
        vintage_map.append((pd.Timestamp(year=year, month=month, day=1), column))

    eligible = [item for item in vintage_map if item[0] <= pull_ts]
    if not eligible:
        raise ValueError(f"No CPI vintage is available for pull_date={pull_ts.date()}")

    return max(eligible, key=lambda item: item[0])[1]


def get_latest_data(
    pull_date: str | pd.Timestamp,
    source_frame: pd.DataFrame | None = None,
) -> pd.DataFrame:
    source_frame = source_frame if source_frame is not None else load_source_frame()
    vintage_col = get_latest_vintage_column(pull_date, list(source_frame.columns))
    return normalize_snapshot(source_frame, vintage_col)


def generate_snapshot_csv(vintage_col: str, output_path: Path) -> Path:
    source = load_source_frame()
    snapshot = normalize_snapshot(source, vintage_col)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot.to_csv(output_path, index=False)
    return output_path


def ensure_snapshots() -> None:
    generate_snapshot_csv("PCPI24M1", INITIAL_SNAPSHOT_PATH)
    generate_snapshot_csv("PCPI25M2", UPDATE_SNAPSHOT_PATH)


def get_con(db_path: Path = DB_PATH) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(db_path))


def create_tables(con: duckdb.DuckDBPyConnection) -> None:
    for table_name in ("cpi_append", "cpi_trunc", "cpi_inc"):
        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                dates DATE PRIMARY KEY,
                cpi DOUBLE
            )
            """
        )


def load_append(con: duckdb.DuckDBPyConnection, frame: pd.DataFrame) -> None:
    con.register("incoming_append", frame)
    con.execute(
        """
        INSERT INTO cpi_append
        SELECT incoming_append.dates, incoming_append.cpi
        FROM incoming_append
        LEFT JOIN cpi_append USING (dates)
        WHERE cpi_append.dates IS NULL
        """
    )
    con.unregister("incoming_append")


def load_trunc(con: duckdb.DuckDBPyConnection, frame: pd.DataFrame) -> None:
    con.execute("DELETE FROM cpi_trunc")
    con.register("incoming_trunc", frame)
    con.execute("INSERT INTO cpi_trunc SELECT * FROM incoming_trunc")
    con.unregister("incoming_trunc")


def load_incremental(con: duckdb.DuckDBPyConnection, frame: pd.DataFrame) -> None:
    con.register("incoming_inc", frame)
    con.execute(
        """
        INSERT INTO cpi_inc
        SELECT * FROM incoming_inc
        ON CONFLICT (dates) DO UPDATE SET cpi = EXCLUDED.cpi
        """
    )
    con.unregister("incoming_inc")


def initialize_from_snapshot(db_path: Path = DB_PATH) -> None:
    ensure_snapshots()
    con = get_con(db_path)
    create_tables(con)
    initial = pd.read_csv(INITIAL_SNAPSHOT_PATH, parse_dates=["dates"])
    for table_name in ("cpi_append", "cpi_trunc", "cpi_inc"):
        con.execute(f"DELETE FROM {table_name}")
        con.register("initial_snapshot", initial)
        con.execute(f"INSERT INTO {table_name} SELECT * FROM initial_snapshot")
        con.unregister("initial_snapshot")
    con.close()


def update_from_snapshot(method: str, db_path: Path = DB_PATH) -> None:
    ensure_snapshots()
    con = get_con(db_path)
    create_tables(con)
    update_frame = pd.read_csv(UPDATE_SNAPSHOT_PATH, parse_dates=["dates"])

    loaders = {
        "append": load_append,
        "trunc": load_trunc,
        "inc": load_incremental,
    }
    loaders[method](con, update_frame)
    con.close()


def load_from_pull_date(method: str, pull_date: str, db_path: Path = DB_PATH) -> None:
    con = get_con(db_path)
    create_tables(con)
    latest = get_latest_data(pull_date)

    loaders = {
        "append": load_append,
        "trunc": load_trunc,
        "inc": load_incremental,
    }
    loaders[method](con, latest)
    con.close()


@dataclass
class BenchmarkResult:
    method: str
    seconds: float
    row_count: int
    revised_rows_vs_truth: int


def benchmark_daily_range(
    start: str = "2024-01-01",
    end: str = "2025-02-28",
) -> list[BenchmarkResult]:
    benchmark_db = ROOT / "benchmark.duckdb"
    if benchmark_db.exists():
        benchmark_db.unlink()

    source = load_source_frame()
    truth = get_latest_data(end, source).rename(columns={"cpi": "truth_cpi"})
    pull_dates = pd.date_range(start=start, end=end, freq="D")
    results: list[BenchmarkResult] = []

    for method in ("append", "trunc", "inc"):
        con = get_con(benchmark_db)
        create_tables(con)
        con.execute(f"DELETE FROM cpi_{method}")
        started = time.perf_counter()
        for pull_date in pull_dates:
            latest = get_latest_data(pull_date, source)
            if method == "append":
                load_append(con, latest)
            elif method == "trunc":
                load_trunc(con, latest)
            else:
                load_incremental(con, latest)
        seconds = time.perf_counter() - started

        table_name = f"cpi_{method}"
        final_frame = con.execute(f"SELECT * FROM {table_name} ORDER BY dates").fetchdf()
        row_count = len(final_frame)
        revised_rows = (
            final_frame.merge(truth, on="dates", how="outer")
            .assign(
                mismatch=lambda df: (
                    df["cpi"].round(6) != df["truth_cpi"].round(6)
                )
                & ~(df["cpi"].isna() & df["truth_cpi"].isna())
            )["mismatch"]
            .sum()
        )
        results.append(
            BenchmarkResult(
                method=method,
                seconds=seconds,
                row_count=row_count,
                revised_rows_vs_truth=int(revised_rows),
            )
        )
        con.close()

    return results


def summarize_tables(db_path: Path = DB_PATH) -> pd.DataFrame:
    con = get_con(db_path)
    rows = []
    for table_name in ("cpi_append", "cpi_trunc", "cpi_inc"):
        count, min_date, max_date = con.execute(
            f"SELECT COUNT(*), MIN(dates), MAX(dates) FROM {table_name}"
        ).fetchone()
        rows.append(
            {
                "table_name": table_name,
                "row_count": count,
                "min_date": min_date,
                "max_date": max_date,
            }
        )
    con.close()
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab 8 CPI loading helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("generate-snapshots")
    subparsers.add_parser("init-simplified")

    update_parser = subparsers.add_parser("update-simplified")
    update_parser.add_argument("--method", choices=["append", "trunc", "inc"], required=True)

    pull_parser = subparsers.add_parser("load-pull-date")
    pull_parser.add_argument("--method", choices=["append", "trunc", "inc"], required=True)
    pull_parser.add_argument("--pull-date", required=True)

    subparsers.add_parser("summary")
    subparsers.add_parser("benchmark")

    args = parser.parse_args()

    if args.command == "generate-snapshots":
        ensure_snapshots()
        print(f"Wrote {INITIAL_SNAPSHOT_PATH}")
        print(f"Wrote {UPDATE_SNAPSHOT_PATH}")
    elif args.command == "init-simplified":
        initialize_from_snapshot()
        print("Initialized cpi_append, cpi_trunc, cpi_inc from PCPI24M1.csv")
    elif args.command == "update-simplified":
        update_from_snapshot(args.method)
        print(f"Updated cpi_{args.method} from PCPI25M2.csv")
    elif args.command == "load-pull-date":
        load_from_pull_date(args.method, args.pull_date)
        print(f"Loaded cpi_{args.method} for pull_date={args.pull_date}")
    elif args.command == "summary":
        print(summarize_tables().to_string(index=False))
    elif args.command == "benchmark":
        print(pd.DataFrame(benchmark_daily_range()).to_string(index=False))


if __name__ == "__main__":
    main()
