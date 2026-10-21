import uuid

from ..database.db import conn
from ..models import STATUSES, now
from ..providers import REGISTRY
from . import sync


class ManageError(Exception):
    def __init__(self, msg, code=400):
        super().__init__(msg)
        self.code = code


def _details(c, rid, d):
    cost = d.get("monthly_cost")
    if cost is not None and cost < 0:
        raise ManageError("Monthly cost cannot be negative.")
    c.execute("""INSERT INTO details(resource_id,notes,tags,owner,monthly_cost) VALUES(?,?,?,?,?)
                 ON CONFLICT(resource_id) DO UPDATE SET notes=excluded.notes,tags=excluded.tags,
                 owner=excluded.owner,monthly_cost=excluded.monthly_cost""",
              (rid, d.get("notes") or "", d.get("tags") or "", d.get("owner") or "", cost))


def create(d: dict) -> dict:
    name = (d.get("name") or "").strip()
    if not name:
        raise ManageError("Name is required.")
    status = d.get("status", "unknown")
    if status not in STATUSES:
        raise ManageError("Invalid status.")
    rid, t = f"custom:{uuid.uuid4().hex[:8]}", now()
    with conn() as c:
        c.execute("INSERT INTO resources(id,provider,resource_type,name,status,region,last_checked,stale,meta) "
                  "VALUES(?,?,?,?,?,?,?,0,'{}')",
                  (rid, "custom", d.get("resource_type") or "server", name, status, d.get("region") or "", t))
        c.execute("INSERT INTO snapshots(resource_id,status,checked_at) VALUES(?,?,?)", (rid, status, t))
        _details(c, rid, d)
    return {"id": rid}


def update(rid: str, d: dict) -> dict:
    with conn() as c:
        r = c.execute("SELECT * FROM resources WHERE id=?", (rid,)).fetchone()
        if not r:
            raise ManageError("Resource not found.", 404)
        _details(c, rid, d)
        if r["provider"] == "custom":
            name = (d.get("name") or r["name"]).strip()
            status = d.get("status", r["status"])
            if not name or status not in STATUSES:
                raise ManageError("Invalid name or status.")
            t = now()
            c.execute("UPDATE resources SET name=?,resource_type=?,region=?,status=?,last_checked=? WHERE id=?",
                      (name, d.get("resource_type") or r["resource_type"], d.get("region", r["region"]), status, t, rid))
            if status != r["status"]:
                c.execute("INSERT INTO snapshots(resource_id,status,checked_at) VALUES(?,?,?)", (rid, status, t))
    return {"id": rid}


def delete(rid: str) -> dict:
    if not rid.startswith("custom:"):
        raise ManageError("Only manual entries can be deleted. Synced resources follow the provider.")
    with conn() as c:
        for t, col in (("resources", "id"), ("details", "resource_id"), ("snapshots", "resource_id")):
            c.execute(f"DELETE FROM {t} WHERE {col}=?", (rid,))
    return {"deleted": rid}


def set_budget(provider: str, limit):
    if provider not in REGISTRY:
        raise ManageError("Unknown provider.", 404)
    with conn() as c:
        if limit in (None, 0):
            c.execute("DELETE FROM budgets WHERE provider=?", (provider,))
        elif limit < 0:
            raise ManageError("Budget cannot be negative.")
        else:
            c.execute("INSERT INTO budgets(provider,monthly_limit) VALUES(?,?) "
                      "ON CONFLICT(provider) DO UPDATE SET monthly_limit=excluded.monthly_limit", (provider, limit))


def reset_synced() -> None:
    """Called when switching sample/live mode so the two never mix."""
    with conn() as c:
        c.execute("DELETE FROM resources WHERE provider!='custom'")
        c.execute("DELETE FROM snapshots WHERE resource_id NOT LIKE 'custom:%'")
        c.execute("DELETE FROM details WHERE resource_id NOT LIKE 'custom:%'")
        c.execute("DELETE FROM sync_runs")


def overview() -> dict:
    res, provs = sync.list_resources(), sync.provider_summaries()
    with conn() as c:
        budgets = {r["provider"]: r["monthly_limit"] for r in c.execute("SELECT * FROM budgets")}
    cost = {}
    for r in res:
        cost[r["provider"]] = cost.get(r["provider"], 0) + (r["monthly_cost"] or 0)
    alerts = []
    for p in provs:
        if p["last_ok"] is False:
            alerts.append({"level": "bad", "text": f"{p['label']} sync failed: {p['error']}"})
    for r in res:
        if r["stale"]:
            alerts.append({"level": "warn", "text": f"{r['name']} ({r['provider']}) has stale data."})
        elif r["status"] == "error":
            alerts.append({"level": "bad", "text": f"{r['name']} ({r['provider']}) is in an error state."})
    for k, lim in budgets.items():
        pct = cost.get(k, 0) / lim * 100
        if pct >= 80:
            alerts.append({"level": "bad" if pct >= 100 else "warn",
                           "text": f"{REGISTRY[k].label} is at {pct:.0f}% of its {lim:g} monthly budget."})
    rows = [{"provider": k, "label": REGISTRY[k].label, "cost": round(cost.get(k, 0), 2), "budget": budgets.get(k)}
            for k in REGISTRY]
    return {"alerts": alerts, "costs": rows, "total_cost": round(sum(cost.values()), 2),
            "note": "Costs are amounts you entered per resource, not billing data from the providers."}
