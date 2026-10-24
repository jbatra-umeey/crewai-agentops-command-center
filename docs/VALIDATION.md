# Validation and publication record

Validated on 2026-10-23, including rerunning checks after workspace recovery. This is a reference implementation, not a production-readiness certification. GitHub Actions results are separate from the local results below.

## Source and preservation

Source: `crewai-agentops-command-center.zip`, SHA-256 `16f3fd04e3361532e6b2f25c6a849dda41c5ea6f8a0d651662540764e8e9f1bd`.

All original source/configuration/documentation paths are retained. Python bytecode and pytest caches shipped in the archive were excluded as generated artifacts. Git does not store empty directories. The target initially contained only its title-only README at commit `a62e2c067c433f536a19ae9b1a98260fda142d8b`; this import expands that placeholder. Publication builds on the existing tree and history, preserving unrelated files and checking the branch head before updating main.

## Local evidence

| Check | Result | Scope |
|---|---|---|
| Backend suite | 26 passed | Auth, validation, approval/rejection, duplicate review, HTTP contract mocks and actual CrewAI Flow with stubbed inference |
| Fixture evaluation CLI | 6 / 6 passed | Synthetic fixture regression, not LLM quality |
| Python dependency consistency | pip check passed | Application dependency installation |
| Next.js production build | Passed | Compile, type checks, static generation |
| Frontend audit | 0 vulnerabilities reported | npm audit on installed lockfile at validation time |
| Backend dependency audit | 7 entries in 3 packages | 6 unique advisory IDs; unresolved below |
| HTTP smoke | Passed | Real Uvicorn fixture endpoints and production Next.js page response |
| Mermaid syntax | 7 / 7 parsed | Syntax parser validation, not visual screenshot review |
| Compose and CI YAML | Parsed; structural checks passed | Services, loopback bindings and adapter variables; not Docker runtime validation |
| Secret scan | 0 candidates | detect-secrets over tracked files and manual configuration review |
| Git whitespace check | Passed | git diff --cached --check |

Validation used Python 3.12, Node 24, CrewAI 1.15.28, FastAPI 0.161.1, Pydantic 2.12.5, httpx 0.28.1 and pytest 9.1.1. Application dependency snapshots are checked in; scanner tooling is excluded from the runtime snapshot.

## Repairs

- Removed built-in server/browser credentials; authentication fails closed without a configured key and uses constant-time comparison.
- Added loopback Compose bindings, environment/secret ignore rules and Docker build-context exclusions.
- Forwarded adapter paths/tokens and browser API build URL through Compose.
- Fixed missing top-level EvalOps dry-run flag and forced dry-run on every outgoing adapter payload.
- Redacted exception content and rejected malformed or credential-bearing upstream URLs.
- Distinguished skipped/error integration traces, rejected unknown agent modes and removed invented recent-deployment evidence from the dashboard.
- Added regression tests, fixture evaluation, dependency snapshots and expanded CI.
- Upgraded Next.js 14.2.35 to 15.5.28 and overrode PostCSS to 8.5.31. The resulting frontend audit is clean. [Maintainer advisory](https://github.com/vercel/next.js/security/advisories/GHSA-2464-fhr4-w9xw).
- Removed unverified claims about upstream repository contents and separated implemented behavior from proposed production topology.

## Unresolved dependency advisories

Command: `pip-audit -r backend/requirements.lock.txt --no-deps --disable-pip --format=json`.

| Package | Unique advisory IDs | Constraint |
|---|---|---|
| chromadb 1.5.9 | PYSEC-2026-311, PYSEC-2026-3813, PYSEC-2026-3814, PYSEC-2026-3815 | Scanner supplied no fixed versions; CrewAI requires chromadb~=1.5.9 |
| mcp 1.28.1 | CVE-2026-59951 | Fixes reported at 1.30.0 / 2.2.0; CrewAI requires mcp~=1.28.1 |
| uv 0.11.33 | PYSEC-2026-4321 | Fix reported at 0.13.4; crewai-cli requires uv~=0.11.6 |

PYSEC-2026-311 was reported twice: seven entries represent six distinct IDs. This application does not launch a Chroma or MCP server, but that is not a complete exploitability assessment. Resolve or formally assess these dependencies before production. Incompatible upgrades were not forced merely to clear a scanner. Container images and installer tooling also need their own audit.

## Not verified and remaining work

- Actual LLM provider inference, agent quality, cost, latency or injection resistance.
- Deployed Jev DecisionOps/EvalOps/MCP Nexus contracts, authentication or tool execution. Only local HTTP mocks were used.
- Docker image builds, Compose startup or external deployment: Docker is unavailable in this environment.
- Browser-driven end-to-end interaction, load, chaos/recovery testing or production identity controls.
- Comprehensive secret absence, penetration testing, dependency exploitability or supply-chain certification. Zero scan candidates is evidence, not a guarantee.

Production still needs durable storage/queues, OIDC/RBAC, trusted reviewer identity, tenant isolation, distributed idempotency, enforced tool policy, monitoring and verified upstream contracts. See [architecture gaps](ARCHITECTURE.md) and [integration prerequisites](INTEGRATIONS.md).
