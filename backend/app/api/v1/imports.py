from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.import_batch import ImportBatch, ImportRow
from app.schemas.import_data import (
    ImportBatchDetail,
    ImportBatchRead,
    ImportConfirmResponse,
    ImportMappingRequest,
    ImportMappingResponse,
    ImportUploadResponse,
)
from app.services.errors import EntityNotFoundError
from app.services.import_service import ImportService

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/transactions", response_model=ImportUploadResponse, status_code=201)
async def upload_transactions(file: UploadFile = File(...), db: Session = Depends(get_db)):
    service = ImportService(db)
    return await service.upload_transactions(file)


@router.post("/{batch_id}/mapping", response_model=ImportMappingResponse)
def mapping(batch_id: int, payload: ImportMappingRequest, db: Session = Depends(get_db)):
    service = ImportService(db)
    return service.apply_mapping(batch_id, payload)


@router.post("/{batch_id}/confirm", response_model=ImportConfirmResponse)
def confirm(batch_id: int, db: Session = Depends(get_db)):
    service = ImportService(db)
    return service.confirm(batch_id)


@router.get("", response_model=list[ImportBatchRead])
def list_import_batches(db: Session = Depends(get_db)):
    rows = db.scalars(select(ImportBatch).order_by(ImportBatch.created_at.desc())).all()
    return list(rows)


@router.get("/{batch_id}", response_model=ImportBatchDetail)
def get_import_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        raise EntityNotFoundError("batch not found")

    counts = dict(
        db.execute(
            select(ImportRow.status, func.count(ImportRow.id))
            .where(ImportRow.import_batch_id == batch_id)
            .group_by(ImportRow.status)
        ).all()
    )
    return {
        "id": batch.id,
        "filename": batch.filename,
        "source_type": batch.source_type,
        "status": batch.status,
        "records_total": batch.records_total,
        "records_valid": batch.records_valid,
        "records_invalid": batch.records_invalid,
        "records_duplicate": batch.records_duplicate,
        "records_inserted": batch.records_inserted,
        "created_at": batch.created_at,
        "updated_at": batch.updated_at,
        "rows_summary": {str(k): int(v) for k, v in counts.items()},
    }
