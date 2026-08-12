from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, and_, case, cast, func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import TransactionType
from app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        type_filter: TransactionType | None = None,
        category_id: int | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Transaction], int]:
        stmt = select(Transaction)
        count_stmt = select(func.count()).select_from(Transaction)

        filters = []
        if start_date is not None:
            filters.append(Transaction.occurred_at >= start_date)
        if end_date is not None:
            filters.append(Transaction.occurred_at <= end_date)
        if type_filter is not None:
            filters.append(Transaction.transaction_type == type_filter)
        if category_id is not None:
            filters.append(Transaction.category_id == category_id)
        if search:
            term = f"%{search}%"
            filters.append((Transaction.description.ilike(term)) | (func.coalesce(Transaction.notes, "").ilike(term)))

        if filters:
            clause = and_(*filters)
            stmt = stmt.where(clause)
            count_stmt = count_stmt.where(clause)

        total = int(self.db.scalar(count_stmt) or 0)
        items = list(
            self.db.scalars(
                stmt.order_by(Transaction.occurred_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total

    def get(self, transaction_id: int) -> Transaction | None:
        return self.db.get(Transaction, transaction_id)

    def create(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        self.db.flush()
        self.db.refresh(transaction)
        return transaction

    def update(self, transaction: Transaction) -> Transaction:
        self.db.add(transaction)
        self.db.flush()
        self.db.refresh(transaction)
        return transaction

    def delete(self, transaction: Transaction) -> None:
        self.db.delete(transaction)
        self.db.flush()

    def dashboard_summary(self, *, start_date: datetime, end_date: datetime) -> dict:
        income_case = case((Transaction.transaction_type == TransactionType.INCOME, Transaction.amount), else_=0)
        expense_case = case((Transaction.transaction_type == TransactionType.EXPENSE, Transaction.amount), else_=0)
        stmt = select(
            cast(func.coalesce(func.sum(income_case), 0), Numeric(14, 2)),
            cast(func.coalesce(func.sum(expense_case), 0), Numeric(14, 2)),
            func.count(Transaction.id),
        ).where(Transaction.occurred_at >= start_date, Transaction.occurred_at <= end_date)
        income, expenses, count = self.db.execute(stmt).one()
        income = Decimal(income)
        expenses = Decimal(expenses)
        net = income - expenses
        savings = max(net, Decimal("0"))
        savings_rate = float(savings / income) if income > 0 else 0.0
        return {
            "total_income": income,
            "total_expenses": expenses,
            "net_balance": net,
            "estimated_savings": savings,
            "savings_rate": savings_rate,
            "transaction_count": int(count or 0),
        }

    def dashboard_categories(self, *, start_date: datetime, end_date: datetime, type_filter: TransactionType | None = None):
        stmt = (
            select(Transaction.category_id, Category.name, cast(func.sum(Transaction.amount), Numeric(14, 2)))
            .join(Category, Category.id == Transaction.category_id)
            .where(Transaction.occurred_at >= start_date, Transaction.occurred_at <= end_date)
            .group_by(Transaction.category_id, Category.name)
            .order_by(func.sum(Transaction.amount).desc())
        )
        if type_filter is not None:
            stmt = stmt.where(Transaction.transaction_type == type_filter)
        return list(self.db.execute(stmt).all())

    def dashboard_timeseries(self, *, start_date: datetime, end_date: datetime):
        day = func.date(Transaction.occurred_at)
        income_case = case((Transaction.transaction_type == TransactionType.INCOME, Transaction.amount), else_=0)
        expense_case = case((Transaction.transaction_type == TransactionType.EXPENSE, Transaction.amount), else_=0)
        stmt = (
            select(
                day.label("d"),
                cast(func.coalesce(func.sum(income_case), 0), Numeric(14, 2)),
                cast(func.coalesce(func.sum(expense_case), 0), Numeric(14, 2)),
            )
            .where(Transaction.occurred_at >= start_date, Transaction.occurred_at <= end_date)
            .group_by(day)
            .order_by(day)
        )
        return list(self.db.execute(stmt).all())
