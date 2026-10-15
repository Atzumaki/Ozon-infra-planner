from fastapi.testclient import TestClient

from infra_planner.api import app
from infra_planner.demo import demo_request

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_plan_endpoint() -> None:
    response = client.post("/v1/plan", json=demo_request().model_dump(mode="json"))
    assert response.status_code == 200
    body = response.json()
    assert body["plan"]["status"] == "optimal"
    assert body["plan"]["server_counts"]
    assert body["forecast"]["validation_mape"]["cpu_cores"] < 10

