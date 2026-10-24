import os
import httpx
from urllib.parse import urlsplit

class EcosystemAdapters:
    """HTTP contracts are opt-in; unconfigured adapters return explicit skipped states."""
    async def call(self, name: str, path: str, payload: dict) -> dict:
        base = os.getenv(f"{name.upper()}_URL", "").rstrip("/")
        if not base:
            return {"integration": name, "status": "skipped", "reason": "URL not configured"}
        try:
            parsed = urlsplit(base)
        except ValueError:
            return {"integration": name, "status": "error", "reason": "Invalid integration URL or path"}
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or not path.startswith("/"):
            return {"integration": name, "status": "error", "reason": "Invalid integration URL or path"}
        token = os.getenv(f"{name.upper()}_TOKEN", "")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.post(base + path, json={**payload, "dry_run": True}, headers=headers)
                r.raise_for_status()
                return {"integration": name, "status": "ok", "response": r.json()}
        except (httpx.HTTPError, ValueError) as exc:
            return {"integration": name, "status": "error", "reason": f"Upstream request failed ({type(exc).__name__})"}

    async def evaluate(self, run: dict):
        return await self.call("evalops", os.getenv("EVALOPS_PATH", "/api/evaluate"), run)

    async def decide(self, run: dict):
        return await self.call("decisionops", os.getenv("DECISIONOPS_PATH", "/api/decide"), run)

    async def mcp(self, action: dict):
        return await self.call("mcp_nexus", os.getenv("MCP_NEXUS_PATH", "/api/execute"), action)
