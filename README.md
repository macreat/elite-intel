# Elite Intel

Business dashboard for tracking income, expenses, and the product catalog.

## Install

1. Go to the PC where the app will run.
2. Get the code:
   - Clone via HTTPS: `git clone https://github.com/macreat/elite-intel.git`
   - Or download the ZIP from GitHub and extract it.
3. Double-click `install.bat` (or `install.sh` if `.sh` files are already
   associated with Git Bash on this PC).
4. Accept the one confirmation prompt. The installer then runs unattended:
   it installs Node.js and Python if missing, installs dependencies, builds
   the dashboard, packages `elite-intel.exe`, and creates a desktop shortcut.
5. Launch the app from the `elite-intel` icon on the desktop.

## Data locations

- **Price catalog**: `backend/data/raw/PRECIOS_PRODUCTOS_PAPELERIA.xlsx`.
  This spreadsheet is the source of truth for product prices. Stock and
  price updates made in the app are written back to this same file, so it
  always reflects the current catalog.
- **2026 transactions**: tracked in the SQLite database at
  `backend/elite.db` (the app's live database, created on first launch) and
  mirrored to the ledger CSV at `backend/data/raw/2026-2.csv`. New
  transactions registered in the app are saved to both.

## Development

See `backend/README.md` and `frontend/src/README.md` for API and dashboard
development notes, and `docker-compose.yml` for the Docker-based development
stack (Postgres + backend + frontend). The desktop build described above
does not use Docker: it runs the backend directly with a local Python
virtual environment and a SQLite database.
