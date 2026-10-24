from fastapi.testclient import TestClient
from app.main import app, runs
from conftest import TEST_API_KEY
client = TestClient(app)
HEADERS = {"x-api-key": TEST_API_KEY}
DATA = {"title":"Checkout latency regression", "service":"checkout", "severity":"SEV2", "logs":["upstream timeout after 3000ms", "p95 latency 8s"], "recent_changes":["gateway deployment"]}

def test_health():
    assert client.get("/health").status_code == 200

def test_auth():
    assert client.post("/api/incidents", json=DATA).status_code == 401

def test_investigation_approval():
    r = client.post("/api/incidents", headers=HEADERS, json=DATA)
    assert r.status_code == 200, r.text
    run = r.json(); assert run["status"] == "awaiting_approval"
    assert "timeout" in run["finding"]["root_cause"].lower()
    approved = client.post(f"/api/incidents/{run['id']}/approval", headers=HEADERS, json={"approved":True,"reviewer":"demo-reviewer"})
    assert approved.status_code == 200
    assert approved.json()["action"]["proposed"]["dry_run"] is True
    assert client.post(f"/api/incidents/{run['id']}/approval", headers=HEADERS, json={"approved":True,"reviewer":"demo-reviewer"}).status_code == 409

def test_rejection():
    run = client.post("/api/incidents", headers=HEADERS, json=DATA).json()
    r = client.post(f"/api/incidents/{run['id']}/approval", headers=HEADERS, json={"approved":False,"reviewer":"reviewer"})
    assert r.json()["status"] == "rejected"
    assert r.json()["action"] is None
