# Evaluation

From `backend/` run `python -m app.evaluation`. The runner uses six synthetic cases in `evaluation/cases.json`, emits JSON, and exits nonzero if a case fails or the dataset is empty. It checks expected fixture cause/risk, evidence copied from input and confidence bounds. Cases cover latency, OOM, memory, insufficient telemetry, instruction-like logs and mixed signals. Mixed signals document the fixture's latency-first rule, not a verified diagnosis.

`python -m pytest -q` also checks auth, input validation, approval/rejection, duplicate review, skipped adapters, outgoing contracts and sanitized errors. A test uses actual CrewAI Flow with inference stubbed. These results do not establish live LLM quality, injection resistance or upstream interoperability.

## Proposed live evaluation increment — not implemented

Build 30+ independently labeled incidents, blinded expert review and adversarial logs. Score causal accuracy, evidence grounding, action safety, tool selection, cost and latency. Candidate gates: grounding >= 0.85, safety == 1, no unapproved side effects. Calibrate these against severity and reviewer agreement.

The optional EvalOps HTTP adapter is advisory; it does not enforce these gates or stop tools based on a score. See [integration boundaries](INTEGRATIONS.md).
