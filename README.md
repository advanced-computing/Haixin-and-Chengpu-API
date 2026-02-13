# NYC Film Permits API

A Flask API for querying NYC film permit data from [NYC Open Data](https://catalog.data.gov/dataset/film-permits).

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

Returns all film permits. Supports filtering, pagination, and output format selection.

**Parameters:**

| Parameter        | Type   | Description                                                                     |
| ---------------- | ------ | ------------------------------------------------------------------------------- |
| `format`         | string | Output format: `json` (default) or `csv`                                        |
| `limit`          | int    | Maximum number of records to return                                             |
| `offset`         | int    | Number of records to skip (default: 0)                                          |
| `Borough`        | string | Filter by borough (e.g., `Manhattan`, `Brooklyn`)                               |
| `Category`       | string | Filter by category (e.g., `Television`, `Theater`, `Film`)                      |
| `EventType`      | string | Filter by event type (e.g., `Shooting Permit`, `Theater Load in and Load Outs`) |
| `Country`        | string | Filter by country                                                               |
| Any other column | string | Filter by any column in the dataset                                             |

**Example requests:**

```
GET /permits?limit=3
GET /permits?Borough=Manhattan&limit=5
GET /permits?Category=Television&format=csv
GET /permits?limit=10&offset=20
GET /permits?Borough=Brooklyn&Category=Film&limit=3
```

**Sample JSON output:**

```json
[
  {
    "EventID": 740992,
    "EventType": "Theater Load in and Load Outs",
    "StartDateTime": "09/21/2023 12:01:00 PM",
    "EndDateTime": "09/23/2023 06:00:00 AM",
    "EnteredOn": "09/15/2023 03:47:05 PM",
    "EventAgency": "Mayor's Office of Media & Entertainment",
    "ParkingHeld": "FROST STREET between DEBEVOISE AVENUE and MORGAN AVENUE",
    "Borough": "Brooklyn",
    "CommunityBoard(s)": "1,",
    "PolicePrecinct(s)": "94,",
    "Category": "Theater",
    "SubCategoryName": "Theater",
    "Country": "United States of America",
    "ZipCode(s)": "11222,"
  }
]
```

**Sample CSV output** (`?format=csv&limit=2`):

```
EventID,EventType,StartDateTime,EndDateTime,EnteredOn,EventAgency,ParkingHeld,Borough,CommunityBoard(s),PolicePrecinct(s),Category,SubCategoryName,Country,ZipCode(s)
740992,Theater Load in and Load Outs,09/21/2023 12:01:00 PM,09/23/2023 06:00:00 AM,...,Brooklyn,1,,94,,Theater,Theater,...
850643,Theater Load in and Load Outs,04/24/2025 12:01:00 PM,04/25/2025 06:00:00 AM,...,Manhattan,3,,9,,Theater,Theater,...
```

### Get a single permit

```
GET /permits/<EventID>
```

Returns a single permit by its unique `EventID`.

**Example:**

```
GET /permits/740992
```

**Sample output:**

```json
[
  {
    "EventID": 740992,
    "EventType": "Theater Load in and Load Outs",
    "StartDateTime": "09/21/2023 12:01:00 PM",
    "Borough": "Brooklyn",
    "Category": "Theater",
    "SubCategoryName": "Theater"
  }
]
```

Returns a `404` error if the permit is not found:

```json
{ "error": "Permit not found" }
```

### List columns

```
GET /columns
```

Returns all available column names that can be used for filtering.

**Sample output:**

```json
{
  "columns": [
    "EventID",
    "EventType",
    "StartDateTime",
    "EndDateTime",
    "EnteredOn",
    "EventAgency",
    "ParkingHeld",
    "Borough",
    "CommunityBoard(s)",
    "PolicePrecinct(s)",
    "Category",
    "SubCategoryName",
    "Country",
    "ZipCode(s)"
  ]
}
```

### Dataset statistics

```
GET /stats
```

Returns basic statistics about the dataset.

**Sample output:**

```json
{
  "total_records": 16290,
  "columns": ["EventID", "EventType", "..."],
  "boroughs": ["Brooklyn", "Manhattan", "Queens", "Bronx", "Staten Island"],
  "categories": ["Theater", "Television", "Film", "Documentary", "..."]
}
```

## Data Source

[Film Permits](https://catalog.data.gov/dataset/film-permits) dataset from NYC Open Data, provided by the Mayor's Office of Media & Entertainment.

## Acknowledgments

We used AI (Claude by Anthropic) to assist with the development of this API and documentation.
