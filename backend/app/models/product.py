from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (Index("idx_products_category_id", "category_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    invoice_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    local_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="COP", server_default="COP")
    stock_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)

    category = relationship("Category", back_populates="products")
    transactions = relationship("Transaction", back_populates="product")
