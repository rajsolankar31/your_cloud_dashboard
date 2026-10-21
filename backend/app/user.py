"""Simple user profile storage for the demo backend.
We keep a singleton dict in memory; in a real app this would be a DB
model with proper authentication. The helper functions are imported by
both the API routes and the sync service to keep the linked accounts
up‑to‑date.
"""

from typing import Dict

_user: Dict = {
    "name": "Anonymous",
    "email": "",
    "linked_accounts": {},
}

def get_user() -> Dict:
    """Return a copy of the current user profile."""
    return _user_copy()

def update_user(name: str | None = None, email: str | None = None, linked_accounts: Dict[str, str] | None = None) -> Dict:
    """Update user fields if provided and return the updated profile copy."""
    if name is not None:
        _user["name"] = name
    if email is not None:
        _user["email"] = email
    if linked_accounts:
        _user["linked_accounts"].update(linked_accounts)
    return _user_copy()

def add_linked_account(provider: str, account_name: str) -> None:
    """Add or update a linked account for a provider."""
    _user["linked_accounts"][provider] = account_name

def _user_copy() -> Dict:
    """Return a shallow copy to avoid accidental mutation via API."""
    return {
        "name": _user["name"],
        "email": _user["email"],
        "linked_accounts": dict(_user["linked_accounts"]),
    }
