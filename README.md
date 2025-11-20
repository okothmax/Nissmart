# Nissmart Take-Home

This repo contains the Nissmart micro-savings + payout prototype. It includes a FastAPI backend that powers ledger operations and a Next.js frontend with user + admin dashboards.

## Backend
- Directory: `backend/`
- Run: `source .venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Database: SQLite (`backend/nissmart.db`) for local development.
- Idempotency: `IdempotencyService` ensures duplicate writes use the same response (requires the frontend to send `Idempotency-Key`).
- Env example: `backend/.env.example` shows the supported variables.

## Frontend
- Directory: `frontend/`
- Run: `npm install` (once) and `npm run dev`.
- Default API base URL: `http://localhost:8000/api` (set `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local`).
- Dashboards:
  - `/`: user dashboard for creating users, viewing balances, and executing deposits/transfers/withdrawals.
  - `/admin/dashboard`: admin dashboard with KPIs, charts, filters, and a button back to the user view.

## Docs & Flows
- Architecture notes: `docs/architecture.md` + `docs/architecture.pdf`.
- Flow diagrams: `docs/flow_diagrams.md` (with Mermaid) + renderable `flow_diagrams.pdf`.
