# ELITE Intel - Business Dashboard

> Centralized financial tracking and analytics platform for small local businesses.

Replaces manual Excel workflows with a structured web dashboard.
Tracks income, expenses, savings, and business performance in real-time.

---

## Features

- **Kardex Import** - Upload Excel/CSV files and auto-detect categories
- **Income Tracking** - Accesorios (40% profit), BeMovilRemote (volume only)
- **Dashboard KPIs** - Income, expenses, net balance, savings rate
- **Transaction History** - Filter by date, type, category, search
- **Category Breakdown** - Pie charts for income and expenses
- **Trend Charts** - Daily, weekly, monthly timeseries

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend                            │
│              React + TypeScript + Vite                  │
│                  Tailwind CSS + Recharts                │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP / JSON
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     Backend                             │
│               FastAPI + Python 3.12                     │
│                                                         │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   API    │  │   Services   │  │  Business Rules  │  │
│  │  Routes  │→ │  Validation  │→ │  Import Logic    │  │
│  └──────────┘  └──────────────┘  └──────────────────┘  │
└──────────────────────────┬──────────────────────────────┘
                           │ SQLAlchemy ORM
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Database                             │
│                  PostgreSQL 15                          │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/eliteSystem.git
cd eliteSystem/repository/elite-intel

# Start all services
docker compose up -d --build

# Access the application
open http://localhost:3002
```

### Services

| Service    | URL                    | Description              |
|------------|------------------------|--------------------------|
| Frontend   | http://localhost:3002   | React dashboard          |
| API Docs   | http://localhost:8080/docs | Swagger/OpenAPI docs  |
| API        | http://localhost:8080   | FastAPI backend          |
| Database   | localhost:5433         | PostgreSQL               |

---

## API Endpoints

### Dashboard

| Method | Endpoint                        | Description                |
|--------|---------------------------------|----------------------------|
| GET    | `/api/v1/dashboard/summary`     | KPIs (income, expenses, net) |
| GET    | `/api/v1/dashboard/timeseries`  | Daily/weekly/monthly trends |
| GET    | `/api/v1/dashboard/categories`  | Category breakdown         |

### Transactions

| Method | Endpoint                         | Description              |
|--------|----------------------------------|--------------------------|
| GET    | `/api/v1/transactions`           | List (paginated, filtered) |
| POST   | `/api/v1/transactions`           | Create transaction       |
| GET    | `/api/v1/transactions/{id}`      | Get single transaction   |
| PUT    | `/api/v1/transactions/{id}`      | Update transaction       |
| DELETE | `/api/v1/transactions/{id}`      | Delete transaction       |

### Import Pipeline

| Method | Endpoint                          | Description              |
|--------|-----------------------------------|--------------------------|
| POST   | `/api/v1/imports/transactions`    | Upload CSV/XLSX file     |
| POST   | `/api/v1/imports/{id}/mapping`    | Apply column mapping     |
| POST   | `/api/v1/imports/{id}/confirm`    | Confirm and insert       |
| GET    | `/api/v1/imports`                 | List import batches      |
| GET    | `/api/v1/imports/{id}`            | Get batch details        |

### Catalog

| Method | Endpoint                    | Description              |
|--------|-----------------------------|--------------------------|
| GET    | `/api/v1/categories`        | List categories          |
| POST   | `/api/v1/categories`        | Create category          |
| PUT    | `/api/v1/categories/{id}`   | Update category          |
| DELETE | `/api/v1/categories/{id}`   | Delete category          |
| GET    | `/api/v1/products`          | List products            |
| POST   | `/api/v1/products`          | Create product           |
| GET    | `/api/v1/catalog`           | Product catalog search   |

---

## Business Rules

### Kardex Import

- **Column B (BeMovilRemote)** - Header detected as `0` or `0.0` instead of "Be Movil"
  - Tracked as volume only, excluded from income/net KPIs
- **Accesorios** - Only 40% profit stored as income
  - Gross amount saved in notes: `accesorios_gross=190000`
  - Stored amount: `76000` (40% of gross)
- **Ahorro mensual** - Treated as INCOME (not expense)
- **Ahorro para pagar** - Treated as EXPENSE
- **TOTALDAY** - Cumulative column, never stored as transactions
- **Pendientes** - Stored as EXPENSE

### Dashboard Defaults

- **Period**: Current Week (not month)
- **BeMovilRemote**: Excluded from income/net balance calculations
- **Charts**: Y-axis max - Week: 1M, Month: 5M, Year: 15M

---

## Directory Structure

```
elite-intel/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── models/           # SQLAlchemy models
│   │   ├── repositories/     # Data access layer
│   │   ├── services/         # Business logic
│   │   │   ├── import_service.py    # Kardex parser
│   │   │   └── business_rules.py    # Income/expense rules
│   │   └── db/               # Database setup
│   ├── migrations/           # Alembic migrations
│   ├── tests/                # pytest test suite
│   └── data/raw/             # Raw CSV/XLSX files
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── charts/       # TrendChart, CategoryBreakdown
│   │   │   ├── transactions/ # TransactionTable, forms
│   │   │   └── filters/      # PeriodFilter, TransactionFilters
│   │   ├── pages/            # DashboardPage, TransactionsPage
│   │   ├── hooks/            # usePeriod, useAsyncData
│   │   ├── services/         # API client
│   │   └── utils/            # formatCurrency, period helpers
│   └── nginx.conf            # Cache-busting config
├── docker-compose.yml        # Container orchestration
└── reference/docs/kardex/    # Source Excel files
```

---

## Tech Stack

| Layer      | Technology                                    |
|------------|-----------------------------------------------|
| Frontend   | React 18, TypeScript, Vite, Tailwind CSS      |
| Charts     | Recharts                                      |
| Backend    | Python 3.12, FastAPI, Pydantic v2             |
| ORM        | SQLAlchemy 2.0, Alembic                       |
| Database   | PostgreSQL 15                                 |
| DevOps     | Docker, Docker Compose                        |
| Testing    | pytest, httpx                                 |

---

## Development

### Backend Tests

```bash
docker compose exec backend pytest tests/ -v
```

### Frontend Build

```bash
docker compose up -d --build frontend
```

### Database Migrations

```bash
docker compose exec backend alembic upgrade head
```

---

## License

MIT License - Copyright (c) 2026
