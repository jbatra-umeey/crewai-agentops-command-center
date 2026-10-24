# Local deployment and operations

## Compose

1. Copy `.env.example` to `.env`.
2. Generate a key with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` and set `API_KEY` in `.env`. Leave integration URLs empty.
3. Run `docker compose config --quiet` and `docker compose up --build`.
4. Open http://localhost:3000, enter the same key, submit an incident, then approve or reject. Approval without upstream URLs returns explicit skipped results.
5. API docs: http://localhost:8000/docs. Health: http://localhost:8000/health.
6. Stop with `docker compose down`. API restarts erase runs.

Ports bind to loopback. Dockerfiles use Python 3.12 and Node 24. Dashboard startup depends on API health, but `/health` only proves process availability, not valid auth, model access or upstream readiness. Container runtime validation is not implied by source tests.

## Without Docker

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.lock.txt
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --env-file ../.env
```

In another terminal run `cd frontend && npm ci && npm run dev`. For production-mode local serving use `npm run build && npm run start`. Refresh clears the dashboard key because it is held only in component state.

`NEXT_PUBLIC_API_URL` is compiled into the browser bundle. Use a browser-reachable URL, not the Compose service hostname `api`. Change Compose build arguments and rebuild. `FRONTEND_ORIGIN` controls the API's allowed browser origin.

## Live CrewAI

Set `AGENT_MODE=live`, `OPENAI_API_KEY`, and `CREWAI_MODEL`; restart the API. This sends logs to the model provider and may incur costs. Sanitize input first. Live provider calls were not tested during publication. Set `CREWAI_TELEMETRY_DISABLED=true` and `OTEL_SDK_DISABLED=true` in the API environment to disable their respective telemetry paths.

## Troubleshooting

| Symptom | Check |
|---|---|
| Compose refuses to start | API_KEY must be nonempty in .env |
| HTTP 503 | Authentication not configured |
| HTTP 401 | Browser key must match server key |
| Browser fetch error | API URL, host binding, CORS and HTTP/HTTPS alignment |
| HTTP 502 | Agent mode spelling and model/provider configuration |
| HTTP 409 | Run already reviewed |
| Adapter skipped | URL unset; expected default |
| Adapter error | Verify upstream contract and server settings without exposing tokens |

Use a single API process. The reference lacks shared state, durable workers, production identity and tenant isolation. Do not expose it on the internet as a production multi-user service.
