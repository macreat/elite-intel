"""Business rules for income tracking categories.

Accesorios: only 40% of gross is stored as INCOME profit (affects incomes / net balance).
BeMovilRemote: volume tracking from kardex column B; excluded from normal income KPIs.
BeMovileIncome: manual net Be Movil gains only (never auto-derived from column B).
"""

from __future__ import annotations

import re
from decimal import Decimal

ACCESORIOS_PROFIT_RATE = Decimal("0.40")
ACCESORIOS_CATEGORY = "Accesorios"
BEMOVIL_REMOTE_CATEGORY = "BeMovilRemote"
BEMOVILE_INCOME_CATEGORY = "BeMovileIncome"

# Categories tracked as INCOME that represent money set aside as savings (e.g. monthly
# savings deposits built up across the month). Estimated Savings sums these directly.
ESTIMATED_SAVINGS_CATEGORIES = frozenset({"Ahorro mensual"})

# Categories tracked as INCOME but excluded from dashboard income / net KPIs and CSV running balance.
KPI_EXCLUDED_INCOME_CATEGORIES = frozenset({BEMOVIL_REMOTE_CATEGORY})

_ACCESORIOS_GROSS_NOTE_RE = re.compile(r"accesorios_gross=([0-9]+(?:\.[0-9]+)?)")
_AMOUNT_QUANTUM = Decimal("0.01")


def _normalize_category_name(name: str) -> str:
    return " ".join((name or "").strip().lower().split())


def is_accesorios_category(name: str) -> bool:
    return _normalize_category_name(name) == _normalize_category_name(ACCESORIOS_CATEGORY)


def is_kpi_excluded_income_category(name: str) -> bool:
    return (name or "").strip() in KPI_EXCLUDED_INCOME_CATEGORIES


def _upsert_accesorios_gross_note(notes: str | None, gross: Decimal) -> str:
    marker = f"accesorios_gross={gross.quantize(_AMOUNT_QUANTUM)}"
    existing = (notes or "").strip()
    if not existing:
        return marker
    if _ACCESORIOS_GROSS_NOTE_RE.search(existing):
        return _ACCESORIOS_GROSS_NOTE_RE.sub(marker, existing)
    return f"{existing}; {marker}"


def resolve_accesorios_amount(
    category_name: str,
    amount: Decimal,
    notes: str | None = None,
) -> tuple[Decimal, str | None]:
    """Convert Accesorios gross to 40% profit income; leave other categories unchanged.

    Idempotent: if notes already record accesories_gross and amount equals that profit,
    the values are returned as-is (avoids double-application on import confirm / re-save).
    """
    if not is_accesorios_category(category_name):
        return amount, notes

    quantized = Decimal(amount).quantize(_AMOUNT_QUANTUM)
    match = _ACCESORIOS_GROSS_NOTE_RE.search(notes or "")
    if match:
        gross = Decimal(match.group(1)).quantize(_AMOUNT_QUANTUM)
        expected_profit = (gross * ACCESORIOS_PROFIT_RATE).quantize(_AMOUNT_QUANTUM)
        if quantized == expected_profit:
            return quantized, notes

    profit = (quantized * ACCESORIOS_PROFIT_RATE).quantize(_AMOUNT_QUANTUM)
    return profit, _upsert_accesorios_gross_note(notes, quantized)
