"""
Mock data generator for testing visualizations and reports.

This script creates realistic sample data with generic/simplified naming:
- Products (watches and coffrets)
- Shops/Malls (generic: Mall 1, Mall 2, etc.)
- Monthly sales records

A COFFRET consists of TWO product SKUs:
  1. One COFFRET product (the gift set/box)
  2. One matching WATCH product (the watch inside the box)

Run this to populate the database with test data for visualization testing.

Usage:
    python mock_data/generate_mock_data.py
    or from Python:
    from mock_data.generate_mock_data import populate_mock_data
    populate_mock_data(conn)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.product import Watch, Coffret
from src.models.shop import Shop
from src.db import repository as repo
from src.db.connection import get_connection

# Sample data for creating mock products - GENERIC DATA
SAMPLE_COLLECTIONS = ["Collection 1", "Collection 2", "Collection 3", "Collection 4", "Collection 5"]
SAMPLE_GENDERS = ["LADIES", "GENTS", "UNISEX"]
SAMPLE_MOVEMENTS = ["QUARTZ", "AUTOMATIC", "MECHANICAL"]
SAMPLE_STRAPS = ["Strap Type A", "Strap Type B", "Strap Type C", "Strap Type D"]
SAMPLE_COLORS = ["Color 1", "Color 2", "Color 3", "Color 4", "Color 5", "Color 6"]
SAMPLE_DIALS = ["Dial Type 1", "Dial Type 2", "Dial Type 3", "Dial Type 4"]
SAMPLE_CASE_SIZES = ["28", "30", "32", "34", "36", "38", "40", "42"]

# Generic shop/mall names
SAMPLE_SHOPS = [
    ("1001", "Mall 1", "City 1", "retail", "Country A", "Distributor X"),
    ("1002", "Mall 2", "City 2", "retail", "Country A", "Distributor Y"),
    ("1003", "Mall 3", "City 1", "retail", "Country A", "Distributor X"),
    ("1004", "Mall 4", "City 3", "retail", "Country A", "Distributor Z"),
    ("1005", "Mall 5", "City 2", "retail", "Country A", "Distributor Y"),
    ("1006", "Mall 6", "City 1", "retail", "Country A", "Distributor X"),
    ("0001", "Main Store", "City 1", "warehouse", "Country A", "Distributor X"),
]

# Base reference numbers
REFERENCE_BASE_WATCH = 500000
REFERENCE_BASE_COFFRET = 600000

def generate_mock_products(count: int = 10) -> list:
    """
    Generate mock product objects.
    
    For each product pair:
    - Create 1 WATCH product
    - Create 1 matching COFFRET product (gift set)
    
    A COFFRET consists of: the coffret itself + the watch
    They are two separate SKUs but represent one gift set offering.
    
    Args:
        count: Number of product PAIRS to create (so 2*count total products)
        
    Returns:
        List of Watch and Coffret objects
    """
    products = []
    
    for i in range(count):
        # Shared product attributes
        collection = random.choice(SAMPLE_COLLECTIONS)
        gender = random.choice(SAMPLE_GENDERS)
        movement = random.choice(SAMPLE_MOVEMENTS)
        dial = random.choice(SAMPLE_DIALS)
        color = random.choice(SAMPLE_COLORS)
        case_size = random.choice(SAMPLE_CASE_SIZES)
        
        # ===== CREATE WATCH =====
        watch_ref = f"WATCH{REFERENCE_BASE_WATCH + i:06d}"
        strap_watch = random.choice(SAMPLE_STRAPS)
        
        watch = Watch(
            reference=watch_ref,
            kind="WATCH",
            collection=collection,
            gender=gender,
            movement=movement,
            dial=dial,
            strap=strap_watch,
            color=color,
            case_size=case_size,
            date_of_creation=datetime.now().date(),
            date_of_reception=datetime.now().date(),
        )
        products.append(watch)
        
        # ===== CREATE MATCHING COFFRET =====
        # A COFFRET is a gift set containing:
        # 1. The coffret itself (presentation box)
        # 2. One watch (often with multiple strap options)
        
        coffret_ref = f"COFFRET{REFERENCE_BASE_COFFRET + i:06d}"
        # Coffret typically comes with multiple strap options
        strap_combo = f"{strap_watch}/{random.choice(SAMPLE_STRAPS)}"
        
        coffret = Coffret(
            reference=coffret_ref,
            kind="COFFRET",
            collection=collection,
            gender=gender,
            movement=movement,
            dial=dial,
            strap=strap_combo,  # Multiple straps in the gift set
            color=color,
            case_size=case_size,
            date_of_creation=datetime.now().date(),
            date_of_reception=datetime.now().date(),
        )
        products.append(coffret)
    
    return products

def generate_mock_sales(conn, products: list, num_months: int = 6, sales_per_month: int = 200):
    """Generate mock sales records."""
    from src.models.shop import Shop as ShopModel
    
    # Insert shops first
    shops_data = []
    for shop_id, mall_name, city, shop_type, country, distributor in SAMPLE_SHOPS:
        shop = ShopModel(
            shop_id=shop_id,
            mall_name=mall_name,
            city=city,
            shop_type=shop_type,
            country=country,
            distributor=distributor,
        )
        repo.upsert_shop(conn, shop)
        shops_data.append((shop_id, mall_name, city, shop_type, country, distributor))
    
    # Generate sales months (last 6 months)
    end_date = datetime.now()
    sales_months = []
    for i in range(num_months):
        month_date = end_date - timedelta(days=30 * i)
        month_str = month_date.strftime("%Y-%m-%d")
        sales_months.append(month_str)
    
    sales_months.reverse()
    
    # Generate sales records
    for month in sales_months:
        for _ in range(sales_per_month):
            product = random.choice(products)
            shop_id, _, _, _, _, _ = random.choice(shops_data)
            quantity = random.randint(1, 15)
            
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sold_elements (shop_id, item_reference, quantity_sold, sale_month)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (shop_id, product.reference, quantity, month)
                )
            conn.commit()

def populate_mock_data(conn=None, num_product_pairs: int = 10, sales_per_month: int = 200) -> dict:
    """
    Main function to populate mock data.
    
    Args:
        conn: Database connection (created if None)
        num_product_pairs: Number of product PAIRS to create 
                          (each pair = 1 watch + 1 coffret = 2 total products)
        sales_per_month: Number of sales records per month
    
    Returns:
        Dictionary with summary of inserted data
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    try:
        print(f"Generating {num_product_pairs} product pairs (watch + coffret)...")
        products = generate_mock_products(count=num_product_pairs)
        total_products = len(products)  # 2x num_product_pairs (watch + coffret per pair)
        
        print(f"Inserting {total_products} products into database ({num_product_pairs} watches + {num_product_pairs} coffrets)...")
        inserted_count = 0
        for product in products:
            status = repo.upsert_product(conn, product)
            if status == "inserted":
                inserted_count += 1
        
        print(f"Inserted {inserted_count} new products")
        
        print("Generating and inserting mock sales data...")
        generate_mock_sales(conn, products, num_months=6, sales_per_month=sales_per_month)
        
        result = {
            "success": True,
            "products_inserted": inserted_count,
            "products_total": total_products,
            "product_pairs": num_product_pairs,
            "sales_generated": 6 * sales_per_month,
            "message": f"Successfully populated mock data: {inserted_count} products ({num_product_pairs} watches + {num_product_pairs} coffrets), {6 * sales_per_month} sales records"
        }
        print(result["message"])
        return result
        
    except Exception as e:
        print(f"Error populating mock data: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if close_conn:
            conn.close()

if __name__ == "__main__":
    conn = get_connection()
    try:
        # Generate 30 product pairs = 60 total products (30 watches + 30 coffrets)
        result = populate_mock_data(conn, num_product_pairs=5, sales_per_month=20)
        print(f"\n✓ {result['message']}" if result['success'] else f"\n✗ Error: {result['error']}")
    finally:
        conn.close()

