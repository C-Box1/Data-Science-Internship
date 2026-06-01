# `src/tests/` — Automatic Quality Checks (Beginner Guide)

> **Simple idea:** Tests are small programs that verify our code still works correctly. Run them after any change to catch mistakes early.

---

## Why bother with tests?

**Without tests:** You change abbreviation code → upload breaks → employee finds out → embarrassing.

**With tests:** You change code → run tests → see immediately if something broke → fix before demo.

**Think of tests like a checklist before a presentation:**
- Does BRCLT still expand to BRACELET? ✓
- Does duplicate reference get dropped? ✓
- Does shop header parsing work? ✓

---

## How to run

```bash
uv run pytest src/tests/test_all.py -v
```

**Expected output:** `23 passed in ~0.4 seconds`

**Reading results:**
```
PASSED  → test_name ... PASSED   ✅ this works
FAILED  → test_name ... FAILED   ❌ something broke — read error message
ERROR   → test_name ... ERROR    ❌ code crashed — read traceback
```

---

## Why one file `test_all.py`?

For a project this size, one organized file is easier for beginners than 10 separate test files. Tests are grouped by class — each class tests one module.

---

## How tests work without PostgreSQL

**Problem:** Database tests normally need PostgreSQL running.

**Solution:** `MagicMock` — a fake object that **pretends** to be the database.

```python
mock_conn = MagicMock()
mock_cursor = MagicMock()
mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
```

**Plain English:** "When code asks for a database cursor, give it a fake one that returns whatever we tell it to."

**Why this matters:** Anyone can run all 23 tests on any computer — no setup required.

---

# Test Class 1: `TestProduct`

Tests the product model (`models/product.py`).

### Helper methods

```python
def _valid_watch_row(self):
    return {"reference": "002H621", "kind": "WATCH", ...}

def _resolver(self):
    return AbbreviationResolver(alias_maps=DEFAULT_ALIASES)
```

**Why helpers?** Avoid copying the same valid row dict into every test.

### Key tests explained

| Test | What it proves | Why it matters |
|------|----------------|----------------|
| `test_normalize_str_strips_whitespace` | `"  hello  "` → `"HELLO"` | Excel has messy spacing |
| `test_zero_dial_becomes_none` | dial=0.0 → None | missing_info.xlsx uses zeros |
| `test_brclt_expands_to_bracelet` | BRCLT → BRACELET | Core abbreviation feature |
| `test_pg_expands_to_pink_gold_case_insensitive` | pg → PINK GOLD | Case insensitivity |
| `test_combo_abbrev_expansion` | MECH/LEATH → MESH/LEATHER STRAP | Coffret combo fields |
| `test_invalid_kind_raises` | kind=STRAP → ValueError | Bad data rejected |

**Example — what `test_brclt_expands_to_bracelet` actually does:**
```python
row = valid_watch_row()
row["bracelet"] = "BRCLT"
product = Product.from_row(row, resolver=resolver)
assert product.bracelet == "BRACELET"  # fails test if wrong
```

If someone accidentally breaks abbreviation expansion, this test fails immediately.

---

# Test Class 2: `TestAbbreviationResolver`

| Test | Proves |
|------|--------|
| `test_case_insensitive_lookup` | brclt, BRCLT, PG, pg all work |
| `test_expand_combo` | MECH/LEATH expands both parts |

---

# Test Class 3: `TestShop`

| Test | Input | Expected |
|------|-------|----------|
| `test_standard_header_parsed` | Kingdom Mall header | shop_id=1113, city=Riyadh |
| `test_main_store_is_warehouse` | 0001 - Main Store | type=warehouse |
| `test_invalid_header_returns_none` | "Item Code" | None (not a shop) |

**Why test "Item Code"?** Row 1 of reports says "Item Code" — must NOT be parsed as a shop.

---

# Test Class 4: `TestProductCleaner`

Uses **fake data** — no real Excel files needed.

Creates pandas `Series` objects to simulate Excel rows:

```python
row = pd.Series({
    "reference": "002H621",
    "kind": "WATCH",
    "collection": "GALIERA",
    "gender": "LADIES",
    "movement": "QUARTZ",
})
result = cleaner._process_row(row, "test.xlsx", 2)
```

| Test | Proves |
|------|--------|
| `test_normalize_columns_fixes_mouvement_typo` | MOUVEMENT → movement |
| `test_valid_row_returns_product` | Good row → Product object |
| `test_duplicate_reference_is_dropped` | Second same ref → None |

---

# Test Class 5: `TestMonthlyReportParser`

| Test | Proves |
|------|--------|
| `test_normalize_reference_rejects_headers` | "Item Code" rejected |
| `test_month_from_filename` | "January 2024" in filename → month=1 |

---

# Test Class 6: `TestRepository`

Uses MagicMock to fake database responses.

**Example — `test_upsert_product_inserts_new_record`:**
```python
cur.fetchone.return_value = None  # pretend product doesn't exist in DB
result = upsert_product(conn, watch)
assert result == "inserted"
conn.commit.assert_called_once()  # verify commit was called
```

**What this verifies:** When DB has no existing product, code inserts and commits.

**Example — `test_load_abbreviation_maps`:**
```python
cur.fetchall.return_value = [("BRCLT", "BRACELET", "bracelet"), ("PG", "PINK GOLD", "color")]
maps = load_abbreviation_maps(conn)
assert maps["color"]["PG"] == "PINK GOLD"
```

---

## When should YOU run tests?

| Situation | Run tests? |
|-----------|------------|
| Before supervisor demo | YES |
| After changing any Python file | YES |
| After changing SQL schema | YES |
| Just reading documentation | No |

---

## What to tell your supervisor

> "We have 23 automated tests covering product validation, abbreviation expansion, shop parsing, Excel cleaning, and database logic. Tests use mocks so they run without PostgreSQL in under half a second. They catch regressions — if a change breaks abbreviation expansion or duplicate detection, we know immediately."

---

## If a test fails

1. Read the FAILED message — it shows expected vs actual
2. Open the test name — find which class/file is affected
3. Open that file's README for context
4. Fix the code OR fix the test (if requirement changed)
5. Re-run until all 23 pass
