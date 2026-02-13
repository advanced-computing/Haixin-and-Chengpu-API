# NYC Film Permits API

A Flask API for querying NYC film permit data from [NYC Open Data](https://data.cityofnewyork.us/City-Government/Film-Permits/tg4x-b46p).

## Setup

```bash
pip install -r requirements.txt
python app.py
```

The server runs at `http://127.0.0.1:5000`.

## Endpoints

### List permits

```
GET /permits
```

**Parameters:**

| Parameter    | Type   | Description                             |
| ------------ | ------ | --------------------------------------- |
| format       | string | `json` (default) or `csv`               |
| limit        | int    | Max number of records to return         |
| offset       | int    | Number of records to skip (default: 0)  |
| Borough      | string | Filter by borough (e.g., `Manhattan`)   |
| Category     | string | Filter by category (e.g., `Television`) |
| EventType    | string | Filter by event type                    |
| [any column] | string | Filter by any column value              |

**Examples:**

```
GET /permits?format=json&limit=5
GET /permits?Borough=Manhattan&limit=3
GET /permits?Category=Television&format=csv
GET /permits?limit=10&offset=20
```

**Sample JSON output:**

```json
[
  {
    "EventID": 749992,
    "EventType": "Theater Load in and Load Outs",
    "StartDateTime": "09/21/2023 12:01:00 PM",
    "EndDateTime": "09/23/2023 06:00:00 AM",
    "Borough": "Brooklyn",
    "Category": "Theater",
    "SubCategoryName": "Theater"
  }
]
```

### Get a single permit

```
GET /permits/<EventID>
```

**Example:**

```
GET /permits/749992
```

Returns 404 if not found.

### List columns

```
GET /columns
```

Returns all available column names for filtering.

### Dataset statistics

```
GET /stats
```

Returns total record count, column names, and unique boroughs/categories.

## Data Source

[NYC Film Permits](https://data.cityofnewyork.us/City-Government/Film-Permits/tg4x-b46p) from NYC Open Data.
