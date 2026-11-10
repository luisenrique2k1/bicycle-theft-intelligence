# Bicycle Theft Intelligence

### End-to-End Data Engineering Portfolio Project

**Python • DuckDB • dbt • SQL • AWS S3 • Terraform • GitHub Actions • Streamlit • Plotly**

Bicycle Theft Intelligence is an end-to-end data engineering project that collects, processes, validates and visualises bicycle theft records from the UK Police API.

The project demonstrates practical data engineering skills through automated ingestion, cloud infrastructure, dimensional data modelling, data quality testing, workflow automation and interactive analytics.

The pipeline processes **36 months of historical data**, containing **18,727 raw records** and **13,953 unique bicycle theft incidents** across selected collection locations in London, Brighton and Guildford.

An interactive Streamlit dashboard enables users to explore monthly trends, compare geographical areas and investigate recorded bicycle theft hotspots using OpenStreetMap.

**Project objective:** Demonstrate how raw public API data can be transformed into a reproducible, tested and accessible analytical platform.

**Data limitations:** Collection locations are sampled, police-recorded locations are approximate, and recorded theft counts do not represent the probability of bicycle theft.

## Modern Data Engineering Architecture — dbt, AWS and Streamlit

The project has evolved into an end-to-end data engineering platform that combines automated ingestion, cloud object storage, SQL transformation, data quality testing and interactive analytics.

### Dataset

The pipeline processes 36 months of UK Police bicycle theft data, covering October 2023 to September 2026.

| Metric | Value |
|---|---:|
| Reporting period | October 2023 – September 2026 |
| Raw records collected | 18,727 |
| Unique bicycle theft incidents | 13,953 |
| Collection areas | London, Brighton and Guildford |
| Raw JSON files | 432 |
| dbt models | 6 |
| dbt automated tests | 25 |

The data covers selected collection points rather than every location within each city. Police-recorded incident counts should not be interpreted as individual theft probabilities.

### Data Engineering Workflow

1. **Extract — Python and UK Police API:** Retrieve monthly bicycle theft records from selected geographical collection points and preserve the raw JSON responses.

2. **Store — Local files and AWS S3:** Maintain the raw files locally and synchronise them separately to an AWS S3 bucket provisioned using Terraform.

3. **Transform — DuckDB and dbt:** Load raw records, clean and deduplicate overlapping observations, create dimensional models and generate analytical marts.

4. **Validate — dbt and pytest:** Run automated checks for data quality, relationships, uniqueness and expected values.

5. **Analyse — Streamlit and Plotly:** Explore monthly trends, compare geographical areas and investigate recorded bicycle theft hotspots on an interactive OpenStreetMap map.

6. **Automate — GitHub Actions:** Run continuous integration checks and a scheduled monthly ingestion workflow.

### dbt Data Models

The dbt project is located in `dbt_bike_theft/` and includes six models:

- `raw_crimes` — Loads source JSON records.
- `stg_crimes` — Cleans and deduplicates the source data.
- `dim_streets` — Provides street-level dimensional information.
- `fct_bicycle_thefts` — Stores deduplicated bicycle theft incidents and collection-area classifications.
- `mart_monthly_thefts` — Supports monthly trend analysis.
- `mart_theft_hotspots` — Supports hotspot analysis.

### Build the dbt Warehouse

From the repository root, after installing the Python dependencies:

```bash
export BIKE_THEFT_RAW_PATH="$PWD/data/raw/*/*.json"
export BIKE_THEFT_DB_PATH="$PWD/dbt_bike_theft/dbt_warehouse.duckdb"

dbt build \
  --project-dir dbt_bike_theft \
  --profiles-dir dbt_bike_theft
```

The dbt build creates the analytical tables and executes the configured data quality tests.

### Launch the Streamlit Dashboard

After building the dbt warehouse:

```bash
python -m streamlit run dashboard/app.py
```

Open `http://localhost:8501` in your browser.

The dashboard provides geographical filters for London, Brighton and Guildford, reporting-period selection, monthly theft trends, area comparisons, ranked hotspots and an interactive OpenStreetMap hotspot map.

### Cloud Infrastructure

The project uses Terraform configuration in `terraform/aws/` to provision an AWS S3 bucket in `eu-north-1` (Stockholm).

The bucket has versioning and public-access blocking enabled. Raw JSON files are uploaded using a separate incremental synchronisation process. The scheduled monthly GitHub Actions workflow does not currently perform automatic S3 synchronisation.

### Continuous Integration and Monthly Automation

Two GitHub Actions workflows are defined:

- `.github/workflows/python-tests.yml` — Runs automated testing and validation.
- `.github/workflows/monthly-ingestion.yml` — Supports scheduled and manual monthly ingestion and warehouse builds.

The monthly workflow is scheduled for the 15th of each month at 08:00 UTC.

### Data Interpretation and Limitations

The dataset contains recorded incidents from selected geographical collection points. It is not a complete census of bicycle theft across London, Brighton or Guildford.

Police-provided crime locations are approximate. Differences in recorded theft counts may reflect collection coverage, reporting practices and bicycle activity rather than differences in individual theft risk.

The dashboard should therefore be used to explore patterns in the collected records, not to calculate the probability that a bicycle will be stolen at a particular location.

## Original Pipeline Architecture — Python, SQL and HTML Dashboard

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
| Python 3.12 | API ingestion, automation and pipeline orchestration |
| UK Police API | Public bicycle theft data source |
| DuckDB | Local analytical data warehouse |
| dbt Core + dbt-duckdb | SQL transformations, dimensional modelling and automated data quality tests |
| SQL | Data cleaning, deduplication, fact tables, dimensions and analytical marts |
| AWS S3 | Cloud object storage for raw JSON data |
| Terraform | Infrastructure as Code for provisioning AWS resources |
| boto3 | Incremental synchronisation of raw files to AWS S3 |
| GitHub Actions | Continuous integration and scheduled monthly ingestion |
| pytest | Automated Python testing |
| Streamlit | Interactive analytics dashboard |
| Plotly | Interactive charts and geographical hotspot visualisation |
| OpenStreetMap | Basemap for the Streamlit hotspot map |
| Docker / Docker Compose | Optional containerised execution of the original pipeline |
| GeoPandas / PyProj | Geographical processing for the original SVG map |
| HTML / SVG / JavaScript | Original offline reporting dashboard |

## Running the Project

### Recommended Setup — dbt and Streamlit

This is the recommended way to run the current Bicycle Theft Intelligence analytics platform.

**Prerequisites:** Python 3.12, Git and a terminal. The repository must contain the raw JSON data files under `data/raw/`.

**1. Clone the repository**

```bash
git clone https://github.com/luisenrique2k1/bicycle-theft-intelligence.git
cd bicycle-theft-intelligence
```

**2. Create and activate a Python virtual environment**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**4. Configure the DuckDB warehouse**

From the repository root:

```bash
export BIKE_THEFT_RAW_PATH="$PWD/data/raw/*/*.json"
export BIKE_THEFT_DB_PATH="$PWD/dbt_bike_theft/dbt_warehouse.duckdb"
```

**5. Build and test the dbt models**

```bash
dbt build \
  --project-dir dbt_bike_theft \
  --profiles-dir dbt_bike_theft
```

This builds six dbt models and runs the configured data quality tests.

**6. Launch the interactive dashboard**

```bash
python -m streamlit run dashboard/app.py
```

Open `http://localhost:8501` in your browser.

The dashboard reads the DuckDB warehouse produced by dbt and supports geographical filtering, monthly trend analysis, area comparisons and interactive theft hotspot mapping.

**Note:** The dbt warehouse must be built before launching the dashboard. AWS credentials and Terraform are not required to run the local analytics dashboard.

---

### Original Pipeline — Python, SQL and HTML Dashboard

The following instructions describe the original pipeline, including the HTML dashboard, geographical preparation and optional Docker execution.

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

The project implements automated validation at multiple stages of the data engineering pipeline.

### Python Testing

The project uses pytest to validate pipeline functionality and transformation behaviour.

Run locally:

```bash
python -m pytest -q
```

The Python tests are also executed automatically through GitHub Actions.

### Original SQL Data Quality Checks

The original DuckDB pipeline implements nine SQL checks covering:

1. Non-null crime identifiers.
2. Unique crime identifiers.
3. Bicycle theft category consistency.
4. Valid UK geographical coordinates.
5. Consistency between reporting month and source folder.
6. Reconciliation of fact records against distinct raw crime identifiers.
7. Referential integrity between fact and street dimension tables.
8. Consistent street identifiers and names.
9. Valid chronological ordering of crime outcomes.

These checks help detect invalid or inconsistent records during warehouse construction.

### dbt Data Quality Tests

The modern dbt pipeline includes **25 automated tests** across six SQL models.

The tests validate model assumptions such as uniqueness, non-null values, relationships and accepted categorical values.

The geographical classification field `collection_area` is validated against the expected collection areas: London, Brighton and Guildford.

Run the complete dbt build and test process from the repository root:

```bash
export BIKE_THEFT_RAW_PATH="$PWD/data/raw/*/*.json"
export BIKE_THEFT_DB_PATH="$PWD/dbt_bike_theft/dbt_warehouse.duckdb"

dbt build \
  --project-dir dbt_bike_theft \
  --profiles-dir dbt_bike_theft
```

A successful dbt build confirms that the models were built and all enabled tests passed for that execution.

### Automated Validation in GitHub Actions

Continuous integration runs pytest, the original SQL validation, dbt transformations and tests, and separate Docker-based checks.

The scheduled monthly ingestion workflow also performs validation before committing newly downloaded data.

## CI/CD — GitHub Actions

The project uses two GitHub Actions workflows to automate testing, data ingestion and warehouse validation.

### Continuous Integration

**Workflow:** `.github/workflows/python-tests.yml`

Triggered by pushes and pull requests targeting the `main` branch.

The workflow runs two independent jobs:

**1. Python and dbt validation**

- Sets up Python 3.12 and installs project dependencies.
- Executes the pytest test suite.
- Validates the original DuckDB SQL transformations using synthetic test fixtures.
- Builds the dbt warehouse from the project dataset.
- Executes the configured dbt data quality tests.

**2. Docker validation**

- Builds the Docker Compose images.
- Runs Python tests inside the pipeline container.
- Validates SQL transformations using synthetic fixtures inside Docker.

The CI workflow validates the data engineering pipeline without requiring AWS credentials.

### Scheduled Monthly Ingestion

**Workflow:** `.github/workflows/monthly-ingestion.yml`

Scheduled for the 15th of each month at 08:00 UTC. It can also be triggered manually using GitHub Actions.

The workflow:

1. Checks out the repository and configures Python 3.12.
2. Installs project dependencies and runs pytest.
3. Fetches the latest published bicycle theft data from the UK Police API.
4. Rebuilds and validates the original DuckDB warehouse.
5. Builds the dbt models and executes their automated tests.
6. Commits and pushes newly downloaded data to the `main` branch when changes are detected.

Concurrency controls prevent overlapping monthly ingestion runs.

### AWS S3 Synchronisation

AWS S3 storage is provisioned using Terraform, and raw JSON files can be synchronised using boto3.

S3 synchronisation is currently a separate operation and is not performed automatically by either GitHub Actions workflow.

### GitHub Actions

[View the project workflows](https://github.com/luisenrique2k1/bicycle-theft-intelligence/actions)

## Limitations and Future Improvements

### Current Limitations

- **Geographical coverage:** The dataset represents selected collection locations in London, Brighton and Guildford, not complete coverage of these cities.
- **Approximate locations:** The UK Police API provides approximate street-level crime locations rather than exact incident coordinates.
- **Recorded incidents versus risk:** Higher incident counts do not necessarily indicate a higher probability of bicycle theft. The dataset does not include reliable bicycle parking or cycling exposure data.
- **Reporting delays:** Police crime data and investigation outcomes may be published or updated after the reporting month.
- **Cloud integration:** Raw JSON files are synchronised to AWS S3 separately. The scheduled monthly ingestion workflow does not currently upload files to S3.
- **Dashboard hosting:** The Streamlit dashboard currently runs locally rather than being hosted as a publicly accessible application.

### Future Improvements

1. **Cloud deployment:** Deploy the Streamlit dashboard so users can access it through a public URL.
2. **Automated S3 synchronisation:** Extend the ingestion workflow to upload newly collected data to AWS S3 using secure GitHub Actions authentication.
3. **Incremental dbt processing:** Investigate incremental materialisation to avoid rebuilding all analytical tables as the dataset grows.
4. **Additional data sources:** Incorporate bicycle parking availability or cycling activity data to provide more meaningful context for recorded theft counts.
5. **Historical outcome updates:** Improve handling of police investigation outcomes that change after initial publication.
6. **Extended geographical analysis:** Explore additional UK collection areas and improve comparisons between locations.

These enhancements would build on the existing automated ingestion, dimensional modelling, data quality testing and interactive analytics platform.


## Development Approach and AI-Assisted Engineering

This project was conceived, planned and directed by me, from the initial idea of analysing bicycle theft data to the design of the data engineering pipeline and interactive dashboard.

I selected the project objectives, data sources, technologies and overall approach, making decisions throughout development about data ingestion, storage, transformation, testing, automation and visualisation.

I used AI tools, including ChatGPT and Claude, as development assistants to support coding, troubleshooting, technical research and learning. AI-assisted suggestions and generated code were reviewed, tested and refined through hands-on development.

Throughout the project, I worked with Python, SQL, DuckDB, dbt, AWS, Terraform, GitHub Actions and Streamlit, investigating errors, validating results and making decisions about the implementation.

The project also involved addressing practical engineering challenges, including duplicate records from overlapping geographical collection areas, data quality validation, reproducible pipeline execution and the limitations of police-recorded crime data.

**AI supported the development process, while the project concept, technical direction, implementation decisions and validation remained under my responsibility.**

## Repository

[GitHub — Bicycle Theft Intelligence](https://github.com/luisenrique2k1/bicycle-theft-intelligence)
