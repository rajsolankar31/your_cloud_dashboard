import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.providers import mock


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/t.db")
    monkeypatch.setenv("USE_MOCK", "true")
    monkeypatch.setenv("SECRETS_PATH", str(tmp_path / "s.json"))
    mock.reset()
    with TestClient(app) as c:
        yield c


def rid(client, name):
    return next(r["id"] for r in client.get("/api/resources").json() if r["name"] == name)


def test_inventory_normalized(client):
    rs = client.get("/api/resources").json()
    assert len(rs) == 9
    assert {"id", "provider", "resource_type", "name", "status", "region", "last_checked"} <= rs[0].keys()


def test_stop_requires_matching_name_and_is_audited(client):
    r = client.post("/api/actions", json={"resource_id": rid(client, "demo-server"), "action": "stop"}).json()
    assert r["status"] == "pending"
    assert client.post(f"/api/actions/{r['id']}/confirm", json={"confirm_name": "wrong"}).status_code == 400
    done = client.post(f"/api/actions/{r['id']}/confirm", json={"confirm_name": "demo-server"}).json()
    assert done["status"] == "success"
    assert next(x for x in client.get("/api/resources").json() if x["name"] == "demo-server")["status"] == "stopped"
    assert client.get("/api/audit").json()[0]["id"] == r["id"]
    assert client.post(f"/api/actions/{r['id']}/confirm", json={"confirm_name": "demo-server"}).status_code == 409


def test_unsupported_action_rejected(client):
    r = client.post("/api/actions", json={"resource_id": rid(client, "main-vcn"), "action": "stop"})
    assert r.status_code == 400
    r = client.post("/api/actions", json={"resource_id": rid(client, "demo-server"), "action": "delete"})
    assert r.status_code == 400


def test_manual_resource_details_budget_alert(client):
    rid_ = client.post("/api/resources", json={"name": "vps-1", "status": "running", "monthly_cost": 900}).json()["id"]
    client.patch(f"/api/resources/{rid_}", json={"notes": "hello", "tags": "prod", "monthly_cost": 900, "status": "error"})
    r = next(x for x in client.get("/api/resources").json() if x["id"] == rid_)
    assert r["notes"] == "hello" and r["status"] == "error" and len(client.get(f"/api/resources/{rid_}/history").json()) == 2
    client.put("/api/budgets/custom", json={"monthly_limit": 1000})
    texts = [a["text"] for a in client.get("/api/overview").json()["alerts"]]
    assert any("90%" in t for t in texts) and any("vps-1" in t for t in texts)
    assert client.delete("/api/resources/oracle:inst-1").status_code == 400
    assert client.delete(f"/api/resources/{rid_}").status_code == 200


def test_connections_never_leak_secret(client):
    client.put("/api/connections/vercel", json={"VERCEL_TOKEN": "sekret"})
    body = client.get("/api/connections").text
    assert "sekret" not in body and '"set":true' in body.replace(" ", "")
    client.put("/api/settings", json={"use_mock": True})
