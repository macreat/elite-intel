# SPEC.md — Business Operations & Analytics Dashboard

**Project:** Small Business Financial & Sales Dashboard  
**Document:** Product & Technical Specification  
**Version:** 0.1.0  
**Status:** MVP Specification  
**Date:** 2026-08-12  
**Primary goal:** Replace the current Excel-based tracking workflow with a simple, reliable dashboard while establishing a clean data foundation for future analytics and Machine Learning.

---

## 1. Project Overview

The business combines several revenue-generating activities, including:

- Papelería
- Impresiones
- Fotocopias
- Escaneo
- Accesorios
- Internet / café internet services
- Recargas
- Purchase and distribution of service packages
- Digital / streaming-related services
- Other products and services added in the future

The current financial tracking process is primarily based on Excel. The first prototype will replace this workflow with a centralized application that allows the business owner to register transactions and immediately visualize the financial state of the business.

The system must also preserve structured historical data so future analytical and Machine Learning components can identify patterns, forecast demand, classify business situations, and support investment decisions.

---

## 2. Objectives

### 2.1 General Objective

Build a minimal, maintainable dashboard for tracking business income, expenses, savings, and financial performance while creating a reliable historical dataset for future analytics and Machine Learning.

### 2.2 Specific Objectives

1. Replace manual Excel-based transaction tracking.
2. Register income and expenses by date and category.
3. Provide daily, monthly, and historical summaries.
4. Calculate total income, total expenses, and net balance.
5. Track a configurable monthly savings target.
6. Provide basic visualizations of business performance.
7. Import existing historical data from CSV/Excel.
8. Preserve transaction-level data for future analysis.
9. Allow new products, services, and categories without redesigning the application.
10. Establish a foundation for future demand forecasting and investment recommendations.

---

## 3. Scope

### 3.1 MVP Includes

- Transaction registration.
- Income and expense tracking.
- Categories and subcategories.
- Date-based filtering.
- Dashboard with financial KPIs.
- Daily and monthly summaries.
- Monthly savings calculation.
- Historical transaction view.
- CSV/Excel historical-data import.
- Basic charts.
- Basic validation and error handling.
- Persistent database storage.

### 3.2 MVP Does Not Include

The following are intentionally deferred:

- Automatic bank synchronization.
- Electronic invoicing.
- Payroll management.
- Full accounting/bookkeeping compliance.
- Inventory management.
- Customer relationship management.
- Multi-business tenancy.
- Mobile native application.
- Automated financial advice.
- Production Machine Learning recommendations.

These may be introduced in later versions.

---

## 4. Users

### Primary User

**Business owner / administrator**

The primary user needs to:

- Record transactions quickly.
- Know how much the business has generated.
- Know where money is being spent.
- Compare periods.
- Monitor savings.
- Identify profitable business categories.
- Eventually receive data-driven recommendations.

### Future Users

Potential future roles:

- Employee/operator.
- Accountant.
- Manager.
- Read-only analyst.

Role-based access control is not required for the MVP but the architecture should not prevent its future implementation.

---

# 5. Functional Requirements

## FR-01 — Transaction Registration

The system shall allow the user to register a financial transaction.

A transaction shall contain at minimum:

- Unique identifier.
- Date and time.
- Transaction type.
- Category.
- Description.
- Amount.
- Optional product/service reference.
- Optional notes.

Transaction types:

- `INCOME`
- `EXPENSE`

### Example

```text
Date:        2026-08-12
Type:        INCOME
Category:    Impresiones
Description: 20 color pages
Amount:       $12,000
```

---

## FR-02 — Transaction Categories

The system shall support configurable categories.

Initial categories should include:

| Type | Category |
|---|---|
| Income | Papelería |
| Income | Accesorios |
| Income | Internet |
| Income | Recargas |
| Income | Impresiones |
| Income | Fotocopias |
| Income | Escaneo |
| Income | Servicios digitales |
| Income | Otros |
| Expense | Proveedores |
| Expense | Servicios públicos |
| Expense | Inventario |
| Expense | Transporte |
| Expense | Mantenimiento |
| Expense | Otros |

Categories must be stored in the database rather than hard-coded into the frontend.

---

## FR-03 — Dashboard

The main dashboard shall provide a concise financial overview.

Required KPIs:

- Total income.
- Total expenses.
- Net balance.
- Estimated savings.
- Savings percentage.
- Number of transactions.
- Current period.

Example:

```text
Income       $2,450,000
Expenses       $980,000
Net balance  $1,470,000
Savings      $1,000,000
Savings rate     40.8%
```

---

## FR-04 — Period Filtering

The user shall be able to filter information by:

- Today.
- Current week.
- Current month.
- Previous month.
- Custom date range.

All dashboard KPIs and charts must react to the selected period.

---

## FR-05 — Transaction History

The system shall provide a table containing historical transactions.

Minimum columns:

- Date.
- Type.
- Category.
- Description.
- Amount.
- Notes.
- Actions.

Supported actions:

- View.
- Edit.
- Delete.

Deletion should require confirmation.

---

## FR-06 — Monthly Savings

The system shall calculate estimated monthly savings.

Basic formula:

```text
Net Balance = Total Income - Total Expenses
```

The first version may define:

```text
Estimated Savings = max(Net Balance, 0)
```

A future version may allow the user to configure:

- Fixed monthly savings target.
- Savings percentage.
- Investment allocation.
- Emergency reserve.
- Business reinvestment percentage.

---

## FR-07 — Category Analysis

The system shall calculate income and expenses grouped by category.

Examples:

```text
Income by category
------------------
Papelería       $500,000
Internet        $350,000
Impresiones     $280,000
Accesorios      $420,000
```

The dashboard should identify:

- Highest-income categories.
- Highest-expense categories.
- Category percentage of total income.
- Category evolution over time.

---

## FR-08 — Basic Analytics

The MVP shall provide descriptive analytics.

Required metrics:

- Daily income.
- Daily expenses.
- Monthly income.
- Monthly expenses.
- Net balance.
- Average daily income.
- Average transaction value.
- Income by category.
- Expenses by category.
- Month-over-month variation.

These metrics are intended to provide value before Machine Learning is introduced.

---

## FR-09 — Historical Data Import

The system shall support importing the existing Excel/CSV data.

The import process should:

1. Upload the file.
2. Detect columns.
3. Map source columns to system fields.
4. Validate records.
5. Report invalid rows.
6. Preview the imported data.
7. Confirm import.
8. Store valid records in the database.

Example source mapping:

```text
Fecha        -> date
Tipo         -> transaction_type
Categoría    -> category
Descripción  -> description
Valor        -> amount
```

The original file must not be modified during import.

---

## FR-10 — Data Validation

The backend shall validate:

- Required fields.
- Valid transaction type.
- Valid category.
- Positive monetary values.
- Valid dates.
- Valid numeric formats.

Invalid records shall not be silently inserted.

---

## FR-11 — Search and Filtering

The transaction history shall support:

- Category filtering.
- Transaction-type filtering.
- Date filtering.
- Text search.
- Amount-based filtering in a future version.

---

## FR-12 — Export

The system should support exporting filtered transaction data to CSV.

This is an MVP-adjacent feature and may be implemented after the initial CRUD workflow.

---

# 6. Non-Functional Requirements

## NFR-01 — Usability

The interface shall be minimal and understandable to a non-technical user.

The user should be able to register a normal transaction in a small number of interactions.

## NFR-02 — Performance

For the MVP:

- Dashboard queries should normally respond in less than 1 second for normal datasets.
- Transaction registration should provide immediate feedback.
- Filtering should not require a full page reload.

## NFR-03 — Reliability

The system shall use persistent storage.

A browser refresh or application restart must not lose registered transactions.

## NFR-04 — Maintainability

The codebase shall separate:

- Frontend.
- Backend.
- Database.
- Data analysis.
- Configuration.

Business logic should not be duplicated between frontend and backend.

## NFR-05 — Scalability

The architecture should support growth from hundreds to hundreds of thousands of transactions without requiring a complete redesign.

## NFR-06 — Security

The system should:

- Validate all backend inputs.
- Avoid storing secrets in source control.
- Use environment variables for credentials.
- Protect administrative endpoints when authentication is introduced.
- Use parameterized database queries / ORM operations.

## NFR-07 — Data Integrity

Transactions must preserve their original timestamp and monetary value.

Database relationships should use stable identifiers rather than category names or descriptions.

---

# 7. Conceptual Architecture

The initial architecture follows a simple layered model:

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
│  API → Services → Validation │
└──────────────┬───────────────┘
               │ SQL / ORM
               ▼
┌──────────────────────────────┐
│          Database            │
│         PostgreSQL           │
└──────────────────────────────┘

             Future
               │
               ▼
┌──────────────────────────────┐
│       Analytics / ML         │
│ pandas + scikit-learn        │
│ forecasting / classification │
└──────────────────────────────┘
```

---

# 8. Logical Architecture

## 8.1 Frontend

Recommended stack:

- React
- TypeScript
- Vite
- Tailwind CSS
- Recharts or equivalent charting library

Responsibilities:

- Render dashboard.
- Manage forms.
- Display transactions.
- Apply UI filters.
- Consume backend API.
- Display validation errors.
- Provide responsive layout.

The frontend must not directly access the database.

---

## 8.2 Backend

Recommended stack:

- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy.
- Alembic.

Responsibilities:

- REST API.
- Business rules.
- Validation.
- Aggregation queries.
- Import processing.
- Database access.
- Future ML service integration.

Suggested layers:

```text
API / Routes
     ↓
Services
     ↓
Repositories / ORM
     ↓
Database
```

---

## 8.3 Database

Recommended database:

**PostgreSQL**

SQLite may be used during very early local prototyping, but PostgreSQL is preferred as the target database because the project is explicitly intended to grow into an analytics system.

---

# 9. Physical Architecture

For local development:

```text
Developer PC
│
├── Frontend container/process
│   └── React + Vite
│
├── Backend container/process
│   └── FastAPI
│
├── Database container
│   └── PostgreSQL
│
└── Data
    ├── CSV imports
    └── exported reports
```

Recommended development environment:

```text
Docker Compose
├── frontend
├── backend
└── postgres
```

The initial prototype may also run directly with local development servers.

---

# 10. Data Model

## 10.1 Transaction

```text
Transaction
-----------
id
date
type
category_id
description
amount
product_id       nullable
notes            nullable
created_at
updated_at
```

## 10.2 Category

```text
Category
--------
id
name
type
description
active
created_at
updated_at
```

## 10.3 Product / Service

```text
Product
-------
id
name
category_id
description
active
created_at
updated_at
```

The product table is optional for the first CRUD implementation but should be considered from the beginning because it will be important for future demand analysis.

## 10.4 Import Batch

```text
ImportBatch
-----------
id
filename
source_type
records_total
records_valid
records_invalid
created_at
```

This provides traceability for historical CSV/Excel imports.

---

# 11. Database Relationships

```text
Category
   │
   ├──────────< Product
   │
   └──────────< Transaction
                     │
                     └────────── Product (optional)
```

Recommended relationship:

```text
Category 1 ──── N Transaction
Category 1 ──── N Product
Product  1 ──── N Transaction
```

---

# 12. API Design

Base path:

```text
/api/v1
```

## Transactions

```http
GET    /transactions
POST   /transactions
GET    /transactions/{id}
PUT    /transactions/{id}
DELETE /transactions/{id}
```

## Categories

```http
GET    /categories
POST   /categories
PUT    /categories/{id}
DELETE /categories/{id}
```

## Products

```http
GET    /products
POST   /products
PUT    /products/{id}
DELETE /products/{id}
```

## Dashboard

```http
GET /dashboard/summary
GET /dashboard/categories
GET /dashboard/timeseries
```

## Import

```http
POST /imports/transactions
GET  /imports
GET  /imports/{id}
```

---

# 13. Dashboard Concept

The first dashboard should prioritize clarity over information density.

Suggested structure:

```text
┌─────────────────────────────────────────────────────┐
│ Business Dashboard                    [Date Filter] │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Income       Expenses       Balance       Savings   │
│ $X           $X             $X            $X        │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│              Income / Expense Trend                 │
│                                                     │
├───────────────────────────┬─────────────────────────┤
│ Income by Category        │ Expenses by Category    │
│                           │                         │
├───────────────────────────┴─────────────────────────┤
│                                                     │
│ Recent Transactions                                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

The interface should avoid unnecessary animations and excessive visual elements.

---

# 14. Initial User Flow

## Register Transaction

```text
Dashboard
   ↓
Add Transaction
   ↓
Select Income / Expense
   ↓
Select Category
   ↓
Enter Amount
   ↓
Add Description
   ↓
Save
   ↓
Validate
   ↓
Persist
   ↓
Refresh Dashboard
```

---

# 15. CSV / Excel Data Strategy

Historical data is considered a first-class project input.

The initial dataset should be treated as:

```text
Raw Data
   ↓
Validation
   ↓
Normalization
   ↓
Cleaning
   ↓
Database
   ↓
Analytics Dataset
   ↓
Machine Learning Dataset
```

Do not train Machine Learning models directly from an unvalidated CSV.

The import pipeline should preserve:

- Original source information.
- Normalized values.
- Import date.
- Validation status.
- Error information.

---

# 16. Data Quality Requirements

Before Machine Learning is implemented, the dataset should be evaluated for:

- Missing dates.
- Missing categories.
- Duplicate transactions.
- Invalid monetary values.
- Inconsistent category names.
- Inconsistent date formats.
- Outliers.
- Incorrect transaction types.
- Missing product/service identifiers.

Example normalization:

```text
"fotocopia"
"Fotocopias"
"FOTOCOPIA"
"copias"

        ↓

"Fotocopias"
```

---

# 17. Analytics Roadmap

The project should evolve through progressively more valuable analytical capabilities.

## Level 1 — Descriptive Analytics

Answer:

- How much did we sell?
- How much did we spend?
- Which category generated the most income?
- Which days are strongest?
- Which months are strongest?

## Level 2 — Diagnostic Analytics

Answer:

- Why did income decrease?
- Which category caused the change?
- Which expenses increased?
- Which products/services are becoming less profitable?

## Level 3 — Predictive Analytics

Answer:

- What could sales look like next month?
- Which categories may increase in demand?
- Which periods are historically stronger?
- What amount of inventory/service capacity may be required?

## Level 4 — Prescriptive Analytics

Answer:

- What should we invest in?
- When should we increase purchasing?
- Which products/services should receive more capital?
- Which categories should receive less investment?

The final level must be presented as a decision-support system, not as an autonomous financial decision-maker.

---

# 18. Machine Learning Strategy

Machine Learning is a future component, not an MVP dependency.

## 18.1 Candidate Problems

### Demand Forecasting

Predict future revenue or transaction volume by:

- Category.
- Product/service.
- Day.
- Week.
- Month.

### Classification

Classify business periods or products into categories such as:

```text
High demand
Medium demand
Low demand
```

Possible features:

- Day of week.
- Month.
- Season.
- Historical revenue.
- Transaction count.
- Category.
- Product/service.
- Previous-period revenue.
- Rolling averages.

### Recommendation / Investment Support

A future system may combine:

```text
Historical demand
+ Revenue
+ Expenses
+ Seasonality
+ Trends
+ Product performance
        ↓
Investment score
        ↓
Suggested categories
```

The system should show the evidence behind recommendations.

---

# 19. Important ML Design Principle

The application must not be designed around a Machine Learning model that does not yet exist.

Instead:

```text
Good transactional data
        ↓
Good analytical dataset
        ↓
Reliable features
        ↓
Model experimentation
        ↓
Model evaluation
        ↓
Prediction
        ↓
Recommendation
```

The most important ML requirement for version 0.1 is therefore **data quality and historical completeness**.

---

# 20. Proposed Project Structure

```text
business-dashboard/
│
├── README.md
├── SPEC.md
├── .gitignore
├── docker-compose.yml
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── db/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── imports/
│
├── ml/
│   ├── notebooks/
│   ├── features/
│   ├── models/
│   └── experiments/
│
├── docs/
│   ├── architecture/
│   ├── database/
│   └── api/
│
└── scripts/
    ├── import_data.py
    └── seed_database.py
```

---

# 21. MVP Development Plan

## Phase 0 — Specification

- [x] Define project objective.
- [x] Define MVP scope.
- [x] Define functional requirements.
- [x] Define non-functional requirements.
- [x] Define initial architecture.
- [x] Define initial data model.

## Phase 1 — Foundation

- [ ] Initialize Git repository.
- [ ] Create project structure.
- [ ] Configure backend.
- [ ] Configure frontend.
- [ ] Configure PostgreSQL.
- [ ] Configure Docker Compose.
- [ ] Configure environment variables.
- [ ] Create database migrations.

## Phase 2 — Core Transactions

- [ ] Implement categories.
- [ ] Implement transaction model.
- [ ] Implement transaction API.
- [ ] Implement transaction form.
- [ ] Implement transaction table.
- [ ] Implement edit/delete.
- [ ] Implement validation.

## Phase 3 — Dashboard

- [ ] Implement KPI cards.
- [ ] Implement period filters.
- [ ] Implement income/expense chart.
- [ ] Implement category charts.
- [ ] Implement monthly savings.
- [ ] Implement recent transactions.

## Phase 4 — Historical Data

- [ ] Analyze current Excel/CSV.
- [ ] Define source-to-database mapping.
- [ ] Build import pipeline.
- [ ] Validate historical records.
- [ ] Import cleaned dataset.
- [ ] Verify totals against the original source.

## Phase 5 — Analytics

- [ ] Add category performance.
- [ ] Add period comparisons.
- [ ] Add trend analysis.
- [ ] Add basic business metrics.
- [ ] Create analytical dataset.

## Phase 6 — Machine Learning

- [ ] Explore historical data.
- [ ] Define ML problem.
- [ ] Engineer features.
- [ ] Establish baseline models.
- [ ] Evaluate models.
- [ ] Track experiments.
- [ ] Integrate predictions.
- [ ] Build recommendation layer.

---

# 22. MVP Acceptance Criteria

The MVP is considered functional when:

1. A user can create an income transaction.
2. A user can create an expense transaction.
3. Transactions persist after restarting the application.
4. Transactions can be edited and deleted.
5. Transactions can be filtered by date and category.
6. The dashboard correctly calculates income.
7. The dashboard correctly calculates expenses.
8. The dashboard correctly calculates net balance.
9. The dashboard calculates estimated savings.
10. Category-level summaries are available.
11. Historical CSV/Excel data can be imported.
12. Invalid imported records are reported.
13. The original source data remains untouched.
14. The resulting database can be queried for future analytics.
15. The application can be extended without redesigning the core transaction model.

---

# 23. Key Business Metrics

The initial system should track:

```text
Total Revenue
Total Expenses
Net Revenue
Estimated Savings
Savings Rate
Transaction Count
Average Transaction Value
Revenue by Category
Expenses by Category
Daily Revenue
Monthly Revenue
Monthly Growth
```

Definitions:

```text
Net Revenue = Total Revenue - Total Expenses

Savings Rate = Estimated Savings / Total Revenue
```

If total revenue is zero:

```text
Savings Rate = 0
```

---

# 24. Future Extensions

Potential versions:

### v0.2

- User authentication.
- Product/service catalog.
- Better import tools.
- CSV export.
- More advanced reports.

### v0.3

- Inventory.
- Supplier management.
- Purchase tracking.
- Profit margins.
- Product-level analytics.

### v0.4

- Advanced analytics.
- Seasonality detection.
- Forecasting.
- ML experimentation interface.

### v0.5+

- Demand prediction.
- Investment recommendations.
- Automated alerts.
- Mobile/PWA support.
- Multi-user roles.
- Cloud deployment.

---

# 25. Design Principles

The project shall follow these principles:

### Simplicity First

The owner should not need accounting or technical knowledge to use the dashboard.

### Data First

Every transaction should create useful historical information.

### Incremental Development

Do not implement advanced features before the core workflow is reliable.

### Separation of Concerns

UI, business logic, persistence, analytics, and ML must remain logically separated.

### Explainability

Future recommendations should provide understandable reasons and supporting metrics.

### Extensibility

Categories, products, services, metrics, and ML models must be extendable.

### Source of Truth

The database becomes the operational source of truth. Excel/CSV files become import/export artifacts rather than the primary operational database.

---

# 26. Initial Technical Decisions

| Area | Decision |
|---|---|
| Frontend | React + TypeScript |
| Build tool | Vite |
| Styling | Tailwind CSS |
| Backend | FastAPI + Python |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Database | PostgreSQL |
| Charts | Recharts or equivalent |
| Data analysis | pandas |
| ML | scikit-learn initially |
| Containerization | Docker Compose |
| API style | REST |
| API version | `/api/v1` |
| Primary data format | PostgreSQL records |
| Historical input | CSV / Excel |

These are initial recommendations and may be revised during implementation if a documented technical reason exists.

---

# 27. Definition of Done — MVP

A feature is considered complete when:

- The requirement is implemented.
- Backend validation exists.
- Database persistence works.
- Frontend interaction works.
- Errors are handled.
- Relevant tests exist.
- The feature does not break existing functionality.
- The behavior is documented when necessary.

The MVP itself is complete when all mandatory acceptance criteria in Section 22 are satisfied.

---

# 28. Next Development Step

The immediate next step is **not Machine Learning**.

The development sequence should begin with:

```text
SPEC.md
   ↓
Repository structure
   ↓
Database schema
   ↓
Backend API
   ↓
Transaction CRUD
   ↓
Dashboard
   ↓
Historical CSV/Excel import
   ↓
Data validation
   ↓
Analytics
   ↓
Machine Learning
```

The first implementation milestone should therefore be a **working local dashboard capable of replacing the current Excel transaction workflow**, while preserving enough structured information to make future analytical and ML development possible.
