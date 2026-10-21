"""Mock data so the whole app works without cloud accounts (Phase 1)."""
from ..models import normalize

_SEED = {
    "oracle": [
        ("inst-1", "compute_instance", "demo-server", "running", "ap-mumbai-1"),
        ("inst-2", "compute_instance", "build-box", "stopped", "ap-mumbai-1"),
        ("vcn-1", "network", "main-vcn", "running", "ap-mumbai-1"),
    ],
    "google": [
        ("vm-1", "compute_instance", "api-vm", "running", "asia-south1"),
        ("vm-2", "compute_instance", "batch-worker", "stopped", "asia-south1"),
        ("bkt-1", "storage", "assets-bucket", "running", "asia-south1"),
    ],
    "vercel": [
        ("prj-1", "project", "portfolio-site", "running", "global"),
        ("prj-2", "project", "docs-site", "running", "global"),
        ("prj-3", "project", "staging-app", "error", "global"),
    ],
}
_state: dict[str, dict[str, str]] = {}


def reset() -> None:
    _state.clear()


def resources(provider: str) -> list[dict]:
    st = _state.setdefault(provider, {})
    return [normalize(provider, nid, rtype, name, st.get(nid, status), region)
            for nid, rtype, name, status, region in _SEED[provider]]


def set_status(provider: str, native_id: str, status: str) -> None:
    _state.setdefault(provider, {})[native_id] = status
