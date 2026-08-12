from sqlalchemy import CHAR, JSON, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import ImportRowStatus, ImportStatus


class ImportBatch(Base, TimestampMixin):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(10), nullable=False)
    content_hash: Mapped[str] = mapped_column(CHAR(64), unique=True, nullable=False)
    mapping_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    mapping_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1", server_default="v1")
    parser_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1", server_default="v1")
    currency_assumption: Mapped[str] = mapped_column(String(3), nullable=False, default="ARS", server_default="ARS")
    status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus, name="import_status_enum"), nullable=False, default=ImportStatus.PENDING
    )
    records_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_valid: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_invalid: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_duplicate: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_inserted: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    rows = relationship("ImportRow", back_populates="batch", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="import_batch")


class ImportRow(Base):
    __tablename__ = "import_rows"
    __table_args__ = (
        Index("idx_import_rows_batch", "import_batch_id"),
        Index("idx_import_rows_fingerprint", "record_fingerprint"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    import_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id", ondelete="CASCADE"), nullable=False)
    source_row_number: Mapped[int] = mapped_column(nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    normalized_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    record_fingerprint: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    status: Mapped[ImportRowStatus] = mapped_column(Enum(ImportRowStatus, name="import_row_status_enum"), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"), nullable=True)

    batch = relationship("ImportBatch", back_populates="rows")
    transaction = relationship("Transaction", back_populates="import_row")
