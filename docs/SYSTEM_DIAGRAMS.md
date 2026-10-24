# System diagrams

Diagrams describe the checked-in implementation unless labeled future target. Real LLM inference, upstream interoperability and container deployment were not verified by local tests. No credential is bundled.

## 1. Component architecture

```mermaid
flowchart TD
  UI[Next.js browser dashboard] -->|API key and incident| API[FastAPI control plane]
  API --> MODE{Agent mode}
  MODE -->|fixture| FIX[Deterministic investigator]
  MODE -->|live| FLOW[CrewAI Flow]
  FLOW --> CREW[Sequential investigator and reviewer Crew]
  CREW --> LLM[Configured model provider]
  LLM --> CREW
  FIX --> FINDING[Pydantic Finding]
  CREW --> FINDING
  FINDING --> STORE[(Process-local runs)]
  API <--> STORE
  UI -->|Approve or reject| API
  API -->|Approved only| ADAPTERS[Sequential HTTP adapters]
  ADAPTERS -.->|Opt-in dry-run requests| JEV[Jev sandbox endpoints]
```

One API process investigates, stores state and handles review. Model calls occur only in live mode. Dotted external links represent unverified contracts.

## 2. Incident and approval sequence

```mermaid
sequenceDiagram
  actor User as Operator
  participant UI as Dashboard
  participant API as FastAPI
  participant Engine as Fixture or CrewAI
  participant External as Jev adapters
  User->>UI: Enter key and incident
  UI->>API: POST incident
  API->>API: Authenticate and validate
  API->>Engine: Investigate synchronously
  alt Investigation succeeds
    Engine-->>API: Validated finding
    API->>API: Save awaiting_approval run
    API-->>UI: Run and finding
    User->>UI: Approve or reject
    UI->>API: POST approval
    API->>API: Authenticate and check pending status
    alt Rejected
      API->>API: Record rejected status
    else Approved
      API->>API: Record approved status
      API->>External: DecisionOps request
      External-->>API: ok, error or skipped
      API->>External: EvalOps request
      External-->>API: ok, error or skipped
      API->>External: MCP Nexus request
      External-->>API: ok, error or skipped
      API->>API: Record integration results
    end
    API-->>UI: Reviewed run
  else Investigation fails
    Engine-->>API: Exception
    API-->>UI: HTTP 502, no run saved
  end
```

Calls are sequential. An adapter error does not stop subsequent requests. Duplicate review returns 409. Successful approval HTTP response does not prove upstream success or tool execution.

## 3. Live CrewAI execution

```mermaid
sequenceDiagram
  participant API as Incident API
  participant Flow as CrewAI Flow
  participant Crew as Sequential Crew
  participant LLM as Model provider
  API->>Flow: Set incident and kickoff
  Flow->>Crew: Triage invokes investigate
  Crew->>LLM: Investigator task with logs
  LLM-->>Crew: Investigation context
  Crew->>LLM: Reviewer task with prior context
  LLM-->>Crew: Structured finding
  Crew->>Crew: Validate Finding schema
  Crew-->>Flow: Finding
  Flow->>Flow: Save finding and return review_gate
  Flow-->>API: Awaiting approval result
```

The actual Flow was tested with inference stubbed. Provider traffic above is the intended live code path, not an observed transaction. The review gate does not durably suspend execution.

## 4. Current local deployment topology

```mermaid
flowchart TD
  subgraph Host[Local development host]
    Browser[Browser]
    subgraph Compose[Compose network]
      Web[Next.js container on port 3000]
      API[FastAPI container on port 8000]
      Memory[(In-memory runs)]
      API --> Memory
      Web -.->|Startup health dependency| API
    end
    Browser -->|Loopback port 3000| Web
    Browser -->|Loopback port 8000 and key| API
  end
  API -.->|Live mode only| Model[Model provider]
  API -.->|Configured URLs only| Sandbox[Jev sandbox services]
```

The browser calls FastAPI directly, not through a Next.js proxy. Compose has no database, Redis, worker service or persistent workflow volume. Restarting the API loses all runs.

## 5. Implemented lifecycle

```mermaid
stateDiagram-v2
  [*] --> Investigating: Valid authenticated POST
  Investigating --> AwaitingApproval: Validated finding stored
  Investigating --> RequestFailed: Exception returns 502
  RequestFailed --> [*]: No run persisted
  AwaitingApproval --> Rejected: approved false
  AwaitingApproval --> Approved: approved true
  state Approved {
    [*] --> CallingAdapters
    CallingAdapters --> ResultsRecorded: ok, error or skipped
  }
  Rejected --> [*]
  Approved --> [*]
```

Only `awaiting_approval`, `approved` and `rejected` are persisted by the API. Investigating/request failure are transient request states. Nested approval stages represent trace/action progress, not additional Run status values. `executed` and `failed` are reserved schema values. Integration errors do not change approval status. Process failure can lose or interrupt every state.

## 6. Integration result handling

```mermaid
flowchart TD
  Approved[Approved run] --> Config{URL configured?}
  Config -->|No| Skip[Return skipped]
  Config -->|Yes| Validate{Valid HTTP URL and path?}
  Validate -->|No| Error[Return redacted error]
  Validate -->|Yes| Post[POST with dry_run true]
  Post --> Response{2xx and valid JSON?}
  Response -->|No or timeout| Error
  Response -->|Yes| Ok[Return ok with response]
  Skip --> Next[Record result and continue]
  Error --> Next
  Ok --> Next
```

This applies independently to all three adapters. DecisionOps does not enforce an execution policy. A dry-run field cannot guarantee that a remote service avoids side effects.

## 7. Future production topology — not implemented

```mermaid
flowchart TD
  Browser[Operator browser] --> Edge[HTTPS ingress and WAF]
  Edge --> UI[Dashboard replicas]
  Edge --> API[API replicas]
  API --> Auth[OIDC and role authorization]
  API --> DB[(PostgreSQL state and audit)]
  API --> Queue[(Durable job queue)]
  Queue --> Workers[Resumable CrewAI workers]
  Workers <--> DB
  Workers --> Policy[Deterministic policy gate]
  Policy --> Approval[Verified human approval]
  Approval --> Gateway[Allowlisted tool gateway]
  Gateway --> Systems[Approved external systems]
  Workers --> Telemetry[OpenTelemetry collector]
  API --> Telemetry
  Secrets[Secret manager] -.-> API
  Secrets -.-> Workers
```

Production additionally requires distributed idempotency, retries, audit integrity, verified contracts, monitoring and dependency remediation. See [architecture gaps](ARCHITECTURE.md).
