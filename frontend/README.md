This is the [Next.js](https://nextjs.org) frontend for the Nissmart take-home, built with the App Router and Tailwind+
sonner for UI feedback.

## Getting started

```bash
cd frontend
npm install
npm run dev
```

The site mixes two dashboards:
1. **User dashboard** at `/` – manage wallet balances, create users, and run deposits/transfers/withdrawals with inline validation.
2. **Admin dashboard** at `/admin/dashboard` – shows KPIs, transaction mix, charts, and filters powered by `/api/dashboard/admin` and `/api/transactions`.

### Environment
Create `.env.local` with:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

### Tooling
- ESLint: `npm run lint`
- TypeScript: repo-wide type checking via `npx tsc --noEmit`
- Dev server: `npm run dev` (default port 3000, requires backend running at port 8000)

### Interacting with the backend
- Uses `apiFetch` wrapper with idempotency-key support defined in `src/lib/api.ts`.
- SWR fetchers call `/api/users`, `/api/ledger/*`, `/api/transactions`, and `/api/dashboard/admin` via `src/lib/hooks.ts`.
- Styled components live under `src/components` (dashboard, UI button, etc.)

Sequences:
1. Navigate to `/` to create/select users.
2. Run operations (deposit/transfer/withdraw), then verify the admin dashboard updates via `/api/dashboard/admin` and paginated `/api/transactions` data.
