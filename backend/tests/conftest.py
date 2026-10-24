import secrets
import pytest
from app.main import runs

TEST_API_KEY = secrets.token_urlsafe(32)

@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    monkeypatch.setenv("API_KEY", TEST_API_KEY)
    monkeypatch.setenv("AGENT_MODE", "fixture")
    monkeypatch.setenv("CREWAI_TELEMETRY_DISABLED", "true")
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
    for name in ("DECISIONOPS", "EVALOPS", "MCP_NEXUS"):
        for suffix in ("URL", "PATH", "TOKEN"):
            monkeypatch.delenv(f"{name}_{suffix}", raising=False)
    runs.clear()
    yield
    runs.clear()
