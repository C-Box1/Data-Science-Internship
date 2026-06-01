# Website Testing Guide (Step-by-Step)

This guide helps you **manually test the website** to confirm everything works. No advanced programming knowledge needed — follow each step in order.

---

## Quick answer: Where are the visualizations?

**URL:** [http://127.0.0.1:5000/analytics](http://127.0.0.1:5000/analytics)

**How to get there:**
1. Start the server (see Part 1 below)
2. Open your browser
3. Click **Reports** in the top navigation bar  
   **OR** go directly to: `http://127.0.0.1:5000/analytics`

**What you will see:**
- **Filter dropdowns** at the top (Shop, City, Kind, etc.)
- **Chart buttons** below (Top Sellout References, Top POS in KSA, Color Analysis, etc.)
- **Chart area** — the bar chart appears here **after you click a button**
- **Table** — exact numbers appear below the chart

**Important:** Charts need **sales data in the database** first. If you have not uploaded products + a monthly report, charts will be empty. Follow Part 3 in this guide to load test data, then Part 5 for charts.

```
Home page  →  click "Reports"  →  /analytics  →  click a chart button  →  chart appears
```

---

## Before you start — checklist

Make sure all of these are done:

| # | Check | How to verify |
|---|-------|---------------|
| 1 | PostgreSQL is running | pgAdmin opens, or Windows Services shows PostgreSQL running |
| 2 | Database `consignment` exists | pgAdmin shows it in the list |
| 3 | Tables created | You ran `sql/schema.sql` and `sql/seed_abbreviations.sql` |
| 4 | `.env` file exists | In project folder with correct password |
| 5 | Packages installed | You ran `uv sync` |
| 6 | Sample Excel files in `data/` folder | At least `combined_file.xlsx` and January sales report |

---

## Part 1 — Start the server

Open a terminal in the project folder and run:

```bash
uv run python -m src.main
```

**You should see:**
```
Watch Consignment Management — starting local server
==================================================
✅  Database connection successful.

Open your browser at: http://127.0.0.1:5000
```

| What you see | Meaning |
|--------------|---------|
| ✅ Database connection successful | Good — continue testing |
| ❌ Could not connect to the database | Fix `.env` or start PostgreSQL before continuing |

**Keep this terminal open** while testing. Closing it stops the website.

---

## Part 2 — Run automatic code tests (optional but recommended)

In a **second terminal** (leave the server running in the first):

```bash
uv run pytest src/tests/test_all.py -v
```

**Expected:** `23 passed`

| Result | Meaning |
|--------|---------|
| 23 passed | Python logic works correctly |
| Any FAILED | Something broke in the code — fix before demo |

These tests check Python logic only. They do **not** test the website in the browser.

---

## Part 3 — Load test data (required for charts)

Charts need data in the database. **Upload in this order:**

### Step 3A — Upload product catalog

1. Open [http://127.0.0.1:5000/upload](http://127.0.0.1:5000/upload)
2. Under **Product Catalog**, click **Choose file**
3. Select one of:
   - `data/combined_file.xlsx` (many products — good for full test)
   - **OR** download template from `/templates`, add 2–3 rows, upload that
4. Click **Upload Products**

**Expected result (green box):**
```
Done! Products loaded: (some number). Inserted: X, Skipped: Y, Conflicts: Z
```

| If you see | What to do |
|------------|------------|
| Green success with Inserted > 0 | ✅ Continue to Step 3B |
| Red error about database | Check PostgreSQL and `.env` |
| Inserted: 0, Skipped: many | Data may already be uploaded — that's OK, continue |

**Note:** If you upload `combined_file.xlsx`, use sheet **Sheet1**. The website template uses sheet **Products** — our sample file uses Sheet1, so upload via the website expects the template format. For `combined_file.xlsx`, you may need to use the Python seed script instead:

```bash
uv run python -c "
from pathlib import Path
from src.db.connection import get_connection
from src.cleaning.pipeline import run_seed_from_data_folder
conn = get_connection()
result = run_seed_from_data_folder(conn, Path('data'))
print(result)
conn.close()
"
```

This loads all reference files from `data/` at once.

### Step 3B — Upload monthly sales report (for charts!)

1. Stay on [http://127.0.0.1:5000/upload](http://127.0.0.1:5000/upload)
2. Under **Monthly Sales & Stock Report**, choose:
   - `data/1-Pierre Lannier January 2024 Sales Per POS.xlsx`
3. Click **Upload Report**

**Expected result (green box):**
```
Done! Sales records: (number), Stock records: (number). Format: pos_wide
```

| If you see | Meaning |
|------------|---------|
| `format: pos_wide` | ✅ Correct format — shops and sales extracted |
| Sales records: 0 | Products or shops may not be in DB yet — do Step 3A first |
| Red foreign key error | Upload products before sales report |

---

## Part 4 — Test each website page

Use this table. Check ✅ when each test passes.

### Home page — `http://127.0.0.1:5000/`

| Test | Action | Expected result |
|------|--------|-----------------|
| Page loads | Open URL | Welcome text + 4 cards visible |
| Navigation works | Click each top link | Each page opens without error |
| Database status | Look at bottom of page | Green "Database connected and ready" |

---

### Templates page — `/templates`

| Test | Action | Expected result |
|------|--------|-----------------|
| Three templates listed | Open page | Product Catalog, Monthly Report, Bulk Entry |
| Download works | Click Download on Product Catalog | `.xlsx` file saves to your computer |
| File opens in Excel | Open downloaded file | Sheet "Products" with blue header row + 2 example rows |
| Instructions sheet | Click "Instructions" tab | Plain English column explanations |

---

### Upload page — `/upload`

| Test | Action | Expected result |
|------|--------|-----------------|
| Product upload | Upload valid product Excel | Green success message |
| Report upload | Upload January POS report | Green message with sales/stock counts |
| No file selected | Click Upload without choosing file | Red "Please choose a file first" |
| Abbreviation popup | Upload row with unknown color code (if any) | Popup asks what the code means |

**Optional abbreviation test:**
1. Download product template
2. Add a row with `COLOR = TESTCODE` (made-up code)
3. Upload
4. Popup should appear for `TESTCODE`
5. Enter full term or click "Not an abbreviation"

---

### Add Products page — `/add-product`

| Test | Action | Expected result |
|------|--------|-----------------|
| Form visible | Open page | One product form with dropdowns |
| Add row | Click "Add another product" | Second product form appears |
| Max 10 rows | Keep clicking Add | Button disables after 10 rows |
| Save one product | Fill reference + required fields, click Save | Green "Saved! Inserted: 1" |
| Duplicate reference | Save same reference twice | Second time may show Skipped or Conflict |

**Sample test product:**
| Field | Value |
|-------|-------|
| Reference | TEST001 |
| Collection | TESTCOL |
| Gender | LADIES |
| Movement | QUARTZ |
| Kind | WATCH |

---

### Abbreviations page — `/abbreviations`

| Test | Action | Expected result |
|------|--------|-----------------|
| Table loads | Open page | Table shows BRCLT, PG, SS, etc. |
| Add abbreviation | Fill form: abbrev=TEST, full term=TEST TERM, field=general, submit | New row appears in table |
| Case insensitivity | Upload product with `pg` in color field | Saves as PINK GOLD in database |

---

### Reports page (VISUALIZATIONS) — `/analytics`

**This is where all charts live.**

| Test | Action | Expected result |
|------|--------|-----------------|
| Page loads | Open `/analytics` | Filter dropdowns + chart buttons visible |
| Filters populate | Wait 1–2 seconds | Shop/City/Month dropdowns fill with data (if data uploaded) |
| Top Sellout chart | Click **Top Sellout References** | Bar chart appears in chart area + table below |
| Top POS chart | Click **Top POS in KSA** | Different chart — stores ranked by sales |
| City chart | Click **Total Sellout by City** | Sales by city/region |
| Color analysis | Click **Color Analysis** | Breakdown by color |
| Kind filter | Select WATCH in Kind filter, click Top Sellout again | Chart updates — coffret sales excluded |
| Shop filter | Select one shop, click Top POS | Only that shop's data |
| No data scenario | Before uploading sales, open page and click chart | "No data for the selected filters" |

**Where exactly is the chart?**

```
┌─────────────────────────────────────────┐
│  Filters: [Shop ▼] [City ▼] [Kind ▼]   │
├─────────────────────────────────────────┤
│  [Top Sellout] [Top POS] [Color] ...   │  ← click these buttons
├─────────────────────────────────────────┤
│                                         │
│     ████  ███  ██  █                    │  ← CHART APPEARS HERE
│     Bar chart (interactive — hover      │     (id="chart-area")
│     shows exact numbers)                │
│                                         │
├─────────────────────────────────────────┤
│  item_code  |  grand_total              │  ← TABLE WITH NUMBERS
│  036P621    |  11                       │     (id="table-area")
└─────────────────────────────────────────┘
```

**Chart tips:**
- **Hover** over bars to see exact values
- Chart needs **internet** for first load (Plotly loads from CDN)
- If chart area stays blank, press **F12** → Console tab → check for errors

**All available chart buttons:**

| Button | What it shows |
|--------|---------------|
| Top Sellout References | Best-selling product codes |
| Top POS in KSA | Best-performing stores |
| Total Sellout by City | Sales by city |
| Bracelet Analysis | Sales grouped by bracelet type |
| Case Size Analysis | Sales grouped by case size |
| Collection Analysis | Sales grouped by collection |
| Gender Analysis | Sales grouped by gender |
| Kind Analysis | WATCH vs COFFRET sales |
| Movement Analysis | Quartz vs Automatic vs Mechanical |
| Dial Analysis | Sales grouped by dial |
| Color Analysis | Sales grouped by color |

---

## Part 5 — Full end-to-end test (recommended demo flow)

Do this once before presenting to your supervisor:

```
1. Start server                    → ✅ database message
2. Run pytest                      → 23 passed
3. Seed or upload products         → Inserted > 0
4. Upload January sales report     → Sales records > 0
5. Open /analytics                 → Filters have options
6. Click "Top Sellout References"  → Chart + table appear
7. Apply Kind = WATCH filter       → Chart updates
8. Open /abbreviations             → Table shows abbreviations
9. Download template from /templates → Excel file saves
10. Add one product via /add-product → Saved successfully
```

**Total time:** about 15–20 minutes first time.

---

## Part 6 — Verify data in the database (optional)

If you have **pgAdmin** or **SQLTools** in VS Code:

```sql
-- How many products?
SELECT COUNT(*) FROM products_information;

-- How many sales records?
SELECT COUNT(*) FROM sold_elements;

-- Top 5 sellers
SELECT item_reference, SUM(quantity_sold) AS total
FROM sold_elements
GROUP BY item_reference
ORDER BY total DESC
LIMIT 5;
```

If these return numbers > 0, your uploads worked and charts should have data.

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|--------------|-----|
| Website won't open | Server not running | Run `uv run python -m src.main` |
| ❌ Database on home page | PostgreSQL off or wrong `.env` | Start PostgreSQL, check password |
| Upload red error | DB not connected | Fix database first |
| Charts empty | No sales data uploaded | Upload products, then January report |
| Filters dropdown empty | No shops/sales in DB yet | Upload monthly report |
| Chart button does nothing | Need internet for Plotly CDN | Connect to internet, refresh page |
| `combined_file.xlsx` upload fails | Wrong sheet name | Use seed script in Part 3A |
| February–November reports: 0 sales | Time-series format (no shops) | Use January report or POS template |
| Popup won't close | JavaScript error | F12 → Console, refresh page |

---

## Quick reference — all URLs

| Page | URL |
|------|-----|
| Home | http://127.0.0.1:5000/ |
| Download templates | http://127.0.0.1:5000/templates |
| Upload data | http://127.0.0.1:5000/upload |
| Add products manually | http://127.0.0.1:5000/add-product |
| **Reports / visualizations** | **http://127.0.0.1:5000/analytics** |
| Abbreviations | http://127.0.0.1:5000/abbreviations |
| Database health check | http://127.0.0.1:5000/api/health |

---

## Summary

| What you want | Where to go |
|---------------|-------------|
| See bar charts | **Reports page** → `/analytics` → click a chart button |
| See exact numbers | Same page — table below the chart |
| Test uploads | `/upload` |
| Test manual entry | `/add-product` |
| Test automatic code | `uv run pytest src/tests/test_all.py -v` |

**Remember:** Visualizations are not on the home page. Go to **Reports** (`/analytics`), upload sales data first, then click a chart button to see the graph.
