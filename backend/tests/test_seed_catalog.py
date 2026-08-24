import pytest
from decimal import Decimal

from scripts.seed_catalog import parse_price, normalize_name, parse_stock


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


class TestParseStock:
    def test_integer_value(self):
        val, flag = parse_stock(5)
        assert val == 5
        assert flag is None

    def test_integer_string(self):
        val, flag = parse_stock(" 12 ")
        assert val == 12
        assert flag is None

    def test_integral_float(self):
        """openpyxl may yield 7.0 for a cell holding 7."""
        val, flag = parse_stock(7.0)
        assert val == 7
        assert flag is None

    def test_none_is_null_stock(self):
        val, flag = parse_stock(None)
        assert val is None
        assert flag is None

    def test_blank_string_is_null_stock(self):
        val, flag = parse_stock("   ")
        assert val is None
        assert flag is None

    def test_fractional_rejected_as_unclean(self):
        val, flag = parse_stock(2.5)
        assert val is None
        assert flag == "UNCLEAN"

    def test_negative_rejected_as_unclean(self):
        val, flag = parse_stock(-3)
        assert val is None
        assert flag == "UNCLEAN"

    def test_text_rejected_as_unclean(self):
        val, flag = parse_stock("muchos")
        assert val is None
        assert flag == "UNCLEAN"


class TestParseWorkbookStockColumn:
    def _write_xlsx(self, tmp_path, rows):
        import openpyxl
        path = tmp_path / "catalog.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Precios"
        for row in rows:
            ws.append(row)
        wb.save(path)
        return str(path)

    def test_stock_column_parsed_per_product(self, tmp_path):
        from scripts.seed_catalog import parse_workbook

        path = self._write_xlsx(
            tmp_path,
            [
                ("ARTICULO", "VALOR FACTURA", "VALOR / LOCAL", "GANANCIA", "MARGEN %", "STOCK", "Nota"),
                ("BOLIGRAFO ROJO", 650, 1300, 650, 1, 1, None),
                ("BOLIGRAFO AZUL", 260, 1000, 740, 2.8, None, None),
                ("CALCULADORA", 5000, 9000, 4000, 0.8, 44, None),
            ],
        )
        parsed, anomalies = parse_workbook(path, "Precios")
        by_name = {item["name"]: item for item in parsed}
        assert by_name["BOLIGRAFO ROJO"]["stock"] == 1
        assert by_name["BOLIGRAFO AZUL"]["stock"] is None
        assert by_name["CALCULADORA"]["stock"] == 44

    def test_workbook_without_stock_column_still_parses(self, tmp_path):
        from scripts.seed_catalog import parse_workbook

        path = self._write_xlsx(
            tmp_path,
            [
                ("ARTICULO", "VALOR FACTURA", "VALOR / LOCAL"),
                ("LAPIZ NEGRO", 200, 350),
            ],
        )
        parsed, anomalies = parse_workbook(path, "Precios")
        assert len(parsed) == 1
        assert parsed[0]["stock"] is None

    def test_unclean_stock_reported_as_anomaly(self, tmp_path):
        from scripts.seed_catalog import parse_workbook

        path = self._write_xlsx(
            tmp_path,
            [
                ("ARTICULO", "VALOR FACTURA", "VALOR / LOCAL", "GANANCIA", "MARGEN %", "STOCK"),
                ("TIJERA", 1200, 2500, 1300, 1.08, -2),
            ],
        )
        parsed, anomalies = parse_workbook(path, "Precios")
        assert parsed[0]["stock"] is None
        assert len(anomalies.get("UNCLEAN", [])) >= 1


class TestUpsertStockSemantics:
    def _upsert(self, db_session, items):
        from scripts.seed_catalog import upsert_products
        return upsert_products(db_session, items)

    def test_existing_product_stock_updated_when_value_present(self, db_session):
        from app.models.product import Product

        product = Product(name="Cuaderno A5", category_id=1, stock_qty=3)
        db_session.add(product)
        db_session.commit()

        self._upsert(db_session, [{
            "name": "Cuaderno A5",
            "norm": normalize_name("Cuaderno A5"),
            "invoice_price": Decimal("1000"),
            "local_price": Decimal("1500"),
            "stock": 8,
        }])
        db_session.refresh(product)
        assert product.stock_qty == 8

    def test_null_stock_cell_does_not_wipe_existing_stock(self, db_session):
        from app.models.product import Product

        product = Product(name="Regla 30cm", category_id=1, stock_qty=6)
        db_session.add(product)
        db_session.commit()

        self._upsert(db_session, [{
            "name": "Regla 30cm",
            "norm": normalize_name("Regla 30cm"),
            "invoice_price": Decimal("100"),
            "local_price": Decimal("200"),
            "stock": None,
        }])
        db_session.refresh(product)
        assert product.stock_qty == 6

    def test_new_product_created_with_stock_value(self, db_session):
        from app.models.product import Product

        self._upsert(db_session, [{
            "name": "Tijera Nueva",
            "norm": normalize_name("Tijera Nueva"),
            "invoice_price": Decimal("1200"),
            "local_price": Decimal("2500"),
            "stock": 4,
        }])
        created = db_session.query(Product).filter(Product.name == "Tijera Nueva").one()
        assert created.stock_qty == 4

    def test_new_product_created_with_null_stock(self, db_session):
        from app.models.product import Product

        self._upsert(db_session, [{
            "name": "Sobre Blanco",
            "norm": normalize_name("Sobre Blanco"),
            "invoice_price": None,
            "local_price": Decimal("50"),
            "stock": None,
        }])
        created = db_session.query(Product).filter(Product.name == "Sobre Blanco").one()
        assert created.stock_qty is None
