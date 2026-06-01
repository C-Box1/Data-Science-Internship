# `templates/` — Website Pages (HTML) (Beginner Guide)

> **Simple idea:** These are the web pages employees see in their browser. They are **HTML files with Jinja2 templates** — Flask fills in dynamic parts before sending to the browser.

---

## What is HTML vs what is Python?

| HTML templates (this folder) | Python (src/ folder) |
|------------------------------|----------------------|
| What employee **sees** | What **runs** on the server |
| Buttons, forms, text | Database, cleaning, logic |
| Static structure | Dynamic data processing |

**How they connect:** Flask function in `app.py` calls `render_template("index.html")` → fills in variables → sends finished HTML to browser.

---

## What is Jinja2?

A way to put **placeholders** in HTML:

```html
<h2>{{ t.label }}</h2>           <!-- replaced with real label -->
{% for t in templates %}         <!-- loop over list -->
  ...
{% endfor %}
```

**Why not hardcode everything?** Template list comes from Python — if we add a 4th template, the page updates automatically.

---

## How all pages share the same look: `base.html`

Every page starts with:
```html
{% extends "base.html" %}
```

**Meaning:** "Use base.html as the wrapper, insert my content in the middle."

**Why this pattern?** Navigation bar written once — appears on every page. Change header once, all pages update.

### `base.html` structure

```
┌─────────────────────────────────────┐
│  HEADER: Logo + navigation links    │
├─────────────────────────────────────┤
│                                     │
│  {% block content %}                │
│  (each page fills this area)        │
│                                     │
├─────────────────────────────────────┤
│  FOOTER: Project name               │
└─────────────────────────────────────┘
  + app.js loaded on every page
  + page-specific scripts optional
```

---

# Page 1: `index.html` — Home

**URL:** `http://127.0.0.1:5000/`

**Purpose:** Welcome screen — orients non-technical employees.

**Content:**
1. Short explanation of what the tool does
2. Four big clickable cards:
   - Download Templates
   - Upload Data
   - Add Products
   - View Reports
3. Database status check (green ✅ or red ❌)

**JavaScript at bottom:**
```javascript
fetch('/api/health')
```
Calls backend to check if PostgreSQL is connected. Updates message on page.

**Why show database status?** Employee knows immediately if something is wrong before trying to upload.

**Scenario — database down:** Employee sees red message, knows to contact IT / check PostgreSQL — not "upload failed mysteriously."

---

# Page 2: `templates_page.html` — Download Excel files

**URL:** `/templates`

**What Flask sends to this page:**
```python
templates = [
  {"key": "product_catalog", "label": "Product Catalog", "file": "product_catalog_template.xlsx"},
  {"key": "monthly_report", "label": "Monthly Sales & Stock Report", "file": "..."},
  {"key": "bulk_entry", "label": "Bulk Entry (up to 10 products)", "file": "..."},
]
```

**Jinja loop creates 3 download boxes** — one per template.

**Download link:** `/download/product_catalog` → Flask sends Excel file.

**Instructions section:** Step-by-step for employees who've never used the system.

**Why numbered steps?** Non-technical users need explicit sequence: download → fill → save → upload.

---

# Page 3: `upload.html` — Upload files

**URL:** `/upload`

**Two independent upload sections:**

| Section | File input ID | Button ID | API endpoint |
|---------|---------------|-----------|--------------|
| Product Catalog | `#product-file` | `#upload-products-btn` | POST /api/upload/products |
| Monthly Report | `#report-file` | `#upload-report-btn` | POST /api/upload/monthly-report |

**Why two sections on one page?** Related task (getting data into system) but different file formats.

### Abbreviation popup (modal)

Hidden `<div id="abbrev-prompt">` — shown by JavaScript when upload finds unknown codes.

**Employee sees:**
```
Unknown abbreviation detected
"XYZ" found in color (reference 002H621). What does it mean?

[Dropdown: select existing term ▼]
[Text box: or enter new full term]
[Save abbreviation]  [Not an abbreviation]
```

**Why modal popup?** Handle unknown codes immediately while employee still has context — don't make them navigate to another page.

**Handled by:** `static/js/upload.js` (see static/README.md)

---

# Page 4: `add_product.html` — Type products manually

**URL:** `/add-product`

**For employees adding 1–10 products without Excel.**

**Flask provides dropdown options:**
```python
genders = ["LADIES", "GENTS", "UNISEX"]
movements = ["QUARTZ", "AUTOMATIC", "MECHANICAL"]
kinds = ["WATCH", "COFFRET"]
max_rows = 10
```

**Why dropdowns not free text for gender/movement/kind?** Prevents typos — "LADY" or "QUARTZ " would fail validation.

**Form fields match product template columns** — same data, different input method.

**"Add another product" button:** Clones the form row (JavaScript in `add_product.js`). Stops at 10.

**Submit:** JavaScript collects all rows → POST `/api/products/manual` as JSON.

---

# Page 5: `analytics.html` — Reports & charts

**URL:** `/analytics`

**Loads Plotly from CDN** (internet library for interactive charts):
```html
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
```

**Why CDN?** Don't bundle Plotly in our project — load from internet. Works offline only if cached.

**Filter section:** 6 dropdowns — populated by JavaScript from `/api/filters`.

**Chart buttons:** Generated from Flask list — 11 buttons total (3 main charts + 8 attribute analyses).

**Display areas:**
- `#chart-area` — Plotly draws chart here
- `#table-area` — HTML table with exact numbers below chart

**Why table AND chart?** Chart for quick visual understanding. Table for exact numbers (supervisor may ask "exactly how many?").

---

# Page 6: `abbreviations.html` — Abbreviation dictionary

**URL:** `/abbreviations`

**Two sections:**
1. **Add form** — abbreviation, full term, field category
2. **Table** — loaded dynamically from API (not hardcoded in HTML)

**Why load table via JavaScript?** Table updates when new abbreviations added — no page reload needed.

**Explains case insensitivity:** "brclt = BRCLT = BRACELET" — sets employee expectations.

---

## How a page loads — full sequence

**Employee clicks "Upload Data" in navigation:**

```
1. Browser: GET /upload
2. Flask: upload_page() function runs
3. Flask: render_template("upload.html")
4. Jinja: wraps upload.html inside base.html
5. Flask: sends complete HTML to browser
6. Browser: displays page, loads style.css + upload.js
7. upload.js: attaches click handlers to upload buttons
8. Employee selects file, clicks Upload
9. upload.js: POST file to /api/upload/products (no page reload)
10. upload.js: updates result box with success/error message
```

**Why no page reload on upload?** Faster, smoother experience. Employee stays on same page, sees result immediately.

---

## Why English only?

Business requirement — all employees use English interface. Labels, instructions, error messages all in English.

---

## What to tell your supervisor

> "The templates folder contains six HTML pages built on a shared layout. Pages are designed for non-technical employees — large buttons, clear labels, step-by-step instructions. Dynamic data comes from Flask variables or JavaScript API calls. Upload and chart pages work without full page reloads for a smoother experience."

---

## Which page to demo for each feature

| Feature to demo | Open this page |
|-----------------|----------------|
| Download Excel template | /templates |
| Upload product file | /upload |
| Manual product entry | /add-product |
| Sales charts | /analytics |
| Manage abbreviations | /abbreviations |
| System overview | / (home) |
