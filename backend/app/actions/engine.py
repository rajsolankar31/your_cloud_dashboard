import json
import uuid

from ..database.db import conn
from ..models import now
from ..providers import REGISTRY
from ..services.sync import sync_provider

IMPACT = {
    "start": "Starts the instance. Compute billing resumes.",
    "stop": "Stops the instance. Anything running on it goes offline.",
    "redeploy": "Creates a new production deployment from the latest build.",
}


class ActionError(Exception):
    def __init__(self, msg: str, code: int = 400):
        super().__init__(msg)
        self.code = code


def _get(action_id: str) -> dict:
    with conn() as c:
        r = c.execute("SELECT * FROM actions WHERE id=?", (action_id,)).fetchone()
    if not r:
        raise ActionError("Action not found.", 404)
    return dict(r)


def request_action(resource_id: str, action: str) -> dict:
    with conn() as c:
        res = c.execute("SELECT * FROM resources WHERE id=?", (resource_id,)).fetchone()
    if not res:
        raise ActionError("Resource not found.", 404)
    res = dict(res)
    if res["stale"]:
        raise ActionError("Resource data is stale. Refresh before requesting an action.")
    if action not in REGISTRY[res["provider"]].actions.get(res["resource_type"], []):
        raise ActionError(f"'{action}' is not supported for this resource.")
    aid = uuid.uuid4().hex[:12]
    with conn() as c:
        c.execute("""INSERT INTO actions(id,provider,resource_id,resource_name,action,status,impact,requested_at)
                     VALUES(?,?,?,?,?,'pending',?,?)""",
                  (aid, res["provider"], resource_id, res["name"], action, IMPACT.get(action, ""), now()))
    return _get(aid)


def confirm(action_id: str, confirm_name: str) -> dict:
    a = _get(action_id)
    if a["status"] != "pending":
        raise ActionError(f"Action is already {a['status']}.", 409)
    # Backend-side check: the caller must retype the exact resource name.
    if confirm_name != a["resource_name"]:
        raise ActionError("Confirmation name does not match the resource name.")
    with conn() as c:
        res = c.execute("SELECT * FROM resources WHERE id=?", (a["resource_id"],)).fetchone()
    if not res:
        raise ActionError("Resource no longer exists.", 404)
    res = dict(res)
    res["meta"] = json.loads(res["meta"] or "{}")
    provider = REGISTRY[a["provider"]]
    if a["action"] not in provider.actions.get(res["resource_type"], []):
        raise ActionError("Action is no longer permitted for this resource.")
    with conn() as c:
        c.execute("UPDATE actions SET status='executing', confirmed_at=? WHERE id=?", (now(), action_id))
    try:
        result = provider.execute(a["action"], res)
        sync_provider(a["provider"])  # verify by re-reading provider state
        status, detail = "success", str(result.get("detail", ""))
        if result.get("request_id"):
            detail += f" (request id: {result['request_id']})"
    except Exception as e:
        status, detail = "failed", str(e)[:300]
    with conn() as c:
        c.execute("UPDATE actions SET status=?, finished_at=?, detail=? WHERE id=?",
                  (status, now(), detail, action_id))
    return _get(action_id)


def cancel(action_id: str) -> dict:
    a = _get(action_id)
    if a["status"] != "pending":
        raise ActionError(f"Action is already {a['status']}.", 409)
    with conn() as c:
        c.execute("UPDATE actions SET status='cancelled', finished_at=? WHERE id=?", (now(), action_id))
    return _get(action_id)


def audit(limit: int = 100) -> list[dict]:
    with conn() as c:
        rows = c.execute("SELECT * FROM actions ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
