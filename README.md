# CrewAI AgentOps Command Center

An incident investigation reference application with a FastAPI backend, Next.js dashboard, CrewAI Flow and two-agent Crew, human review, offline evaluation, and optional HTTP adapters for Jev DecisionOps, Jev EvalOps and Jev MCP Nexus.

**Status: executable reference implementation, not production-certified.** Fixture mode needs no LLM. Live mode is implemented but provider inference and Jev interoperability are unverified. All workflow state is in memory. See [validation evidence and gaps](docs/VALIDATION.md).

## Quick start

```bash
cp .env.example .env
# Generate a local key, then set API_KEY in .env to its output:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
docker compose up --build
```

Open http://localhost:3000, enter your local key, run an investigation, review evidence, then approve or reject. Integration URLs are empty by default, so approval reports `skipped` for each adapter. API docs: http://localhost:8000/docs. Ports bind to loopback. Container validation remains separate from source/build checks.

## Included

- FastAPI incident create/list/detail and approval endpoints, Pydantic schemas and required API key.
- Fixture investigator and live CrewAI Flow with investigator/reviewer agents and structured findings.
- Dashboard for evidence, confidence, risk, remediation, review and trace inspection.
- Three optional Jev adapters with configurable paths/tokens, dry-run requests and explicit failure results.
- Six synthetic evaluation cases, API/adapter regression tests and actual CrewAI Flow testing with stubbed inference.
- Dockerfiles, Compose, Python dependency snapshot, npm lockfile and GitHub Actions validation.
- Seven Mermaid component, sequence, topology, integration and state-machine diagrams.

## Tests and evaluation

Use Python 3.12 and Node 24:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.lock.txt
cd backend
python -m pytest -q
python -m app.evaluation
cd ../frontend
npm ci
npm run build
npm audit --audit-level=high
```

Evaluation cases test deterministic fixture behavior, not live model quality. `requirements.txt` records direct dependency ranges; `requirements.lock.txt` records the resolved Linux validation environment. Docker and CI install the snapshot.

## API example

Set `API_KEY` in your terminal to the local value configured in `.env`:

```bash
curl -X POST http://localhost:8000/api/incidents \
  -H 'Content-Type: application/json' -H "x-api-key: $API_KEY" \
  -d '{"title":"Checkout latency regression","service":"checkout","severity":"SEV2","logs":["upstream timeout after 3000ms","p95 latency 8s"]}'
```

Use returned `id` in `POST /api/incidents/{id}/approval` with `{"approved":true,"reviewer":"your-id"}` and the same headers. Approved means reviewed, not successfully remediated. Repeated review returns 409.

## Live mode and integrations

Set `AGENT_MODE=live`, `OPENAI_API_KEY`, `CREWAI_MODEL` and restart for live inference. This sends logs to the provider and may incur costs. No live model call was made during publication.

Jev adapters are preserved under `DECISIONOPS_*`, `EVALOPS_*`, `MCP_NEXUS_*`. Paths are configurable assumptions, not verified upstream contracts. Every request includes `dry_run: true`; enforcement depends on the remote service. DecisionOps does not yet gate MCP calls. Keep URLs disabled until sandbox compatibility is verified.

## Documentation

- [Architecture and production boundaries](docs/ARCHITECTURE.md)
- [Mermaid system diagrams](docs/SYSTEM_DIAGRAMS.md)
- [Jev integration contracts](docs/INTEGRATIONS.md)
- [Evaluation and roadmap](docs/EVALUATION.md)
- [Deployment and troubleshooting](docs/DEPLOYMENT.md)
- [Validation and remaining gaps](docs/VALIDATION.md)

## Security and operational limits

Generate your own local key; no built-in credential is provided and `.env` is ignored. Reviewer identity is self-asserted, state is process-local, and OIDC/RBAC, durable jobs, tenant isolation, rate limits and audited tool policy are absent. A browser-entered shared key is for an isolated local demo. Address the documented gaps and unresolved dependency advisories before production use.
