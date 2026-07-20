from __future__ import annotations

import logging
import os
import random
import time

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.models import HealthResponse, Order, OrderCreate, Product
from app.observability import (
    APP_ENV,
    ORDERS_CREATED,
    SERVICE_NAME,
    RequestContextMiddleware,
    configure_logging,
    configure_tracing,
    metrics_response,
)
from app.store import OutOfStockError, ProductNotFoundError, ShopStore

logger = logging.getLogger(__name__)
store = ShopStore.with_seed_data()


def parse_cors_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ALLOW_ORIGINS")
    if raw_origins:
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    if APP_ENV == "local":
        return ["http://127.0.0.1:5173", "http://localhost:5173"]

    return []


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="Observable Shop",
        version="0.1.0",
        description="Small API service for deployment and observability practice.",
    )

    cors_origins = parse_cors_origins()
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["content-type", "x-request-id"],
        )

    app.add_middleware(RequestContextMiddleware)
    configure_tracing(app)

    @app.get("/health/live", response_model=HealthResponse, tags=["health"])
    def liveness() -> HealthResponse:
        return HealthResponse(status="ok", service=SERVICE_NAME, environment=APP_ENV)

    @app.get("/health/ready", response_model=HealthResponse, tags=["health"])
    def readiness() -> HealthResponse:
        return HealthResponse(status="ready", service=SERVICE_NAME, environment=APP_ENV)

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return metrics_response()

    @app.get("/products", response_model=list[Product], tags=["products"])
    def list_products() -> list[Product]:
        return store.list_products()

    @app.get("/products/{sku}", response_model=Product, tags=["products"])
    def get_product(sku: str) -> Product:
        try:
            return store.get_product(sku)
        except ProductNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found") from exc

    @app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED, tags=["orders"])
    def create_order(order: OrderCreate) -> Order:
        try:
            created = store.create_order(order)
        except ProductNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found") from exc
        except OutOfStockError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not enough stock") from exc

        ORDERS_CREATED.labels(order.sku).inc()
        logger.info("order created")
        return created

    @app.get("/orders", response_model=list[Order], tags=["orders"])
    def list_orders() -> list[Order]:
        return store.list_orders()

    @app.post("/orders/{order_id}/pay", response_model=Order, tags=["orders"])
    def pay_order(order_id: str) -> Order:
        try:
            return store.mark_order_paid(order_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found") from exc

    @app.get("/simulate/slow", tags=["simulation"])
    def simulate_slow_request() -> dict[str, float]:
        delay = random.uniform(0.2, 1.2)
        time.sleep(delay)
        return {"delay_seconds": round(delay, 3)}

    @app.get("/simulate/error", tags=["simulation"])
    def simulate_error() -> None:
        logger.warning("simulated failure requested")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Simulated error")

    return app


app = create_app()
