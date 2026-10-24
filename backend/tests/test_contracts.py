import asyncio
import json
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.adapters import EcosystemAdapters
from app import agents
from conftest import TEST_API_KEY

client = TestClient(app)
HEADERS = {"x-api-key": TEST_API_KEY}
DATA = {"title": "Checkout latency", "service": "checkout", "logs": ["timeout"]}

@pytest.mark.parametrize("method,path,body", [
    ("GET", "/api/incidents", None),
    ("GET", "/api/incidents/missing", None),
    ("POST", "/api/incidents", DATA),
    ("POST", "/api/incidents/missing/approval", {"approved": True, "reviewer": "test"}),
])
def test_protected_routes(method, path, body):
    assert client.request(method, path, json=body).status_code == 401
    assert client.request(method, path, json=body, headers={"x-api-key": "invalid"}).status_code == 401

def test_unconfigured_auth_fails_closed(monkeypatch):
    monkeypatch.delenv("API_KEY")
    assert client.get("/api/incidents", headers=HEADERS).status_code == 503

@pytest.mark.parametrize("payload", [{**DATA, "logs": []}, {**DATA, "severity": "SEV9"}, {**DATA, "title": "x"}])
def test_input_validation(payload):
    assert client.post("/api/incidents", headers=HEADERS, json=payload).status_code == 422

def test_missing_runs():
    assert client.get("/api/incidents/missing", headers=HEADERS).status_code == 404
    assert client.post("/api/incidents/missing/approval", headers=HEADERS, json={"approved": False, "reviewer": "test"}).status_code == 404

def test_all_integrations_receive_dry_run(monkeypatch):
    requests = []
    original_client = httpx.AsyncClient
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"accepted": True, "dry_run": True})
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: original_client(transport=httpx.MockTransport(handler), **kw))
    for name in ("DECISIONOPS", "EVALOPS", "MCP_NEXUS"):
        monkeypatch.setenv(f"{name}_URL", "https://upstream.invalid")
        monkeypatch.setenv(f"{name}_PATH", f"/contract/{name.lower()}")
        monkeypatch.setenv(f"{name}_TOKEN", TEST_API_KEY)
    run = client.post("/api/incidents", headers=HEADERS, json=DATA).json()
    assert requests == []
    response = client.post(f"/api/incidents/{run['id']}/approval", headers=HEADERS, json={"approved": True, "reviewer": "test"})
    assert response.status_code == 200
    assert len(requests) == 3
    assert [r.url.path for r in requests] == ["/contract/decisionops", "/contract/evalops", "/contract/mcp_nexus"]
    for request in requests:
        assert json.loads(request.content)["dry_run"] is True
        assert request.headers["Authorization"] == f"Bearer {TEST_API_KEY}"
    evaluation = json.loads(requests[1].content)
    assert evaluation["incident"] == {**DATA, "severity": "SEV2", "recent_changes": []}
    assert evaluation["finding"]["evidence"] == ["timeout"]
    assert response.json()["trace"][-1]["state"] == "completed"

def test_rejection_does_not_contact_adapters(monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Rejected incident must not invoke adapters")
    monkeypatch.setattr(EcosystemAdapters, "call", forbidden)
    run = client.post("/api/incidents", headers=HEADERS, json=DATA).json()
    result = client.post(f"/api/incidents/{run['id']}/approval", headers=HEADERS, json={"approved": False, "reviewer": "test"})
    assert result.json()["status"] == "rejected"
    assert result.json()["action"] is None

@pytest.mark.parametrize("failure", ["http", "timeout", "json"])
def test_adapter_failure_is_explicit_and_redacted(monkeypatch, failure):
    original_client = httpx.AsyncClient
    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("sensitive upstream details", request=request)
        if failure == "json":
            return httpx.Response(200, text="sensitive upstream details")
        return httpx.Response(500, text="sensitive upstream details")
    monkeypatch.setenv("EVALOPS_URL", "https://upstream.invalid")
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: original_client(transport=httpx.MockTransport(handler), **kw))
    result = asyncio.run(EcosystemAdapters().evaluate({"dry_run": False}))
    assert result["status"] == "error"
    assert "sensitive" not in result["reason"]
    assert "upstream.invalid" not in result["reason"]

@pytest.mark.parametrize("base", ["file:///tmp/data", "https://user:" + TEST_API_KEY + "@upstream.invalid", "https://[invalid"])
def test_bad_adapter_configuration(monkeypatch, base):
    monkeypatch.setenv("DECISIONOPS_URL", base)
    result = asyncio.run(EcosystemAdapters().decide({}))
    assert result["status"] == "error"
    assert TEST_API_KEY not in result["reason"]

def test_unconfigured_integrations_are_skipped():
    run = client.post("/api/incidents", headers=HEADERS, json=DATA).json()
    result = client.post(f"/api/incidents/{run['id']}/approval", headers=HEADERS, json={"approved": True, "reviewer": "test"}).json()
    assert result["trace"][-1]["state"] == "skipped"
    for name in ("decisionops", "evalops", "mcp_nexus"):
        assert result["action"][name]["status"] == "skipped"

def test_unknown_mode_does_not_silently_use_fixture(monkeypatch):
    monkeypatch.setenv("AGENT_MODE", "lve")
    assert client.post("/api/incidents", headers=HEADERS, json=DATA).status_code == 502

def test_real_crewai_flow_with_stubbed_inference(monkeypatch):
    # Actual Flow dispatch only: does not verify an LLM/provider.
    monkeypatch.setenv("AGENT_MODE", "live")
    monkeypatch.setattr(agents, "investigate", agents.fixture_investigation)
    response = client.post("/api/incidents", headers=HEADERS, json=DATA)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "awaiting_approval"
    assert response.json()["finding"]["evidence"] == ["timeout"]
