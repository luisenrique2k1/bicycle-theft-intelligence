# Bicycle Theft Intelligence
### UK Police Data Engineering Pipeline | Python • DuckDB • SQL • Docker • GitHub Actions

A reproducible data engineering project that collects, processes and analyses bicycle theft records from the UK Police API.

The project transforms raw JSON records into a structured DuckDB warehouse and generates an interactive HTML dashboard featuring geographical hotspots, monthly trends, investigation outcomes and data quality results.

**Who is it for?** Cyclists, cycling clubs and anyone interested in exploring recorded bicycle theft patterns.

**Important:** Recorded incidents are not a direct measure of personal theft risk. Police locations are approximate, reporting is incomplete, and areas with more bicycle activity may naturally have more recorded incidents.

## Architecture

```text
UK Police API
     |
     v
Python Data Ingestion
     |
     v
Raw JSON Files
     |
     v
DuckDB Data Warehouse
     |
     +-- Raw Layer
     +-- Staging & Deduplication
     +-- Dimensional Model
     +-- Analytical Data Marts
     |
     v
SQL Data Quality Validation
     |
     v
Interactive HTML Dashboard
```

GitHub Actions provides automated testing and SQL validation. Docker provides an optional, containerised execution environment.

## Key Features

- **Python ingestion:** Retrieves bicycle theft data from the UK Police API and preserves raw JSON responses.
- **DuckDB warehouse:** Implements raw, staging, dimensional and analytical SQL layers.
- **Data quality:** Nine automated SQL checks validate identifiers, coordinates, relationships, dates and record counts.
- **Deduplication:** Handles overlapping API collection areas and missing persistent identifiers.
- **Interactive London map:** Offline SVG basemap with geographical hotspots, zoom and pan.
- **Trend analysis:** Monthly trends, rolling averages, year-on-year comparisons and reporting-year summaries.
- **Investigation outcomes:** Analyses recorded police outcome categories.
- **Automated testing:** Python pytest suite and SQL validation.
- **CI/CD:** GitHub Actions runs automated checks on pushes and pull requests.
- **Docker:** Optional containerised execution without installing project Python dependencies on the host.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Data ingestion, transformation orchestration and reporting |
| DuckDB | Analytical database |
| SQL | Data modelling, marts and quality checks |
| Pytest | Automated testing |
| Docker / Docker Compose | Containerised execution |
| GitHub Actions | Continuous integration |
| GeoPandas / PyProj | Geographical processing and coordinate transformation |
| OpenStreetMap | London geographical basemap |
| HTML / SVG / JavaScript | Interactive offline dashboard |

## Running the Project

The project supports two execution methods.

### Option 1 — Without Docker

**Requirements:** Python 3.12 and Bash.

Clone the repository:

```bash
git clone https://github.com/luisenrique2k1/bicycle-theft-intelligence.git
cd bicycle-theft-intelligence
```

Run:

```bash
./run.sh
```

The script creates or uses a Python virtual environment, installs dependencies, runs tests, builds the DuckDB warehouse, validates data quality and generates the HTML dashboard.

Other commands:

```bash
./run.sh test
./run.sh build
./run.sh fetch 2025-09
```

Fetching additional police data requires internet access. Existing raw files are reused.

### Option 2 — With Docker

**Requirements:** Docker Engine with Docker Compose.

Clone the same repository, then run:

```bash
docker compose up --build
```

Docker builds a Python 3.12 environment, installs dependencies, runs automated tests, executes SQL transformations and writes the database and dashboard to the host project directory.

To run tests only:

```bash
docker compose run --rm bike-theft-pipeline python -m pytest -q
```

The container exits after processing is complete. Exit code `0` indicates successful execution.

**Both execution methods use the same Python and SQL code.** Docker is optional.

### Dashboard Output

The generated dashboard is:

```text
reports/report.html
```

Open it in a web browser.

**Geographical assets are required:** The full dashboard expects generated London map files in `reports/`. These files are excluded from Git because of their size. See the map-generation instructions below.

## Data Source

Bicycle theft records are retrieved from the [UK Police street-level crimes API](https://data.police.uk/docs/method/crime-street/).

- Crime category: `bicycle-theft`
- Source licence: Open Government Licence v3.0
- API authentication: Not required
- Collection areas: Selected locations including London, Brighton and Guildford

Raw API responses are preserved in:

```text
data/raw/YYYY-MM/
```

The ingestion process handles overlapping collection areas, missing persistent identifiers and incomplete outcome information.

## DuckDB Data Model

| SQL file | Responsibility |
|---|---|
| `01_raw.sql` | Load raw police records |
| `02_staging.sql` | Clean, standardise and deduplicate |
| `03_model.sql` | Create fact and dimension tables |
| `04_marts.sql` | Generate analytical reporting tables |
| `90_checks.sql` | Validate data quality |

The warehouse includes bicycle theft facts, location and month dimensions, investigation outcomes and analytical marts.

Rebuilding the warehouse is designed to be repeatable.

## Interactive London Map

The dashboard uses a geographically referenced OpenStreetMap SVG basemap, transformed into British National Grid coordinates (`EPSG:27700`).

The map supports interactive navigation and hotspot exploration.

### Generating Map Assets

The geographical source data is stored locally in:

```text
data/geography/
```

The map-generation script requires these OpenStreetMap shapefile layers:

```text
gis_osm_landuse_a_free_1.shp
gis_osm_water_a_free_1.shp
gis_osm_roads_free_1.shp
```

Their associated `.dbf`, `.shx`, `.prj` and other supporting files must also be present.

The project uses OpenStreetMap shapefiles from Geofabrik. Obtain the appropriate regional extract from [Geofabrik Downloads](https://download.geofabrik.de/) and place the required layers in `data/geography/`.

Map generation requires GeoPandas and its geographical dependencies in addition to the core pipeline requirements.

With the geographical dependencies installed, run:

```bash
python scripts/generate_london_map.py
```

This generates the SVG basemap and its geographical metadata under `reports/`.

The generated map and large source datasets are not committed to the repository.

**Note:** The core SQL transformations and automated tests can run without the map assets. Full dashboard generation requires them.

## Testing and Data Quality

Run Python tests locally:

```bash
python -m pytest -q
```

Or use:

```bash
./run.sh test
```

The project implements nine SQL quality checks covering:

1. Non-null crime identifiers
2. Unique crime identifiers
3. Bicycle theft category consistency
4. Valid UK coordinates
5. Month and source-folder consistency
6. Fact-to-raw record reconciliation
7. Street dimension referential integrity
8. Consistent street identifiers and names
9. Valid chronological ordering of crime outcomes

Any failed SQL check causes the pipeline build to fail.

## CI/CD — GitHub Actions

The GitHub Actions workflow is defined in:

```text
.github/workflows/python-tests.yml
```

It runs on pushes and pull requests targeting `main`.

The workflow:

1. Checks out the repository.
2. Configures Python 3.12.
3. Installs project dependencies.
4. Executes pytest.
5. Builds DuckDB transformations against synthetic test fixtures.
6. Runs all nine SQL data quality checks.

The dashboard integration test is skipped in CI when the excluded geographical assets are unavailable.

[View GitHub Actions](https://github.com/luisenrique2k1/bicycle-theft-intelligence/actions)

## Limitations and Future Improvements

- Expand the historical dataset for stronger year-on-year comparisons.
- Incorporate later-arriving police outcome records.
- Compare recorded thefts against bicycle parking capacity or cycling activity.
- Introduce scheduled ingestion and incremental updates.
- Improve automated geographical asset preparation.
- Extend CI/CD to build and validate the Docker image.
- Consider cloud deployment and orchestration for scheduled pipeline execution.

## AI-Assisted Development

This project was developed with AI-assisted coding support, including Claude and ChatGPT.

Claude helped draft the initial ingestion, SQL transformations, tests and README structure. Subsequent development included improvements to the interactive dashboard, geographical processing, automated validation, Docker execution and GitHub Actions integration.

The project uses synthetic fixtures to validate transformation logic independently of the live Police API.

**Development decisions to document before portfolio submission:**

- **Kept:** The layered DuckDB architecture and automated data quality checks.
- **Rejected:** Reliance on `persistent_id` alone for deduplication, because it can be missing.
- **Changed:** Improved the London map performance, added reproducible Docker execution and automated CI/CD validation.

These notes should be reviewed and adjusted to reflect the developer's own decisions and contributions accurately.

## Repository

[GitHub — Bicycle Theft Intelligence](https://github.com/luisenrique2k1/bicycle-theft-intelligence)