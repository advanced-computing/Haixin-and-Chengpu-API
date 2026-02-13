import pandas as pd
from flask import Flask, Response, request

app = Flask(__name__)

df = pd.read_csv("data.csv")
ID_COLUMN = "EventID"


@app.route("/permits", methods=["GET"])
def list_permits():
    """List all film permits with optional filtering, pagination, and format selection."""
    result = df.copy()

    # Filter by any column
    for col in df.columns:
        value = request.args.get(col)
        if value is not None:
            result = result[result[col].astype(str) == value]

    # Pagination
    limit = request.args.get("limit", default=None, type=int)
    offset = request.args.get("offset", default=0, type=int)
    result = result.iloc[offset:]
    if limit is not None:
        result = result.iloc[:limit]

    # Output format
    output_format = request.args.get("format", default="json")
    if output_format == "csv":
        return Response(result.to_csv(index=False), mimetype="text/csv")
    else:
        return Response(
            result.to_json(orient="records", indent=2),
            mimetype="application/json",
        )


@app.route("/permits/<int:event_id>", methods=["GET"])
def get_permit(event_id):
    """Retrieve a single permit by EventID."""
    match = df[df[ID_COLUMN] == event_id]

    if match.empty:
        return Response(
            '{"error": "Permit not found"}',
            status=404,
            mimetype="application/json",
        )

    output_format = request.args.get("format", default="json")
    if output_format == "csv":
        return Response(match.to_csv(index=False), mimetype="text/csv")
    else:
        return Response(
            match.to_json(orient="records", indent=2),
            mimetype="application/json",
        )


@app.route("/columns", methods=["GET"])
def list_columns():
    """List all available column names."""
    return {"columns": list(df.columns)}


@app.route("/stats", methods=["GET"])
def get_stats():
    """Return basic statistics about the dataset."""
    return {
        "total_records": len(df),
        "columns": list(df.columns),
        "boroughs": df["Borough"].dropna().unique().tolist(),
        "categories": df["Category"].dropna().unique().tolist(),
    }


if __name__ == "__main__":
    app.run(debug=True)
