# Frontend Source

Core application logic and UI components for the React dashboard.

**Contents:**
- `components/` - Reusable UI widgets, KPI cards, forms, charts, and import wizard steps.
- `pages/` - Page-level views (Dashboard, Transactions, Transaction Form, Import).
- `services/` - Axios HTTP client and API integrations.
- `types/` - TypeScript interfaces for domain and API payloads.
- `utils/` - Shared formatting and period/date helpers.

**Connects to:** Backend REST API at `/api/v1` via `VITE_API_BASE_URL`.
