# Unified Cloud Dashboard

Phase 1 foundation: React + Vite UI, FastAPI backend, SQLite history and audit log, mock providers, and an approval-gated action flow. Replace this file with your full project README.

## Run

```bash
# backend
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows (use source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy ..\.env.example .env                         # cp on macOS/Linux
uvicorn app.main:app --reload                     # http://127.0.0.1:8000/docs

# frontend (second terminal)
cd frontend
npm install
npm run dev                                       # http://localhost:5173
```

Tests: `cd backend && pytest`

## Status

| Area | State |
|---|---|
| Normalized resource model, SQLite snapshots, stale flags | Done |
| Mock OCI / Google / Vercel data | Done |
| Approval flow (request, retype name, backend check, execute, verify, audit) | Done, tested in mock mode |
| Vercel live adapter (projects list, redeploy) | Written, not tested against a real account |
| OCI and Google live adapters | Not started (roadmap Phase 3) |
| Manual resources, details (owner, tags, notes, cost), budgets, alerts, auto-refresh, credentials page | Done |
| Real billing data and metrics charts from providers | Not started (Phase 4) |

Set `USE_MOCK=false` and `VERCEL_TOKEN` to try live Vercel.
