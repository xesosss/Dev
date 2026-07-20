from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_liveness() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "x-request-id" in response.headers


def test_list_products() -> None:
    response = client.get("/products")

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_create_order_and_pay() -> None:
    response = client.post("/orders", json={"sku": "coffee-001", "quantity": 1})

    assert response.status_code == 201
    order = response.json()
    assert order["status"] == "pending"

    paid_response = client.post(f"/orders/{order['id']}/pay")

    assert paid_response.status_code == 200
    assert paid_response.json()["status"] == "paid"


def test_missing_product_returns_404() -> None:
    response = client.get("/products/missing")

    assert response.status_code == 404


def test_metrics_endpoint_exposes_prometheus_text() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text

