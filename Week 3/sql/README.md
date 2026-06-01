# `sql/` — Database Structure (Beginner Guide)

> **Simple idea:** These files create the PostgreSQL tables where all data lives permanently. Run them **once** when setting up the project.

---

## What is a database schema?

A **schema** is the blueprint — it defines what tables exist, what columns they have, and what rules data must follow.

**Think of it like designing filing cabinets before putting papers in:**
- Cabinet 1 (products) — one folder per product reference
- Cabinet 2 (shops) — one folder per store
- Cabinet 3 (sales) — one card per product+shop+month sold
- etc.

---

## How to run (do this during setup)

**Step 1 — Create empty database** (in pgAdmin or psql):
```sql
CREATE DATABASE consignment;
```

**Step 2 — Run schema:**
```bash
psql -U postgres -d consignment -f sql/schema.sql
```

**Step 3 — Run seed data:**
```bash
psql -U postgres -d consignment -f sql/seed_abbreviations.sql
```

**Order matters:** schema creates empty tables, seed fills abbreviations table.

---

## Why `DROP TABLE IF EXISTS` at the top?

```sql
DROP TABLE IF EXISTS sold_elements CASCADE;
DROP TABLE IF EXISTS present_elements CASCADE;
...
```

**Meaning:** Delete old tables if they exist, then recreate fresh.

**Why reverse order?** Child tables (sales) reference parent tables (products). Must delete children first.

**⚠️ WARNING:** Running schema.sql on a database with real data **deletes everything**. Only run on fresh setup or when intentionally resetting.

**Why CASCADE?** Automatically removes foreign key dependencies — one command cleans everything.

---

# Table 1: `products_information`

**What it stores:** Every watch and coffret in the catalog.

### Column guide

| Column | Type | Required | Example | Notes |
|--------|------|----------|---------|-------|
| products_id | auto number | auto | 1, 2, 3 | Internal ID, you rarely see this |
| reference | text | YES | 002H621 | **Main identifier** — unique |
| kind | text | YES | WATCH | Only WATCH or COFFRET allowed |
| collection | text | YES | GALIERA | Product line name |
| gender | text | YES | LADIES | LADIES, GENTS, or UNISEX |
| movement | text | YES | QUARTZ | QUARTZ, AUTOMATIC, MECHANICAL |
| dial | text | no | SILVER | Can be empty |
| bracelet | text | no | MESH | Can be empty |
| color | text | no | STAINLESS STEEL | Expanded from SS |
| case_size | text | no | 30 or 21x28.4 | **Text not number** — preserves ranges |
| date_of_creation | date | no | NULL | Rarely used |
| date_of_reception | date | no | NULL | Rarely used |

### Rules (constraints)

```sql
CHECK (kind IN ('WATCH', 'COFFRET'))
UNIQUE (reference)
```

**Why CHECK constraints?** Even if Python validation fails, database rejects invalid kind.

**Why UNIQUE on reference?** One row per product code — duplicates handled by upsert logic in Python.

### Example row

| reference | kind | collection | gender | movement | bracelet | color |
|-----------|------|------------|--------|----------|----------|-------|
| 002H621 | WATCH | GALIERA | LADIES | QUARTZ | MESH | STAINLESS STEEL |

---

# Table 2: `market_information`

**What it stores:** Shop / point-of-sale locations.

| Column | Example | Notes |
|--------|---------|-------|
| shop_id | 1113 | 4-digit code, primary key |
| mall_name | Kingdom Mall | From report header |
| city | Riyadh | NULL for warehouse/online |
| country | Saudi Arabia | Default |
| distributor | AlHomaidhi | NULL for warehouse/online |
| shop_type | retail | retail, warehouse, or online |

**Why shop_id as primary key?** It's stable — same shop always has same ID across monthly reports.

---

# Table 3: `present_elements`

**What it stores:** Closing stock — how many units in each shop at month end.

| Column | Meaning |
|--------|---------|
| item_reference | Which product (FK → products) |
| shop_id | Which shop (FK → shops) |
| report_month | Which month (stored as 2024-01-01 for January) |
| closing_stock | How many units in stock |

**Unique rule:** One record per (product + shop + month).

**Why foreign keys?**
```sql
FOREIGN KEY (item_reference) REFERENCES products_information (reference)
FOREIGN KEY (shop_id) REFERENCES market_information (shop_id)
```
Cannot record stock for product "FAKE123" if it's not in the catalog.

**Example:**
| item_reference | shop_id | report_month | closing_stock |
|----------------|---------|--------------|---------------|
| 002H621 | 1113 | 2024-01-01 | 5 |

Meaning: At end of January 2024, shop 1113 had 5 units of 002H621.

---

# Table 4: `sold_elements`

**What it stores:** Sales — how many units sold per product per shop per month.

| Column | Meaning |
|--------|---------|
| item_reference | Which product |
| shop_id | Which shop |
| sale_month | Which month |
| quantity_sold | How many sold |
| sale_source | 'monthly_report' (from Excel) or 'manual' (typed in) |

**Same unique rule:** One record per (product + shop + month).

**Example:**
| item_reference | shop_id | sale_month | quantity_sold |
|----------------|---------|------------|---------------|
| 002H621 | 1122 | 2024-01-01 | 2 |

Meaning: In January 2024, shop 1122 sold 2 units of 002H621.

---

# Table 5: `abbreviations`

**What it stores:** Short code → full name mappings.

| Column | Example |
|--------|---------|
| abbreviation | BRCLT |
| full_term | BRACELET |
| field_category | bracelet |
| created_at | auto timestamp |

**Design choice — many abbreviations, one full term:**
```
BRCLT  → BRACELET
BRACE  → BRACELET   (both valid, both in database)
```

**Why not one-to-one?** Real employees use different shortcuts for the same thing.

**Unique rule:** `(abbreviation, field_category)` — BRCLT can exist in bracelet category once.

**Case handling:** Stored uppercase. Python lookup is case-insensitive.

---

# Indexes (lines 107–137)

```sql
CREATE INDEX idx_sold_shop ON sold_elements (shop_id);
CREATE INDEX idx_sold_month ON sold_elements (sale_month);
```

**What is an index?** Like a book's index — helps PostgreSQL find rows faster.

**Why needed?** Reports page queries sales by shop and month constantly. Without indexes, queries slow down as data grows.

**Trade-off:** Indexes speed up reading, slightly slow down writing. Worth it for our use case.

---

# `seed_abbreviations.sql`

Inserts starter abbreviations. Safe to run multiple times:

```sql
ON CONFLICT (abbreviation, field_category) DO NOTHING
```

**Meaning:** If BRCLT already exists, skip — don't error.

### Full seed list

| Abbrev | Full Term | Category |
|--------|-----------|----------|
| BRCLT, BRACE | BRACELET | bracelet |
| LEATH | LEATHER STRAP | bracelet |
| MECH | MESH | bracelet |
| JEW | JEWELLERY STRAP | bracelet |
| YG | YELLOW GOLD | color |
| RG | ROSE GOLD | color |
| PG | PINK GOLD | color |
| SS | STAINLESS STEEL | color |
| BK | BLACK | color |
| WH | WHITE | color |
| AUTO | AUTOMATIC | movement |

**Why seed defaults?** System works immediately after setup — employee doesn't need to define common codes first.

---

## How tables relate (visual)

```
products_information
    ↑ FK              ↑ FK
    │                 │
present_elements   sold_elements
    ↑ FK              ↑ FK
    └────────┬────────┘
             │
    market_information

abbreviations (standalone — no connections)
```

**Reading this diagram:**
- Sales and stock both point to a product AND a shop
- Abbreviations table is independent — used during cleaning, not linked by foreign key

---

## Common scenarios

| Employee action | Tables affected |
|-----------------|-----------------|
| Upload product catalog | products_information |
| Upload monthly report | market_information + sold_elements + present_elements |
| Add abbreviation on website | abbreviations |
| View top sellers chart | sold_elements JOIN products JOIN shops |

| Error | Cause | Solution |
|-------|-------|----------|
| Foreign key violation | Sales before products | Upload catalog first |
| Unique violation on reference | Bug — upsert should prevent | Check repository.py |
| CHECK constraint on kind | Invalid kind in data | Fix Excel row |

---

## Why VARCHAR for case_size not INTEGER?

Real data: `"21x28.4"`, `"21X28,4"`, `"30"`, `"32.5"`

Numbers can't store `"21x28.4"`. Text preserves exact employee input.

---

## What to tell your supervisor

> "The database has five tables. Products and shops are master data. Sold and present elements are monthly transactional records with foreign keys ensuring every sale references a real product and shop. Abbreviations support expandable short codes. CHECK constraints and UNIQUE constraints enforce data integrity at the database level as a safety net behind Python validation."
