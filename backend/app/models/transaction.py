from datetime import datetime
from decimal import Decimal

from sqlalchemy import CHAR, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import TransactionSource, TransactionType


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        UniqueConstraint("import_batch_id", "source_row_number", name="uq_transactions_import_batch_row"),
        UniqueConstraint("source_fingerprint", name="uq_transactions_source_fingerprint"),
        Index("idx_transactions_occurred_at", "occurred_at"),
        Index("idx_transactions_type_occurred_at", "transaction_type", "occurred_at"),
        Index("idx_transactions_category_id", "category_id"),
        Index("idx_transactions_import_batch_id", "import_batch_id"),
        Index("idx_transactions_fingerprint", "record_fingerprint"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_date_raw: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type_enum"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    category_name_raw: Mapped[str | None] = mapped_column(String(150), nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="ARS", server_default="ARS")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[TransactionSource] = mapped_column(
        Enum(TransactionSource, name="transaction_source_enum"),
        nullable=False,
        default=TransactionSource.MANUAL,
        server_default="MANUAL",
    )
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"), nullable=True)
    source_row_number: Mapped[int | None] = mapped_column(nullable=True)
    record_fingerprint: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    source_fingerprint: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)

    category = relationship("Category", back_populates="transactions")
    product = relationship("Product", back_populates="transactions")
    import_batch = relationship("ImportBatch", back_populates="transactions")
    import_row = relationship("ImportRow", back_populates="transaction", uselist=False)
