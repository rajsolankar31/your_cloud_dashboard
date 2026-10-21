from datetime import datetime, timezone

STATUSES = {"running", "stopped", "deploying", "error", "unknown"}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize(provider: str, native_id: str, resource_type: str, name: str,
              status: str, region: str | None = None, meta: dict | None = None) -> dict:
    """Common resource shape shared by every provider adapter."""
    return {
        "id": f"{provider}:{native_id}",
        "provider": provider,
        "resource_type": resource_type,
        "name": name,
        "status": status if status in STATUSES else "unknown",
        "region": region,
        "last_checked": now(),
        "meta": meta or {},
    }
