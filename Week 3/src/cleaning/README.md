# `src/cleaning/` — Cleaning Excel Files (Beginner Guide)

> **Simple idea:** Employees upload messy Excel files. This folder reads them, fixes problems, expands abbreviations, and produces clean Python objects ready for the database.
>
> **ETL** = Extract (read Excel) → Transform (clean/fix) → Load (save to DB). The `pipeline.py` file orchestrates all three steps.

---

## Why cleaning is a separate step

**Real Excel problems we found in the actual data files:**

| Problem | Example from real data |
|---------|------------------------|
| Trailing spaces in headers | `"COLLECTION "` instead of `"COLLECTION"` |
| French spelling | `"MOUVEMENT"` instead of `"MOVEMENT"` |
| Typos in headers | `"CASE SZE "` instead of `"CASE SIZE"` |
| Zero as empty value | `0.0` in dial column meaning "no dial" |
| Duplicate references | Same product in multiple source files |
| Abbreviations | `BRCLT` instead of `BRACELET` |
| Two report formats | January = shop columns; May = date columns |

**If we skipped cleaning:** Database fills with garbage, charts break, employees lose trust in the tool.

---

## The four files and their jobs

| File | Job | When it runs |
|------|-----|--------------|
| `abbreviation_resolver.py` | Expand BRCLT→BRACELET, pg→PINK GOLD | Every product row |
| `product_cleaner.py` | Read product Excel files | Product catalog upload |
| `monthly_report_parser.py` | Read sales/stock reports | Monthly report upload |
| `pipeline.py` | Connect cleaning → database | Called by app.py |

**Why not one big cleaner file?** Each file handles a different Excel format. Easier to fix one without breaking the other.

---

# File 1: `abbreviation_resolver.py`

## The problem it solves

Employees and source Excel files use **short codes**:
- `BRCLT` or `brclt` = bracelet type
- `PG` or `pg` = pink gold
- `MECH/LEATH` = mesh + leather strap combo

We store **full names** in the database for clarity. This file translates short → full.

## Where abbreviations are stored

**Primary source:** PostgreSQL `abbreviations` table (employee can add new ones via website)

**Fallback:** `DEFAULT_ALIASES` dictionary in this file — used when:
- Running tests (no database needed)
- Database connection fails

**Why both?** Tests must work offline. Production uses the database so employees can add new codes without changing code.

## Class `AbbreviationResolver`

### How it is created

```python
# Production (upload on website):
resolver = AbbreviationResolver(conn)  # loads from database

# Tests:
resolver = AbbreviationResolver(alias_maps=DEFAULT_ALIASES)  # hardcoded
```

### Method: `expand(value, field_category)`

**Most important method.** Expands abbreviations in a cell value.

**Algorithm in plain English:**
1. If value is empty → return nothing
2. Split on `/` (handles combos like `MECH/LEATH`)
3. For each part, look it up in the dictionary (case-insensitive)
4. If found → replace with full term
5. If not found AND looks like a short code → mark as "unknown"
6. Join parts back with `/`

**Examples:**

| Input | Category | Output | Unknown? |
|-------|----------|--------|----------|
| `"BRCLT"` | bracelet | `"BRACELET"` | No |
| `"brclt"` | bracelet | `"BRACELET"` | No — case insensitive |
| `"pg"` | color | `"PINK GOLD"` | No |
| `"MECH/LEATH"` | bracelet | `"MESH/LEATHER STRAP"` | No — each part expanded |
| `"TITANIUM"` | bracelet | `"TITANIUM"` | No — not a short code, kept as-is |
| `"XYZ"` | color | `"XYZ"` | **Yes** — triggers employee popup |

**Why mark unknown instead of failing?**  
Employee can define the code on the spot. Upload continues for other rows.

**Why `len(part) <= 6 and part.isalpha()` for unknown detection?**  
Short letter codes are probably abbreviations. `"TITANIUM"` is long — probably a real word, not an abbrev.

### Method: `reload()`

After employee adds new abbreviation via popup, call `reload()` to refresh the dictionary without restarting the server.

---

# File 2: `product_cleaner.py`

## What files it can read

**From `/data` folder (development bootstrap):**
| File | Sheet |
|------|-------|
| combined_file.xlsx | Sheet1 |
| elio_list.xlsx | Feuil2 |
| list_for_elio_2.xlsx OR list for elio 2.xlsx | Sheet1 |
| missing_info.xlsx | Sheet2 |

**From website upload:** Any Excel file with the 9-column template format, sheet named `"Products"`.

## `COLUMN_MAP` — fixing header names

Excel headers are inconsistent. This dictionary maps every variant to one clean name:

```
"MOUVEMENT"  →  "movement"
"CASE SZE "   →  "case_size"
"casesze"    →  "case_size"
```

**Why a dictionary instead of if-statements?**  
Easy to add new typos when we discover them — just add one line to the map.

## Class `ProductCleaner` — internal memory

When processing files, the cleaner remembers:

| Variable | Purpose |
|----------|---------|
| `_seen_references` | Set of references already processed — prevents duplicates |
| `_cleaning_log` | List of every dropped row + reason — for auditing |
| `_unknown_abbrevs` | Codes needing employee input |

**Why track across files in `load_all()`?**  
If `combined_file.xlsx` and `elio_list.xlsx` both contain `002H621`, second occurrence is dropped.

## Method: `_load_file(filepath, sheet_name)`

**Step 1:** `pd.read_excel()` — pandas reads the Excel sheet into a table (DataFrame)

**Step 2:** `_normalize_columns()` — fix header names using COLUMN_MAP

**Step 3:** `_drop_empty_columns()` — remove columns that are entirely empty  
**Why?** `elio_list.xlsx` has 17 extra empty columns that confuse processing.

**Step 4:** Loop each row → `_process_row()`

## Method: `_process_row(row, source_file, row_idx)`

**Decision tree for each row:**

```
Row has reference?
├── NO  → drop, log "missing reference"
└── YES → Reference already seen?
          ├── YES → drop, log "duplicate reference"
          └── NO  → Required fields filled?
                    ├── NO  → drop, log "missing required field"
                    └── YES → Product.from_row()
                              ├── ValueError → drop, log "validation error"
                              └── Success → add to results, track unknown abbrevs
```

**Why drop bad rows instead of stopping entire upload?**  
One bad row should not block 499 good rows. Employee gets a summary at the end.

## Real scenario walkthrough

**Employee uploads Excel with 5 rows:**

| Row | Reference | Problem | Result |
|-----|-----------|---------|--------|
| 1 | 002H621 | None | ✅ Inserted |
| 2 | 002H621 | Duplicate of row 1 | ❌ Dropped |
| 3 | (empty) | No reference | ❌ Dropped |
| 4 | 999X999 | gender="INVALID" | ❌ Dropped (validation error) |
| 5 | 003L542 | bracelet=NEWCODE (unknown) | ✅ Inserted + popup for NEWCODE |

**Summary returned:** inserted=2, skipped=0, conflict=0, unknown_abbreviations=[NEWCODE]

---

# File 3: `monthly_report_parser.py`

## Two Excel formats in the real data

### Format A: POS Wide (January 2024) — **THIS IS OUR TEMPLATE**

```
Row 0:  Pierre Lannier | 1113 - Kingdom Mall... | | 1122 - Garnata Center...
Row 1:  Item Code      | Sales | Cls Stock       | Sales | Cls Stock
Row 2:  002H621        | 0     | 1               | 2     | 0
Row 3:  003L542        | 1     | 0               | 0     | 3
```

**How to read this:**
- Row 0: shop names (one per shop block)
- Row 1: under each shop, two columns — Sales then Cls Stock (closing stock)
- Row 2+: one product per row, numbers under each shop

### Format B: Time Series (Feb–Nov reports) — **LEGACY, NOT SUPPORTED FOR UPLOAD**

```
Row 0:  Pierre Lannier | 2024-01-01 | 2024-02-01 | 2024-03-01 | ...
Row 1:  002H621        | 0          | 0          | 1          | ...
```

**Problem:** No shop columns — just dates. We cannot know WHICH shop sold the product.

**Our behavior:** Log a message saying "use POS template" but do NOT insert (would need fake shop ID).

**Why not invent a fake shop?** That would corrupt analytics — sales would appear under a shop that doesn't exist.

## How format is detected

```python
def _is_pos_wide_format(row0):
    # Does row 0 contain something like "1113 - Kingdom Mall"?
    if header starts with 4 digits + " - ":
        return True  → POS wide
    else:
        return False → time series
```

## POS wide parsing — detailed walkthrough

**Given January report uploaded, products and shops already in DB:**

1. **Extract shops from row 0:**
   - `"1113 - Kingdom Mall - Riyadh - AlHomaidhi"` → Shop object (id=1113)
   - Remember column index for each shop

2. **Get report month from filename:**
   - `"1-Pierre Lannier January 2024 Sales Per POS.xlsx"` → `2024-01-01`

3. **For each data row (starting row 2):**
   - Column A = product reference
   - Under shop 1113: Sales column + Cls Stock column
   - Under shop 1122: Sales column + Cls Stock column

4. **For each shop + product combination:**
   - Sales > 0 AND product in DB AND shop in DB → add to `sold` list
   - Stock >= 0 AND product in DB AND shop in DB → add to `present` list

**Why require product AND shop in DB first?**  
Database has foreign keys — you cannot record a sale for a product that doesn't exist in the catalog.

**Example row processing:**

```
Row: 002H621 | shop 1113 sales=0 stock=1 | shop 1122 sales=2 stock=0

sold:    (002H621, 1113) → skip (sales=0)
         (002H621, 1122) → add sale qty=2 ✅

present: (002H621, 1113) → add stock=1 ✅
         (002H621, 1122) → add stock=0 ✅
```

## Helper methods explained

| Method | What it does | Example |
|--------|--------------|---------|
| `_normalize_reference` | Accept product codes, reject headers | "002H621" ✅, "Item Code" ❌ |
| `_month_from_filename` | Parse month from file name | "January 2024" → Jan 1 2024 |
| `_parse_month_value` | Convert Excel date to date object | 2024-01-01 00:00:00 → date(2024,1,1) |
| `_safe_int` | Convert cell to integer safely | "2" → 2, empty → None, "abc" → None |

---

# File 4: `pipeline.py` — The Conductor

**Think of an orchestra conductor** — doesn't play any instrument, but tells everyone when to play.

## `run_product_upload(conn, filepath)`

```
Step 1: Create AbbreviationResolver(conn)     ← load abbreviations from DB
Step 2: Create ProductCleaner(resolver)       ← prepare cleaner
Step 3: cleaner.load_uploaded_file(filepath)  ← read Excel → list of Products
Step 4: bulk_insert_products(conn, products)  ← save to database
Step 5: Return summary + logs + unknown abbrevs
```

**Why in this order?** Must load abbreviations BEFORE cleaning rows (so BRCLT expands correctly).

## `run_manual_products(conn, rows)`

Same as upload but rows come from HTML form (JSON) instead of Excel file.

**Why separate function?** No file to read — data is already a Python list of dicts.

## `run_monthly_report_upload(conn, filepath)`

```
Step 1: get_all_references(conn)           ← what's in product catalog?
Step 2: get_all_shop_ids(conn)             ← what shops exist?
Step 3: MonthlyReportParser(...).parse_file(filepath)
Step 4: bulk_insert_shops(conn, shops)     ← save any new shops from headers
Step 5: bulk_insert_sold_elements(...)     ← save sales
Step 6: bulk_insert_present_elements(...) ← save stock
```

**Why get references/shops first?** Parser skips rows that would violate foreign keys.

## `run_seed_from_data_folder(conn, data_dir)`

Development helper — loads all 4 reference files from `/data` folder at once.

---

## Correct upload order (IMPORTANT)

```
1. Upload PRODUCT CATALOG first     → fills products_information
2. Upload MONTHLY REPORT second     → fills shops, sold_elements, present_elements
```

**If reversed:** Sales rows reference products that don't exist → silently skipped → empty charts.

---

## What to tell your supervisor

> "The cleaning folder is our data quality gate. Product cleaner handles catalog Excel files with typo-tolerant headers and deduplication. Abbreviation resolver expands short codes using a database dictionary with case-insensitive lookup. Monthly parser reads POS sales reports and extracts shops from column headers. Pipeline connects everything in the correct order. Bad rows are dropped and logged — one error doesn't stop the entire upload."

---

## Practice exercise

Trace this upload through every cleaning file:

**File:** product_catalog_template.xlsx, one row:  
`350J621, MULTIPLES, LADIES, QUARTZ, SILVER, MECH/LEATH, SS/ROSE, 30, COFFRET`

1. `product_cleaner._normalize_columns` — headers OK?
2. `product_cleaner._process_row` — reference valid?
3. `abbreviation_resolver.expand("MECH/LEATH", "bracelet")` — result?
4. `Product.from_row` — Watch or Coffret?
5. `pipeline.run_product_upload` — what summary returns?

Answer: Coffret, bracelet="MESH/LEATHER STRAP", inserted=1
