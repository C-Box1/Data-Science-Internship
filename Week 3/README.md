# Watch Consignment Management

A local web tool for Pierre Lannier employees to upload product catalogs and monthly sales reports, clean the data automatically, store it in PostgreSQL, and view sales visualizations — without needing any coding knowledge.

---

## What this project does (in plain English)

1. **Download templates** — Official Excel forms with the correct column layout.
2. **Fill in Excel** — Employees add products or monthly sales on their computer.
3. **Upload** — The website reads the file, cleans it, expands abbreviations (e.g. `BRCLT` → `BRACELET`, `pg` → `PINK GOLD`), and saves to the database.
4. **Add products manually** — Enter 1–10 products through a simple form.
5. **View reports** — Charts for top sellers, sales by shop/city, and product attribute breakdowns (matching the analysis sheets in `Watchs_Analysis_November 2024.xlsx`).

---

## Code documentation (for understanding & supervisor presentations)

> **These READMEs are written for beginners.** Each one explains what the code does, **why it was built that way**, and walks through real examples step by step. You do not need to be an expert programmer to follow them.

Every source directory has its own README:

| Directory | README | Start here if you want to understand... |
|-----------|--------|----------------------------------------|
| `src/` | [src/README.md](src/README.md) | **The big picture** — read this first |
| `src/models/` | [src/models/README.md](src/models/README.md) | What makes a valid product or shop |
| `src/db/` | [src/db/README.md](src/db/README.md) | How data is saved to PostgreSQL |
| `src/cleaning/` | [src/cleaning/README.md](src/cleaning/README.md) | How Excel files are cleaned |
| `src/analytics/` | [src/analytics/README.md](src/analytics/README.md) | How charts and reports work |
| `src/templates_excel/` | [src/templates_excel/README.md](src/templates_excel/README.md) | How download templates are created |
| `src/tests/` | [src/tests/README.md](src/tests/README.md) | How automatic tests verify the code |
| `sql/` | [sql/README.md](sql/README.md) | Every database table explained |
| `templates/` | [templates/README.md](templates/README.md) | Each website page explained |
| `static/` | [static/README.md](static/README.md) | CSS styling + JavaScript behavior |

### Recommended reading order (if you are new to programming)

1. [src/README.md](src/README.md) — understand the full flow (15 min)
2. [sql/README.md](sql/README.md) — understand what gets stored (10 min)
3. [src/models/README.md](src/models/README.md) — understand validation rules (15 min)
4. [src/cleaning/README.md](src/cleaning/README.md) — follow one Excel row through the system (20 min)
5. [templates/README.md](templates/README.md) + [static/README.md](static/README.md) — what the employee sees (10 min)

Each README includes:
- **Glossary** of technical words
- **"Why we did it this way"** sections
- **Step-by-step walkthroughs** with real data examples
- **"What to tell your supervisor"** talking points
- **Common questions** answered in plain English

---

## Requirements


| Tool                   | Version            | Why you need it                          |
| ---------------------- | ------------------ | ---------------------------------------- |
| **Python**             | 3.11 or newer      | Runs the backend and web server          |
| **PostgreSQL**         | 14+ recommended    | Stores all product, shop, and sales data |
| **uv**                 | Latest             | Installs Python packages quickly         |
| **VS Code** (optional) | Any recent version | Recommended editor                       |
| **Microsoft Excel**    | Any recent version | For filling in the templates             |


### VS Code extensions (recommended)

- **Python** (Microsoft) — run and debug Python
- **SQLTools** + **SQLTools PostgreSQL** — browse the database visually

---

## Step-by-step setup (first time)

### 1. Install Python 3.11+

Download from [python.org](https://www.python.org/downloads/) or use Miniconda:

```bash
conda create -n consignment python=3.11
conda activate consignment
```

### 2. Install PostgreSQL

1. Download from [postgresql.org](https://www.postgresql.org/download/)
2. During install, remember the password you set for the `postgres` user
3. Open **pgAdmin** or **SQL Shell (psql)** and create a database:

```sql
CREATE DATABASE consignment;
```

### 3. Clone / open this project folder

```bash
cd "(project_name)"
```

### 4. Install Python packages

```bash
uv sync
```

This installs: Flask, pandas, openpyxl, psycopg2, plotly, pytest, python-dotenv.

### 5. Configure database credentials

Create a file named `.env` in the project root (copy from below):

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=consignment
DB_USER=postgres
DB_PASSWORD=your_password_here
```

Replace `your_password_here` with your PostgreSQL password.

### 6. Create database tables

In pgAdmin or psql, connected to the `consignment` database, run these two files in order:

1. `sql/schema.sql` — creates all 5 tables + abbreviations table
2. `sql/seed_abbreviations.sql` — adds default abbreviation mappings (BRCLT, PG, etc.)

**In psql:**

```bash
psql -U postgres -d consignment -f sql/schema.sql
psql -U postgres -d consignment -f sql/seed_abbreviations.sql
```

### 7. Start the website

```bash
uv run python -m src.main
```

Open your browser at: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

**Visualizations (charts):** [http://127.0.0.1:5000/analytics](http://127.0.0.1:5000/analytics) — click **Reports** in the navigation bar.

**Full manual testing guide:** See [TESTING_GUIDE.md](TESTING_GUIDE.md) for step-by-step website tests.

**Demo & Presentation Guide:** See [DEMO_GUIDE.md](DEMO_GUIDE.md) for how to showcase the system to supervisors or stakeholders.

Press `Ctrl+C` in the terminal to stop the server.

---

## Demo & Presentations

**For showing the system to supervisors or stakeholders:**

See [DEMO_GUIDE.md](DEMO_GUIDE.md) — Complete walkthrough including:
- Quick start in 5 minutes
- Step-by-step demo (10–15 minutes)
- Key features to emphasize
- Talking points and answers to common questions
- Demo checklist
- Troubleshooting tips

**For a quick summary of all recent changes:**

See [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md) — Overview of updates including:
- Terminology fixes (bracelet → strap)
- New pie charts
- Mock data system
- Database reset functions
- Documentation updates
- Test results (23/23 passing ✓)

---

## Project folder structure

```
Week 3/
├── data/                          Sample Excel files (not committed to git)
├── excel_templates/               Generated download templates (auto-created)
├── sql/
│   ├── schema.sql                 Database table definitions
│   └── seed_abbreviations.sql     Default abbreviation seeds
├── static/
│   ├── css/style.css              Website styling
│   └── js/                        Page-specific JavaScript
├── templates/                     HTML pages (Flask)
├── uploads/                       Temporary uploaded files
├── src/
│   ├── main.py                    Start the web server
│   ├── app.py                     Flask routes and API
│   ├── models/
│   │   ├── product.py             Watch / Coffret data classes
│   │   ├── shop.py                Shop parser from report headers
│   │   └── abbreviation.py        Abbreviation data class
│   ├── cleaning/
│   │   ├── product_cleaner.py     Cleans product Excel uploads
│   │   ├── monthly_report_parser.py  Parses sales/stock reports
│   │   ├── abbreviation_resolver.py  DB-backed abbreviation lookup
│   │   └── pipeline.py            Orchestrates upload → clean → DB
│   ├── db/
│   │   ├── connection.py          PostgreSQL connection
│   │   └── repository.py          All SQL insert/query functions
│   ├── analytics/
│   │   ├── queries.py             SQL for charts (top sellers, by city, etc.)
│   │   └── charts.py              Plotly chart builder
│   ├── templates_excel/
│   │   └── generator.py           Creates downloadable Excel templates
│   └── tests/
│       └── test_all.py            Unit tests
├── pyproject.toml                 Python version and dependencies
└── README.md                      This file
```

---

## Excel templates explained

### Product Catalog (`product_catalog_template.xlsx`)

Same 9 columns as the original reference files (`combined_file.xlsx`, etc.):


| Column     | Required | Example                       |
| ---------- | -------- | ----------------------------- |
| REFERENCE  | Yes      | 002H621                       |
| COLLECTION | Yes      | GALIERA                       |
| GENDER     | Yes      | LADIES, GENTS, UNISEX         |
| MOUVEMENT  | Yes      | QUARTZ, AUTOMATIC, MECHANICAL |
| DIAL       | No       | SILVER                        |
| BRACELET   | No       | MECH/LEATH                    |
| COLOR      | No       | SS, PG, RG                    |
| CASE SZE   | No       | 30 or 21x28.4                 |
| KIND       | Yes      | WATCH or COFFRET              |


### Monthly Sales & Stock Report (`monthly_sales_stock_template.xlsx`)

Matches the January 2024 POS format:

- Row 1: shop headers (`SHOP_ID - Mall - City - Distributor`)
- Row 2: alternating `Sales` and `Cls Stock` columns
- Row 3+: product references with quantities

---

## Abbreviations

The `abbreviations` table stores short codes. Lookup is **case-insensitive**:


| Abbreviation | Full term       | Field    |
| ------------ | --------------- | -------- |
| BRCLT, BRACE | BRACELET        | bracelet |
| PG           | PINK GOLD       | color    |
| SS           | STAINLESS STEEL | color    |
| MECH         | MESH            | bracelet |


When an unknown abbreviation is detected during upload, the website asks whether to:

- Link it to an existing full term
- Add it as a new abbreviation
- Ignore it (leave as-is)

Manage abbreviations at: **[http://127.0.0.1:5000/abbreviations](http://127.0.0.1:5000/abbreviations)**

---

## Visualizations available

Based on `data/Watchs_Analysis_November 2024.xlsx`:


| Button on website                                                                    | Excel sheet equivalent    |
| ------------------------------------------------------------------------------------ | ------------------------- |
| Top Sellout References                                                               | Top 20 Sellout references |
| Top POS in KSA                                                                       | Top 20 POS in KSA         |
| Total Sellout by City                                                                | Total Sellout by City     |
| Bracelet / Color / Collection / Gender / Kind / Movement / Dial / Case Size Analysis | Matching analysis sheets  |


Filters (shop, city, kind, collection, month range) only show values **already present in the database**.

---

## Running tests

```bash
uv run pytest src/tests/test_all.py -v
```

Tests cover product validation, abbreviation expansion, shop parsing, cleaning logic, and database operations (mocked — no PostgreSQL needed).

---

## Loading sample data (optional)

Place the provided Excel files in the `data/` folder, then use the website upload page or run from Python:

```python
from pathlib import Path
from src.db.connection import get_connection
from src.cleaning.pipeline import run_seed_from_data_folder

conn = get_connection()
run_seed_from_data_folder(conn, Path("data"))
conn.close()
```

---

## Website Navigation & Features

**The website is designed for non-technical employees.** All pages are accessible from the navigation bar at the top.

### Home (`/`)

The main welcome page explaining what the system does in simple language.

- **Read this if:** You're new to the system
- **Key info:** Overview of the 5-step workflow

---

### Templates (`/templates`)

**Download official Excel forms** with the correct column layout.

Three templates available:

1. **Product Catalog** — List of watches and coffrets
   - Use for: Uploading new or updated watch references
   - Columns: Reference, Collection, Gender, Movement, Dial, Strap, Color, Case Size, Kind
   - Format: Each row = one product

2. **Monthly Sales & Stock Report** — Sales quantities per shop
   - Use for: Recording monthly sales and stock levels
   - Format: Shops across columns, products down rows
   - Tracks both sales and closing stock

3. **Bulk Entry (up to 10 products)** — Manual entry form in Excel
   - Use for: Adding 1–10 products without uploading
   - Format: Simple form with all product fields

**How to use:**
1. Click "Download" for the template you need
2. Fill it in on your computer with Excel
3. Save the file
4. Come back to this website and upload it

---

### Upload (`/upload`)

**Upload completed Excel files** to add products and sales data to the database.

Two options:

#### Product Catalog Upload
- Accepts files from the **Product Catalog template**
- Also accepts legacy format files: `combined_file.xlsx`, `elio_list.xlsx`, etc.
- The system automatically detects the sheet and column layout
- After upload, you can respond to abbreviation questions

#### Monthly Sales & Stock Report Upload
- Accepts files from the **Monthly Sales & Stock Report template**
- Matches shop headers to existing stores in the database
- Records sales and stock levels by product and shop

**What happens during upload:**
1. System reads the Excel file
2. Cleans data (fixes typos, expands abbreviations)
3. If abbreviations are unknown → you decide whether to link or add new ones
4. All data is saved to the database
5. You see a summary (inserted, conflicts, unknown abbreviations)

**Troubleshooting uploads:**
- "Foreign key error" → Upload products first, then sales
- "No matching shop" → Add the shop in a sale first, or check the shop name spelling
- "Unknown abbreviation" → Either link to existing or create new abbreviation

---

### Add Product (`/add-product`)

**Manually enter 1–10 products** through a web form.

Use this if:
- You have just a few products to add
- You don't want to use Excel
- You want to quickly test the system

**Fields:**
- Reference (required)
- Collection, Gender, Movement (required dropdowns)
- Dial, Strap, Color, Case Size (optional)
- Kind: Choose WATCH or COFFRET
  - **WATCH:** Single watch with one strap type
  - **COFFRET:** Gift set = watch + presentation box with multiple strap types (e.g., "MESH/LEATHER")

**Example:**
- A watch: Reference=002H621, Kind=WATCH, Strap=MESH
- A coffret set: Reference=350J621, Kind=COFFRET, Strap=MESH/LEATHER

---

### Analytics (`/analytics`)

**View sales charts and reports** with powerful filtering.

#### Chart Types

**Bar Charts (Traditional):**
- **Top Sellout References** — Which product codes sold the most? Shows total quantity sold.
- **Top POS in KSA** — Which stores sold the most? Shows total sales by shop.
- **Total Sellout by City** — Sales broken down by Saudi city (Riyadh, Jeddah, etc.).
- **Attribute Breakdowns** (Bar charts):
  - Gender, Kind, Movement, Collection, Color, Strap, Dial, Case Size
  - Shows total sales grouped by each attribute

**Pie Charts (Visual %  allocation):**
- **Sales by Gender (Pie)** — What % of total sales are LADIES, GENTS, UNISEX?
- **Sales by Kind (Pie)** — What % are WATCH vs COFFRET?
- **Sales by Movement (Pie)** — What % are QUARTZ, AUTOMATIC, MECHANICAL?

#### Filters

Apply filters to narrow down data:

- **Shop** — Select a specific store (e.g., "Kingdom Mall")
- **City** — Select a city (e.g., "Riyadh")
- **Kind** — Show only WATCH or only COFFRET sales
- **Collection** — Show sales for specific collections
- **Month Range** — Show sales for specific month(s)

**How to use filters:**
1. Select filter values from dropdowns (only existing data appears)
2. Click the chart button to update
3. The chart updates to show filtered data
4. Try different combinations to explore

#### Pie Chart Filtering (Top N Items)

For pie charts, you can limit which items appear:

- **No filter (default):** Shows ALL items
- **Top 5:** Shows the 5 highest-selling items (by %) + groups rest as "Other"
- **Top 10:** Shows top 10 + others
- **Custom:** Enter any number

**Why use Top N?**
- Too many items make a pie chart unreadable
- Focus on the biggest sellers
- See what % the top items represent of total sales

**Example:**
- "Sales by Gender" with Top 5 might show:
  - LADIES: 45% (1000 units)
  - GENTS: 35% (778 units)
  - UNISEX: 20% (445 units)
  - Other: 0%
  (If there were more categories, they'd be grouped as "Other")

#### Reading the Charts

**Each chart shows:**
- **Count:** Number of items sold (e.g., "1000 watches")
- **Percentage:** What % of the total (e.g., "45.2%")
- **Title:** What the chart measures
- **Sorting:** Highest values first (top to bottom or left to right)

**Example reading:**
- Chart title: "Top Sellout References"
- Bar labeled "002H621" with value "45 (14.1%)"
- Meaning: Product 002H621 sold 45 units, which is 14.1% of all watches sold

---

### Abbreviations (`/abbreviations`)

**View and manage abbreviation mappings.**

Abbreviations are short codes that expand to full terms:

| Short Code | Expands to      | Field  |
| ---------- | --------------- | ------ |
| BRCLT      | BRACELET        | Strap  |
| PG         | PINK GOLD       | Color  |
| SS         | STAINLESS STEEL | Color  |
| MECH       | MESH            | Strap  |

**Existing mappings:**
- Shown in a table
- Organized by field (Color, Strap, Movement)

**Add new abbreviation:**
1. Choose field category
2. Enter short code (e.g., "PLT")
3. Pick or type the full term (e.g., "PLATINUM")
4. Click "Add"

**Unknown abbreviations:**
- During upload, if an abbreviation isn't found, the system asks what to do
- You can link it to an existing full term OR create a new abbreviation
- After you respond, future uploads will recognize it

---

## Testing & Development

### Mock Data for Testing

For testing visualizations without real data:

```bash
python mock_data/generate_mock_data.py
```

This populates the database with:
- 50 realistic mock products
- 6 months of historical sales
- Distributed across 7 sample shops

See [mock_data/README.md](mock_data/README.md) for details.

### Resetting Data

**Clear ALL data** (for testing different scenarios):
```python
from src.db.connection import get_connection
from src.db.repository import truncate_all_data

conn = get_connection()
truncate_all_data(conn)
conn.close()
```

**Clear only sales data** (keep products):
```python
from src.db.repository import truncate_sales_data

conn = get_connection()
truncate_sales_data(conn)
conn.close()
```

Or use the API endpoints:
- `POST /api/admin/reset-all-data` — Clear everything
- `POST /api/admin/reset-sales-data` — Clear only sales
- `POST /api/admin/populate-mock-data` — Fill with mock data

---

## Troubleshooting


| Problem                             | Solution                                                       |
| ----------------------------------- | -------------------------------------------------------------- |
| "Could not connect to database"     | Check PostgreSQL is running and `.env` credentials are correct |
| Upload fails with foreign key error | Upload product catalog before monthly sales reports            |
| Empty charts                        | Upload sales data first; filters only show existing data       |
| Template download empty             | Restart the server — templates are auto-generated on first run |


---

## Tech stack summary

- **Backend:** Python 3.11+, Flask
- **Database:** PostgreSQL
- **Data processing:** pandas, openpyxl
- **Charts:** Plotly
- **Frontend:** HTML, CSS, JavaScript (no framework — kept simple for non-technical users)
- **Package manager:** uv

