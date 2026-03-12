import duckdb

# Connect to persistent database file (creates it if it doesn't exist)
con = duckdb.connect("permits.db")

# Load CSV data into permits table
con.execute("""
    CREATE OR REPLACE TABLE permits AS
    SELECT * FROM read_csv_auto('data.csv')
""")

# Create users table
con.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username VARCHAR,
        age INTEGER,
        country VARCHAR
    )
""")

# Verify
count = con.execute("SELECT COUNT(*) FROM permits").fetchone()[0]
print(f"✅ Loaded {count} rows into permits table.")
print("✅ Users table ready.")

con.close()
