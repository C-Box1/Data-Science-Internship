# Mock Data for Testing

This directory contains tools and data for testing visualizations and reports without using real production data.

## Files

- **generate_mock_data.py** — Python script to populate the database with realistic sample products and sales data

## Quick Start

### Populate the database with mock data:

```bash
python mock_data/generate_mock_data.py
```

This creates:
- 50 products (25 watches + 25 matching coffrets)
- 6 months of historical sales data
- 7 sample shops/malls

### From Python code:

```python
from mock_data.generate_mock_data import populate_mock_data
from src.db.connection import get_connection

conn = get_connection()
result = populate_mock_data(conn, num_products=50, sales_per_month=200)
print(result['message'])
conn.close()
```

## Sample Data Details

### Products
- Collections: GALIERA, MULTIPLES, TRADITION, ELEGANCE, SPORT, VINTAGE
- Kinds: WATCH and COFFRET (gift sets with watch + box)
- Genders: LADIES, GENTS, UNISEX
- Movements: QUARTZ, AUTOMATIC, MECHANICAL
- Straps: LEATHER STRAP, MESH, BRACELET, JEWELLERY STRAP
  - For Coffrets, straps are combos (e.g., "LEATHER STRAP/MESH")
- Colors: YELLOW GOLD, ROSE GOLD, PINK GOLD, STAINLESS STEEL, BLACK, WHITE, SILVER

### Shops
Mock shops are distributed across Saudi Arabia:
- Kingdom Mall, Riyadh
- Red Sea Mall, Jeddah
- Centrepoint, Riyadh
- Panorama Mall, Dammam
- Nakheel Mall, Riyadh
- Marina Mall, Riyadh
- Main Store (warehouse), Riyadh

### Sales Data
- 6 months of historical sales (latest month back to 6 months ago)
- ~200 sales records per month (randomly distributed across products and shops)
- Quantities: 1–15 units per sale

## Use Cases

### Testing Visualizations
After running `populate_mock_data()`, visit the Analytics page to see:
- Top Sellout References
- Top POS (Point of Sale) in KSA
- Sales by City
- Attribute breakdowns (Gender, Kind, Movement, Color, Strap, etc.)
- Pie charts with filtering by top N items

### Testing Filters
Try different filter combinations:
- By Kind (WATCH vs COFFRET)
- By Collection
- By Gender
- By Time range (sales months)
- By Specific Shop

### Visualization Development
Use the mock data to:
- Test new chart types
- Develop filtering features
- Test data transformations
- Verify performance with larger datasets

## Resetting the Database

To clear all data and start fresh:

```python
from src.db.connection import get_connection
from src.db.repository import truncate_all_data

conn = get_connection()
truncate_all_data(conn)
conn.close()
```

Then repopulate with mock data:

```python
from mock_data.generate_mock_data import populate_mock_data
populate_mock_data(conn)
```

## Tips

- **More realism**: Increase sales_per_month to 500+ for larger datasets
- **Different time ranges**: Edit SAMPLE_SHOPS to match your actual store list
- **Custom products**: Modify SAMPLE_COLLECTIONS, SAMPLE_MOVEMENTS, etc. in generate_mock_data.py
- **Consistent data**: The script uses random.seed() internally for reproducibility (if needed)

## Notes

- Mock data is completely separate from production data
- All mock product references start with `REF` to distinguish them
- Running multiple times will skip duplicate products (they exist check)
- Mock sales data is always new (no duplicates check for sales)
