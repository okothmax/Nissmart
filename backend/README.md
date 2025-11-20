# Nissmart Ledger Backend

## Overview
- FastAPI service with SQLAlchemy async models (users, accounts, transactions).
- Idempotent ledger operations (deposit, transfer, withdrawal) via `IdempotencyService`.
- Admin dashboard metrics exposed at `/api/dashboard/admin`.

## Quick start
```bash
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Key environment
- `.env`/environment should provide `DATABASE_URL` (SQLite by default in this repo). Idempotency and migrations run against the same DB.

## Important endpoints
| Method | Path | Description |
| --- | --- | --- |
| `POST /api/users` | create user (requires Idempotency-Key header) |
| `GET /api/users?limit=100` | list users |
| `GET /api/ledger/balance/{user_id}` | fetch ledger balances |
| `POST /api/ledger/deposit`/`transfer`/`withdraw` | create ledger transactions (Idempotency-Key required) |
| `GET /api/transactions` | paginated/filterable transaction feed with `start_date`, `end_date`, `type` params |
| `GET /api/dashboard/admin` | summary metrics for the admin dashboard |

## Testing & maintenance
- Run `pytest` from the backend directory.
- Alembic migrations live under `alembic/` and are applied via `alembic upgrade head`.

## Notes
- Idempotency keys are mandatory for write operations (`POST /api/users`, `/ledger/*`) to keep ledger operations safe.
- The API router is prefixed with `/api`, so all frontend calls should include that.
