from __future__ import annotations

import json
import logging
import os
import sys
import time
from contextvars import ContextVar
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

SERVICE_NAME = os.getenv("SERVICE_NAME", "observable-shop")
APP_ENV = os.getenv("APP_ENV", "local")
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests.",
    ["method", "path", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
)
IN_PROGRESS_REQUESTS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being served.",
    ["method", "path"],
)
ORDERS_CREATED = Counter(
    "orders_created_total",
    "Total created orders.",
    ["sku"],
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": SERVICE_NAME,
            "environment": APP_ENV,
            "request_id": request_id_var.get(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for field in ("method", "path", "status_code", "duration_ms"):
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        return json.dumps(payload, ensure_ascii=True)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        token = request_id_var.set(request_id)
        in_progress_path = request.url.path
        start = time.perf_counter()
        status_code = 500

        IN_PROGRESS_REQUESTS.labels(request.method, in_progress_path).inc()
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["x-request-id"] = request_id
            return response
        finally:
            duration = time.perf_counter() - start
            route = request.scope.get("route")
            route_path = getattr(route, "path", in_progress_path)

            IN_PROGRESS_REQUESTS.labels(request.method, in_progress_path).dec()
            REQUEST_COUNT.labels(request.method, route_path, str(status_code)).inc()
            REQUEST_LATENCY.labels(request.method, route_path).observe(duration)

            logging.getLogger("app.request").info(
                "request completed",
                extra={
                    "method": request.method,
                    "path": route_path,
                    "status_code": status_code,
                    "duration_ms": round(duration * 1000, 2),
                },
            )
            request_id_var.reset(token)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


def configure_tracing(app: FastAPI) -> None:
    resource = Resource.create(
        {
            "service.name": SERVICE_NAME,
            "deployment.environment": APP_ENV,
        }
    )
    provider = TracerProvider(resource=resource)

    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))

    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
