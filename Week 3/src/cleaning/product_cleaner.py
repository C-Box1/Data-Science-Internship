"""
cleaning/product_cleaner.py
----------------------------
Reads and cleans product reference Excel files (uploaded or from /data).
Returns a deduplicated list of Product objects ready for DB insertion.

The enforced website template uses the same 9-column structure as the
original reference files (combined_file.xlsx, elio_list.xlsx, etc.).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from src.cleaning.abbreviation_resolver import AbbreviationResolver
from src.models.product import Product

logger = logging.getLogger(__name__)

COLUMN_MAP: dict[str, str] = {
    "reference": "reference",
    "collection": "collection",
    "collection ": "collection",
    "gender": "gender",
    "mouvement": "movement",
    "movement": "movement",
    "dial": "dial",
    "bracelet": "bracelet",
    "bracelet ": "bracelet",
    "color": "color",
    "case size": "case_size",
    "case sze": "case_size",
    "case sze ": "case_size",
    "casesze": "case_size",
    "kind": "kind",
}

REFERENCE_FILES: list[tuple[str, str]] = [
    ("combined_file.xlsx", "Sheet1"),
    ("elio_list.xlsx", "Feuil2"),
    ("list_for_elio_2.xlsx", "Sheet1"),
    ("list for elio 2.xlsx", "Sheet1"),
    ("missing_info.xlsx", "Sheet2"),
]

PRODUCT_SHEET_CANDIDATES = ["Products", "Sheet1", "Bulk Entry", "Feuil2", "Sheet2"]


def detect_product_sheet(filepath: Path) -> str:
    """
    Pick the correct sheet for product uploads.
    Website templates use 'Products'; sample files like combined_file.xlsx use 'Sheet1'.
    """
    xl = pd.ExcelFile(filepath)
    for name in PRODUCT_SHEET_CANDIDATES:
        if name in xl.sheet_names:
            return name
    return xl.sheet_names[0]


PRODUCT_TEMPLATE_COLUMNS = [
    "REFERENCE",
    "COLLECTION",
    "GENDER",
    "MOUVEMENT",
    "DIAL",
    "BRACELET",
    "COLOR",
    "CASE SZE",
    "KIND",
]


class ProductCleaner:
    """Loads, normalizes, and deduplicates product records from Excel files."""

    def __init__(
        self,
        data_dir: Path,
        resolver: Optional[AbbreviationResolver] = None,
    ) -> None:
        self.data_dir = data_dir
        self.resolver = resolver or AbbreviationResolver()
        self._seen_references: set[str] = set()
        self._cleaning_log: list[dict] = []
        self._unknown_abbrevs: list[dict] = []

    def load_all(self) -> list[Product]:
        all_products: list[Product] = []
        for filename, sheet_name in REFERENCE_FILES:
            filepath = self.data_dir / filename
            if not filepath.exists():
                continue
            products = self._load_file(filepath, sheet_name)
            logger.info("Loaded %s valid products from %s", len(products), filename)
            all_products.extend(products)
        return all_products

    def load_uploaded_file(
        self,
        filepath: Path,
        sheet_name: Optional[str] = None,
    ) -> list[Product]:
        """Clean a single uploaded Excel file."""
        if sheet_name is None:
            sheet_name = detect_product_sheet(filepath)
        return self._load_file(filepath, sheet_name)

    def get_cleaning_log(self) -> list[dict]:
        return self._cleaning_log

    def get_unknown_abbreviations(self) -> list[dict]:
        return self._unknown_abbrevs

    def _load_file(self, filepath: Path, sheet_name: str) -> list[Product]:
        try:
            df = pd.read_excel(filepath, sheet_name=sheet_name, header=0)
        except Exception as exc:
            logger.error("Could not read %s: %s", filepath, exc)
            return []

        df = self._normalize_columns(df)
        df = self._drop_empty_columns(df)

        products: list[Product] = []
        for idx, row in df.iterrows():
            product = self._process_row(row, str(filepath.name), idx)
            if product is not None:
                products.append(product)
        return products

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        new_cols = {}
        for col in df.columns:
            if col is None:
                continue
            normalized = str(col).strip().lower()
            new_cols[col] = COLUMN_MAP.get(normalized, normalized)
        return df.rename(columns=new_cols)

    def _drop_empty_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.dropna(axis=1, how="all")

    def _process_row(
        self,
        row: pd.Series,
        source_file: str,
        row_idx: int,
    ) -> Optional[Product]:
        row_dict = row.to_dict()

        ref = row_dict.get("reference")
        if pd.isna(ref) or str(ref).strip() == "":
            self._log_drop(source_file, row_idx, "missing reference", row_dict)
            return None

        ref = str(ref).strip().upper()
        row_dict["reference"] = ref

        if ref in self._seen_references:
            self._log_drop(source_file, row_idx, f"duplicate reference {ref}", row_dict)
            return None

        for field_name in ["collection", "gender", "movement", "kind"]:
            val = row_dict.get(field_name)
            if pd.isna(val) if isinstance(val, float) else (val is None or str(val).strip() == ""):
                self._log_drop(
                    source_file,
                    row_idx,
                    f"missing required field: {field_name}",
                    row_dict,
                )
                return None

        try:
            product = Product.from_row(row_dict, resolver=self.resolver)
        except ValueError as exc:
            self._log_drop(source_file, row_idx, f"validation error: {exc}", row_dict)
            return None

        if product._unknown_abbrevs:
            for item in product._unknown_abbrevs:
                item["reference"] = ref
                item["source_file"] = source_file
                self._unknown_abbrevs.append(item)

        self._seen_references.add(ref)
        return product

    def _log_drop(self, source_file: str, row_idx: int, reason: str, row_dict: dict) -> None:
        self._cleaning_log.append(
            {
                "source_file": source_file,
                "row_index": row_idx,
                "reason": reason,
                "reference": row_dict.get("reference", ""),
            }
        )

    def save_cleaning_report(self, output_path: Path) -> None:
        if self._cleaning_log:
            pd.DataFrame(self._cleaning_log).to_csv(output_path, index=False)
            logger.info("Cleaning report saved to %s", output_path)
