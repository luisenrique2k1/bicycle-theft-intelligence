from pathlib import Path

import duckdb
import streamlit as st
import plotly.express as px

# Dashboard configuration
st.set_page_config(
    page_title="Bicycle Theft Intelligence",
    page_icon="🚲",
    layout="wide",
)

# Database location
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "dbt_bike_theft" / "dbt_warehouse.duckdb"

@st.cache_data
def load_monthly_data(selected_area):
    if not DB_PATH.exists():
        raise FileNotFoundError(
            "DuckDB warehouse not found. Run dbt build first."
        )

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.execute(
            """
            SELECT
                crime_month,
                COUNT(*) AS total_thefts,
                COUNT(DISTINCT street_id) AS affected_streets,
                COUNT(outcome_category) AS crimes_with_outcome
            FROM fct_bicycle_thefts
            WHERE (? = 'All areas' OR collection_area = ?)
            GROUP BY crime_month
            ORDER BY crime_month
            """,
            [selected_area, selected_area],
        ).df()

@st.cache_data
def load_hotspot_data(start_month, end_month, selected_area):
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.execute(
            """
            SELECT
                f.street_id,
                COALESCE(
                    MAX(d.street_name),
                    'Unknown location'
                ) AS street_name,
                COUNT(*) AS total_thefts,
                COUNT(DISTINCT f.crime_month) AS months_with_thefts,
                AVG(f.latitude) AS latitude,
                AVG(f.longitude) AS longitude
            FROM fct_bicycle_thefts AS f
            LEFT JOIN dim_streets AS d
                ON f.street_id = d.street_id
            WHERE f.crime_month BETWEEN ? AND ?
              AND (? = 'All areas' OR f.collection_area = ?)
            GROUP BY f.street_id
            ORDER BY total_thefts DESC, f.street_id
            """,
            [start_month, end_month, selected_area, selected_area],
        ).df()

@st.cache_data
def load_area_comparison(start_month, end_month, selected_area):
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.execute(
            """
            SELECT
                crime_month,
                collection_area,
                COUNT(*) AS total_thefts
            FROM fct_bicycle_thefts
            WHERE crime_month BETWEEN ? AND ?
              AND (? = 'All areas' OR collection_area = ?)
            GROUP BY crime_month, collection_area
            ORDER BY crime_month, collection_area
            """,
            [
                start_month,
                end_month,
                selected_area,
                selected_area,
            ],
        ).df()

# Page heading
st.title("🚲 Bicycle Theft Intelligence")
st.write(
    "Exploring recorded bicycle theft incidents using "
    "UK Police open data, Python, DuckDB and dbt."
)

st.caption(
    "Data covers selected geographical areas and should not "
    "be interpreted as complete citywide crime coverage."
)

# Geographical collection area filter
selected_area = st.selectbox(
    "Select geographical area",
    options=[
        "All areas",
        "London",
        "Brighton",
        "Guildford",
    ],
    index=0,
    help=(
        "Areas represent sampled UK Police API collection "
        "locations, not complete citywide crime coverage."
    ),
)

# Load analytics data
try:
    monthly = load_monthly_data(selected_area)
except Exception as exc:
    st.error(f"Unable to load analytics data: {exc}")
    st.stop()


# Display metrics

st.divider()

# Interactive monthly theft trend
st.subheader("Monthly Bicycle Theft Trends")

# Filter monthly trends by reporting period
available_months = monthly["crime_month"].dt.date


start_month, end_month = st.select_slider(
    "Select reporting period",
    options=available_months.tolist(),
    value=(
        available_months.min(),
        available_months.max(),
    ),
    format_func=lambda d: d.strftime("%b %Y"),
)



filtered_monthly = monthly[
    (monthly["crime_month"].dt.date >= start_month)
    & (monthly["crime_month"].dt.date <= end_month)
].copy()

# Summary metrics for the selected reporting period
filtered_total_thefts = int(filtered_monthly["total_thefts"].sum())
filtered_months = len(filtered_monthly)

# Load hotspots for the selected reporting period
hotspots = load_hotspot_data(start_month, end_month, selected_area)
filtered_streets = len(hotspots)

# Display dynamic summary metrics
col1, col2, col3 = st.columns(3)

col1.metric(
    "Recorded Bicycle Thefts",
    f"{filtered_total_thefts:,}",
)

col2.metric(
    "Affected Streets",
    f"{filtered_streets:,}",
)

col3.metric(
    "Months Covered",
    filtered_months,
)

st.divider()

fig = px.line(
    filtered_monthly,
    x="crime_month",
    y="total_thefts",
    markers=True,
    labels={
        "crime_month": "Month",
        "total_thefts": "Recorded Bicycle Thefts",
    },
    title="Recorded Bicycle Thefts by Month",
)

fig.update_layout(
    hovermode="x unified",
    xaxis_title="Month",
    yaxis_title="Number of Thefts",
)

# Geographical comparison chart
st.divider()
st.subheader("Bicycle Theft Trends by Collection Area")

area_comparison = load_area_comparison(
    start_month,
    end_month,
    selected_area,
)

comparison_scale = st.radio(
    "Chart scale",
    options=["Linear", "Logarithmic"],
    horizontal=True,
)

fig_comparison = px.line(
    area_comparison,
    x="crime_month",
    y="total_thefts",
    color="collection_area",
    markers=True,
    labels={
        "crime_month": "Month",
        "total_thefts": "Recorded Bicycle Thefts",
        "collection_area": "Collection Area",
    },
    title="Monthly Recorded Bicycle Thefts by Collection Area",
)

fig_comparison.update_layout(
    height=450,
    hovermode="x unified",
)

if comparison_scale == "Logarithmic":
    fig_comparison.update_yaxes(
        type="log",
        tickmode="array",
        tickvals=[1, 10, 100, 1000],
        ticktext=["1", "10", "100", "1,000"],
        title="Recorded Bicycle Thefts (log scale)",
    )
else:
    fig_comparison.update_yaxes(
        type="linear",
        tickmode="auto",
        title="Recorded Bicycle Thefts",
    )

st.plotly_chart(
    fig_comparison,
    width="stretch",
)

st.caption(
    "These figures represent recorded incidents within sampled "
    "collection areas. Differences in geographical coverage mean "
    "that counts should not be interpreted as comparable crime rates."
)

# Top 10 bicycle theft hotspots
st.divider()
st.subheader("Top 10 Bicycle Theft Hotspots")

top_10 = hotspots.head(10).copy()

# Street names can repeat, so include street ID for unique labels.
top_10["location"] = (
    top_10["street_name"]
    + " ("
    + top_10["street_id"].astype(str)
    + ")"
)

fig_hotspots = px.bar(
    top_10,
    x="total_thefts",
    y="location",
    orientation="h",
    title="Locations with the Most Recorded Bicycle Thefts",
    labels={
        "total_thefts": "Recorded Bicycle Thefts",
        "location": "Police-Reported Location",
    },
)

fig_hotspots.update_layout(
    yaxis={"categoryorder": "total ascending"},
    height=500,
)

st.plotly_chart(fig_hotspots, width="stretch")

st.caption(
    "Police-reported locations are approximate. "
    "Counts represent incidents within the sampled geographical areas."
)
st.plotly_chart(fig, width="stretch")

st.divider()

st.subheader("Monthly Bicycle Theft Data")

st.dataframe(
    filtered_monthly,
    width="stretch",
    hide_index=True,
)
# Interactive bicycle theft hotspot map
st.divider()
st.subheader("Bicycle Theft Hotspot Map")

# Control the number of hotspots displayed
hotspot_limit = st.selectbox(
    "Number of hotspots to display",
    options=["Top 25", "Top 50", "Top 100", "All locations"],
    index=1,
)

if hotspot_limit == "All locations":
    map_hotspots = hotspots.copy()
else:
    limit = int(hotspot_limit.split()[1])
    map_hotspots = hotspots.nlargest(limit, "total_thefts").copy()

map_data = map_hotspots.dropna(
    subset=["latitude", "longitude"]
).copy()

# Map centre and zoom based on selected area
map_settings = {
    "All areas": {"lat": 51.35, "lon": -0.15, "zoom": 8},
    "London": {"lat": 51.51, "lon": -0.10, "zoom": 11},
    "Brighton": {"lat": 50.825, "lon": -0.137, "zoom": 13},
    "Guildford": {"lat": 51.236, "lon": -0.572, "zoom": 13},
}

map_view = map_settings[selected_area]

fig_map = px.scatter_map(
    map_data,
    lat="latitude",
    lon="longitude",
    size="total_thefts",
    color="total_thefts",
    hover_name="street_name",
    hover_data={
        "total_thefts": True,
        "months_with_thefts": True,
        "latitude": False,
        "longitude": False,
    },
    color_continuous_scale=[
    [0.0, "#2563eb"],
    [0.25, "#06b6d4"],
    [0.5, "#f59e0b"],
    [0.75, "#f97316"],
    [1.0, "#dc2626"],
],
    range_color=(1, 106),
    size_max=16,

    map_style="open-street-map",
    title="Recorded Bicycle Theft Hotspots",
)

# Improve hotspot marker visibility
fig_map.update_traces(
    marker={
        "sizemin": 3,
        "opacity": 0.65,
    }
)

fig_map.update_layout(
    height=700,
    margin={"r": 0, "t": 50, "l": 0, "b": 0},
    map=dict(
        center={
            "lat": map_view["lat"],
            "lon": map_view["lon"],
        },
        zoom=map_view["zoom"],
    ),
)

st.plotly_chart(fig_map, width="stretch")
