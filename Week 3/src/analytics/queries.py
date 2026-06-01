"""
analytics/queries.py
--------------------
SQL-backed analytics matching the Watchs_Analysis_November 2024.xlsx sheets.

Available visualizations (buttons on the website):
  - top_sellout_references   → Top 20 Sellout references
  - top_pos                  → Top 20 POS in KSA
  - sellout_by_city          → Total Sellout by City
  - attribute_breakdown      → Bracelet / Color / Collection / Gender / Kind /
                               Movement / Dial / Case Size analysis
  - shop_detail              → Per-shop sales breakdown
"""

from __future__ import annotations

from typing import Optional

from psycopg2.extensions import connection as PgConnection

ATTRIBUTE_FIELDS = {
    "strap": "p.bracelet",
    "color": "p.color",
    "collection": "p.collection",
    "gender": "p.gender",
    "kind": "p.kind",
    "movement": "p.movement",
    "dial": "p.dial",
    "case_size": "p.case_size",
}


def _build_filters(
    shop_id: Optional[str] = None,
    city: Optional[str] = None,
    kind: Optional[str] = None,
    collection: Optional[str] = None,
    month_from: Optional[str] = None,
    month_to: Optional[str] = None,
) -> tuple[str, list]:
    clauses: list[str] = []
    params: list = []

    if shop_id:
        clauses.append("s.shop_id = %s")
        params.append(shop_id)
    if city:
        clauses.append("m.city = %s")
        params.append(city)
    if kind:
        clauses.append("p.kind = %s")
        params.append(kind)
    if collection:
        clauses.append("p.collection = %s")
        params.append(collection)
    if month_from:
        clauses.append("s.sale_month >= %s")
        params.append(month_from)
    if month_to:
        clauses.append("s.sale_month <= %s")
        params.append(month_to)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


def top_sellout_references(
    conn: PgConnection,
    limit: int = 20,
    **filters,
) -> list[dict]:
    where, params = _build_filters(**filters)
    sql = f"""
        SELECT p.reference AS item_code, SUM(s.quantity_sold) AS grand_total
        FROM sold_elements s
        JOIN products_information p ON p.reference = s.item_reference
        JOIN market_information m ON m.shop_id = s.shop_id
        {where}
        GROUP BY p.reference
        ORDER BY grand_total DESC
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, [*params, limit])
        rows = cur.fetchall()
    return [{"item_code": r[0], "grand_total": int(r[1])} for r in rows]


def top_pos(conn: PgConnection, limit: int = 20, **filters) -> list[dict]:
    where, params = _build_filters(**filters)
    sql = f"""
        SELECT m.mall_name AS store_name, SUM(s.quantity_sold) AS total_sold
        FROM sold_elements s
        JOIN market_information m ON m.shop_id = s.shop_id
        JOIN products_information p ON p.reference = s.item_reference
        {where}
        GROUP BY m.shop_id, m.mall_name
        ORDER BY total_sold DESC
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, [*params, limit])
        rows = cur.fetchall()
    return [{"store_name": r[0], "total_sold": int(r[1])} for r in rows]


def sellout_by_city(conn: PgConnection, **filters) -> list[dict]:
    where, params = _build_filters(**filters)
    sql = f"""
        SELECT m.shop_id, SUM(s.quantity_sold) AS total_sold,
               COALESCE(m.city, 'Unknown') AS region
        FROM sold_elements s
        JOIN market_information m ON m.shop_id = s.shop_id
        JOIN products_information p ON p.reference = s.item_reference
        {where}
        GROUP BY m.shop_id, m.city
        ORDER BY total_sold DESC
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [
        {"shop_id": r[0], "total_sold": int(r[1]), "region": r[2]}
        for r in rows
    ]


def attribute_breakdown(
    conn: PgConnection,
    attribute: str,
    **filters,
) -> list[dict]:
    if attribute not in ATTRIBUTE_FIELDS:
        raise ValueError(f"Unknown attribute: {attribute}")

    field = ATTRIBUTE_FIELDS[attribute]
    where, params = _build_filters(**filters)
    sql = f"""
        SELECT COALESCE({field}, 'Unknown') AS label,
               SUM(s.quantity_sold) AS total_sold
        FROM sold_elements s
        JOIN products_information p ON p.reference = s.item_reference
        JOIN market_information m ON m.shop_id = s.shop_id
        {where}
        GROUP BY label
        ORDER BY total_sold DESC
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [{"label": r[0], "total_sold": int(r[1])} for r in rows]


def shop_detail(
    conn: PgConnection,
    shop_id: str,
    **filters,
) -> list[dict]:
    where, params = _build_filters(shop_id=shop_id, **filters)
    sql = f"""
        SELECT p.reference, p.collection, p.gender, p.movement,
               p.dial, p.bracelet, p.color, p.case_size, p.kind,
               SUM(s.quantity_sold) AS total_sold
        FROM sold_elements s
        JOIN products_information p ON p.reference = s.item_reference
        JOIN market_information m ON m.shop_id = s.shop_id
        {where}
        GROUP BY p.reference, p.collection, p.gender, p.movement,
                 p.dial, p.bracelet, p.color, p.case_size, p.kind
        ORDER BY total_sold DESC
    """
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [
        {
            "reference": r[0],
            "collection": r[1],
            "gender": r[2],
            "movement": r[3],
            "dial": r[4],
            "strap": r[5],
            "color": r[6],
            "case_size": r[7],
            "kind": r[8],
            "total_sold": int(r[9]),
        }
        for r in rows
    ]


CHART_HANDLERS = {
    "top_sellout_references": top_sellout_references,
    "top_pos": top_pos,
    "sellout_by_city": sellout_by_city,
}

ATTRIBUTE_CHARTS = list(ATTRIBUTE_FIELDS.keys())
