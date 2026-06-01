"""
app.py
------
Flask web application — local server for non-technical employees.

Pages:
  /                  Home
  /templates         Download Excel templates
  /upload            Upload filled Excel files
  /add-product       Enter 1–10 products manually
  /analytics         Filters + visualizations
  /abbreviations     View / add abbreviation mappings
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from src.analytics import charts, queries
from src.cleaning.abbreviation_resolver import AbbreviationResolver
from src.cleaning.pipeline import (
    run_manual_products,
    run_monthly_report_upload,
    run_product_upload,
)
from src.db.connection import get_connection, test_connection
from src.db import repository as repo
from src.models.abbreviation import Abbreviation
from src.models.product import Product
from src.templates_excel.generator import ensure_all_templates

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = PROJECT_ROOT / "excel_templates"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
MAX_MANUAL_ROWS = 10

app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "templates"),
    static_folder=str(PROJECT_ROOT / "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


def _conn():
    return get_connection()


@app.before_request
def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(exist_ok=True)
    ensure_all_templates(TEMPLATES_DIR)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/templates")
def templates_page():
    paths = ensure_all_templates(TEMPLATES_DIR)
    return render_template(
        "templates_page.html",
        templates=[
            {"key": "product_catalog", "label": "Product Catalog", "file": paths["product_catalog"].name},
            {"key": "monthly_report", "label": "Monthly Sales & Stock Report", "file": paths["monthly_report"].name},
            {"key": "bulk_entry", "label": "Bulk Entry (up to 10 products)", "file": paths["bulk_entry"].name},
        ],
    )


@app.route("/upload")
def upload_page():
    return render_template("upload.html")


@app.route("/add-product")
def add_product_page():
    return render_template(
        "add_product.html",
        genders=["LADIES", "GENTS", "UNISEX"],
        movements=["QUARTZ", "AUTOMATIC", "MECHANICAL"],
        kinds=["WATCH", "COFFRET"],
        max_rows=MAX_MANUAL_ROWS,
    )


@app.route("/analytics")
def analytics_page():
    return render_template(
        "analytics.html",
        chart_types=[
            {"id": "top_sellout_references", "label": "Top Sellout References", "type": "bar"},
            {"id": "top_pos", "label": "Top POS in KSA", "type": "bar"},
            {"id": "sellout_by_city", "label": "Total Sellout by City", "type": "bar"},
            *[{"id": f"attr_{a}", "label": f"{a.replace('_', ' ').title()} Analysis", "type": "bar"} for a in queries.ATTRIBUTE_CHARTS],
            # Pie charts for key attributes
            {"id": "pie_gender", "label": "Sales by Gender (Pie)", "type": "pie"},
            {"id": "pie_kind", "label": "Sales by Kind (Pie)", "type": "pie"},
            {"id": "pie_movement", "label": "Sales by Movement (Pie)", "type": "pie"},
        ],
    )


@app.route("/abbreviations")
def abbreviations_page():
    return render_template("abbreviations.html")


# ---------------------------------------------------------------------------
# Template downloads
# ---------------------------------------------------------------------------

@app.route("/download/<template_key>")
def download_template(template_key: str):
    paths = ensure_all_templates(TEMPLATES_DIR)
    mapping = {
        "product_catalog": paths["product_catalog"],
        "monthly_report": paths["monthly_report"],
        "bulk_entry": paths["bulk_entry"],
    }
    path = mapping.get(template_key)
    if path is None:
        return jsonify({"error": "Unknown template"}), 404
    return send_file(path, as_attachment=True)


# ---------------------------------------------------------------------------
# Upload API
# ---------------------------------------------------------------------------

@app.route("/api/upload/products", methods=["POST"])
def api_upload_products():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    save_path = UPLOAD_DIR / secure_filename(file.filename)
    file.save(save_path)

    try:
        conn = _conn()
        result = run_product_upload(conn, save_path)
        conn.close()
        return jsonify({"success": True, **result})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/upload/monthly-report", methods=["POST"])
def api_upload_monthly_report():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    save_path = UPLOAD_DIR / secure_filename(file.filename or "report.xlsx")
    file.save(save_path)

    try:
        conn = _conn()
        result = run_monthly_report_upload(conn, save_path)
        conn.close()
        return jsonify({"success": True, **result})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/products/manual", methods=["POST"])
def api_manual_products():
    payload = request.get_json(silent=True) or {}
    rows = payload.get("products", [])
    if not rows:
        return jsonify({"error": "No products provided"}), 400
    if len(rows) > MAX_MANUAL_ROWS:
        return jsonify({"error": f"Maximum {MAX_MANUAL_ROWS} products at once"}), 400

    try:
        conn = _conn()
        result = run_manual_products(conn, rows)
        conn.close()
        return jsonify({"success": True, **result})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Abbreviations API
# ---------------------------------------------------------------------------

@app.route("/api/abbreviations", methods=["GET"])
def api_list_abbreviations():
    try:
        conn = _conn()
        data = repo.get_all_abbreviations(conn)
        conn.close()
        return jsonify(data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/abbreviations", methods=["POST"])
def api_add_abbreviation():
    payload = request.get_json(silent=True) or {}
    action = payload.get("action", "add")

    if action == "ignore":
        return jsonify({"success": True, "action": "ignored"})

    abbrev = Abbreviation(
        abbreviation=payload.get("abbreviation", ""),
        full_term=payload.get("full_term", ""),
        field_category=payload.get("field_category", "general"),
    )

    try:
        conn = _conn()
        status = repo.add_abbreviation(conn, abbrev)
        conn.close()
        return jsonify({"success": True, "status": status})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/abbreviations/full-terms/<category>")
def api_full_terms(category: str):
    try:
        conn = _conn()
        terms = repo.get_existing_full_terms(conn, category)
        conn.close()
        return jsonify(terms)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Analytics API
# ---------------------------------------------------------------------------

@app.route("/api/filters")
def api_filters():
    try:
        conn = _conn()
        options = repo.get_filter_options(conn)
        conn.close()
        return jsonify(options)
    except Exception as exc:
        return jsonify({"error": str(exc), "shops": [], "sale_months": []}), 500


@app.route("/api/analytics/<chart_id>")
def api_analytics(chart_id: str):
    filters = {
        "shop_id": request.args.get("shop_id") or None,
        "city": request.args.get("city") or None,
        "kind": request.args.get("kind") or None,
        "collection": request.args.get("collection") or None,
        "month_from": request.args.get("month_from") or None,
        "month_to": request.args.get("month_to") or None,
    }
    
    # Get top_items filter (for pie charts) - default to None (show all)
    top_items_str = request.args.get("top_items")
    top_items = int(top_items_str) if top_items_str and top_items_str.isdigit() else None

    try:
        conn = _conn()

        # Handle pie chart requests
        if chart_id.startswith("pie_"):
            attribute = chart_id.replace("pie_", "")
            rows = queries.attribute_breakdown(conn, attribute, **filters)
            title = f"Sales by {attribute.replace('_', ' ').title()}"
            chart_json = charts.pie_chart_from_rows(title, rows, "label", "total_sold", max_items=top_items)
        
        # Handle bar chart attribute breakdowns
        elif chart_id.startswith("attr_"):
            attribute = chart_id.replace("attr_", "")
            rows = queries.attribute_breakdown(conn, attribute, **filters)
            title = f"{attribute.replace('_', ' ').title()} Analysis"
            chart_json = charts.chart_from_rows(title, rows, "label", "total_sold")
        
        # Handle standard bar charts
        elif chart_id in queries.CHART_HANDLERS:
            handler = queries.CHART_HANDLERS[chart_id]
            rows = handler(conn, **filters)
            label_map = {
                "top_sellout_references": ("item_code", "grand_total", "Top Sellout References"),
                "top_pos": ("store_name", "total_sold", "Top POS in KSA"),
                "sellout_by_city": ("region", "total_sold", "Total Sellout by City"),
            }
            lk, vk, title = label_map[chart_id]
            chart_json = charts.chart_from_rows(title, rows, lk, vk)
        else:
            conn.close()
            return jsonify({"error": "Unknown chart"}), 404

        conn.close()
        return jsonify({"chart": chart_json, "rows": rows, "top_items": top_items})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/health")
def api_health():
    ok = test_connection()
    return jsonify({"database": ok})


# ---------------------------------------------------------------------------
# Database Management (for testing/development)
# ---------------------------------------------------------------------------

@app.route("/api/admin/reset-all-data", methods=["POST"])
def api_reset_all_data():
    """
    WARNING: This endpoint clears ALL data from the database.
    Only available for testing/development purposes.
    """
    try:
        conn = _conn()
        result = repo.truncate_all_data(conn)
        conn.close()
        return jsonify(result)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/admin/reset-sales-data", methods=["POST"])
def api_reset_sales_data():
    """
    Clear only sales data (sold_elements and inventory_snapshots).
    Keeps products and shops intact. Useful for testing different sales scenarios.
    """
    try:
        conn = _conn()
        result = repo.truncate_sales_data(conn)
        conn.close()
        return jsonify(result)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/admin/populate-mock-data", methods=["POST"])
def api_populate_mock_data():
    """
    Populate the database with realistic mock data for testing.
    """
    try:
        from mock_data.generate_mock_data import populate_mock_data
        conn = _conn()
        # Get optional parameters from request
        payload = request.get_json(silent=True) or {}
        num_products = payload.get("num_products", 50)
        sales_per_month = payload.get("sales_per_month", 200)
        
        result = populate_mock_data(conn, num_products=num_products, sales_per_month=sales_per_month)
        conn.close()
        return jsonify(result)
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


def create_app() -> Flask:
    return app


if __name__ == "__main__":
    ensure_all_templates(TEMPLATES_DIR)
    app.run(debug=True, host="127.0.0.1", port=5000)
