"""Prepare the NYC sample: uv run python analytics/prepare_sample.py."""

import csv
import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import NAMESPACE_URL, UUID, uuid5

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://data.cityofnewyork.us/resource/2yzn-sicd.json"
RAW_FILE = ROOT / ".cache/nyc-taxi/coordinate_candidates_2015-01.json"
OUTPUT = ROOT / "analytics/data/nyc_trips_2015.csv"
SAMPLE_SIZE = 10_000
SEED = 42
COLUMNS = [
    "pickup_datetime",
    "dropoff_datetime",
    "pickup_latitude",
    "pickup_longitude",
    "dropoff_latitude",
    "dropoff_longitude",
    "trip_distance",
    "total_amount",
    "payment_type",
]
# A systematic time subset across every day/hour avoids downloading millions of rows.
# This is not a simple random sample of the entire month's population.
QUERY = {
    "$select": ":id AS source_id," + ",".join(COLUMNS),
    "$where": "pickup_datetime >= '2015-01-01T00:00:00' AND pickup_datetime < '2015-02-01T00:00:00' "
    "AND date_extract_mm(pickup_datetime) IN (17,42) "
    "AND date_extract_ss(pickup_datetime) IN (0,15,30,45)",
    "$order": ":id",
    "$limit": 50000,
}


def is_valid(row: dict) -> bool:
    """Keep completed, paid trips within a documented NYC-area bounding box."""
    if any(row.get(column) is None for column in COLUMNS):
        return False
    start, end = (
        datetime.fromisoformat(row["pickup_datetime"]),
        datetime.fromisoformat(row["dropoff_datetime"]),
    )
    return (
        datetime(2015, 1, 1) <= start < end < datetime(2015, 2, 1)
        and row["payment_type"] in ("1", "2")
        and 0 < float(row["trip_distance"]) <= 100
        and 0 < float(row["total_amount"]) <= 1_000
        and all(
            40.49 <= float(row[f"{point}_latitude"]) <= 40.93
            for point in ("pickup", "dropoff")
        )
        and all(
            -74.26 <= float(row[f"{point}_longitude"]) <= -73.68
            for point in ("pickup", "dropoff")
        )
    )


def main() -> None:
    RAW_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not RAW_FILE.exists():
        print(
            "Downloading original NYC coordinate records across January 2015.",
            flush=True,
        )
        with urlopen(SOURCE_URL + "?" + urlencode(QUERY), timeout=180) as response:
            payload = response.read()
        json.loads(payload)
        RAW_FILE.write_bytes(payload)
    source = json.loads(RAW_FILE.read_text())
    if len(source) >= QUERY["$limit"]:
        raise ValueError(
            "The API response may be truncated; narrow the time subset before sampling."
        )
    candidates = [row for row in source if is_valid(row)]
    if len(candidates) < SAMPLE_SIZE:
        raise ValueError(
            f"Only {len(candidates)} valid candidates; need {SAMPLE_SIZE}."
        )
    rng = random.Random(SEED)
    sampled = sorted(
        rng.sample(candidates, SAMPLE_SIZE), key=lambda row: row["source_id"]
    )
    mapped = []
    # January 2015 New York timestamps are EST, UTC-05:00 (no DST transition).
    est = timezone(timedelta(hours=-5))
    for row in sampled:
        mapped.append(
            {
                "id": str(uuid5(NAMESPACE_URL, f"{SOURCE_URL}#{row['source_id']}")),
                "passenger_id": str(UUID(int=rng.choice((1, 2)))),
                "driver_id": str(UUID(int=rng.choice((3, 4)))),
                "status": "COMPLETED",
                "payment_status": "PAID",
                "city": "New York",
                "started_at": datetime.fromisoformat(row["pickup_datetime"])
                .replace(tzinfo=est)
                .isoformat(),
                "completed_at": datetime.fromisoformat(row["dropoff_datetime"])
                .replace(tzinfo=est)
                .isoformat(),
                **{column: float(row[column]) for column in COLUMNS[2:6]},
                "distance_meters": round(float(row["trip_distance"]) * 1609.344),
                "cost": str(
                    Decimal(row["total_amount"]).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                ),
                "currency": "USD",
                "source_id": row["source_id"],
            }
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(mapped[0]))
        writer.writeheader()
        writer.writerows(mapped)
    manifest = {
        "source_url": SOURCE_URL,
        "query": QUERY,
        "source_sha256": hashlib.sha256(RAW_FILE.read_bytes()).hexdigest(),
        "sample_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "seed": SEED,
        "rows": len(mapped),
        "source_rows": len(source),
        "valid_candidates": len(candidates),
        "notes": "Random 10k sample from a systematic time subset, not an unbiased sample of all January trips. Real journeys; synthetic passenger/driver links. Cost is total_amount in USD. The bounding box is not an administrative boundary.",
    }
    OUTPUT.with_suffix(".json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
