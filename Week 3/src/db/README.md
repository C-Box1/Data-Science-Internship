# `src/db/` — Talking to PostgreSQL (Beginner Guide)

> **Simple idea:** This folder is the **only place** in the project that actually talks to the database. Every save, lookup, and query goes through here.

---

## Why separate database code from everything else?

**Bad approach (everything mixed together):**
```
product_cleaner.py reads Excel AND writes SQL AND builds charts
```
If the database table changes, you hunt through 10 files to fix it.

**Our approach:**
```
cleaning/ → produces clean Python objects
db/repository.py → knows ALL the SQL
```

**Benefits:**
1. All SQL in one file — easy to find and fix
2. If you switch from PostgreSQL to another database, change only `connection.py` and `repository.py`
3. Tests can "fake" the database without PostgreSQL installed

---

## The two files in this folder

| File | Job | Analogy |
|------|-----|---------|
| `connection.py` | Open and close the database door | Phone number + key to the storage room |
| `repository.py` | Read and write data | The person who actually puts boxes on shelves |

---

# File 1: `connection.py`

## What is PostgreSQL?

A program that runs on your computer and stores data in **tables** (like Excel sheets, but permanent and strict about rules).

Our Python code cannot talk to PostgreSQL directly — it needs a **driver** called `psycopg2`.

## What is `.env`?

A secret settings file (not shared on GitHub) with your database password:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=consignment
DB_USER=postgres
DB_PASSWORD=your_password_here
```

**Why not hardcode the password in Python?**  
Security — passwords should never be in source code. `.env` stays on your machine only.

## Line-by-line explanation

```python
from dotenv import load_dotenv
load_dotenv()
```
**Meaning:** Read the `.env` file when Python starts.  
**Why at the top?** So `get_connection()` can find DB_PASSWORD immediately.

```python
def get_connection() -> PgConnection:
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 5432)),
        dbname=os.environ.get("DB_NAME", "consignment"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", ""),
    )
    return conn
```

**What each parameter means:**
| Parameter | Meaning | Default if missing from .env |
|-----------|---------|------------------------------|
| host | Which computer has PostgreSQL | localhost (your PC) |
| port | Which "door" PostgreSQL listens on | 5432 |
| dbname | Which database inside PostgreSQL | consignment |
| user | Username to log in | postgres |
| password | Password for that user | empty string |

**Why defaults?** So the code still tries reasonable values even if `.env` is incomplete.

```python
def test_connection() -> bool:
    try:
        conn = get_connection()
        conn.close()
        print("✅  Database connection successful.")
        return True
    except Exception as e:
        print(f"❌  Could not connect to the database: {e}")
        return False
```

**Why a separate test function?**  
`main.py` calls this at startup so you know immediately if something is wrong — before an employee tries to upload.

**Why close immediately?**  
We only want to check if connection works, not keep it open.

---

# File 2: `repository.py`

## Key concept: connection and cursor

Think of PostgreSQL like a **library**:

| Concept | Library analogy | Code |
|---------|-----------------|------|
| Connection (`conn`) | Your library card — gets you in the building | `get_connection()` |
| Cursor (`cur`) | A request slip you fill out | `conn.cursor()` |
| SQL query | The book you request | `cur.execute("SELECT ...")` |
| commit() | Confirming you want to keep the book | `conn.commit()` |
| fetchone() / fetchall() | Librarian brings back results | Reading query results |

**Why `with conn.cursor() as cur:`?**  
Automatically closes the cursor when done — like returning the request slip. Prevents resource leaks.

**Why `conn.commit()`?**  
Changes are not permanent until you commit. Without commit, INSERT disappears when connection closes.

---

## Products: `upsert_product(conn, product)`

**"Upsert" = UPDATE or INSERT** — fancy word for "save this product intelligently."

### The three outcomes (VERY IMPORTANT for supervisor)

```
Does reference 002H621 already exist in database?
│
├── NO  → INSERT new row        → return "inserted"
│
└── YES → Compare all fields
          │
          ├── ALL fields identical  → return "skipped" (duplicate, ignore)
          │
          └── SOME fields different → return "conflict" (needs human review)
```

### Why three outcomes instead of always overwriting?

| Approach | Problem |
|----------|---------|
| Always insert | Crash — duplicate key error |
| Always overwrite | Silently destroys correct data with wrong data |
| **Our approach** | Safe — skip exact duplicates, flag conflicts for review |

### Real examples

**Example 1 — New product (inserted):**
```
Database: (empty — no 002H621)
Upload:   002H621, WATCH, GALIERA, LADIES, QUARTZ, MESH, SS, 30
Result:   "inserted" ✅
```

**Example 2 — Exact duplicate (skipped):**
```
Database: 002H621, WATCH, GALIERA, LADIES, QUARTZ, MESH, SS, 30
Upload:   002H621, WATCH, GALIERA, LADIES, QUARTZ, MESH, SS, 30
Result:   "skipped" — same data uploaded twice, no harm done
```

**Example 3 — Conflict (needs review):**
```
Database: 002H621, WATCH, GALIERA, ...
Upload:   002H621, WATCH, CAPRICE, ...  (different collection!)
Result:   "conflict" ⚠️ — same reference, different info — human must decide
```

### Why `%(reference)s` instead of f-strings?

```python
# SAFE (what we use):
cur.execute("SELECT ... WHERE reference = %s", (product.reference,))

# DANGEROUS (never do this):
cur.execute(f"SELECT ... WHERE reference = '{product.reference}'")
```

**Why?** If someone put malicious text in a reference field, f-strings could allow SQL injection. `%s` placeholders keep data separate from the query structure.

---

## `bulk_insert_products(conn, products)`

Loops through a list of Product objects, calling `upsert_product` for each.

**Returns:**
```python
{"inserted": 40, "skipped": 3, "conflict": 2}
```

**Why not one big SQL INSERT for all products?**  
Because each product needs the three-outcome check individually. Simpler logic, easier to debug.

---

## Shops: `upsert_shop(conn, shop)`

**Exact same three-outcome logic** as products, but for the `market_information` table.

**When shops get inserted:** When a monthly sales report is uploaded — shops are parsed from column headers.

---

## Stock: `bulk_insert_present_elements(conn, records)`

**What is "present elements"?** Closing stock — how many units of each product were in each shop at month end.

**Uses `ON CONFLICT DO UPDATE`:**
```sql
INSERT INTO present_elements (...)
VALUES (...)
ON CONFLICT (item_reference, shop_id, report_month)
    DO UPDATE SET closing_stock = EXCLUDED.closing_stock
```

**Plain English:** If this exact record already exists (same product + shop + month), update the stock number instead of failing.

**Why?** Employee re-uploads corrected January report → stock numbers update, no duplicate error.

**Example:**
```
First upload:  002H621 at shop 1113, January, stock=5
Second upload: 002H621 at shop 1113, January, stock=7
Result:        stock updated to 7 (not a second row)
```

---

## Sales: `bulk_insert_sold_elements(conn, records)`

Same pattern as stock. Stores how many units were **sold** per product per shop per month.

**Also uses ON CONFLICT DO UPDATE** for re-uploads.

---

## Utility functions

### `get_all_references(conn)` → set of all product codes in DB

**Why needed?** Monthly report parser checks: "Is this product in our catalog?" If not, skip the row instead of crashing with foreign key error.

### `get_all_shop_ids(conn)` → set of all shop IDs in DB

**Same reason** — skip sales for unknown shops.

---

## Abbreviations functions

### `load_abbreviation_maps(conn)`

Reads entire abbreviations table, returns nested dictionary:

```python
{
  "bracelet": {"BRCLT": "BRACELET", "BRACE": "BRACELET", "MECH": "MESH"},
  "color": {"PG": "PINK GOLD", "SS": "STAINLESS STEEL", "RG": "ROSE GOLD"},
  "movement": {"AUTO": "AUTOMATIC"}
}
```

**Why load all at once?** Faster than querying database for every single cell during Excel processing.

**Why uppercase keys?** Case-insensitive lookup — `pg`, `PG`, `Pg` all find the same entry.

### `add_abbreviation(conn, abbrev)`

Checks if abbreviation already exists (case-insensitive). If not, inserts it.

**Returns:** `"inserted"` or `"exists"`

### `get_existing_full_terms(conn, category)`

Returns list like `["BRACELET", "MESH", "LEATHER STRAP"]` for the popup dropdown when employee defines unknown abbreviation.

---

## Filters: `get_filter_options(conn)`

**Purpose:** Fill the dropdown menus on the Reports page.

**Critical rule:** Only returns values that **actually exist in uploaded data**.

```python
{
  "shops": [...],        # only shops in market_information
  "sale_months": [...],  # only months with sales records
  "kinds": ["WATCH", "COFFRET"],
  "collections": [...],
  "cities": [...]
}
```

**Why this matters:**  
Employee cannot accidentally filter for "Shop 9999" or "March 2025" if that data was never uploaded. Prevents empty/confusing charts.

**Example — empty database:**
All dropdowns empty except default "All shops" option. Charts show "No data."

**Example — after uploading January sales for 3 shops:**
Shop dropdown shows exactly those 3 shops. Month dropdown shows `2024-01-01`.

---

## Full upload journey through db/

```
1. get_connection()           → open door to database
2. load_abbreviation_maps()   → load BRCLT→BRACELET etc.
3. (cleaning happens)
4. upsert_product() × N       → save each product
5. bulk_insert_sold_elements  → save sales rows
6. conn.close()               → close door
```

---

## Common errors and what they mean

| Error message | Cause | Fix |
|---------------|-------|-----|
| connection refused | PostgreSQL not running | Start PostgreSQL service |
| password authentication failed | Wrong `.env` password | Fix DB_PASSWORD |
| foreign key violation | Sales uploaded before products | Upload product catalog first |
| unique violation | Same reference inserted twice outside upsert logic | Should not happen — report as bug |

---

## What to tell your supervisor

> "All database access goes through two files. connection.py reads credentials from a secure .env file. repository.py contains every SQL query. Products use smart insert logic — new records are added, exact duplicates are skipped, and conflicts are flagged instead of silently overwriting. Sales and stock support re-upload via upsert. Filter dropdowns only show data that exists in the system."
