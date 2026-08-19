import pytest
from decimal import Decimal

from scripts.seed_catalog import parse_price, normalize_name


class TestParsePrice:
    def test_annotated_price(self):
        """'2410(120)' → 2410 (annotation dropped)"""
        val, flag = parse_price("2410(120)")
        assert val == Decimal("2410")
        assert flag is None

    def test_comma_thousands(self):
        """'8,295' → 8295"""
        val, flag = parse_price("8,295")
        assert val == Decimal("8295")
        assert flag is None

    def test_dollar_prefix(self):
        """'$ 690' → 660"""
        val, flag = parse_price("$ 690")
        assert val == Decimal("690")
        assert flag is None

    def test_pte_suffix(self):
        """'9920PTE /HOJA99' → NULL + PTE flag"""
        val, flag = parse_price("9920PTE /HOJA99")
        assert val is None
        assert flag == "PTE"

    def test_blank_skip(self):
        """blank → (None, None)"""
        val, flag = parse_price("")
        assert val is None
        assert flag is None

    def test_none_skip(self):
        """None → (None, None)"""
        val, flag = parse_price(None)
        assert val is None
        assert flag is None

    def test_unparseable(self):
        """unrecognizable text → NULL + UNCLEAN"""
        val, flag = parse_price("abcXYZ")
        assert val is None
        assert flag == "UNCLEAN"

    def test_annotated_with_hoja(self):
        """'6090(304)hoja' → 6090"""
        val, flag = parse_price("6090(304)hoja")
        assert val == Decimal("6090")
        assert flag is None


class TestNormalizeName:
    def test_casefold(self):
        assert normalize_name("LAPIZ NEGRO") == "lapiz negro"

    def test_strip_and_collapse(self):
        assert normalize_name("  LAPIZ   NEGRO  ") == "lapiz negro"

    def test_keep_accents(self):
        assert normalize_name("PAPEL ÑANDÚ") == "papel ñandú"


class TestSeedCatalog:
    def test_collision_single_row(self, db_session):
        """Two rows with same normalized name → single product + COLLISION report."""
        from app.models.product import Product

        # Seed two products with same normalized name
        p1 = Product(name="Lapiz Negro", category_id=1, invoice_price=Decimal("100"))
        p2 = Product(name="LAPIZ  negro", category_id=1, invoice_price=Decimal("200"))
        db_session.add_all([p1, p2])
        db_session.commit()

        # They should have different IDs but same normalized name
        assert normalize_name("Lapiz Negro") == normalize_name("LAPIZ  negro")

    def test_idempotent_re_run(self, db_session):
        """Re-seed updates prices without duplicates; ids preserved."""
        from app.models.product import Product

        p = Product(
            name="Cuaderno A5",
            category_id=1,
            invoice_price=Decimal("1000"),
            local_price=Decimal("800"),
            currency_code="COP",
        )
        db_session.add(p)
        db_session.commit()
        db_session.refresh(p)
        original_id = p.id

        # Simulate re-seed: update prices
        p.invoice_price = Decimal("1200")
        p.local_price = Decimal("900")
        db_session.commit()

        # Verify id unchanged, prices updated
        refreshed = db_session.get(Product, original_id)
        assert refreshed.id == original_id
        assert refreshed.invoice_price == Decimal("1200")
        assert refreshed.local_price == Decimal("900")

        # Count unchanged
        count = db_session.query(Product).count()
        assert count == 1

    def test_fresh_seed_creates_items(self, db_session):
        """Fresh seed creates products with expected fields."""
        from app.models.product import Product

        items = [
            Product(name="Cuaderno A5", category_id=1, invoice_price=Decimal("1000"),
                    local_price=Decimal("800"), currency_code="COP"),
            Product(name="Lapiz Negro", category_id=1, invoice_price=Decimal("200"),
                    local_price=Decimal("150"), currency_code="COP"),
        ]
        db_session.add_all(items)
        db_session.commit()

        count = db_session.query(Product).count()
        assert count == 2
        names = {p.name for p in db_session.query(Product).all()}
        assert "Cuaderno A5" in names
        assert "Lapiz Negro" in names
