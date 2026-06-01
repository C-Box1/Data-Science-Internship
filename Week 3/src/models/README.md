# `src/models/` — What Valid Data Looks Like (Beginner Guide)

> **Simple idea:** Before saving anything to the database, we first build a Python object that represents one product, one shop, or one abbreviation. These files define the **rules** those objects must follow.

---

## Why do we need "models" at all?

**Without models:** Excel data goes straight to the database. If someone types `gender = "LADY"` or `kind = "BRACELET"`, bad data gets stored forever.

**With models:** Python checks every field first. Bad data is rejected with a clear error **before** touching the database.

**Think of it like a bouncer at a club:**

- Excel row = person trying to enter
- Model validation = bouncer checking ID
- Database = inside the club

Only rows that pass validation get in.

---

## Why three separate files?

| File                | Represents             | Real-world thing                          |
| ------------------- | ---------------------- | ----------------------------------------- |
| `product.py`      | One watch or coffret   | A product in the catalog                  |
| `shop.py`         | One store/POS          | A shop in the monthly sales report header |
| `abbreviation.py` | One short code mapping | BRCLT means BRACELET                      |

We split them because a product and a shop have completely different fields and rules.

---

# File 1: `product.py`

## The three product types

```
Product (base class — shared rules)
   ├── Watch   (kind is always WATCH)
   └── Coffret (kind is always COFFRET — a gift set with watch + box)
```

**Why subclasses instead of one class?**
A Coffret has special behavior (`combo_contents()` splits the bracelet field on `/`). A Watch does not. Subclasses let us add Coffret-specific logic without complicating Watch code.

**Why a base `Product` class?**
Both Watch and Coffret share the same fields (reference, collection, gender, etc.). We write validation once in `Product`, not twice.

---

## Constants — the allowed values

```python
VALID_KINDS     = {"WATCH", "COFFRET"}
VALID_GENDERS   = {"LADIES", "GENTS", "UNISEX"}
VALID_MOVEMENTS = {"QUARTZ", "AUTOMATIC", "MECHANICAL"}
```

**Why hardcode these?**
The database has the same CHECK constraints. Python catches errors **earlier** with a friendly message instead of a cryptic database error.

**What happens if Excel has `gender = "WOMEN"`?**
`ValueError: Invalid gender 'WOMEN'. Must be one of {'LADIES', 'GENTS', 'UNISEX'}`
The row is dropped and logged in the cleaning report.

---

## Helper: `_normalize_str(value)`

**Problem:** Excel data is messy — `" ladies "`, `"Ladies"`, `"LADIES"` should all become the same thing.

**Solution:** Strip spaces, convert to uppercase.

| Excel cell value        | After `_normalize_str` |
| ----------------------- | ------------------------ |
| `"  ladies  "`        | `"LADIES"`             |
| `"GALIERA"`           | `"GALIERA"`            |
| empty cell /`None`    | `None` (means missing) |
| `"   "` (only spaces) | `None`                 |

**Why uppercase everything?**
So `"ss"`, `"SS"`, and `"Ss"` all match the same abbreviation lookup and database value.

---

## Helper: `_is_zero_placeholder(value)`

**Problem discovered in real data:** The file `missing_info.xlsx` uses `0` or `0.0` in cells that should be empty (missing dial, missing bracelet).

**Solution:** Treat zero as "no value".

| Cell value         | Treated as            |
| ------------------ | --------------------- |
| `0`              | missing (`None`)    |
| `0.0`            | missing (`None`)    |
| `"MESH"`         | real value `"MESH"` |
| `30` (case size) | real value `"30"`   |

**Why not treat all zeros as missing?**
Case size `0` is unlikely but sales quantity `0` in reports is valid (means no sales). This helper is only used for optional **text** fields in products.

---

## Class `Product` — field by field

| Field             | Required? | Example                  | Stored in DB?                |
| ----------------- | --------- | ------------------------ | ---------------------------- |
| reference         | YES       | `002H621`              | YES — unique ID             |
| kind              | YES       | `WATCH` or `COFFRET` | YES                          |
| collection        | YES       | `GALIERA`              | YES                          |
| gender            | YES       | `LADIES`               | YES                          |
| movement          | YES       | `QUARTZ`               | YES                          |
| dial              | no        | `SILVER` or `None`   | YES                          |
| strap             | no        | `MESH` or `None`     | YES (DB column: bracelet)   |
| color             | no        | `SS` or `None`       | YES                          |
| case_size         | no        | `30` or `21x28.4`    | YES — kept as **text** |
| date_of_creation  | no        | usually `None`         | YES                          |
| date_of_reception | no        | usually `None`         | YES                          |

**Understanding the "strap" field:**

- **For WATCH:** Single strap type (e.g., `MESH`, `LEATHER STRAP`)
- **For COFFRET:** Multiple straps in the gift set (e.g., `MESH/LEATHER STRAP`)
  - The `/` separates different strap types in the box
  - Example: `MESH/LEATHER STRAP/JEWELLERY STRAP` = 3 different straps included

**Why "strap" not "bracelet"?**
- Strap = the watch band you wear
- Bracelet can be confusing (sounds like the strap itself is a bracelet)
- COFFRET contains multiple straps, so the term "straps" is more accurate

**Database note:** The database column is still named `bracelet` for backward compatibility, but the Python code calls it `strap` for clarity.

**Hidden fields (NOT saved to database):**

| Field                | Purpose                                                               |
| -------------------- | --------------------------------------------------------------------- |
| `_is_partial`      | `True` if any optional field is missing — flags incomplete records |
| `_unknown_abbrevs` | List of short codes the system did not recognize — triggers UI popup |

**Why underscore prefix `_`?**
Python convention meaning "internal use only — not part of the public data."

---

## `_validate()` — automatic checking

**When does it run?** Immediately after the object is created (`__post_init__`).

**Why automatic?** You cannot accidentally create an invalid Product — validation always runs.

**Example failure:**

```python
Product(reference="", kind="WATCH", collection="GALIERA", gender="LADIES", movement="QUARTZ")
# → ValueError: reference cannot be empty
```

---

## `from_row(row, resolver)` — THE MOST IMPORTANT METHOD

**What it receives:** One row from Excel as a Python dictionary:

```python
{
  "reference": "002H621",
  "kind": "WATCH",
  "collection": "GALIERA",
  "gender": "LADIES",
  "movement": "QUARTZ",
  "bracelet": "BRCLT",
  "color": "pg",
  ...
}
```

**What it returns:** A `Watch` or `Coffret` object with clean, expanded values.

### Step-by-step (follow along with the code)

**Step 1 — Normalize text fields**

```python
ref = _normalize_str(row.get("reference"))  # "002h621" → "002H621"
```

**Why:** Consistent uppercase references in the database.

**Step 2 — Expand movement abbreviations**

```python
movement_resolved = resolver.resolve_token(movement, "movement")
# "AUTO" → "AUTOMATIC"
```

**Why:** Employees might type AUTO instead of AUTOMATIC.

**Step 3 — Handle optional fields (dial, bracelet, color, case_size)**

```python
def opt(key):
    val = row.get(key)
    if val is None or _is_zero_placeholder(val):
        return None
    return _normalize_str(val)
```

**Why the inner function?** Same logic for 4 fields — write once, reuse.

**Step 4 — Expand bracelet and color abbreviations**

```python
bracelet, br_unknown = resolver.expand(bracelet_raw, "bracelet")
color, col_unknown = resolver.expand(color_raw, "color")
```

**Example:** `"MECH/LEATH"` → `"MESH/LEATHER STRAP"`
**Why split on `/`?** Coffret products combine two bracelet types in one cell.

**Step 5 — Decide if record is partial**

```python
is_partial = any(f is None for f in [dial, bracelet, color, case_size])
```

**Why track this?** Supervisor may want a list of incomplete products to fill in later.

**Step 6 — Create Watch or Coffret**

```python
if kind_raw == "COFFRET":
    obj = Coffret(**kwargs)
else:
    obj = Watch(**kwargs)
```

**Why not always Product?** Subclasses enforce `kind` and add Coffret-specific methods.

### Real examples — input → output

| Excel input                            | What Python creates                               |
| -------------------------------------- | ------------------------------------------------- |
| kind=WATCH, bracelet=BRCLT, color=pg   | Watch, bracelet="BRACELET", color="PINK GOLD"     |
| kind=COFFRET, bracelet=MECH/LEATH      | Coffret, bracelet="MESH/LEATHER STRAP"            |
| kind=WATCH, dial=0.0                   | Watch, dial=None, _is_partial=True                |
| kind=STRAP                             | ValueError — row dropped                         |
| bracelet=UNKNOWN (not in abbrev table) | Watch, bracelet="UNKNOWN", _unknown_abbrevs=[...] |

---

## `to_db_dict()` — preparing for database insert

**Why a separate method?**
The Python object has extra fields (`_is_partial`) that the database does not need. `to_db_dict()` returns **only** the columns that match the SQL table.

```python
{
  "reference": "002H621",
  "kind": "WATCH",
  "collection": "GALIERA",
  ...
}
```

This dict goes directly into `repository.upsert_product()`.

**Why dict keys match column names?**
So SQL can use `%(reference)s` placeholders safely.

---

## Class `Watch`

```python
class Watch(Product):
    def __post_init__(self):
        self.kind = "WATCH"
        super().__post_init__()
```

**Why force `kind = "WATCH"`?**
Even if Excel says something else, a Watch object is always WATCH. Double safety.

---

## Class `Coffret`

```python
def combo_contents(self) -> list[str]:
    if not self.strap:
        return []
    return [p.strip() for p in self.strap.split("/")]
```

**What is a Coffret?**
A gift set = watch + presentation box (sometimes with multiple strap options).

**Example:** A coffret might include:
- 1 watch (the main product)
- 1 presentation box (the packaging)
- 2–3 different strap types to swap

**The strap field encodes what's in the box:**
- Single strap: `MESH` (one strap included)
- Combo: `MESH/LEATHER STRAP` (two straps in the box)
- Combo: `MESH/LEATHER STRAP/JEWELLERY STRAP` (three straps)

**`combo_contents()` method:**
Splits the strap field on `/` to extract individual items.

Example: strap = `"MESH/LEATHER STRAP"` → `["MESH", "LEATHER STRAP"]`

**Real data example:** `MECH/LEATH` in Excel → expanded to `MESH/LEATHER STRAP` → combo_contents returns `["MESH", "LEATHER STRAP"]`

**Why useful?**
- Inventory tracking: "How many MESH straps in stock across all coffrets?"
- Analysis: "Sales of coffrets with LEATHER straps"
- Reporting: Break down combo contents for detailed reports

---

# File 2: `shop.py`

## Where shop data comes from

Shops are **not** in a separate Excel catalog. They are extracted from **column headers** in monthly sales reports:

```
1113 - Kingdom Mall - Riyadh - AlHomaidhi - مركز المملكة
```

Each shop gets its own columns (Sales + Cls Stock) in the report.

---

## Special shop IDs

```python
INTERNAL_SHOP_IDS = {"0001", "0002"}   # warehouse — no city, no distributor
ONLINE_SHOP_IDS   = {"0006"}           # online store
```

**Why special handling?**
Main Store (0001) and Online Store (0006) don't have a city or distributor in the real reports. Forcing city=None prevents fake data.

---

## `from_header(header)` — parsing explained

**Input example:**

```
"1113 - Kingdom Mall - Riyadh - AlHomaidhi - مركز المملكة - الرياض"
```

**Step 1:** Must start with 4 digits (`1113`). Otherwise return `None` — it's not a shop header (might be "Item Code" or "Pierre Lannier").

**Step 2:** Split on `" - "`:

```
["1113", "Kingdom Mall", "Riyadh", "AlHomaidhi", "مركز المملكة", "الرياض"]
```

**Step 3:** Keep only parts with English/ASCII characters. Stop at first Arabic-only part:

```
["1113", "Kingdom Mall", "Riyadh", "AlHomaidhi"]
```

**Why ignore Arabic?**
We store English names in the database. Arabic is duplicate info for display in the original Excel only.

**Step 4:** Assign parts:

| Index | Field                      |
| ----- | -------------------------- |
| 0     | shop_id = "1113"           |
| 1     | mall_name = "Kingdom Mall" |
| 2     | city = "Riyadh"            |
| 3     | distributor = "AlHomaidhi" |

**Step 5:** Apply shop type (warehouse/online/retail)

### Examples table

| Header string                                 | shop_id         | mall_name    | city   | shop_type |
| --------------------------------------------- | --------------- | ------------ | ------ | --------- |
| `1113 - Kingdom Mall - Riyadh - AlHomaidhi` | 1113            | Kingdom Mall | Riyadh | retail    |
| `0001 - Main Store`                         | 0001            | Main Store   | None   | warehouse |
| `0006 - Online Store`                       | 0006            | Online Store | None   | online    |
| `Item Code`                                 | None (rejected) | —           | —     | —        |

---

# File 3: `abbreviation.py`

The simplest model — just a container for three values:

```python
@dataclass
class Abbreviation:
    abbreviation: str      # short code, e.g. "BRCLT"
    full_term: str           # full name, e.g. "BRACELET"
    field_category: str      # which field: "bracelet", "color", etc.
    abbrev_id: int | None    # database ID (None when creating new)
```

**Why a dataclass?**
Python automatically creates `__init__`, `__repr__`, etc. Less boilerplate code.

**`to_db_dict()` always uppercases:**

```python
{"abbreviation": "PG", "full_term": "PINK GOLD", "field_category": "color"}
```

**Why uppercase on save?** Lookup is case-insensitive — storing uppercase keeps database consistent.

---

## How models connect to the rest of the project

```
Excel row (messy dict)
       ↓
Product.from_row()  ← uses AbbreviationResolver
       ↓
Watch or Coffret object (clean, validated)
       ↓
product.to_db_dict()
       ↓
repository.upsert_product()  → PostgreSQL
```

---

## Questions your supervisor might ask

**Q: Why not validate in the database only?**
A: We validate in both places. Python gives friendly errors during upload. Database constraints are the last line of defense.

**Q: Why is case_size a string not a number?**
A: Real data has values like `"21x28.4"` and `"21X28,4"` — not plain numbers. String preserves the original format.

**Q: What is a dataclass?**
A: A Python shortcut that auto-generates boring code (constructor, string representation) from a list of fields.

**Q: What happens to a bad row?**
A: It never becomes a Product object. ProductCleaner logs it and continues with the next row.

---

## What to practice explaining

Pick one row from `combined_file.xlsx` and walk through:

1. Raw Excel values
2. What `_normalize_str` does to each field
3. What abbreviation expansion does
4. What the final Watch object looks like
5. What `to_db_dict()` sends to the database

That single example covers 80% of what models do.
