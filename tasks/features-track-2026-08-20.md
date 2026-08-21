# Feature tracking work order (from reference/docs/mds/features.md)

Repo root for this work: `/home/lnxmacreat/wsp/projects/eliteSystem/repository/elite-intel`
Source of truth: `/home/lnxmacreat/wsp/projects/eliteSystem/reference/docs/mds/features.md`
Kardex reference: `/home/lnxmacreat/wsp/projects/eliteSystem/reference/docs/kardex/kardex.xlsx`
CSV ledger path: `backend/data/raw/2026-2.csv`

Do not commit. Do not redeploy docker (coordinator will redeploy after review).

## Feature 1 - Income / expense tracking rules

### Already correct / keep
- Kardex day values are per-day amounts; accumulating them is fine.
- Column B (`Be Movil`) must NOT feed the normal monthly income total / current August balance the way other sales columns do.
- The `Total` / Total-day corner columns must NOT be stored as transactions; they are validation-only against the xlsx.
- Existing skip of `Total` columns in kardex import must remain.

### Accesorios (profit-only into incomes)
- Accesorios gross sales are NOT full income.
- When Accesorios amounts are recorded (manual transaction or import), store/credit only **40%** of the gross as INCOME profit that affects incomes and net balance.
- Example: Accesorios gross `190000` COP -> income tracked `76000` COP (40%).
- Prefer keeping an audit trail of the gross somehow (description note or metadata) if the schema already supports it without a heavy redesign; otherwise document the convention in code comments and tests.

### Be Movil split categories (new semantics)
Introduce / ensure two categories (names may already exist or need seeding/migration):

1. **BeMovilRemote** (or clear equivalent label consistent with existing category naming): track ALL Be Movil sales volume sold to date (gross remote sales tracking). This is volume tracking, not mixed into normal income totals the same way as Fotocopias/etc.
2. **BeMovileIncome** (or clear equivalent): track ONLY net Be Movil gains entered **manually by a human**. Do not auto-derive these from column B sales.

Column B Be Movil in kardex must not continue to be silently dropped without a plan: either map tracked volume into BeMovilRemote without affecting normal income KPIs, or keep skip for income KPIs while documenting how BeMovilRemote gets populated. Prefer implementing BeMovilRemote volume tracking from column B if feasible without breaking existing tests; otherwise implement categories + manual path and leave a clear TODO with tests for the Accesorios 40% and BeMovileIncome manual path.

### CSV refresh
- Empty `backend/data/raw/2026-2.csv` so it is ready for fresh transaction testing.
- Keep the CSV header row only: `Fecha,Tipo,Categoría,Descripción,Valor`
- Do not leave proof/test rows in that file.

## Feature 2 - Chart Y-axis by PERIOD

In the dashboard trend chart (`frontend/src/components/charts/TrendChart.tsx` or wherever period charts live):

- Current week (and today if same chart): Y max = **1M** (1_000_000)
- Month (and previous_month if same chart): Y max = **5M** (5_000_000)
- Year (and all_time if same chart): Y max = **15M** (15_000_000)

If this is already implemented correctly, verify with a quick read/test and do not churn it.

## Expected verification
- Unit/API tests covering Accesorios 40% income conversion.
- Tests that Be Movil column B does not inflate normal income totals incorrectly.
- CSV is header-only.
- Chart Y max matches the period rules above.
- Run focused tests for the files you touch; fix failures you introduce.

## Out of scope
- git commit / push
- docker compose redeploy
- unrelated refactors
