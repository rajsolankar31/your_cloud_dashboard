from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..actions import engine
from ..providers import REGISTRY
from ..services import sync

router = APIRouter(prefix="/api")


class ActionRequest(BaseModel):
    resource_id: str
    action: str


class Confirm(BaseModel):
    confirm_name: str


def _wrap(fn, *a):
    try:
        return fn(*a)
    except engine.ActionError as e:
        raise HTTPException(e.code, str(e))


@router.get("/providers")
def providers():
    return sync.provider_summaries()


@router.get("/resources")
def resources(provider: str | None = None):
    return sync.list_resources(provider)


@router.get("/resources/{resource_id}/history")
def history(resource_id: str):
    return sync.history(resource_id)


@router.post("/sync")
def sync_all():
    return sync.sync_all()


@router.post("/sync/{provider}")
def sync_one(provider: str):
    if provider not in REGISTRY:
        raise HTTPException(404, "Unknown provider.")
    return sync.sync_provider(provider)


@router.post("/actions")
def request_action(body: ActionRequest):
    return _wrap(engine.request_action, body.resource_id, body.action)


@router.post("/actions/{action_id}/confirm")
def confirm(action_id: str, body: Confirm):
    return _wrap(engine.confirm, action_id, body.confirm_name)


@router.post("/actions/{action_id}/cancel")
def cancel(action_id: str):
    return _wrap(engine.cancel, action_id)


@router.get("/audit")
def audit():
    return engine.audit()


# ---- management, connections, tracking ----
from ..security import secrets  # noqa: E402
from ..services import manage  # noqa: E402
from ..config import use_mock  # noqa: E402


def _m(fn, *a):
    try:
        return fn(*a)
    except manage.ManageError as e:
        raise HTTPException(e.code, str(e))


@router.post("/resources")
def create_resource(body: dict):
    return _m(manage.create, body)


@router.patch("/resources/{resource_id}")
def update_resource(resource_id: str, body: dict):
    return _m(manage.update, resource_id, body)


@router.delete("/resources/{resource_id}")
def delete_resource(resource_id: str):
    return _m(manage.delete, resource_id)


@router.get("/overview")
def overview():
    return manage.overview()


@router.put("/budgets/{provider}")
def budget(provider: str, body: dict):
    _m(manage.set_budget, provider, body.get("monthly_limit"))
    return {"ok": True}


@router.get("/connections")
def connections():
    return {"use_mock": use_mock(),
            "providers": [{"key": k, "label": p.label, "mode": p.mode(), "fields": secrets.fields(k)}
                          for k, p in REGISTRY.items() if k != "custom"]}


@router.put("/connections/{provider}")
def save_connection(provider: str, body: dict):
    names = {f["name"] for f in secrets.fields(provider)}
    if provider not in REGISTRY or not names:
        raise HTTPException(404, "Nothing to configure for this provider.")
    secrets.save({k: v for k, v in body.items() if k in names})
    return {"ok": True}


@router.put("/settings")
def settings(body: dict):
    secrets.save({"USE_MOCK": "true" if body.get("use_mock") else "false"})
    manage.reset_synced()
    sync.sync_all()
    return {"use_mock": use_mock()}

# -------------------------------------------------------------------
# User profile endpoints (in‑memory singleton for demo purposes)
# -------------------------------------------------------------------
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

# Simple global user instance
_user = None

def get_user():
    global _user
    if _user is None:
        # default anonymous user
        _user = {
            "name": "Anonymous",
            "email": "",
            "linked_accounts": {}
        }
    return _user

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    linked_accounts: Dict[str, str] | None = None

@router.get("/user")
def get_user_profile():
    return get_user()

@router.put("/user")
def update_user_profile(payload: UserUpdate):
    u = get_user()
    if payload.name is not None:
        u["name"] = payload.name
    if payload.email is not None:
        u["email"] = payload.email
    if payload.linked_accounts is not None:
        u["linked_accounts"].update(payload.linked_accounts)
    return u

