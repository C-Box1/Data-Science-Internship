"""
cleaning/monthly_report_parser.py
-----------------------------------
Parses monthly Sales & Stock Excel reports into sold_elements and
present_elements records.

Handles two report layouts found in the data folder:
  1. POS wide format (January 2024): shop headers in row 0, Sales/Cls Stock pairs
  2. Time-series format (Feb–Nov): month dates in row 0, sales quantities only
"""

from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from src.models.shop import Shop

logger = logging.getLogger(__name__)

ITEM_CODE_PATTERN = re.compile(r"^[A-Z0-9]{6,8}$", re.IGNORECASE)


class MonthlyReportParser:
    """Parse monthly sales/stock Excel reports."""

    def __init__(self, known_references: set[str], known_shop_ids: set[str]) -> None:
        self.known_references = {r.upper() for r in known_references}
        self.known_shop_ids = known_shop_ids
        self._log: list[dict] = []

    def parse_file(self, filepath: Path) -> dict:
        """
        Parse one monthly report file.

        Returns:
            {
                "shops": list[Shop],
                "sold": list[dict],
                "present": list[dict],
                "report_month": date | None,
                "format": str,
            }
        """
        df = pd.read_excel(filepath, sheet_name=0, header=None)
        if df.empty:
            return self._empty_result()

        row0 = df.iloc[0]
        if self._is_pos_wide_format(row0):
            return self._parse_pos_wide(df, filepath)

        return self._parse_time_series(df, filepath)

    def get_log(self) -> list[dict]:
        return self._log

    def _empty_result(self) -> dict:
        return {
            "shops": [],
            "sold": [],
            "present": [],
            "report_month": None,
            "format": "empty",
        }

    def _is_pos_wide_format(self, row0: pd.Series) -> bool:
        for val in row0:
            if isinstance(val, str) and re.match(r"^\d{4}\s-", val.strip()):
                return True
        return False

    def _parse_pos_wide(self, df: pd.DataFrame, filepath: Path) -> dict:
        shops: list[Shop] = []
        sold: list[dict] = []
        present: list[dict] = []

        row0 = df.iloc[0]
        row1 = df.iloc[1] if len(df) > 1 else pd.Series()

        report_month = self._month_from_filename(filepath)

        shop_columns: list[tuple[int, str]] = []
        for col_idx, header in enumerate(row0):
            if not isinstance(header, str):
                continue
            shop = Shop.from_header(header.strip())
            if shop is None:
                continue
            shops.append(shop)
            shop_columns.append((col_idx, shop.shop_id))

        # Shops from this file are valid even if not in DB yet (first upload).
        allowed_shop_ids = self.known_shop_ids | {sid for _, sid in shop_columns}

        for col_idx, shop_id in shop_columns:
            metric = str(row1.iloc[col_idx]).strip().lower() if col_idx < len(row1) else ""
            stock_col = col_idx + 1 if metric == "sales" else col_idx

            for row_idx in range(2, len(df)):
                ref = self._normalize_reference(df.iloc[row_idx, 0])
                if ref is None:
                    continue

                sales_val = self._safe_int(df.iloc[row_idx, col_idx])
                stock_val = self._safe_int(df.iloc[row_idx, stock_col])

                if sales_val and sales_val > 0 and report_month:
                    if ref in self.known_references and shop_id in allowed_shop_ids:
                        sold.append(
                            {
                                "item_reference": ref,
                                "shop_id": shop_id,
                                "sale_month": report_month,
                                "quantity_sold": sales_val,
                                "sale_source": "monthly_report",
                            }
                        )

                if stock_val is not None and stock_val >= 0 and report_month:
                    if ref in self.known_references and shop_id in allowed_shop_ids:
                        present.append(
                            {
                                "item_reference": ref,
                                "shop_id": shop_id,
                                "report_month": report_month,
                                "closing_stock": stock_val,
                            }
                        )

        return {
            "shops": shops,
            "sold": sold,
            "present": present,
            "report_month": report_month,
            "format": "pos_wide",
        }

    def _parse_time_series(self, df: pd.DataFrame, filepath: Path) -> dict:
        sold: list[dict] = []
        row0 = df.iloc[0]
        month_columns: list[tuple[int, date]] = []

        for col_idx, val in enumerate(row0):
            parsed = self._parse_month_value(val)
            if parsed is not None:
                month_columns.append((col_idx, parsed))

        for row_idx in range(1, len(df)):
            ref = self._normalize_reference(df.iloc[row_idx, 0])
            if ref is None:
                continue

            for col_idx, sale_month in month_columns:
                qty = self._safe_int(df.iloc[row_idx, col_idx])
                if qty and qty > 0 and ref in self.known_references:
                    # Time-series reports lack per-shop columns — skip DB insert
                    # and log so employees know to use the POS-wide template instead.
                    self._log.append(
                        {
                            "reference": ref,
                            "reason": "time_series format has no shop columns — use POS template",
                        }
                    )

        return {
            "shops": [],
            "sold": sold,
            "present": [],
            "report_month": month_columns[-1][1] if month_columns else self._month_from_filename(filepath),
            "format": "time_series",
        }

    def _normalize_reference(self, value: object) -> Optional[str]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        ref = str(value).strip().upper()
        if ref in {"ITEM CODE", "PIERRE LANNIER", "PIERRE LANNIER WATCHES"}:
            return None
        if ITEM_CODE_PATTERN.match(ref):
            return ref
        return None

    def _parse_month_value(self, value: object) -> Optional[date]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        try:
            ts = pd.to_datetime(value)
            return date(ts.year, ts.month, 1)
        except (ValueError, TypeError):
            return None

    def _month_from_filename(self, filepath: Path) -> Optional[date]:
        name = filepath.name.lower()
        months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }
        year_match = re.search(r"(20\d{2})", name)
        year = int(year_match.group(1)) if year_match else 2024
        for month_name, month_num in months.items():
            if month_name in name:
                return date(year, month_num, 1)
        return None

    def _safe_int(self, value: object) -> Optional[int]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None
