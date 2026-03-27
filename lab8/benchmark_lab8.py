from cpi_lab import benchmark_daily_range
import pandas as pd


if __name__ == "__main__":
    results = pd.DataFrame(benchmark_daily_range())
    print(results.to_string(index=False))
