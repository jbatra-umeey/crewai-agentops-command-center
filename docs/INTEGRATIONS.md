# Jev integration contracts

The original optional adapters are preserved. These are configurable HTTP bridges, not a native MCP client. Paths below are **local defaults, not verified upstream API contracts**. No live Jev service was called during publication. Repository links identify the intended projects, without asserting their current deployment or contents.

| Project | Prefix | Default POST path | Intended purpose |
|---|---|---|---|
| [Jev DecisionOps](https://github.com/jbatra-umeey/jev-decisionops) | `DECISIONOPS` | `/api/decide` | Advisory assessment of proposed action |
| [Jev EvalOps](https://github.com/jbatra-umeey/jev-evalops) | `EVALOPS` | `/api/evaluate` | Evaluation of incident and finding |
| [Jev MCP Nexus](https://github.com/jbatra-umeey/jev-mcp-nexus) | `MCP_NEXUS` | `/api/execute` | Sandbox tool gateway request |

Each prefix supports `_URL`, `_PATH`, `_TOKEN`. Compose forwards all nine settings. `_URL` is an HTTP(S) base URL without embedded credentials, query or fragment; `_PATH` begins with `/`. The token becomes a server-side Bearer header. Use local `.env` for development and a secret manager for production. Never accept a destination from untrusted incident content.

## Payloads

DecisionOps and MCP Nexus receive:

```json
{
  "kind": "draft_remediation",
  "incident_id": "<run-id>",
  "recommendation": "<finding.remediation>",
  "dry_run": true
}
```

EvalOps receives the serialized Run with top-level `dry_run: true`: `id`, `status: approved`, `incident`, `finding`, `action: null`, and `trace` through approval. It does not receive the preceding DecisionOps result because `run.action` is assigned after all calls finish. No reference answer, scoring rubric or release quality gate is supplied automatically.

An upstream success must be a 2xx response with JSON. No domain response schema is validated: `ok` means HTTP/JSON success, not policy approval, execution success or evaluation quality.

| Result | Meaning |
|---|---|
| `skipped` | No URL; no HTTP request sent |
| `ok` | 2xx response decoded as JSON, returned under `response` |
| `error` | Configuration, network, timeout, HTTP or JSON failure; redacted reason |

Requests are sequential: DecisionOps, EvalOps, MCP Nexus. Failures do not stop subsequent calls. There are no retries and no redirects. The HTTP client has a five-second timeout per operation, not a global investigation deadline. The Run remains `approved` even if integrations fail. Inspect `action` and `trace`.

## Local contract checks

MockTransport tests inspect all three paths, Bearer headers and dry-run flags; verify the EvalOps incident/finding body; and exercise non-2xx, timeout, malformed JSON, invalid URL and disabled configuration. Rejection tests prove adapters are not invoked. These mocks verify this repository only.

## Before connecting a real service

1. Inspect deployed OpenAPI/protocol schemas and implement request/response mappings.
2. Confirm the sandbox endpoint enforces dry-run and never mutates production systems.
3. Configure scoped credentials and allowlisted destinations. Plain HTTP is for trusted local use only.
4. Add upstream-owned contract tests and negative policy cases. Make deny decisions stop tool calls before enabling execution.
5. Define idempotency, retry/backoff, response size limits, error taxonomy and audit linkage.
6. Verify authentication, latency, cancellation, redaction and outage recovery against the sandbox and retain evidence.

A genuine MCP integration additionally requires transport/session negotiation, tool discovery, argument validation and policy enforcement. Naming an HTTP adapter MCP Nexus does not implement these capabilities.
