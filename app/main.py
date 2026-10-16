"""FastAPI entrypoint for the local taxi demo."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers import driver_routers, passenger_routers, receipt_routers, trip_routers

app = FastAPI(title="Super Taxis", version="0.1.0")

app.include_router(passenger_routers.router)
app.include_router(driver_routers.router)
app.include_router(trip_routers.router)
app.include_router(receipt_routers.router)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
