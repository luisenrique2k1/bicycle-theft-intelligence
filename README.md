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

GitHub Actions provides automated testing and SQL validation. Docker provides an optional, containerised execution environment. A separate geographical preparation stage downloads OpenStreetMap data when needed and generates the London basemap.

## Key Features

- **Python ingestion:** Retrieves bicycle theft data from the UK Police API and preserves raw JSON responses.
- **DuckDB warehouse:** Implements raw, staging, dimensional and analytical SQL layers.
- **Data quality:** Nine automated SQL checks validate identifiers, coordinates, relationships, dates and record counts.
- **Deduplication:** Handles overlapping API collection areas and missing persistent identifiers.
- **Interactive London map:** Offline SVG basemap with geographical hotspots, zoom and pan.
- **Trend analysis:** Monthly trends, rolling averages, year-on-year comparisons and reporting-year summaries.
- **Investigation outcomes:** Analyses recorded police outcome categories.
- **Automated geographical preparation:** Downloads and extracts Greater London OpenStreetMap shapefiles when missing.
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
| OpenStreetMap / Geofabrik | London geographical basemap data |
| HTML / SVG / JavaScript | Interactive offline dashboard |

## Running the Project

The project supports two execution methods. **Both use the same Python and SQL pipeline code; Docker is optional.**

### Option 1 — Without Docker

**Requirements:** Python 3.12, Bash, internet access for first-time geographical downloads, and sufficient free disk space for the OpenStreetMap extract.

Clone the repository:

```bash
git clone https://github.com/luisenrique2k1/bicycle-theft-intelligence.git
cd bicycle-theft-intelligence
```

Run:

```bash
./run.sh
```

The script creates or reuses a Python virtual environment, installs required dependencies (including GeoPandas), prepares geographical data if missing, generates the London map, builds the DuckDB warehouse and HTML dashboard, and runs the Python tests.

Other commands:

```bash
./run.sh test
./run.sh build
./run.sh fetch 2025-09
```

- `test` runs Python tests without downloading geographical data.
- `build` prepares the map and rebuilds the warehouse and dashboard.
- `fetch` retrieves police data for the specified month; it requires internet access.

Existing raw data files are reused during a normal build. Running `./run.sh` does **not** automatically fetch new police records.

### Option 2 — With Docker

**Requirements:** Docker Engine with Docker Compose, internet access for the first geographical download, and sufficient disk space.

Clone the same repository, then run:

```bash
docker compose up --build
```

Docker Compose builds and runs two services in sequence:

1. **`bike-theft-geo`:** Checks for geographical shapefiles, downloads them from Geofabrik when missing, and generates the London SVG basemap and map metadata.
2. **`bike-theft-pipeline`:** Runs Python tests, executes SQL transformations and quality checks, and writes the DuckDB database and dashboard to the host project directory.

The pipeline service starts only after the geographical preparation service completes successfully. Both containers are expected to exit with code `0` after processing.

To run tests only in the pipeline container:

```bash
docker compose run --rm --no-deps bike-theft-pipeline python -m pytest -q
```

### Dashboard Output

The generated dashboard is:

```text
reports/report.html
```

Open it in a web browser. The London basemap is generated automatically when using `./run.sh` or `docker compose up --build`. The large geographical source data and generated map assets are excluded from Git.

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

### Automatic Geographical Data Preparation

The project automatically downloads and prepares Greater London OpenStreetMap geographical data. **No manual shapefile download is required.**

To prepare the map and run the full pipeline locally:

```bash
./run.sh
```

Or use Docker:

```bash
docker compose up --build
```

The geographical setup checks whether the required files already exist and skips downloading them when they are present. Otherwise, it downloads the Greater London shapefile archive from Geofabrik, extracts the required layers and generates the basemap.

### Geographical Data Sources

The source data comes from [Geofabrik's Greater London OpenStreetMap extract](https://download.geofabrik.de/europe/united-kingdom/england/greater-london.html).

The following layers are required:

```text
gis_osm_landuse_a_free_1
gis_osm_water_a_free_1
gis_osm_roads_free_1
```

Each layer requires `.shp`, `.shx`, `.dbf` and `.prj` components.

The extracted source files are stored in:

```text
data/geography/
```

Map generation uses GeoPandas and British National Grid (`EPSG:27700`) coordinates. Generated outputs include:

```text
reports/london_basemap_georeferenced.svg
reports/london_theft_map_bounds.json
```

### Optional: Custom Download Directory

The setup script accepts a custom destination for isolated testing:

```bash
.venv/bin/python scripts/setup_geography.py \
  --destination /tmp/bike-theft-geography-test
```

This downloads and extracts the shapefiles into the specified directory without changing `data/geography/`. It does **not** change the input directory used by `scripts/generate_london_map.py`; the normal build continues to use `data/geography/`.

### Reproducibility and Data Storage

The source ZIP archive was approximately **208 MB** when tested; its size can change as OpenStreetMap data is updated. Extracted files require additional disk space.

Large geographical datasets and generated map assets are excluded from Git to keep the repository lightweight.

**Attribution:** © OpenStreetMap contributors. OpenStreetMap data is available under the Open Database License (ODbL). See [OpenStreetMap copyright and licence](https://www.openstreetmap.org/copyright).

**Note:** Core SQL transformations and Python tests can run without the map assets. The complete interactive London dashboard requires the generated map files.

## Testing and Data Quality

Run Python tests locally:

```bash
.venv/bin/python -m pytest -q
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

The dashboard integration test is skipped in CI when excluded geographical assets are unavailable. **The current CI workflow does not download the full OpenStreetMap dataset or build Docker images.** Docker and the real geographical download were also tested manually during development.

[View GitHub Actions](https://github.com/luisenrique2k1/bicycle-theft-intelligence/actions)

## Limitations and Future Improvements

- Expand the historical dataset for stronger year-on-year comparisons.
- Incorporate later-arriving police outcome records.
- Compare recorded thefts against bicycle parking capacity or cycling activity.
- Introduce scheduled ingestion and incremental updates.
- Extend CI/CD to build and validate Docker images and geographical preparation.
- Add a full clean-clone end-to-end integration test.
- Consider cloud deployment and orchestration for scheduled pipeline execution.

## AI-Assisted Development

This project was developed with AI-assisted coding support, including Claude and ChatGPT.

Claude helped draft the initial ingestion, SQL transformations, tests and README structure. Subsequent development included improvements to the interactive dashboard, geographical processing, automated validation, Docker execution and GitHub Actions integration.

The project uses synthetic fixtures to validate transformation logic independently of the live Police API.

**Development decisions to document before portfolio submission:**

- **Kept:** The layered DuckDB architecture and automated data quality checks.
- **Rejected:** Reliance on `persistent_id` alone for deduplication, because it can be missing.
- **Changed:** Improved London map performance, added automated geographical data preparation, reproducible Docker execution and automated CI/CD validation.

These notes should be reviewed and adjusted to reflect the developer's own decisions and contributions accurately.

## Repository

[GitHub — Bicycle Theft Intelligence](https://github.com/luisenrique2k1/bicycle-theft-intelligence)
