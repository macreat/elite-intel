from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import catalog, categories, dashboard, imports, products, transactions
from app.core.config import settings
from app.services.errors import DomainError

app = FastAPI(title="Elite Intel Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def handle_domain_error(_: Request, exc: DomainError):
    status_code = 400
    if exc.code == "ENTITY_NOT_FOUND":
        status_code = 404
    return JSONResponse(status_code=status_code, content={"error_code": exc.code, "message": exc.message})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get(f"{settings.API_V1_PREFIX}/health")
def health_v1():
    return {"status": "ok"}


app.include_router(imports.router, prefix=settings.API_V1_PREFIX)
app.include_router(transactions.router, prefix=settings.API_V1_PREFIX)
app.include_router(categories.router, prefix=settings.API_V1_PREFIX)
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(catalog.router, prefix=settings.API_V1_PREFIX)

def _resolve_static_dir(configured_static_dir=None, backend_root=None):
    candidates = []
    if configured_static_dir is None:
        configured_static_dir = settings.STATIC_DIR
    if backend_root is None:
        backend_root = Path(__file__).resolve().parents[2]

    if configured_static_dir:
        candidates.append(Path(configured_static_dir))

    backend_root_parent = backend_root.parent
    candidates.append(backend_root_parent / "frontend" / "dist")
    candidates.append(backend_root_parent.parent / "frontend" / "dist")

    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def _register_frontend_routes(target_app: FastAPI, static_dir: Path):
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        target_app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @target_app.get("/runtime-config.js")
    def runtime_config():
        return FileResponse(static_dir / "runtime-config.js")

    @target_app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        candidate = static_dir / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(static_dir / "index.html")


static_dir = _resolve_static_dir()
if static_dir:
    _register_frontend_routes(app, static_dir)
