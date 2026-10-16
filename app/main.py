"""FastAPI entrypoint for the local taxi demo."""

from fastapi import FastAPI

from app.routers import driver_routers, passenger_routers, receipt_routers, trip_routers

app = FastAPI(title="Super Taxis", version="0.1.0")

app.include_router(passenger_routers.router)
app.include_router(driver_routers.router)
app.include_router(trip_routers.router)
app.include_router(receipt_routers.router)
