import duckdb
from flask import Flask, Response, request

app = Flask(__name__)
DB_PATH = "permits.db"


def get_con():
    return duckdb.connect(DB_PATH)


# ── Permits endpoints ──────────────────────────────────────────────────────────

@app.route("/permits", methods=["GET"])
def list_permits():
    """List all film permits with optional filtering, pagination, and format selection."""
    con = get_con()

    query = "SELECT * FROM permits WHERE 1=1"
    params = []

    borough = request.args.get("Borough")
    if borough:
        query += " AND Borough = ?"
        params.append(borough)

    category = request.args.get("Category")
    if category:
        query += " AND Category = ?"
        params.append(category)

    limit = request.args.get("limit", default=100, type=int)
    offset = request.args.get("offset", default=0, type=int)
    query += f" LIMIT {limit} OFFSET {offset}"

    rows = con.execute(query, params).fetchdf()
    con.close()

    output_format = request.args.get("format", default="json")
    if output_format == "csv":
        return Response(rows.to_csv(index=False), mimetype="text/csv")
    return Response(rows.to_json(orient="records", indent=2), mimetype="application/json")


@app.route("/permits/<int:event_id>", methods=["GET"])
def get_permit(event_id):
    """Retrieve a single permit by EventID."""
    con = get_con()
    rows = con.execute("SELECT * FROM permits WHERE EventID = ?", [event_id]).fetchdf()
    con.close()

    if rows.empty:
        return Response('{"error": "Permit not found"}', status=404, mimetype="application/json")

    output_format = request.args.get("format", default="json")
    if output_format == "csv":
        return Response(rows.to_csv(index=False), mimetype="text/csv")
    return Response(rows.to_json(orient="records", indent=2), mimetype="application/json")


@app.route("/stats", methods=["GET"])
def get_stats():
    """Return basic statistics about the dataset."""
    con = get_con()
    total = con.execute("SELECT COUNT(*) FROM permits").fetchone()[0]
    boroughs = con.execute("SELECT DISTINCT Borough FROM permits WHERE Borough IS NOT NULL").fetchdf()["Borough"].tolist()
    categories = con.execute("SELECT DISTINCT Category FROM permits WHERE Category IS NOT NULL").fetchdf()["Category"].tolist()
    con.close()
    return {
        "total_records": total,
        "boroughs": boroughs,
        "categories": categories,
    }


# ── Users endpoints ────────────────────────────────────────────────────────────

@app.route("/users", methods=["POST"])
def add_user():
    """Add a new user. Body: { username, age, country }"""
    data = request.get_json()
    if not data or not all(k in data for k in ("username", "age", "country")):
        return Response('{"error": "username, age, and country are required"}',
                        status=400, mimetype="application/json")

    con = get_con()
    con.execute(
        "INSERT INTO users (username, age, country) VALUES (?, ?, ?)",
        [data["username"], data["age"], data["country"]]
    )
    con.close()
    return Response('{"message": "User added successfully"}', status=201, mimetype="application/json")


@app.route("/users", methods=["GET"])
def get_users():
    """Return total users, average age, and top 3 countries by user count."""
    con = get_con()
    total = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    avg_age = con.execute("SELECT ROUND(AVG(age), 2) FROM users").fetchone()[0]
    top_countries = con.execute("""
        SELECT country, COUNT(*) as user_count
        FROM users
        GROUP BY country
        ORDER BY user_count DESC
        LIMIT 3
    """).fetchdf().to_dict(orient="records")
    con.close()
    return {
        "total_users": total,
        "average_age": avg_age,
        "top_3_countries": top_countries,
    }


if __name__ == "__main__":
    app.run(debug=True)
