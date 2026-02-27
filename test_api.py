"""
Unit tests for NYC Film Permits Flask API
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# Point app.py to the real data.csv
os.chdir(os.path.dirname(__file__))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ── GET /permits ──────────────────────────────────────────────────────────────

def test_list_permits_returns_200(client):
    response = client.get("/permits")
    assert response.status_code == 200


def test_list_permits_returns_json_by_default(client):
    response = client.get("/permits")
    assert response.content_type == "application/json"


def test_list_permits_limit(client):
    response = client.get("/permits?limit=5")
    data = response.get_json()
    assert len(data) == 5


def test_list_permits_offset(client):
    response_0 = client.get("/permits?limit=1&offset=0")
    response_1 = client.get("/permits?limit=1&offset=1")
    first = response_0.get_json()[0]["EventID"]
    second = response_1.get_json()[0]["EventID"]
    assert first != second


def test_list_permits_filter_by_borough(client):
    response = client.get("/permits?Borough=Manhattan&limit=10")
    data = response.get_json()
    assert all(r["Borough"] == "Manhattan" for r in data)


def test_list_permits_filter_by_category(client):
    response = client.get("/permits?Category=Film&limit=10")
    data = response.get_json()
    assert all(r["Category"] == "Film" for r in data)


def test_list_permits_csv_format(client):
    response = client.get("/permits?limit=5&format=csv")
    assert "text/csv" in response.content_type
    assert b"EventID" in response.data


def test_list_permits_invalid_filter_returns_empty(client):
    response = client.get("/permits?Borough=NARNIA")
    data = response.get_json()
    assert data == []


# ── GET /permits/<event_id> ───────────────────────────────────────────────────

def test_get_permit_valid_id(client):
    # Get a real EventID first
    first = client.get("/permits?limit=1").get_json()[0]
    event_id = first["EventID"]
    response = client.get(f"/permits/{event_id}")
    assert response.status_code == 200


def test_get_permit_returns_correct_record(client):
    first = client.get("/permits?limit=1").get_json()[0]
    event_id = first["EventID"]
    response = client.get(f"/permits/{event_id}")
    data = response.get_json()
    assert data[0]["EventID"] == event_id


def test_get_permit_not_found_returns_404(client):
    response = client.get("/permits/0000001")
    assert response.status_code == 404


def test_get_permit_404_has_error_key(client):
    response = client.get("/permits/0000001")
    data = response.get_json()
    assert "error" in data


def test_get_permit_csv_format(client):
    first = client.get("/permits?limit=1").get_json()[0]
    event_id = first["EventID"]
    response = client.get(f"/permits/{event_id}?format=csv")
    assert "text/csv" in response.content_type


# ── GET /columns ──────────────────────────────────────────────────────────────

def test_columns_returns_200(client):
    response = client.get("/columns")
    assert response.status_code == 200


def test_columns_includes_event_id(client):
    response = client.get("/columns")
    data = response.get_json()
    assert "EventID" in data["columns"]


def test_columns_includes_borough(client):
    response = client.get("/columns")
    data = response.get_json()
    assert "Borough" in data["columns"]


# ── GET /stats ────────────────────────────────────────────────────────────────

def test_stats_returns_200(client):
    response = client.get("/stats")
    assert response.status_code == 200


def test_stats_has_total_records(client):
    response = client.get("/stats")
    data = response.get_json()
    assert "total_records" in data
    assert data["total_records"] > 0


def test_stats_boroughs_are_valid(client):
    response = client.get("/stats")
    data = response.get_json()
    valid_boroughs = {"Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"}
    for b in data["boroughs"]:
        assert b in valid_boroughs


def test_stats_categories_not_empty(client):
    response = client.get("/stats")
    data = response.get_json()
    assert len(data["categories"]) > 0
