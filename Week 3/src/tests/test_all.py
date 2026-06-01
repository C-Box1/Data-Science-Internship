"""
tests/test_all.py
------------------
Tests for every module in the project.

Run:
    uv run pytest src/tests/test_all.py -v

DB tests use mocks — no PostgreSQL required for the full suite.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models.product import Product, Watch, Coffret, _normalize_str, _is_zero_placeholder
from src.models.shop import Shop
from src.models.abbreviation import Abbreviation
from src.cleaning.product_cleaner import ProductCleaner
from src.cleaning.abbreviation_resolver import AbbreviationResolver, DEFAULT_ALIASES
from src.cleaning.monthly_report_parser import MonthlyReportParser


class TestProduct(unittest.TestCase):
    def _valid_watch_row(self) -> dict:
        return {
            "reference": "002H621",
            "kind": "WATCH",
            "collection": "GALIERA",
            "gender": "LADIES",
            "movement": "QUARTZ",
            "dial": "SILVER",
            "bracelet": "MESH",
            "color": "SS",
            "case_size": "30",
        }

    def _valid_coffret_row(self) -> dict:
        return {
            "reference": "350J621",
            "kind": "COFFRET",
            "collection": "MULTIPLES",
            "gender": "LADIES",
            "movement": "QUARTZ",
            "dial": "SILVER",
            "bracelet": "MECH/LEATH",
            "color": "SS/ROSE",
            "case_size": "30",
        }

    def _resolver(self) -> AbbreviationResolver:
        return AbbreviationResolver(alias_maps=DEFAULT_ALIASES)

    def test_normalize_str_strips_whitespace(self):
        self.assertEqual(_normalize_str("  hello  "), "HELLO")

    def test_normalize_str_returns_none_for_empty(self):
        self.assertIsNone(_normalize_str("   "))

    def test_zero_dial_becomes_none(self):
        row = self._valid_watch_row()
        row["dial"] = 0.0
        product = Product.from_row(row, resolver=self._resolver())
        self.assertIsNone(product.dial)

    def test_watch_created_from_valid_row(self):
        product = Product.from_row(self._valid_watch_row(), resolver=self._resolver())
        self.assertIsInstance(product, Watch)

    def test_brclt_expands_to_bracelet(self):
        row = self._valid_watch_row()
        row["bracelet"] = "BRCLT"
        product = Product.from_row(row, resolver=self._resolver())
        self.assertEqual(product.strap, "BRACELET")

    def test_brace_expands_to_bracelet(self):
        row = self._valid_watch_row()
        row["bracelet"] = "BRACE"
        product = Product.from_row(row, resolver=self._resolver())
        self.assertEqual(product.strap, "BRACELET")

    def test_pg_expands_to_pink_gold_case_insensitive(self):
        row = self._valid_watch_row()
        row["color"] = "pg"
        product = Product.from_row(row, resolver=self._resolver())
        self.assertEqual(product.color, "PINK GOLD")

    def test_combo_abbrev_expansion(self):
        row = self._valid_coffret_row()
        product = Product.from_row(row, resolver=self._resolver())
        self.assertEqual(product.strap, "MESH/LEATHER STRAP")

    def test_coffret_combo_contents_parsed(self):
        product = Product.from_row(self._valid_coffret_row(), resolver=self._resolver())
        self.assertEqual(len(product.combo_contents()), 2)

    def test_invalid_kind_raises(self):
        row = self._valid_watch_row()
        row["kind"] = "STRAP"
        with self.assertRaises(ValueError):
            Product.from_row(row, resolver=self._resolver())


class TestAbbreviationResolver(unittest.TestCase):
    def test_case_insensitive_lookup(self):
        resolver = AbbreviationResolver(alias_maps=DEFAULT_ALIASES)
        self.assertEqual(resolver.resolve_token("brclt", "bracelet"), "BRACELET")
        self.assertEqual(resolver.resolve_token("PG", "color"), "PINK GOLD")
        self.assertEqual(resolver.resolve_token("pg", "color"), "PINK GOLD")

    def test_expand_combo(self):
        resolver = AbbreviationResolver(alias_maps=DEFAULT_ALIASES)
        expanded, unknown = resolver.expand("MECH/LEATH", "bracelet")
        self.assertEqual(expanded, "MESH/LEATHER STRAP")
        self.assertEqual(unknown, [])


class TestShop(unittest.TestCase):
    def test_standard_header_parsed(self):
        shop = Shop.from_header("1113 - Kingdom Mall - Riyadh - AlHomaidhi")
        self.assertEqual(shop.shop_id, "1113")
        self.assertEqual(shop.mall_name, "Kingdom Mall")

    def test_main_store_is_warehouse(self):
        shop = Shop.from_header("0001 - Main Store")
        self.assertEqual(shop.shop_type, "warehouse")

    def test_invalid_header_returns_none(self):
        self.assertIsNone(Shop.from_header("Item Code"))


class TestProductCleaner(unittest.TestCase):
    def _make_cleaner(self) -> ProductCleaner:
        return ProductCleaner(Path("/fake/data"), resolver=AbbreviationResolver(alias_maps=DEFAULT_ALIASES))

    def test_normalize_columns_fixes_mouvement_typo(self):
        import pandas as pd
        cleaner = self._make_cleaner()
        df = pd.DataFrame(columns=["REFERENCE", "MOUVEMENT"])
        df_normalized = cleaner._normalize_columns(df)
        self.assertIn("movement", df_normalized.columns)

    def test_valid_row_returns_product(self):
        import pandas as pd
        cleaner = self._make_cleaner()
        row = pd.Series({
            "reference": "002H621", "kind": "WATCH", "collection": "GALIERA",
            "gender": "LADIES", "movement": "QUARTZ",
        })
        result = cleaner._process_row(row, "test.xlsx", 2)
        self.assertIsInstance(result, Product)

    def test_duplicate_reference_is_dropped(self):
        import pandas as pd
        cleaner = self._make_cleaner()
        row = pd.Series({
            "reference": "002H621", "kind": "WATCH", "collection": "GALIERA",
            "gender": "LADIES", "movement": "QUARTZ",
        })
        cleaner._process_row(row, "test.xlsx", 2)
        result = cleaner._process_row(row, "test.xlsx", 3)
        self.assertIsNone(result)


class TestMonthlyReportParser(unittest.TestCase):
    def test_normalize_reference_rejects_headers(self):
        parser = MonthlyReportParser(set(), set())
        self.assertIsNone(parser._normalize_reference("Item Code"))
        self.assertEqual(parser._normalize_reference("002H621"), "002H621")

    def test_month_from_filename(self):
        parser = MonthlyReportParser(set(), set())
        month = parser._month_from_filename(Path("1-Pierre Lannier January 2024 Sales Per POS.xlsx"))
        self.assertEqual(month.month, 1)
        self.assertEqual(month.year, 2024)


class TestRepository(unittest.TestCase):
    def _make_mock_conn(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        return mock_conn, mock_cursor

    def _make_watch(self) -> Watch:
        resolver = AbbreviationResolver(alias_maps=DEFAULT_ALIASES)
        return Product.from_row({
            "reference": "002H621", "kind": "WATCH", "collection": "GALIERA",
            "gender": "LADIES", "movement": "QUARTZ",
            "dial": "SILVER", "bracelet": "MESH", "color": "SS", "case_size": "30",
        }, resolver=resolver)

    def test_upsert_product_inserts_new_record(self):
        from src.db.repository import upsert_product
        conn, cur = self._make_mock_conn()
        cur.fetchone.return_value = None
        result = upsert_product(conn, self._make_watch())
        self.assertEqual(result, "inserted")
        conn.commit.assert_called_once()

    def test_add_abbreviation(self):
        from src.db.repository import add_abbreviation
        conn, cur = self._make_mock_conn()
        cur.fetchone.return_value = None
        abbrev = Abbreviation("BRACE", "BRACELET", "bracelet")
        result = add_abbreviation(conn, abbrev)
        self.assertEqual(result, "inserted")

    def test_load_abbreviation_maps(self):
        from src.db.repository import load_abbreviation_maps
        conn, cur = self._make_mock_conn()
        cur.fetchall.return_value = [("BRCLT", "BRACELET", "bracelet"), ("PG", "PINK GOLD", "color")]
        maps = load_abbreviation_maps(conn)
        self.assertEqual(maps["bracelet"]["BRCLT"], "BRACELET")
        self.assertEqual(maps["color"]["PG"], "PINK GOLD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
