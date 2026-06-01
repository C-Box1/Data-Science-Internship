"""
db/repository.py
-----------------
All database operations live here — inserting and querying.

What this file does in plain English:
    - Takes cleaned Product and Shop objects and inserts them into PostgreSQL
    - Handles the duplicate logic: skip exact duplicates, flag conflicts
    - Inserts monthly sales records and inventory snapshots
    - Every function receives a connection (opened by connection.py)

Why it exists as a separate file:
    Keeps all SQL in one place. If a table changes, you update one function here.
    The rest of the code (cleaning, parsing) never needs to know SQL exists.

Key concept — cursor:
    A cursor is like a pen you use to write SQL through the connection.
    You open a cursor, write your SQL, the database executes it, you read results.
    You close the cursor when done. One connection can have many cursors.
"""

import logging
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import execute_values   # efficient bulk inserts

from src.models.product import Product
from src.models.shop import Shop
from src.models.abbreviation import Abbreviation

logger = logging.getLogger(__name__)


# =============================================================================
# PRODUCTS
# =============================================================================

def upsert_product(conn: PgConnection, product: Product) -> str:
    """
    Insert a product into products_information.

    What 'upsert' means:
        - If the reference does NOT exist → INSERT (new record)
        - If the reference already exists with the SAME values → skip silently
        - If the reference exists with DIFFERENT values → log a conflict warning
          (we do not overwrite automatically — a human must resolve this)

    Returns one of: 'inserted', 'skipped', 'conflict'
    """
    with conn.cursor() as cur:

        # First check if a product with this reference already exists
        cur.execute(
            "SELECT kind, collection, gender, movement, dial, bracelet, color, case_size "
            "FROM products_information WHERE reference = %s",
            (product.reference,)
        )
        existing = cur.fetchone()   # returns a tuple if found, None if not found

        if existing is None:
            # No existing record — safe to insert
            cur.execute(
                """
                INSERT INTO products_information
                    (reference, kind, collection, gender, movement,
                     dial, bracelet, color, case_size,
                     date_of_creation, date_of_reception)
                VALUES
                    (%(reference)s, %(kind)s, %(collection)s, %(gender)s, %(movement)s,
                     %(dial)s, %(bracelet)s, %(color)s, %(case_size)s,
                     %(date_of_creation)s, %(date_of_reception)s)
                """,
                product.to_db_dict()
                # product.to_db_dict() returns a plain dict like:
                # {"reference": "002H621", "kind": "WATCH", "collection": "GALIERA", ...}
                # The %(key)s placeholders match the dict keys safely (prevents SQL injection)
            )
            conn.commit()   # commit = save the change permanently to the database
            logger.debug(f"Inserted product: {product.reference}")
            return "inserted"

        else:
            # A record exists — check if it is an exact match
            existing_values = list(existing)
            incoming_values = [
                product.kind, product.collection, product.gender, product.movement,
                product.dial, product.strap, product.color, product.case_size
            ]

            if existing_values == incoming_values:
                # Exact duplicate — silently skip
                logger.debug(f"Skipped exact duplicate: {product.reference}")
                return "skipped"
            else:
                # Partial conflict — log it for human review
                logger.warning(
                    f"CONFLICT for reference {product.reference}:\n"
                    f"  EXISTING: {existing_values}\n"
                    f"  INCOMING: {incoming_values}"
                )
                return "conflict"


def bulk_insert_products(conn: PgConnection, products: list[Product]) -> dict:
    """
    Insert a list of products one by one, collecting a summary.

    Returns a dict like:
        {"inserted": 450, "skipped": 40, "conflict": 10}
    """
    summary = {"inserted": 0, "skipped": 0, "conflict": 0}

    for product in products:
        result = upsert_product(conn, product)
        summary[result] += 1   # increment the correct counter

    logger.info(
        f"Products summary — "
        f"inserted: {summary['inserted']}, "
        f"skipped: {summary['skipped']}, "
        f"conflicts: {summary['conflict']}"
    )
    return summary


# =============================================================================
# SHOPS
# =============================================================================

def upsert_shop(conn: PgConnection, shop: Shop) -> str:
    """
    Insert a shop into market_information.
    Same logic as upsert_product — skip exact duplicates, warn on conflicts.

    Returns: 'inserted', 'skipped', or 'conflict'
    """
    with conn.cursor() as cur:

        cur.execute(
            "SELECT mall_name, city, country, distributor, shop_type "
            "FROM market_information WHERE shop_id = %s",
            (shop.shop_id,)
        )
        existing = cur.fetchone()

        if existing is None:
            cur.execute(
                """
                INSERT INTO market_information
                    (shop_id, mall_name, city, country, distributor, shop_type)
                VALUES
                    (%(shop_id)s, %(mall_name)s, %(city)s,
                     %(country)s, %(distributor)s, %(shop_type)s)
                """,
                shop.to_db_dict()
            )
            conn.commit()
            logger.debug(f"Inserted shop: {shop.shop_id} — {shop.mall_name}")
            return "inserted"

        else:
            existing_values = list(existing)
            incoming_values = [
                shop.mall_name, shop.city, shop.country,
                shop.distributor, shop.shop_type
            ]

            if existing_values == incoming_values:
                logger.debug(f"Skipped exact duplicate shop: {shop.shop_id}")
                return "skipped"
            else:
                logger.warning(
                    f"CONFLICT for shop {shop.shop_id}:\n"
                    f"  EXISTING: {existing_values}\n"
                    f"  INCOMING: {incoming_values}"
                )
                return "conflict"


def bulk_insert_shops(conn: PgConnection, shops: list[Shop]) -> dict:
    """Insert a list of Shop objects. Returns a summary dict."""
    summary = {"inserted": 0, "skipped": 0, "conflict": 0}
    for shop in shops:
        result = upsert_shop(conn, shop)
        summary[result] += 1
    logger.info(
        f"Shops summary — "
        f"inserted: {summary['inserted']}, "
        f"skipped: {summary['skipped']}, "
        f"conflicts: {summary['conflict']}"
    )
    return summary


# =============================================================================
# PRESENT ELEMENTS (inventory snapshots)
# =============================================================================

def upsert_present_element(conn: PgConnection, item_reference: str, shop_id: str, report_month: str, closing_stock: int,
) -> str:
    """
    Insert or update a monthly inventory snapshot.

    The UNIQUE constraint on (item_reference, shop_id, report_month)
    means we use ON CONFLICT DO UPDATE — if the row already exists,
    update the closing_stock value instead of inserting a duplicate.

    This handles the case where you re-import the same monthly report —
    instead of crashing, it just updates the numbers.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO present_elements
                (item_reference, shop_id, report_month, closing_stock)
            VALUES
                (%s, %s, %s, %s)
            ON CONFLICT (item_reference, shop_id, report_month)
                DO UPDATE SET closing_stock = EXCLUDED.closing_stock
            """,
            # %s placeholders — psycopg2 fills them in order from the tuple
            (item_reference, shop_id, report_month, closing_stock)
        )
    conn.commit()
    return "upserted"


def bulk_insert_present_elements(
    conn: PgConnection, records: list[dict]
) -> int:
    """
    Efficiently insert many inventory snapshot records at once.

    Each dict in records must have:
        item_reference, shop_id, report_month, closing_stock

    Uses execute_values for bulk performance — much faster than one INSERT at a time.
    Returns the number of rows processed.
    """
    if not records:
        return 0

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO present_elements
                (item_reference, shop_id, report_month, closing_stock)
            VALUES %s
            ON CONFLICT (item_reference, shop_id, report_month)
                DO UPDATE SET closing_stock = EXCLUDED.closing_stock
            """,
            # execute_values expects a list of tuples
            [
                (r["item_reference"], r["shop_id"], r["report_month"], r["closing_stock"])
                for r in records
            ]
        )
    conn.commit()
    logger.info(f"Inserted/updated {len(records)} inventory snapshots")
    return len(records)


# =============================================================================
# SOLD ELEMENTS (monthly sales records)
# =============================================================================

def bulk_insert_sold_elements(
    conn: PgConnection, records: list[dict]
) -> int:
    """
    Efficiently insert many monthly sales records at once.

    Each dict in records must have:
        item_reference, shop_id, sale_month, quantity_sold, sale_source

    ON CONFLICT updates quantity_sold if the same record is re-imported.
    Returns the number of rows processed.
    """
    if not records:
        return 0

    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO sold_elements
                (item_reference, shop_id, sale_month, quantity_sold, sale_source)
            VALUES %s
            ON CONFLICT (item_reference, shop_id, sale_month)
                DO UPDATE SET
                    quantity_sold = EXCLUDED.quantity_sold,
                    sale_source   = EXCLUDED.sale_source
            """,
            [
                (
                    r["item_reference"],
                    r["shop_id"],
                    r["sale_month"],
                    r["quantity_sold"],
                    r.get("sale_source", "monthly_report"),
                )
                for r in records
            ]
        )
    conn.commit()
    logger.info(f"Inserted/updated {len(records)} sales records")
    return len(records)


# =============================================================================
# UTILITY — check what references exist in the DB
# =============================================================================

def get_all_references(conn: PgConnection) -> set[str]:
    """
    Return the set of all product references currently in the database.
    Used by the report parser to skip sales rows for unknown references
    instead of crashing with a foreign key error.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT reference FROM products_information")
        rows = cur.fetchall()   # returns list of tuples like [("002H621",), ("003L542",)]
    return {row[0] for row in rows}   # convert to a flat set of strings


def get_all_shop_ids(conn: PgConnection) -> set[str]:
    """Return the set of all shop IDs currently in the database."""
    with conn.cursor() as cur:
        cur.execute("SELECT shop_id FROM market_information")
        rows = cur.fetchall()
    return {row[0] for row in rows}


# =============================================================================
# ABBREVIATIONS
# =============================================================================

def load_abbreviation_maps(conn: PgConnection) -> dict[str, dict[str, str]]:
    """
    Load all abbreviations grouped by field_category.
    Keys are uppercased for case-insensitive lookup.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT abbreviation, full_term, field_category FROM abbreviations"
        )
        rows = cur.fetchall()

    maps: dict[str, dict[str, str]] = {}
    for abbrev, full_term, category in rows:
        maps.setdefault(category, {})[abbrev.upper()] = full_term.upper()
    return maps


def get_all_abbreviations(conn: PgConnection) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT abbrev_id, abbreviation, full_term, field_category
            FROM abbreviations
            ORDER BY field_category, abbreviation
            """
        )
        rows = cur.fetchall()
    return [
        {
            "abbrev_id": r[0],
            "abbreviation": r[1],
            "full_term": r[2],
            "field_category": r[3],
        }
        for r in rows
    ]


def add_abbreviation(conn: PgConnection, abbrev: Abbreviation) -> str:
    """Insert a new abbreviation. Returns 'inserted' or 'exists'."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT abbrev_id FROM abbreviations
            WHERE UPPER(abbreviation) = UPPER(%s) AND field_category = %s
            """,
            (abbrev.abbreviation, abbrev.field_category),
        )
        if cur.fetchone():
            return "exists"

        cur.execute(
            """
            INSERT INTO abbreviations (abbreviation, full_term, field_category)
            VALUES (%(abbreviation)s, %(full_term)s, %(field_category)s)
            """,
            abbrev.to_db_dict(),
        )
    conn.commit()
    return "inserted"


def get_existing_full_terms(conn: PgConnection, field_category: str) -> list[str]:
    """Return distinct full terms for a category (for linking new abbreviations)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT full_term FROM abbreviations
            WHERE field_category = %s
            ORDER BY full_term
            """,
            (field_category,),
        )
        rows = cur.fetchall()
    return [r[0] for r in rows]


# =============================================================================
# FILTER OPTIONS — only values that exist in uploaded data
# =============================================================================

def get_filter_options(conn: PgConnection) -> dict:
    """
    Return filter dropdown values derived only from data already in the DB.
    Prevents filtering by shops/months that do not exist yet.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT shop_id, mall_name, city, country
            FROM market_information
            ORDER BY shop_id
            """
        )
        shops = [
            {"shop_id": r[0], "mall_name": r[1], "city": r[2], "country": r[3]}
            for r in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT DISTINCT sale_month FROM sold_elements
            ORDER BY sale_month
            """
        )
        sale_months = [r[0].isoformat() for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT kind FROM products_information ORDER BY kind")
        kinds = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT collection FROM products_information ORDER BY collection")
        collections = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT DISTINCT city FROM market_information WHERE city IS NOT NULL ORDER BY city")
        cities = [r[0] for r in cur.fetchall()]

    return {
        "shops": shops,
        "sale_months": sale_months,
        "kinds": kinds,
        "collections": collections,
        "cities": cities,
    }


# =============================================================================
# DATABASE RESET — for testing and development
# =============================================================================

def truncate_all_data(conn: PgConnection) -> dict:
    """
    Clear all data from the database (for testing/development).
    Keeps the schema intact — only data is removed.
    
    WARNING: This operation cannot be undone!
    
    Returns:
        Dictionary with summary of truncated tables
    """
    tables_to_truncate = [
        "sold_elements",
        "inventory_snapshots",
        "products_information",
        "market_information",
        # Note: abbreviations are typically kept (they are reference data)
    ]
    
    try:
        with conn.cursor() as cur:
            for table in tables_to_truncate:
                cur.execute(f"TRUNCATE TABLE {table} CASCADE")
                logger.info(f"Truncated table: {table}")
            conn.commit()
        
        result = {
            "success": True,
            "tables_truncated": tables_to_truncate,
            "message": f"Successfully truncated {len(tables_to_truncate)} tables"
        }
        logger.info(result["message"])
        return result
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error truncating tables: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to truncate database"
        }


def truncate_sales_data(conn: PgConnection) -> dict:
    """
    Clear only sales data (sold_elements and inventory_snapshots).
    Keeps products and shops intact.
    Useful for testing different time periods of sales data.
    
    Returns:
        Dictionary with summary of truncated tables
    """
    tables_to_truncate = [
        "sold_elements",
        "inventory_snapshots",
    ]
    
    try:
        with conn.cursor() as cur:
            for table in tables_to_truncate:
                cur.execute(f"TRUNCATE TABLE {table} CASCADE")
                logger.info(f"Truncated table: {table}")
            conn.commit()
        
        result = {
            "success": True,
            "tables_truncated": tables_to_truncate,
            "message": f"Successfully truncated {len(tables_to_truncate)} sales tables"
        }
        logger.info(result["message"])
        return result
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error truncating sales tables: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to truncate sales data"
        }