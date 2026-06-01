# `src/analytics/` — Sales Reports & Charts (Beginner Guide)

> **Simple idea:** After sales data is in the database, employees want to see charts — top sellers, sales by shop, sales by color, etc. This folder runs SQL queries to get numbers, then builds charts.

---

## Why analytics is separate from cleaning

| cleaning/ | analytics/ |
|-----------|--------------|
| Gets data **into** the database | Gets data **out** for reports |
| Runs during upload | Runs when employee clicks a chart button |
| Writes (INSERT) | Reads (SELECT) |

**Why not query inside app.py?**  
SQL for charts is complex. Keeping it in `queries.py` keeps `app.py` readable and lets you test queries independently.

---

## Why not read from Excel files for charts?

**Old way (Excel analysis file):** Charts in `Watchs_Analysis_November 2024.xlsx` were built manually from static data.

**Our way:** Charts read **live from PostgreSQL** — always reflect latest uploads.

**Benefits:**
- Upload new January data → charts update immediately
- Filters actually work (shop, month, kind)
- No manual Excel refresh needed

---

## The two files

| File | Job | Output |
|------|-----|--------|
| `queries.py` | SQL questions ("top 20 products?") | List of dictionaries with numbers |
| `charts.py` | Turn numbers into bar chart | Plotly JSON for browser |

**Why two steps?** Separation — you could export the table without a chart, or change chart style without changing SQL.

---

# File 1: `queries.py`

## How filters work (read this carefully)

Employee picks filters on Reports page:
- Shop: Kingdom Mall (1113)
- Kind: WATCH only
- Month: January to March

These become SQL `WHERE` conditions:

```sql
WHERE s.shop_id = '1113'
  AND p.kind = 'WATCH'
  AND s.sale_month >= '2024-01-01'
  AND s.sale_month <= '2024-03-01'
```

**Function `_build_filters()`** builds this dynamically:
- If employee picks nothing → no WHERE clause → show ALL data
- If employee picks shop only → filter by shop only

**Why dynamic?** One query function handles every filter combination — no need for 50 separate functions.

## The three main charts (match Excel analysis sheets)

### 1. `top_sellout_references` → "Top 20 Sellout references"

**Question it answers:** Which product codes sold the most total units?

**SQL logic (plain English):**
1. Look at all sales records
2. Join with product table (to apply kind/collection filters)
3. Join with shop table (to apply city filter)
4. Group by product reference
5. Sum quantity_sold
6. Sort highest first
7. Take top 20

**Returns:**
```python
[
  {"item_code": "036P621", "grand_total": 11},
  {"item_code": "036P651", "grand_total": 9},
  ...
]
```

**Real scenario:** Employee filters kind=WATCH → only watch sales counted, coffret sales excluded.

### 2. `top_pos` → "Top 20 POS in KSA"

**Question it answers:** Which stores sold the most?

**Returns:**
```python
[
  {"store_name": "Kingdom Mall", "total_sold": 45},
  {"store_name": "Garnata Center", "total_sold": 38},
]
```

**Why join products table?** So kind/collection filters still work — "top shops for WATCH sales only."

### 3. `sellout_by_city` → "Total Sellout by City"

**Question it answers:** How much sold per city/region?

**Returns:**
```python
[
  {"shop_id": "1113", "total_sold": 45, "region": "Riyadh"},
  {"shop_id": "1201", "total_sold": 30, "region": "Jeddah"},
]
```

**Note:** `region` is actually the shop's city name from `market_information`.

## Attribute breakdown charts

**Excel sheets:** Bracelet Analysis, Color Analysis, Collection Analysis, Gender Analysis, Kind Analysis, Movement Analysis, Dial Analysis, Case Size Analysis

**One function handles all eight:** `attribute_breakdown(conn, attribute, **filters)`

**Question it answers:** For sales matching filters, how many sold per bracelet type? per color? etc.

**Example — Color Analysis, no filters:**
```python
[
  {"label": "STAINLESS STEEL", "total_sold": 120},
  {"label": "ROSE GOLD", "total_sold": 85},
  {"label": "Unknown", "total_sold": 5},   ← products with no color filled in
]
```

**Why `COALESCE(field, 'Unknown')`?** Products with empty color still appear in chart instead of being invisible.

## `shop_detail(conn, shop_id)` — per-shop breakdown

Matches individual shop sheets in the analysis Excel (e.g., "1113 - Kingdom Mall").

Returns every product sold at that shop with full product details + total sold.

## Registry at bottom of file

```python
CHART_HANDLERS = {
    "top_sellout_references": top_sellout_references,
    "top_pos": top_pos,
    "sellout_by_city": sellout_by_city,
}
ATTRIBUTE_CHARTS = ["bracelet", "color", "collection", "gender", "kind", "movement", "dial", "case_size"]
```

**Why a registry?** `app.py` can loop through chart names without hardcoding each one. Adding a new chart = add one function + one registry entry.

---

# File 2: `charts.py`

## Why Plotly?

| Option | Pros | Cons |
|--------|------|------|
| Matplotlib | Simple Python charts | Static images, not interactive |
| **Plotly** | Interactive (hover, zoom), works in browser | Slightly more setup |
| Excel charts | Familiar | Not live, not on website |

Plotly charts render in the browser — employee can hover to see exact numbers.

## `bar_chart(title, labels, values, horizontal)`

Creates a bar chart and returns **JSON string** (not an image file).

**Why JSON?** JavaScript in the browser reads JSON and draws the chart using `Plotly.newPlot()`.

**Vertical vs horizontal:**
- ≤8 items → vertical bars (labels on x-axis)
- \>8 items → horizontal bars (easier to read long product names)

## `chart_from_rows(title, rows, label_key, value_key)`

Convenience function:
1. Pull labels from rows (e.g., `item_code` column)
2. Pull values from rows (e.g., `grand_total` column)
3. Decide vertical or horizontal
4. Call `bar_chart()`

**Example:**
```python
rows = [{"item_code": "036P621", "grand_total": 11}]
chart_from_rows("Top Sellout", rows, "item_code", "grand_total")
# → JSON that browser turns into a bar chart
```

---

## Full chart request — step by step

**Employee action:** Opens Reports page, selects shop 1113, clicks "Top Sellout References"

```
1. analytics.js reads filter dropdowns
2. JavaScript: GET /api/analytics/top_sellout_references?shop_id=1113
3. app.py receives request, calls top_sellout_references(conn, shop_id="1113")
4. queries.py runs SQL with WHERE s.shop_id = '1113'
5. Returns rows: [{item_code: "036P621", grand_total: 11}, ...]
6. charts.py converts rows to Plotly JSON
7. app.py sends: {chart: "{...json...}", rows: [...]}
8. analytics.js calls Plotly.newPlot() → chart appears
9. analytics.js builds HTML table below chart
```

**Total time:** Under 1 second for typical data.

---

## New feature: Pie Charts with Top-N Filtering

### Why pie charts?

Bar charts show **counts** (e.g., "LADIES: 100 watches sold").

Pie charts show **percentages** (e.g., "LADIES: 45% of all watches").

**When to use each:**
- Bar chart: "Which products sold the most?" (focus on rankings)
- Pie chart: "What % is each gender?" (focus on distribution)

### Pie chart availability

Three new pie chart buttons:
- **Sales by Gender (Pie)** — What % are LADIES / GENTS / UNISEX?
- **Sales by Kind (Pie)** — What % are WATCH vs COFFRET (gift sets)?
- **Sales by Movement (Pie)** — What % are QUARTZ / AUTOMATIC / MECHANICAL?

All three support the same filters as bar charts (shop, city, month range, etc.).

### Top-N Filtering (limiting items in pie chart)

**Problem:** If you have many categories, a pie chart becomes unreadable:
- 50 tiny slices = useless
- Hard to see patterns
- Cluttered labels

**Solution:** Show only the top N items by sales percentage, group the rest as "Other".

**How it works:**
```
Employee selects:
  - Chart: "Sales by Movement"
  - Filters: Shop = Kingdom Mall
  - Top items: 5

Result:
  - Top 5 movement types shown as slices
  - All other movements grouped as "Other"
  - Only top sellers visible
  - Employee sees patterns clearly
```

### Pie chart API & parameters

**Request:**
```
GET /api/analytics/pie_gender?shop_id=1113&top_items=5
GET /api/analytics/pie_kind?top_items=10
GET /api/analytics/pie_movement  ← no top_items = show all
```

**Response:**
```json
{
  "chart": "{...plotly json...}",
  "rows": [...all data...],
  "top_items": 5
}
```

### Pie chart display

Each slice shows:
- **Label:** Category name (e.g., "LADIES")
- **Count:** Number of items (e.g., "450 units")
- **Percentage:** % of total (e.g., "45.2%")

Hover over a slice to see the full details.

**Example reading a pie chart:**
- Chart title: "Sales by Gender"
- One slice labeled: "LADIES\n1000 (45.1%)"
- Meaning: 1000 watches are LADIES watches, representing 45.1% of all watches sold

### Charts.py functions for pie charts

**New function: `pie_chart(title, labels, values, show_percentages=True, max_items=None)`**

Builds a pie chart with optional top-N filtering.

```python
def pie_chart(title, labels, values, show_percentages=True, max_items=5):
    # 1. Sort items by value descending
    # 2. If more items than max_items, keep only top max_items
    # 3. Group remaining items as "Other"
    # 4. Calculate percentages for all items
    # 5. Return Plotly pie chart JSON
```

**Parameters:**
- `title` — Chart title
- `labels` — Category names
- `values` — Counts per category
- `show_percentages` — Include % in chart labels (default: True)
- `max_items` — Max slices to show (None = show all)

**New function: `pie_chart_from_rows(title, rows, label_key, value_key, max_items=None)`**

Convenience function like `chart_from_rows()` but for pie charts.

```python
pie_chart_from_rows("Sales by Gender", rows, "label", "total_sold", max_items=5)
```

### Handling zero values

**How zero values are handled:**

If a category has **0 sales**:
- In bar charts → empty bar (still appears)
- In pie charts → 0% → excluded (no slice created)
  - Reason: A 0% slice adds no information and wastes space

**Example:**
```
Data: LADIES (100), GENTS (50), UNISEX (0)

Bar chart: Three bars (UNISEX bar is empty)
Pie chart: Two slices (UNISEX not shown because 0%)
```

This avoids confusing employees with empty pie slices.

---

## Full chart request — step by step

**Employee action:** Opens Reports page, selects shop 1113, clicks "Top Sellout References"

```
1. analytics.js reads filter dropdowns
2. JavaScript: GET /api/analytics/top_sellout_references?shop_id=1113
3. app.py receives request, calls top_sellout_references(conn, shop_id="1113")
4. queries.py runs SQL with WHERE s.shop_id = '1113'
5. Returns rows: [{item_code: "036P621", grand_total: 11}, ...]
6. charts.py converts rows to Plotly JSON
7. app.py sends: {chart: "{...json...}", rows: [...]}
8. analytics.js calls Plotly.newPlot() → chart appears
9. analytics.js builds HTML table below chart
```

**Total time:** Under 1 second for typical data.

---

## Scenarios and what employee sees

| Scenario | What happens |
|----------|--------------|
| No data uploaded yet | Empty chart area + "No data for selected filters" |
| Data exists, no filters | Chart shows all sales across all shops |
| Filter shop that doesn't exist in DB | Impossible — dropdown only shows existing shops |
| Filter month with no sales | Empty result — not an error |
| 100 products, top 20 chart | Shows only top 20 (limit=20) |

---

## What to tell your supervisor

> "Analytics reads live sales data from PostgreSQL — never from static Excel files. Each chart button maps to a SQL query inspired by the original Watchs_Analysis workbook. Filters are built dynamically and only offer values already in the database. Plotly renders interactive bar charts in the browser. The same data appears as a table below each chart for exact numbers."

---

## Chart → Excel sheet mapping (for presentation)

| Website button | Original Excel sheet | Chart type |
|----------------|----------------------|------------|
| Top Sellout References | Top 20 Sellout references | Bar |
| Top POS in KSA | Top 20 POS in KSA | Bar |
| Total Sellout by City | Total Sellout by City | Bar |
| Bracelet Analysis | Bracelet Analysis | Bar |
| Color Analysis | Color Analysis | Bar |
| Collection Analysis | Collection Analysis | Bar |
| Gender Analysis | Gender Analysis | Bar |
| Kind Analysis | Kind Analysis | Bar |
| Movement Analysis | Movement Analysis | Bar |
| Dial Analysis | Dial Analysis | Bar |
| Case Size Analysis | Case Size Analysis | Bar |
| Sales by Gender (Pie) | Gender Analysis | **Pie** |
| Sales by Kind (Pie) | Kind Analysis | **Pie** |
| Sales by Movement (Pie) | Movement Analysis | **Pie** |

**New pie charts offer:** Percentage view + top-N filtering for clarity when viewing many categories.
