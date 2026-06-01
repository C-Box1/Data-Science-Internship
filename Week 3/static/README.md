# `static/` — Website Styling & Interactivity (Beginner Guide)

> **Simple idea:** This folder makes the website **look good** (CSS) and **respond to clicks** (JavaScript). Employees never see these files directly — the browser loads them automatically.

---

## What is static vs dynamic?

| Static files (this folder) | Dynamic (Flask/Python) |
|---------------------------|------------------------|
| Same for every user | Changes per request |
| CSS, JavaScript | HTML with data, API responses |
| Browser caches them | Generated fresh each time |

**URL pattern:** `http://127.0.0.1:5000/static/css/style.css`

Flask serves these automatically from the `static/` folder.

---

## Folder structure

```
static/
├── css/
│   └── style.css      ← all visual styling
└── js/
    ├── app.js         ← shared helper functions
    ├── upload.js      ← upload page behavior
    ├── add_product.js ← manual entry form
    ├── analytics.js   ← charts page
    └── abbreviations.js ← abbreviations page
```

**Why separate JS files per page?** Each page only loads what it needs. Upload page doesn't load chart code.

---

# CSS: `style.css`

## Design goals for non-technical employees

1. **Big clickable areas** — cards, buttons easy to hit
2. **Clear color coding** — green = success, red = error, navy = actions
3. **Readable fonts** — Segoe UI, adequate spacing
4. **No jargon in UI** — labels say "Upload Products" not "POST /api/upload"

## CSS Variables (lines 3–13)

```css
:root {
  --navy: #1f4e79;
  --bg: #f4f6f9;
  --success: #1b7f4a;
  --error: #b42318;
}
```

**What is `:root`?** Global settings for the whole site.

**Why variables?** Change `--navy` once → all buttons and headers update. Consistent branding.

## Important classes explained

| CSS class | Visual effect | Used where |
|-----------|---------------|------------|
| `.site-header` | Dark blue top bar | Every page |
| `.card` | White box with shadow | Content sections |
| `.card-grid` | Responsive grid of cards | Home page 4 buttons |
| `.btn-primary` | Navy filled button | Main actions (Upload, Save) |
| `.btn-secondary` | Gray button | Secondary actions (Add row) |
| `.btn-chart` | Outlined button | Chart selection on Reports page |
| `.form-grid` | Multi-column form layout | All input forms |
| `.result-box` | Colored message area | Upload success/error |
| `.result-box.success` | Green background | "Done! 40 inserted" |
| `.result-box.error` | Red background | "No file uploaded" |
| `.modal` | Dark overlay + popup | Abbreviation prompt |
| `.hidden` | `display: none` | Hide elements until needed |
| `.chart-area` | Min height 420px | Space for Plotly chart |

## Why cards on home page?

```css
.card-grid .card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(31, 78, 121, 0.14);
}
```

Subtle lift on hover — signals "this is clickable" without being flashy.

---

# JavaScript files

## What is JavaScript's job here?

Python (Flask) runs on **your computer (server)**. JavaScript runs in the **employee's browser**.

JavaScript handles:
- File uploads without page reload
- Showing/hiding popup modals
- Drawing charts
- Filling dropdown menus from API data

**Communication pattern:**
```
JavaScript  ──fetch()──►  Flask API  ──►  Python/Database
JavaScript  ◄──JSON────  Flask API  ◄──  Results
JavaScript updates the page
```

---

## `app.js` — Shared helpers (every page)

### `showMessage(el, html, isError)`

Updates a div with a message and applies green or red styling.

```javascript
showMessage(resultEl, '<strong>Done!</strong> 40 inserted', false);
// → green success box

showMessage(resultEl, 'Please choose a file first.', true);
// → red error box
```

**Why a helper?** Same message styling on upload page, manual entry page — write once.

### `formatSummary(summary)`

Turns `{inserted: 40, skipped: 3, conflict: 2}` into readable text.

**Why?** Backend sends structured data. Employee reads plain English sentence.

### `postJSON(url, body)`

Sends POST request with JSON body. Used by forms that don't upload files.

**Why separate from file upload?** File upload uses `FormData`, not JSON.

---

## `upload.js` — Upload page

### Main function: `uploadFile(endpoint, fileInput, resultEl)`

**Step-by-step when employee clicks "Upload Products":**

```
1. Get file from <input type="file">
2. If no file selected → show red error "Please choose a file first"
3. Show "Uploading and cleaning…" message
4. Create FormData, append file
5. fetch('/api/upload/products', {method: 'POST', body: formData})
6. Wait for JSON response
7. If error → show red message
8. If success → show green message with counts
9. If unknown_abbreviations in response → show popup modal
```

**Why FormData?** Standard way to send files to a web server. Browser handles encoding.

### Abbreviation popup queue

```javascript
let pendingAbbrevQueue = [];
```

**Scenario — upload finds 2 unknown codes:**

```
Upload completes successfully
  → pendingAbbrevQueue = [{token: "XYZ", ...}, {token: "ABC", ...}]
  → show modal for XYZ
  → employee saves XYZ
  → show modal for ABC
  → employee clicks "Not an abbreviation"
  → queue empty, modal closes
```

**Why a queue?** Handle one abbreviation at a time — employee not overwhelmed with multiple popups.

**Save button logic:**
```javascript
const fullTerm = existing || newTerm;  // dropdown OR text input
postJSON('/api/abbreviations', {action: 'add', abbreviation: item.token, full_term: fullTerm, ...})
```

**Why dropdown AND text input?** Employee can link to existing term ("XYZ is another word for ROSE GOLD") or define new term.

---

## `add_product.js` — Manual entry

### Add row button

Clones first product form row, clears values, increments counter.

```javascript
if (rowCount >= MAX_ROWS) {
  document.getElementById('add-row-btn').disabled = true;
}
```

**Why disable at 10?** Matches business rule in `app.py` (`MAX_MANUAL_ROWS = 10`).

### Form submit

**Prevents normal form submit** (which would reload page):
```javascript
e.preventDefault();
```

Collects all rows into JSON array, POSTs to `/api/products/manual`.

**Skips rows with empty reference** — employee can leave blank rows without error.

---

## `analytics.js` — Reports page

### `loadFilters()` — runs on page load

```javascript
fetch('/api/filters')
  → fill shop dropdown
  → fill city dropdown
  → fill kind dropdown
  → fill collection dropdown
  → fill month dropdowns
```

**Why on page load?** Dropdowns ready before employee clicks anything.

**If database empty:** Dropdowns have only "All" option — charts will show no data.

### `loadChart(chartId, btn)` — when employee clicks chart button

```
1. Highlight clicked button (active class)
2. Read current filter values
3. Build URL: /api/analytics/top_sellout_references?shop_id=1113&kind=WATCH
4. fetch(url)
5. Parse response: {chart: "...plotly json...", rows: [...]}
6. Plotly.newPlot('chart-area', chartData.data, chartData.layout)
7. Build HTML table from rows
```

**Why Plotly in browser not server?** Interactive — employee hovers bars to see exact values. Server just sends data, browser draws.

### `getFilterParams()`

Converts dropdown selections to URL query string.

**Month handling:**
```javascript
if (from) params.set('month_from', from + '-01');
```
Employee selects "2024-01" → sends "2024-01-01" to match database date format.

---

## `abbreviations.js` — Abbreviations page

### `loadAbbrevTable()`

Fetches all abbreviations, builds HTML table dynamically.

**Why dynamic table?** When employee adds new abbreviation via form, table refreshes without page reload.

### Form submit

POST new abbreviation → clear form → reload table.

---

## How browser loads these files

In `base.html`:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
<script src="{{ url_for('static', filename='js/app.js') }}"></script>
```

Each page adds its own script:
```html
{% block scripts %}
<script src="{{ url_for('static', filename='js/upload.js') }}"></script>
{% endblock %}
```

**`url_for`** — Flask function that generates correct URL. Works even if app is deployed to different path.

---

## Common employee scenarios

| Employee action | JS file | What happens |
|-----------------|---------|--------------|
| Click Upload without file | upload.js | Red error immediately |
| Upload valid Excel | upload.js | Green success + counts |
| Upload with unknown abbrev | upload.js | Success + popup modal |
| Add 11th product row | add_product.js | Button disabled at 10 |
| Click chart with no data | analytics.js | "No data for selected filters" |
| Add new abbreviation | abbreviations.js | Table updates instantly |

---

## What to tell your supervisor

> "The static folder contains all frontend styling and interactivity. CSS provides a clean, non-technical interface with clear success and error states. JavaScript handles file uploads, form submission, chart rendering, and abbreviation prompts — all communicating with the Python backend through REST API calls without page reloads. Each page loads only the JavaScript it needs."

---

## Learning tip

Open browser **Developer Tools** (F12) → **Network** tab while uploading a file. You'll see:
- POST request to `/api/upload/products`
- JSON response with insert counts

This connects what you read in documentation to what actually happens in the browser.
