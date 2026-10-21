import json

from ..database.db import conn
from ..models import now
from ..providers import REGISTRY
from ..cache import cached


def sync_provider(key: str) -> dict:
    p = REGISTRY[key]
    if key == "custom":
        return {"provider": key, "ok": True, "count": 0, "error": None}
    started = now()
    try:
        items = p.list_resources()
    except Exception as e:  # one provider's failure must not break the others
        msg = str(e)[:300]
        with conn() as c:
            c.execute("UPDATE resources SET stale=1 WHERE provider=?", (key,))
            c.execute("INSERT INTO sync_runs(provider,started_at,ok,count,error) VALUES(?,?,0,0,?)",
                      (key, started, msg))
        return {"provider": key, "ok": False, "error": msg, "count": 0}
    with conn() as c:
        seen = []
        for r in items:
            seen.append(r["id"])
            c.execute(
                """INSERT INTO resources(id,provider,resource_type,name,status,region,last_checked,stale,meta)
                   VALUES(?,?,?,?,?,?,?,0,?) ON CONFLICT(id) DO UPDATE SET
                   name=excluded.name,status=excluded.status,region=excluded.region,
                   last_checked=excluded.last_checked,stale=0,meta=excluded.meta""",
                (r["id"], key, r["resource_type"], r["name"], r["status"], r["region"],
                 r["last_checked"], json.dumps(r["meta"])))
            c.execute("INSERT INTO snapshots(resource_id,status,checked_at) VALUES(?,?,?)",
                      (r["id"], r["status"], r["last_checked"]))
        if seen:  # resources that disappeared are flagged stale, not deleted
            q = ",".join("?" * len(seen))
            c.execute(f"UPDATE resources SET stale=1 WHERE provider=? AND id NOT IN ({q})", (key, *seen))
        c.execute("INSERT INTO sync_runs(provider,started_at,ok,count) VALUES(?,?,1,?)",
                  (key, started, len(items)))
    return {"provider": key, "ok": True, "count": len(items), "error": None}


def sync_all() -> list[dict]:
    return [sync_provider(k) for k in REGISTRY if REGISTRY[k].mode() not in ("unconfigured", "manual")]


def provider_summaries() -> list[dict]:
    out = []
    with conn() as c:
        for k, p in REGISTRY.items():
            run = c.execute("SELECT * FROM sync_runs WHERE provider=? ORDER BY id DESC LIMIT 1", (k,)).fetchone()
            n = c.execute("SELECT COUNT(*) FROM resources WHERE provider=?", (k,)).fetchone()[0]
            out.append({"key": k, "label": p.label, "mode": p.mode(), "resources": n,
                        "last_sync": run["started_at"] if run else None,
                        "last_ok": bool(run["ok"]) if run else None,
                        "error": run["error"] if run else None})
    return out


def list_resources(provider: str | None = None) -> list[dict]:
    sql = ("SELECT r.*, d.notes, d.tags, d.owner, d.monthly_cost FROM resources r "
           "LEFT JOIN details d ON d.resource_id = r.id"
           + (" WHERE r.provider=?" if provider else "") + " ORDER BY r.provider, r.name")
    with conn() as c:
        rows = c.execute(sql, (provider,) if provider else ()).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["meta"] = json.loads(d["meta"] or "{}")
        d["stale"] = bool(d["stale"])
        d["actions"] = [] if d["stale"] else REGISTRY[d["provider"]].actions.get(d["resource_type"], [])
        out.append(d)
    return out


def history(resource_id: str) -> list[dict]:
    with conn() as c:
        rows = c.execute("SELECT status,checked_at FROM snapshots WHERE resource_id=? ORDER BY id DESC LIMIT 100",
                         (resource_id,)).fetchall()
    return [dict(r) for r in rows]
