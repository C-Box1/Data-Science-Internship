"""
templates_excel/generator.py
----------------------------
Creates downloadable Excel templates that match the enforced upload format.
Employees download these, fill them in Excel, and re-upload through the website.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

from src.cleaning.product_cleaner import PRODUCT_TEMPLATE_COLUMNS

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True)


def generate_product_template(output_path: Path) -> Path:
    """
    Product catalog template — same 9 columns as combined_file.xlsx.
    Includes one example WATCH row and one example COFFRET row.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Products"

    ws.append(PRODUCT_TEMPLATE_COLUMNS)
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT

    ws.append(
        [
            "002H621",
            "GALIERA",
            "LADIES",
            "QUARTZ",
            "SILVER",
            "MESH",
            "SS",
            "30",
            "WATCH",
        ]
    )
    ws.append(
        [
            "350J621",
            "MULTIPLES",
            "LADIES",
            "QUARTZ",
            "SILVER",
            "MECH/LEATH",
            "SS/ROSE",
            "30",
            "COFFRET",
        ]
    )

    instructions = wb.create_sheet("Instructions")
    instructions["A1"] = "How to fill this template"
    instructions["A3"] = "REFERENCE — unique product code (required)"
    instructions["A4"] = "COLLECTION — product line name (required)"
    instructions["A5"] = "GENDER — LADIES, GENTS, or UNISEX (required)"
    instructions["A6"] = "MOUVEMENT — QUARTZ, AUTOMATIC, or MECHANICAL (required)"
    instructions["A7"] = "DIAL — dial description (optional)"
    instructions["A8"] = "BRACELET — bracelet type; use / for combos e.g. MECH/LEATH (optional)"
    instructions["A9"] = "COLOR — color code e.g. SS, RG, PG (optional)"
    instructions["A10"] = "CASE SZE — case size, can be a range like 21x28.4 (optional)"
    instructions["A11"] = "KIND — WATCH or COFFRET (required)"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path


def generate_monthly_report_template(output_path: Path) -> Path:
    """
    Monthly sales & stock template — POS wide format (January style).
    One shop block with Sales + Cls Stock columns.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Per POS"

    ws["A1"] = "Pierre Lannier"
    ws["B1"] = "1113 - Kingdom Mall - Riyadh - AlHomaidhi"
    ws["D1"] = "1122 - Garnata Center - Riyadh - AlHomaidhi"

    ws["A2"] = "Item Code"
    ws["B2"] = "Sales"
    ws["C2"] = "Cls Stock"
    ws["D2"] = "Sales"
    ws["E2"] = "Cls Stock"

    ws["A3"] = "002H621"
    ws["B3"] = 0
    ws["C3"] = 1
    ws["D3"] = 2
    ws["E3"] = 0

    instructions = wb.create_sheet("Instructions")
    instructions["A1"] = "Monthly Sales & Stock Report Template"
    instructions["A3"] = "Row 1: shop headers — format: SHOP_ID - Mall Name - City - Distributor"
    instructions["A4"] = "Row 2: alternating Sales and Cls Stock under each shop"
    instructions["A5"] = "Row 3+: one product reference per row with quantities"
    instructions["A6"] = "Add more shop columns by repeating Sales / Cls Stock pairs"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path


def generate_manual_entry_template(output_path: Path, max_rows: int = 10) -> Path:
    """Small bulk-entry template — up to 10 products at once."""
    df = pd.DataFrame(columns=PRODUCT_TEMPLATE_COLUMNS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False, sheet_name="Bulk Entry")
    return output_path


def ensure_all_templates(templates_dir: Path) -> dict[str, Path]:
    """Generate all templates if they do not exist yet."""
    templates_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "product_catalog": generate_product_template(templates_dir / "product_catalog_template.xlsx"),
        "monthly_report": generate_monthly_report_template(
            templates_dir / "monthly_sales_stock_template.xlsx"
        ),
        "bulk_entry": generate_manual_entry_template(templates_dir / "bulk_entry_template.xlsx"),
    }
    return paths
