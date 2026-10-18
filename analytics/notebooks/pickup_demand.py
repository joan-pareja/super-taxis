# Databricks notebook source
# DBTITLE 1,Overview
# MAGIC %md
# MAGIC # NYC taxi pickup activity
# MAGIC 10,000 reproducibly sampled January 2015 yellow taxi journeys from the
# MAGIC [NYC TLC](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).
# MAGIC Run `uv run python analytics/prepare_sample.py` locally to prepare the input.
# MAGIC
# MAGIC Passenger and driver IDs are randomly assigned demo links, not original identities.
# MAGIC The sample follows our Trip model, with `source_id` added for traceability.
# MAGIC It is sampled from a systematic minute/second subset across the month,
# MAGIC not a statistically representative random sample of all January journeys.
# MAGIC No PostgreSQL data is read or changed. This is a public-data analytical demonstration.
# MAGIC Cost means the original total charged, in USD; miles are converted to metres.
# MAGIC Times include their original New York UTC offset. Filtering and hashes are in the input manifest.

# COMMAND ----------
# DBTITLE 1,Install plotting dependency
# MAGIC %pip install plotly==6.3.0

# COMMAND ----------
# DBTITLE 1,Load and verify the sample
# ------------------------- Load and verify the sample ------------------------
# -----------------------------------------------------------------------------

# pyright: reportMissingImports=false
import csv
import hashlib
import json
from pathlib import Path

import plotly.express as px
from databricks.sdk.runtime import dbutils, display, displayHTML, spark

dbutils.widgets.text("input_path", "../data/nyc_trips_2015.csv")

input_path = Path(dbutils.widgets.get("input_path"))
manifest = json.loads(input_path.with_suffix(".json").read_text())

assert hashlib.sha256(input_path.read_bytes()).hexdigest() == manifest["sample_sha256"]

print(json.dumps(manifest, indent=2))

# Confirm native spatial support before loading the table.
display(
    spark.sql("""
        SELECT
            ST_AsText(ST_Point(-73.9857, 40.7484, 4326)) AS spatial_check
    """)
)

# COMMAND ----------
# DBTITLE 1,Create and validate the Delta table
# -------------------- Create and validate the Delta table --------------------
# -----------------------------------------------------------------------------

# Workspace files are read on the driver; Spark receives this small 10k-row sample.
# Larger production inputs would be read directly from governed cloud storage.
with input_path.open(newline="", encoding="utf-8") as stream:
    reader = csv.DictReader(stream)
    columns = reader.fieldnames

    assert columns is not None

    rows = [tuple(row[column] for column in columns) for row in reader]

spark.createDataFrame(
    rows, ", ".join(f"{column} STRING" for column in columns)
).createOrReplaceTempView("source_trips")

spark.sql("CREATE SCHEMA IF NOT EXISTS workspace.super_taxis")

spark.sql("""
    CREATE OR REPLACE TABLE workspace.super_taxis.nyc_trips_2015
    USING DELTA
    COMMENT 'NYC TLC January 2015 sample; synthetic demo identity links; not operational taxi data.'
    AS
    SELECT
        id,
        passenger_id,
        driver_id,
        status,
        payment_status,
        city,
        CAST(started_at AS TIMESTAMP) AS started_at,
        CAST(completed_at AS TIMESTAMP) AS completed_at,
        CAST(pickup_latitude AS DOUBLE) AS pickup_latitude,
        CAST(pickup_longitude AS DOUBLE) AS pickup_longitude,
        CAST(dropoff_latitude AS DOUBLE) AS dropoff_latitude,
        CAST(dropoff_longitude AS DOUBLE) AS dropoff_longitude,
        CAST(distance_meters AS INT) AS distance_meters,
        CAST(cost AS DECIMAL(12, 2)) AS cost,
        currency,
        source_id
    FROM source_trips
""")

checks = spark.sql("""
    SELECT
        COUNT(*) AS rows,
        COUNT(DISTINCT id) AS unique_ids,
        COUNT_IF(
            completed_at <= started_at
            OR cost <= 0
            OR distance_meters <= 0
            OR started_at IS NULL
            OR completed_at IS NULL
            OR cost IS NULL
            OR pickup_latitude IS NULL
            OR pickup_longitude IS NULL
        ) AS invalid_rows
    FROM workspace.super_taxis.nyc_trips_2015
""").first()

assert checks["rows"] == checks["unique_ids"] == 10_000
assert checks["invalid_rows"] == 0
display(
    spark.sql("""
        SELECT
            *
        FROM workspace.super_taxis.nyc_trips_2015
        LIMIT 10
    """)
)

# COMMAND ----------
# DBTITLE 1,How the spatial grid works
# MAGIC %md
# MAGIC ## Count pickups in 500-metre squares
# MAGIC `ST_Point` uses longitude then latitude. `ST_Transform` projects WGS84 into
# MAGIC UTM zone 18N (EPSG:32618), where grid widths are measured in metres.
# MAGIC Floor division assigns every point to exactly one cell, including boundary points.
# MAGIC These counts describe this historical sample, not current demand or road congestion.

# COMMAND ----------
# DBTITLE 1,Build the 500-metre pickup grid
# ---------------------- Build the 500-metre pickup grid ----------------------
# -----------------------------------------------------------------------------

spark.sql("""
    CREATE OR REPLACE TEMP VIEW pickup_cells AS
    SELECT
        *,
        CAST(FLOOR(ST_X(pickup_point) / 500) AS BIGINT) AS cell_x,
        CAST(FLOOR(ST_Y(pickup_point) / 500) AS BIGINT) AS cell_y,
        HOUR(FROM_UTC_TIMESTAMP(started_at, 'America/New_York')) AS pickup_hour
    FROM (
        SELECT
            *,
            ST_Transform(
                ST_Point(pickup_longitude, pickup_latitude, 4326),
                32618
            ) AS pickup_point
        FROM workspace.super_taxis.nyc_trips_2015
    )
""")

spark.sql("""
    CREATE OR REPLACE TEMP VIEW pickup_grid AS
    SELECT
        cell_x,
        cell_y,
        COUNT(*) AS pickups,
        SUM(cost) AS total_cost_usd,
        ST_AsGeoJSON(
            ST_Transform(
                ST_GeomFromWKT(
                    FORMAT_STRING(
                        'POLYGON((%s %s,%s %s,%s %s,%s %s,%s %s))',
                        cell_x * 500,
                        cell_y * 500,
                        (cell_x + 1) * 500,
                        cell_y * 500,
                        (cell_x + 1) * 500,
                        (cell_y + 1) * 500,
                        cell_x * 500,
                        (cell_y + 1) * 500,
                        cell_x * 500,
                        cell_y * 500
                    ),
                    32618
                ),
                4326
            )
        ) AS geometry_json
    FROM pickup_cells
    GROUP BY
        cell_x,
        cell_y
""")

assert (
    spark.sql("""
        SELECT
            SUM(pickups)
        FROM pickup_grid
    """).first()[0]
    == 10_000
)
display(
    spark.sql("""
        SELECT
            cell_x,
            cell_y,
            pickups,
            total_cost_usd
        FROM pickup_grid
        ORDER BY pickups DESC
        LIMIT 20
    """)
)

# COMMAND ----------
# DBTITLE 1,Map pickup activity
# ---------------------------- Map pickup activity ----------------------------
# -----------------------------------------------------------------------------

cells = spark.table("pickup_grid").toPandas()
cells["cell_id"] = cells["cell_x"].astype(str) + ":" + cells["cell_y"].astype(str)

features = [
    {
        "type": "Feature",
        "id": row.cell_id,
        "properties": {},
        "geometry": json.loads(row.geometry_json),
    }
    for row in cells.itertuples()
]

figure = px.choropleth_mapbox(
    cells,
    geojson={"type": "FeatureCollection", "features": features},
    locations="cell_id",
    color="pickups",
    color_continuous_scale="YlOrRd",
    mapbox_style="open-street-map",
    center={"lat": 40.75, "lon": -73.97},
    zoom=10,
    opacity=0.65,
    title="NYC pickups per 500 m cell — January 2015 sample",
)

figure.update_layout(margin={"l": 0, "r": 0, "t": 50, "b": 0}, height=600)
displayHTML(figure.to_html(include_plotlyjs="cdn"))

# COMMAND ----------
# DBTITLE 1,Compare pickup activity by hour
# ---------------------- Compare pickup activity by hour ----------------------
# -----------------------------------------------------------------------------

hourly = spark.sql("""
    SELECT
        pickup_hour,
        COUNT(*) AS pickups
    FROM pickup_cells
    GROUP BY pickup_hour
    ORDER BY pickup_hour
""").toPandas()
displayHTML(
    px.bar(
        hourly, x="pickup_hour", y="pickups", title="Pickups by New York local hour"
    ).to_html(include_plotlyjs="cdn")
)
display(
    spark.sql("""
        SELECT
            pickup_hour,
            cell_x,
            cell_y,
            COUNT(*) AS pickups
        FROM pickup_cells
        GROUP BY
            pickup_hour,
            cell_x,
            cell_y
        ORDER BY pickups DESC
        LIMIT 20
    """)
)

# COMMAND ----------
# DBTITLE 1,Interpretation and limitations
# MAGIC %md
# MAGIC ## Interpretation
# MAGIC Darker cells show more observed pickups in this sample. Hourly counts can
# MAGIC help explain how taxi placement might change over a day. A random 10k sample
# MAGIC is exploratory: it is not a forecast or a measurement of unmet demand.
# MAGIC The filter is an NYC-area bounding box, not a clipped city boundary or road network.
# MAGIC Synthetic driver assignments must not be used to evaluate real drivers or availability.
