from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import categories, dashboard, imports, products, transactions
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


app.include_router(transactions.router, prefix=settings.API_V1_PREFIX)
app.include_router(categories.router, prefix=settings.API_V1_PREFIX)
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(imports.router, prefix=settings.API_V1_PREFIX)
