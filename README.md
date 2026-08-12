# ELITE System - Business Operations & Analytics Dashboard

Centralized financial tracking and analytics platform designed for small local businesses offering papelería, printing, internet services, digital service packages, and phone recharges.
Replaces manual Excel workflows with a structured web dashboard and establishes a reliable data foundation for demand forecasting and machine learning.

## Architecture Overview

```text
┌──────────────────────────────┐
│          Frontend            │
│      React + Tailwind        │
└──────────────┬───────────────┘
               │ HTTP / JSON
               ▼
┌──────────────────────────────┐
│           Backend            │
│       FastAPI / Python       │
│                              │
│  API -> Services -> Validation│
└──────────────┬───────────────┘
               │ SQL / ORM
               ▼
┌──────────────────────────────┐
│          Database            │
│         PostgreSQL           │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       Analytics / ML         │
│ pandas + scikit-learn        │
│ forecasting / classification │
└──────────────────────────────┘
```

## Directory Structure Map

```text
eliteSystem/
├── README.md                 # Root documentation and project overview
├── LICENSE                   # Software license (MIT)
├── .gitignore                # Git ignore rules
├── docker-compose.yml        # Local container orchestration
├── .env.example              # Environment variables template
├── frontend/                 # React + TypeScript + Vite web client
├── backend/                  # FastAPI + Python REST server and domain services
├── data/                     # Data storage pipeline (raw, processed, imports)
├── ml/                       # Machine learning models, notebooks, and feature engineering
├── docs/                     # Technical specifications, architecture, and API docs
├── scripts/                  # Data migration, ETL, and database seeding utilities
└── reference/                # Specification documents and baseline reference code
```

## Technology Stack Summary

- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Recharts
- **Backend:** Python 3.11+, FastAPI, Pydantic, SQLAlchemy, Alembic
- **Database:** PostgreSQL 15+
- **Data & ML:** pandas, scikit-learn, Jupyter
- **DevOps:** Docker, Docker Compose

## Quick Links

- [Product Specification](reference/docs/mds/spec.md)
- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)
- [Database Documentation](docs/database/README.md)
- [API Documentation](docs/api/README.md)

## License and Ownership Notice

Copyright (c) 2026.
All rights reserved.
Released under the MIT License.
See the `LICENSE` file for details.
