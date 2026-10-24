import os
import secrets
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from .models import Incident, Approval, Run
from .agents import investigate, build_incident_flow
from .adapters import EcosystemAdapters

app = FastAPI(title="CrewAI AgentOps Command Center", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")], allow_methods=["GET", "POST"], allow_headers=["*"])
runs: dict[str, Run] = {}  # DEMO ONLY: replace with Postgres and a durable job queue for production
adapters = EcosystemAdapters()

def require_key(x_api_key: str | None):
    expected = os.getenv("API_KEY", "")
    if not expected:
        raise HTTPException(status_code=503, detail="API authentication is not configured")
    if not x_api_key or not secrets.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/health")
def health():
    return {"status": "ok", "mode": os.getenv("AGENT_MODE", "fixture")}

@app.post("/api/incidents", response_model=Run)
def create_incident(incident: Incident, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    try:
        if os.getenv("AGENT_MODE", "fixture") == "live":
            flow = build_incident_flow()()
            flow.state.incident = incident.model_dump()
            flow.kickoff()
            finding = flow.state.finding
        else:
            finding = investigate(incident).model_dump()
        run = Run(id=str(uuid4()), status="awaiting_approval", incident=incident, finding=finding, trace=[{"stage":"investigation", "mode":os.getenv("AGENT_MODE", "fixture")}, {"stage":"approval", "state":"pending"}])
        runs[run.id] = run
        return run
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Investigation failed: {type(exc).__name__}")

@app.get("/api/incidents", response_model=list[Run])
def list_incidents(x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    return list(runs.values())

@app.get("/api/incidents/{run_id}", response_model=Run)
def get_incident(run_id: str, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    if run_id not in runs: raise HTTPException(404, "Run not found")
    return runs[run_id]

@app.post("/api/incidents/{run_id}/approval", response_model=Run)
async def approve(run_id: str, approval: Approval, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    if run_id not in runs: raise HTTPException(404, "Run not found")
    run = runs[run_id]
    if run.status != "awaiting_approval": raise HTTPException(409, "Already reviewed")
    run.status = "approved" if approval.approved else "rejected"
    run.trace.append({"stage":"approval", "reviewer":approval.reviewer, "approved":approval.approved})
    if approval.approved:
        action = {"kind":"draft_remediation", "incident_id":run_id, "recommendation":run.finding.remediation, "dry_run":True}
        # A dry-run flag is a request, not enforcement inside the remote service.
        run.action = {"proposed":action, "decisionops":await adapters.decide(action), "evalops":await adapters.evaluate({**run.model_dump(), "dry_run": True}), "mcp_nexus":await adapters.mcp(action)}
        statuses = [run.action[name]["status"] for name in ("decisionops", "evalops", "mcp_nexus")]
        state = "error" if "error" in statuses else ("skipped" if all(s == "skipped" for s in statuses) else "completed")
        run.trace.append({"stage":"integrations", "state":state, "dry_run":True})
    return run
