# Business Operations & Analytics Dashboard - UI/UX Design

This document outlines the user interface and user experience design for the MVP of the Business Operations & Analytics Dashboard, focusing on simplicity, clarity, and ease of use for a non-technical business owner.

## 1. Information Architecture & Navigation

The application uses a flat, simple navigation structure. A persistent sidebar (desktop) or bottom/hamburger menu (mobile) will provide access to the primary routes.

### Routes

- **`/` (Dashboard):** The main landing page. Provides a financial overview, KPI cards, charts, and a quick glance at recent transactions.
- **`/transactions` (History):** A detailed table view of all historical transactions with advanced filtering, search, edit, and delete capabilities.
- **`/transactions/new` (Add Transaction):** A dedicated, focused form to register a new income or expense transaction quickly. Alternatively, this can be presented as a modal/slide-over across the application.
- **`/import` (Data Import):** A specialized wizard flow for uploading, mapping, validating, and importing historical CSV/Excel data.

## 2. Dashboard Layout

Following the principles of clarity over density, the dashboard displays high-level financial information immediately upon loading.

### Layout Structure (Top to Bottom)

1. **Header Area:** 
   - Page Title: "Business Dashboard"
   - **Global Period Filter:** A dropdown/toggle for selecting the date range (Today, Current Week, Current Month, Previous Month, Custom Range).
2. **KPI Cards (Grid):**
   - **Income:** Total income for the selected period (Green).
   - **Expenses:** Total expenses for the selected period (Red).
   - **Net Balance:** Total Income - Total Expenses (Blue or Neutral).
   - **Estimated Savings:** Calculated savings amount.
   - **Savings Rate:** Percentage of savings vs total income.
   - **Transaction Count:** Total number of transactions in the period.
3. **Primary Visualization:**
   - **Income / Expense Trend Chart:** A line or bar chart showing income and expenses over time (days or weeks, depending on the selected period).
4. **Category Breakdown (Two Columns):**
   - **Income by Category:** A donut chart or horizontal bar chart showing top income sources.
   - **Expenses by Category:** A donut chart or horizontal bar chart showing top expense areas.
5. **Recent Transactions:**
   - A compact list of the 5-10 most recent transactions (Date, Type indicator, Category, Description, Amount).
   - A "View All" link pointing to `/transactions`.

## 3. Transaction Entry UX

The transaction entry flow is optimized for speed, requiring minimal clicks to register a sale or expense.

### Form Fields

- **Type:** Radio button toggle between "Income" and "Expense" (default to Income).
- **Date:** Date picker, defaulting to today/now.
- **Category:** Dropdown select. Options change dynamically based on the selected Type.
- **Amount:** Numeric input field. Prefixed with currency symbol.
- **Description:** Short text input for details (e.g., "20 color pages").
- **Notes:** (Optional) Text area for additional context.

### User Flow

1. User clicks "Add Transaction" (accessible via a persistent primary button).
2. User selects Type (Income/Expense).
3. User selects Category.
4. User enters Amount and Description.
5. User clicks "Save".

### Validation & Feedback

- Required fields (Type, Date, Category, Amount) must have visual cues.
- Amount must be a positive number.
- On error: Inline red text below the offending field.
- On success: A brief toast notification ("Transaction saved successfully") and the form clears for the next entry or redirects back to the dashboard.

## 4. Transaction History Table

A comprehensive view of all registered financial movements.

### Columns

- **Date:** Formatted as YYYY-MM-DD.
- **Type:** Visual badge (e.g., Green pill for Income, Red pill for Expense).
- **Category:** The assigned category name.
- **Description:** The transaction description.
- **Amount:** Formatted currency.
- **Actions:** Edit and Delete icon buttons.

### Filters & Search (Sticky Header or Toolbar)

- **Period Presets:** Dropdown (Today, Week, Month, Previous Month, Custom).
- **Type Filter:** Dropdown (All, Income, Expense).
- **Category Filter:** Dropdown (All, specific categories).
- **Text Search:** Input box searching across Description and Notes.

### Actions UX

- **Edit:** Opens a pre-filled transaction form (modal or separate page).
- **Delete:** Triggers a confirmation modal to prevent accidental data loss ("Are you sure you want to delete this transaction? This action cannot be undone.").

## 5. CSV/Excel Import Flow UX

A robust wizard designed to safely ingest historical data without polluting the database.

### Steps

1. **Upload:** A drag-and-drop zone or file picker for CSV/Excel files.
2. **Column Mapping:** The system guesses the mapping based on headers. The user sees a two-column list: System Fields (Date, Type, Category, Description, Amount) mapped to Dropdowns containing the Uploaded File's columns.
3. **Validation Report:** The system processes the file in memory and displays a summary: "X valid rows found. Y invalid rows found." 
   - Invalid rows are listed in a table highlighting the specific errors (e.g., "Invalid date format", "Negative amount").
4. **Preview:** A quick table view of the first 10 valid records as they will appear in the system.
5. **Confirm:** A final "Import X Transactions" button.
6. **Success State:** A summary screen with a button to return to the Dashboard.

## 6. Period Filter Behavior

- The period filter is a global context setter on the Dashboard.
- When changed (e.g., from "Current Month" to "Current Week"):
  - All KPI cards recalculate instantly.
  - The Trend chart re-renders the X-axis for the new time scale.
  - The Category charts recalculate their proportions.
  - The Recent Transactions list filters to show only records within that date range.
- The UI must reflect loading states on these components while new data is fetched.

## 7. Loading, Empty & Error States

- **Loading:** Use subtle skeleton loaders or spinners for KPI cards, charts, and tables. Avoid full-page blocking loaders.
- **Empty States:** 
  - *Dashboard (No data for period):* "No transactions found for this period. Add a transaction to see your metrics." Include a primary button to "Add Transaction".
  - *Charts:* Display a muted placeholder graphic indicating insufficient data.
- **Error States:**
  - *Network/API errors:* A dismissible banner or toast notification indicating the issue (e.g., "Failed to load dashboard data. Please try again.").
  - *Form errors:* Inline validation messages.

## 8. Responsive Behavior

The design is **desktop-first** but fully functional on tablets and mobile devices.

- **Desktop (1024px+):** Sidebar navigation. Dashboard uses a multi-column grid (e.g., 3-4 KPI cards per row, two charts side-by-side).
- **Tablet (768px - 1023px):** Sidebar collapses to icons or a top nav. KPI cards drop to 2 per row. Charts stack vertically if needed.
- **Mobile (< 768px):** Bottom tab navigation or hamburger menu. KPI cards stack 1 or 2 per row. Charts are simplified or require horizontal scrolling. Tables convert to a card-based list layout (each transaction is a card instead of a table row) to avoid horizontal scrolling issues.

## 9. Minimal Visual System (Tailwind CSS Base)

The UI will rely on a clean, minimal aesthetic using Tailwind CSS utility classes. Clarity and legibility are prioritized over density.

### Color Palette

- **Backgrounds:** Light gray/off-white (`bg-slate-50` or `bg-gray-50`) for the application background. White (`bg-white`) for cards and surface areas.
- **Text:** Dark slate (`text-slate-900`) for primary text. Medium gray (`text-slate-500`) for secondary text and labels.
- **Primary/Brand:** A professional blue (`text-blue-600`, `bg-blue-600`) for active states, primary buttons, and links.
- **Semantic Colors:**
  - *Income / Success:* Green (`text-emerald-600`, `bg-emerald-100` for badges).
  - *Expense / Error:* Red (`text-rose-600`, `bg-rose-100` for badges).
  - *Warning:* Amber/Yellow (`text-amber-600`).
- **Borders:** Subtle dividers (`border-slate-200`).

### Typography

- **Font Family:** System sans-serif (Inter, Roboto, SF Pro) provided by Tailwind's default sans stack.
- **Hierarchy:**
  - Page Titles: `text-2xl font-semibold`
  - Card Titles / Headers: `text-lg font-medium`
  - Base Text: `text-sm` or `text-base`
  - Small / Meta text: `text-xs text-slate-500`

### Spacing & Components

- **Spacing:** Generous padding around elements. Cards use `p-6`, sections separated by `gap-6` or `gap-8`.
- **Borders & Shadows:** Clean, soft edges. Cards use subtle shadows (`shadow-sm`) and rounded corners (`rounded-lg` or `rounded-xl`).
- **Animations:** Minimal. Only functional transitions (e.g., hover states on buttons `transition-colors duration-200`, simple modal fade-ins). No heavy or distracting animations.
