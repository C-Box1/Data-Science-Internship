# Demo & Presentation Guide for Supervisor

**Last Updated:** June 1, 2026  
**Project:** Watch Consignment Management System

---

## Quick Start (5 minutes)

### Prerequisites
- PostgreSQL running locally
- Python 3.11+
- Project folder open

### 1. Start the Database & Web Server

Open terminal in project root and run:

```bash
# Activate virtual environment (if not already active)
source .venv/Scripts/activate

# Start the web server
uv run python -m src.main
```

**Expected output:**
```
WARNING in app.run_with_ssl: Using the development server...
Running on http://127.0.0.1:5000
```

**Open browser:** http://127.0.0.1:5000

---

## Demo Walkthrough (10-15 minutes)

### Part 1: Home Page & Navigation

**URL:** http://127.0.0.1:5000

**What to show:**
- Clean, simple interface with navigation bar
- 6 main sections: Home, Templates, Upload, Add Product, Analytics, Abbreviations

**What to say:**
> "This system is designed for non-technical employees. Everything is accessible from the top menu. No coding knowledge required."

---

### Part 2: Download Templates

**URL:** http://127.0.0.1:5000/templates

**Click:** "Product Catalog" download

**What to show:**
- Three template types available
- Product Catalog matches the original reference file format
- Monthly Sales & Stock Report matches POS format
- Bulk Entry for manual 1–10 product entry

**What to say:**
> "Employees download the correct Excel template, fill it in on their computer, then upload it here. The website handles all the data cleaning."

---

### Part 3: Populate with Mock Data

**Run this in Python terminal or in your script:**

```bash
# In a new terminal (keep server running in first terminal)
cd /path/to/project

# Activate venv
source .venv/Scripts/activate

# Run mock data generator
python mock_data/generate_mock_data.py
```

**Expected output:**
```
Generating mock products...
Inserting 50 products into database...
Inserted 50 new products
Generating and inserting mock sales data...
✓ Successfully populated mock data: 50 products, 1200 sales records
```

**What to say:**
> "I just populated the database with realistic test data — 50 products and 6 months of sales across 7 stores. This simulates real usage."

---

### Part 4: View Analytics & Charts

**URL:** http://127.0.0.1:5000/analytics

**Demo these charts in order:**

#### A. Bar Charts

1. **Click "Top Sellout References"**
   - Shows product codes ranked by total units sold
   - Highest seller first with count and percentage
   - Hover to see exact numbers
   
   **What to say:**
   > "This shows which product codes our top performers are. The bar shows both the count and percentage of total sales."

2. **Click "Top POS in KSA"**
   - Shows which stores/shops sold the most
   - Ranked by total sales volume
   
   **What to say:**
   > "This is store performance — which POS locations generated the most revenue."

3. **Try filters:**
   - Select "Kind" = "WATCH" (exclude coffrets)
   - Click "Top Sellout References" again
   - Chart updates to show only watch sales
   
   **What to say:**
   > "Filters update dynamically. Employees can analyze just watches, just gift sets, or specific collections. The filters only show data that actually exists in the database."

#### B. Pie Charts (NEW)

1. **Click "Sales by Gender (Pie)"**
   - Shows percentage distribution of sales by gender
   - Hover to see count and percentage for each slice
   - Clean, visual way to see market split
   
   **What to say:**
   > "Pie charts show percentages. This one shows what % of sales are ladies watches vs gents vs unisex. Much better for seeing overall distribution."

2. **Click "Sales by Kind (Pie)"**
   - Shows WATCH vs COFFRET (gift sets) split
   - Demonstrates the coffret concept clearly
   
   **What to say:**
   > "A COFFRET is a gift set — watch plus presentation box. This chart shows how many sales are gift sets vs regular watches."

3. **Click "Sales by Movement (Pie)"**
   - Shows mechanical vs automatic vs quartz distribution
   
   **What to say:**
   > "Mechanical movements are luxury, Quartz is common, Automatic is in between. This shows which movements our customers prefer."

#### C. Top-N Filtering for Pie Charts

**On a pie chart, look for the "Top Items" control:**

1. Default view shows all categories
2. Set "Top 5" - chart updates to show only top 5 items
3. Other categories grouped as "Other"

**What to say:**
> "With many categories, pie charts get cluttered. The 'Top N' feature lets employees focus on top sellers. For example, 'Top 5 collections' shows the 5 biggest revenue generators."

#### D. Attribute Breakdowns

**Click "Color Analysis"**
- Shows sales broken down by watch color
- STAINLESS STEEL most popular
- Ranked by total units sold

**What to say:**
> "We have 8 attribute analyses: Gender, Kind, Movement, Collection, Color, Strap, Dial, Case Size. Each shows what % of sales are that type."

---

### Part 5: Add Product Manually

**URL:** http://127.0.0.1:5000/add-product

**Fill in example:**
- Reference: `999Z001` (something obvious for demo)
- Collection: `DEMO COLLECTION`
- Gender: `LADIES`
- Movement: `QUARTZ`
- Strap: `MESH`
- Color: `PINK GOLD`
- Kind: `WATCH`
- Click "Add Product"

**What to show:**
- Form validates instantly
- Success message appears
- Can add up to 10 products at once

**What to say:**
> "Employees who don't want to use Excel can add products directly here. Maximum 10 at a time. All fields validate — if they pick an invalid option, the system tells them."

---

### Part 6: Upload Data

**URL:** http://127.0.0.1:5000/upload

**Show but don't necessarily do:**
- Product Catalog upload area
- Monthly Sales & Stock Report upload area
- File drop or browse button
- System automatically detects Excel format

**What to say:**
> "Uploads are where the real power comes in. Employees upload filled Excel files, the system cleans the data automatically, expands abbreviations, and asks about any unknown codes. Then everything goes into PostgreSQL."

---

### Part 7: Manage Abbreviations

**URL:** http://127.0.0.1:5000/abbreviations

**Show:**
- Table of existing abbreviations
- Organized by field (Color, Strap, Movement)
- Examples: BRCLT → BRACELET, PG → PINK GOLD, MECH → MESH

**What to say:**
> "Abbreviations map short codes to full terms. BRCLT becomes BRACELET, PG becomes PINK GOLD. When unknown codes appear during upload, employees link them here or create new mappings."

---

## Key Features to Emphasize (Talking Points)

### 1. Watch vs Coffret Distinction
> "A watch is a single watch. A COFFRET is a gift set — watch PLUS presentation box PLUS often multiple strap types. The system now correctly tracks this — a coffret's 'strap' field can list multiple straps (e.g., 'MESH/LEATHER STRAP')."

### 2. Pie Charts for Percentage Analysis
> "New pie charts give a visual percentage breakdown. Employees see at a glance what % of sales are each category. Top-N filtering prevents cluttered charts — they choose Top 5, Top 10, or see all."

### 3. Live Database
> "All charts are live from PostgreSQL. Upload new data = charts update instantly. No manual Excel refreshing. Employees see real-time sales performance."

### 4. Smart Abbreviations
> "The system learns. Unknown abbreviations trigger a question during upload. Answer once, it remembers forever. Data entry is fast and flexible."

### 5. Testing & Demo Data
> "The mock data generator creates realistic test data instantly. 50 products, 6 months of sales, 7 stores. Perfect for demos, training, or testing new features."

### 6. Database Reset
> "For testing different scenarios, we can reset all data or just sales data. Keep products, clear sales, reload new sales from different months. Great for training."

---

## Advanced Demo (Optional, 5 minutes)

### Run Tests

**In terminal:**

```bash
uv run pytest src/tests/test_all.py -v
```

**Show output:**
```
23 passed in 4.73s
```

**What to say:**
> "The system has 23 automated tests that verify everything works correctly — product validation, abbreviation expansion, database operations, etc. All tests pass with no errors."

### Show Code Structure

**In VS Code, open:** `src/README.md`

**Explain:**
- Clear separation: models → cleaning → database → analytics
- Each folder has its own README with beginner-friendly explanations
- Code is well-documented for maintenance

---

## Common Demo Questions & Answers

| Question | Answer |
|----------|--------|
| What if someone uploads bad data? | System validates every field. Bad data is rejected with a clear error and logged. |
| How do new abbreviations get added? | During upload, if an abbreviation is unknown, the system asks the employee to link it or create a new one. After that, it's remembered. |
| Can we filter charts? | Yes! Shop, city, kind, collection, month range. Filters only show data that exists in the database. |
| What's the difference between a chart and a table? | Charts show trends visually. Below each chart is a table with exact numbers and percentages for precision. |
| Can we export data? | Yes, the chart table can be copied/exported. Full SQL access available for custom reports. |
| How long does an upload take? | Usually 1–2 seconds for a typical file. System validates, cleans, expands abbreviations, then saves. |
| What if we make a mistake uploading? | Use the database reset function to clear data and start fresh. Or clear just sales data and keep the product catalog. |

---

## Troubleshooting During Demo

| Issue | Solution |
|-------|----------|
| "Could not connect to database" | Check PostgreSQL is running: `psql -U postgres -d consignment` in terminal |
| Empty analytics | Make sure mock data was loaded: `python mock_data/generate_mock_data.py` |
| Charts not updating after filter | Refresh page (F5) or make sure filter dropdowns show the values you're selecting |
| Upload fails | Check file format is Excel (.xlsx) and columns match template names |
| Slow performance | Normal if using many filters. Try narrowing filters (shop, month) to speed up queries |

---

## Demo Checklist

- [ ] PostgreSQL running
- [ ] Web server started (`uv run python -m src.main`)
- [ ] Browser open to http://127.0.0.1:5000
- [ ] Mock data loaded (`python mock_data/generate_mock_data.py`)
- [ ] Tests passing (`uv run pytest src/tests/test_all.py -v`)

**Recommended demo order:**
1. Home page overview
2. Download templates
3. Populate mock data
4. Show analytics with filters
5. Demonstrate pie charts & top-N filtering
6. Show add product form
7. Explain abbreviations
8. (Optional) Run tests to show reliability

---

## What to Tell Your Supervisor

### Executive Summary

> "This system automates the entire product and sales data workflow. Employees download Excel templates, fill them in, upload to the website, and the system cleans the data, expands abbreviations, and saves everything to PostgreSQL. Reports then show live charts — top sellers, sales by store/city, and breakdowns by product attributes (gender, movement, color, etc.). Charts include both bar charts and new pie charts with percentage analysis. Filters update dynamically. All data is validated before storage. The system is fast, reliable, and requires no coding knowledge from employees."

### Key Stats

- **23 unit tests** — all passing ✓
- **0 errors** in code validation
- **6 chart types** with filtering
- **3 new pie charts** with percentage visualization
- **Top-N filtering** for chart clarity (Top 5, 10, custom)
- **Mock data tool** for instant testing
- **Database reset** functions for scenario testing
- **Comprehensive README** documentation updated

### Architecture Highlights

- **Separation of concerns:** Models → Cleaning → Database → Analytics
- **Live database:** PostgreSQL (not static Excel)
- **Type validation:** Bad data rejected before storage
- **Smart abbreviations:** System learns from corrections
- **Scalable:** Works with hundreds of stores and thousands of products

---

## Files Referenced in This Guide

- **Main entry:** [src/main.py](../src/main.py)
- **Web routes:** [src/app.py](../src/app.py)
- **Analytics queries:** [src/analytics/queries.py](../src/analytics/queries.py)
- **Chart builder:** [src/analytics/charts.py](../src/analytics/charts.py)
- **Product models:** [src/models/product.py](../src/models/product.py)
- **Mock data:** [mock_data/generate_mock_data.py](../mock_data/generate_mock_data.py)
- **Tests:** [src/tests/test_all.py](../src/tests/test_all.py)

---

## Post-Demo Next Steps

1. **Ask supervisor:** Any charts or features they'd like to add?
2. **Discuss:** Data retention and backup strategy
3. **Plan:** Training session for employees
4. **Schedule:** Regular backups and system maintenance

---

**Good luck with your presentation!** 🎯
