"""
cleaning/pipeline.py
--------------------
Orchestrates the full ETL flow: clean → resolve abbreviations → insert into DB.
"""

from __future__ import annotations

import logging
from pathlib import Path

from psycopg2.extensions import connection as PgConnection

from src.cleaning.abbreviation_resolver import AbbreviationResolver
from src.cleaning.monthly_report_parser import MonthlyReportParser
from src.cleaning.product_cleaner import ProductCleaner
from src.db import repository as repo
from src.models.product import Product
from src.models.shop import Shop

logger = logging.getLogger(__name__)


def run_product_upload(
    conn: PgConnection,
    filepath: Path,
    sheet_name: str = "Products",
) -> dict:
    resolver = AbbreviationResolver(conn)
    cleaner = ProductCleaner(filepath.parent, resolver=resolver)
    products = cleaner.load_uploaded_file(filepath, sheet_name=sheet_name)

    summary = repo.bulk_insert_products(conn, products)
    return {
        "products_loaded": len(products),
        "insert_summary": summary,
        "cleaning_log": cleaner.get_cleaning_log(),
        "unknown_abbreviations": cleaner.get_unknown_abbreviations(),
    }


def run_manual_products(conn: PgConnection, rows: list[dict]) -> dict:
    resolver = AbbreviationResolver(conn)
    products: list[Product] = []
    unknown: list[dict] = []

    for row in rows:
        product = Product.from_row(row, resolver=resolver)
        products.append(product)
        unknown.extend(product._unknown_abbrevs)

    summary = repo.bulk_insert_products(conn, products)
    return {
        "insert_summary": summary,
        "unknown_abbreviations": unknown,
    }


def run_monthly_report_upload(conn: PgConnection, filepath: Path) -> dict:
    known_refs = repo.get_all_references(conn)
    known_shops = repo.get_all_shop_ids(conn)

    parser = MonthlyReportParser(known_refs, known_shops)
    parsed = parser.parse_file(filepath)

    shop_summary = repo.bulk_insert_shops(conn, parsed["shops"])
    sold_count = repo.bulk_insert_sold_elements(conn, parsed["sold"])
    present_count = repo.bulk_insert_present_elements(conn, parsed["present"])

    return {
        "format": parsed["format"],
        "report_month": str(parsed["report_month"]) if parsed["report_month"] else None,
        "shops_summary": shop_summary,
        "sold_records": sold_count,
        "present_records": present_count,
        "parse_log": parser.get_log(),
    }


def run_seed_from_data_folder(conn: PgConnection, data_dir: Path) -> dict:
    """Load all reference Excel files from /data (development bootstrap)."""
    resolver = AbbreviationResolver(conn)
    cleaner = ProductCleaner(data_dir, resolver=resolver)
    products = cleaner.load_all()

    product_summary = repo.bulk_insert_products(conn, products)
    return {
        "products_loaded": len(products),
        "insert_summary": product_summary,
        "unknown_abbreviations": cleaner.get_unknown_abbreviations(),
    }
