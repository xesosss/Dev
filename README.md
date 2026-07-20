# Observable Shop

Observable Shop is a small FastAPI service for practicing a realistic deploy flow.

The repository intentionally contains application code only. Infrastructure files such as
Dockerfile, docker-compose, Nginx, Prometheus, Grafana, Fluentd, Logstash, Elasticsearch, Kibana,
and Jaeger configuration should be created during the deployment exercise.

## Local run

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open:

- API docs: http://127.0.0.1:8000/docs
- Liveness: http://127.0.0.1:8000/health/live
- Readiness: http://127.0.0.1:8000/health/ready
- Metrics: http://127.0.0.1:8000/metrics
- Frontend: http://127.0.0.1:5173

## Useful environment variables

- `SERVICE_NAME`: service name used in logs and traces. Default: `observable-shop`.
- `APP_ENV`: deployment environment label. Default: `local`.
- `LOG_LEVEL`: Python logging level. Default: `INFO`.
- `CORS_ALLOW_ORIGINS`: comma-separated browser origins allowed to call the API.
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OTLP HTTP endpoint for traces, for example
  `http://otel-collector:4318`.

## Development checks

```powershell
pytest
ruff check .
```
