import os

import httpx

from ..config import use_mock
from ..models import normalize
from . import mock
from .base import Provider, ProviderError

API = "https://api.vercel.com"
STATE_MAP = {"READY": "running", "BUILDING": "deploying", "QUEUED": "deploying",
             "INITIALIZING": "deploying", "ERROR": "error", "CANCELED": "stopped"}


class VercelProvider(Provider):
    key, label = "vercel", "Vercel"
    actions = {"project": ["redeploy"]}

    def configured(self) -> bool:
        return bool(os.getenv("VERCEL_TOKEN"))

    def _client(self) -> httpx.Client:
        params = {"teamId": os.environ["VERCEL_TEAM_ID"]} if os.getenv("VERCEL_TEAM_ID") else {}
        return httpx.Client(base_url=API, timeout=15, params=params,
                            headers={"Authorization": f"Bearer {os.environ['VERCEL_TOKEN']}"})

    def list_resources(self):
        if use_mock():
            return mock.resources(self.key)
        if not self.configured():
            raise ProviderError("VERCEL_TOKEN is not set.")
        try:
            with self._client() as c:
                r = c.get("/v9/projects")
                r.raise_for_status()
                out = []
                for p in r.json().get("projects", []):
                    latest = (p.get("latestDeployments") or [{}])[0]
                    out.append(normalize(
                        self.key, p["id"], "project", p["name"],
                        STATE_MAP.get(latest.get("readyState", ""), "unknown"), "global",
                        {"latest_deployment": latest.get("id")}))
                return out
        except httpx.HTTPError as e:
            raise ProviderError(f"Vercel API request failed: {type(e).__name__}") from e

    def execute(self, action, resource):
        native = resource["id"].split(":", 1)[1]
        if use_mock():
            mock.set_status(self.key, native, "running")
            return {"detail": "mock redeploy applied"}
        dep = resource["meta"].get("latest_deployment")
        if not dep:
            raise ProviderError("No previous deployment to redeploy from.")
        try:
            with self._client() as c:
                # Untested against a live account; verify against current Vercel docs.
                r = c.post("/v13/deployments", params={"forceNew": 1},
                           json={"name": resource["name"], "deploymentId": dep, "target": "production"})
                r.raise_for_status()
                return {"detail": "redeploy triggered", "request_id": r.headers.get("x-vercel-id")}
        except httpx.HTTPError as e:
            raise ProviderError(f"Vercel API request failed: {type(e).__name__}") from e
