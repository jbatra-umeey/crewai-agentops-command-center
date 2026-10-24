# Architecture and boundaries

The ZIP provides one incident investigation vertical slice. FastAPI holds a process-local dictionary of runs. Next.js is a browser client. Live mode uses a CrewAI Flow containing a sequential investigator and reviewer Crew; fixture mode bypasses CrewAI and uses deterministic keyword rules.

## Code map

| Path | Responsibility |
|---|---|
| `backend/app/main.py` | Authentication, incident create/list/read, approval and adapter sequencing |
| `backend/app/models.py` | Pydantic incident, finding, approval and run schemas |
| `backend/app/agents.py` | Fixture investigator, live two-agent Crew, in-memory CrewAI Flow |
| `backend/app/adapters.py` | Optional Jev HTTP requests and explicit skipped/error results |
| `backend/app/evaluation.py` | Offline fixture regression evaluation CLI |
| `backend/tests/` | API, adapter contract mocks, evaluation, actual Flow with stubbed inference |
| `frontend/app/` | Incident form, findings, approval controls, trace display |
| `evaluation/cases.json` | Six synthetic regression cases; no customer telemetry |
| `docker-compose.yml` | Local API and dashboard services |

See [system diagrams](SYSTEM_DIAGRAMS.md), [integration contracts](INTEGRATIONS.md), [deployment](DEPLOYMENT.md) and [validation evidence](VALIDATION.md).

## Request and state semantics

Investigation is synchronous within the HTTP request. Success creates an `awaiting_approval` run. Failure returns HTTP 502 without storing a failed run. Approval updates the in-memory status before awaiting three sequential adapter calls. Rejection never invokes adapters. A repeated review returns HTTP 409, but this is not distributed idempotency or a retry protocol.

`approved` records a human decision, not successful remediation. Adapter errors are recorded in `action` and the integration trace. `executed` and `failed` remain reserved Run schema values and are never assigned by the current API. The CrewAI Flow itself does not pause for human input; its review gate returns and the separate API controls approval.

## Trust boundaries

- Logs are untrusted input. The live prompt instructs agents not to obey embedded commands; this is not a proven injection defense.
- Finding validation enforces types and confidence bounds, not factual accuracy or safety.
- API_KEY is required, compared in constant time, and entered by the operator into an in-memory dashboard input. No credential is bundled. The browser holds the supplied key during the session.
- Reviewer names are self-asserted. A shared key is not per-user authentication, authorization or an audit identity.
- Every adapter request contains `dry_run: true`. An HTTP POST still crosses a trust boundary; the remote endpoint must enforce it. No rollback, allowlist or protocol-level enforcement is provided.
- DecisionOps results are advisory: they do not gate the following EvalOps or MCP Nexus calls. Keep integrations disabled until verified sandbox contracts exist.
- Exceptions are redacted; arbitrary successful upstream JSON is still shown to authenticated clients. Redact upstream responses before handling sensitive data.

## Production gaps

1. PostgreSQL state, migrations, audit integrity, retention, backups and tenant isolation.
2. Durable background jobs, resumption, timeouts, cancellation and distributed idempotency. Use one API process for this demo.
3. OIDC sessions, RBAC, signed reviewer identity, TLS, rate limits and request size limits.
4. Verified Jev schemas, policy decisions that gate actions, sandbox endpoints, egress allowlists, secret management and response redaction.
5. Real provider smoke tests, injection testing, expert-labeled evaluations, quality thresholds, latency/cost budgets and failure recovery.
6. OpenTelemetry instrumentation, dashboards, paging, deployment/load/chaos tests and dependency vulnerability remediation.
7. Container digests, non-root hardened images, SBOMs, a license decision and supply-chain review. Lockfiles are not a certification.

No external deployment or real remediation was performed during publication.
