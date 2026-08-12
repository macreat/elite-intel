from sqlalchemy import Boolean, Enum, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import TransactionType


class Category(Base, TimestampMixin):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("name", "type", name="uq_categories_name_type"),
        Index("idx_categories_type_active", "type", "active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType, name="transaction_type_enum"), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    transactions = relationship("Transaction", back_populates="category")
    products = relationship("Product", back_populates="category")
