# `src/` — The Brain of the Project (Beginner Guide)

> **Who is this for?** You, if you are not confident in programming yet but need to explain the project to your supervisor.
>
> **How to use this file:** Read it top to bottom once. Then open the sub-folder READMEs when you need more detail on one part.

---

## Glossary (words you will see a lot)

| Word | Plain English meaning |
|------|----------------------|
| **Backend** | The Python code that runs on your computer — employees never see it directly |
| **Frontend** | The website pages (HTML/CSS/JavaScript) that employees click on |
| **Flask** | A Python library that turns your code into a local website |
| **Route** | A URL address like `/upload` that triggers a specific function |
| **API** | A URL that returns data (JSON) instead of a full webpage — used by JavaScript |
| **PostgreSQL** | The database program that permanently stores products, shops, and sales |
| **Pipeline** | A series of steps: read file → clean → save to database |
| **Model** | A Python "template" that describes what one product or shop looks like |
| **Repository** | The only file allowed to run SQL queries against the database |

---

## The big picture (read this first)

Imagine a **restaurant**:

| Restaurant part | Our project equivalent |
|-----------------|------------------------|
| Dining room (what customers see) | Website (`templates/` + `static/`) |
| Waiter (takes orders) | `app.py` (Flask) |
| Kitchen (prepares food) | `cleaning/` + `models/` |
| Storage room (keeps ingredients) | PostgreSQL database |
| Menu templates | `templates_excel/` (downloadable Excel files) |

**What happens when an employee uploads an Excel file:**

```
1. Employee clicks "Upload" in the browser
2. JavaScript sends the file to app.py
3. app.py saves the file and calls pipeline.py
4. pipeline.py uses cleaning/ to read and fix the Excel data
5. models/ checks the data is valid (correct gender, kind, etc.)
6. db/repository.py saves it into PostgreSQL
7. app.py sends a success message back to the browser
8. Employee sees "Done! 40 products inserted"
```

---

## Why is the code split into folders?

**We could have put everything in one giant file.** We did not, because:

1. **Easier to find bugs** — if uploads break, you look in `cleaning/`, not the whole project
2. **Easier to explain** — each folder has one job
3. **Easier to test** — each piece can be tested separately
4. **Easier to change** — if the database changes, you only edit `db/repository.py`

This is a standard professional pattern called **separation of concerns** (each part cares about one thing).

---

## Sub-folders — where to read next

| Folder | README | One-sentence summary |
|--------|--------|---------------------|
| `models/` | [README.md](models/README.md) | Defines what a valid Product, Shop, and Abbreviation looks like |
| `db/` | [README.md](db/README.md) | Connects to PostgreSQL and runs all INSERT/SELECT queries |
| `cleaning/` | [README.md](cleaning/README.md) | Reads Excel files, fixes typos, expands abbreviations |
| `analytics/` | [README.md](analytics/README.md) | Builds sales charts from database data |
| `templates_excel/` | [README.md](templates_excel/README.md) | Creates the Excel files employees download |
| `tests/` | [README.md](tests/README.md) | Automatic checks that the code still works |

---

# File 1: `main.py` — How you START the website

**This is the only file you run manually.**

### What it does in plain English

It is like pressing the **power button** on the application. It:
1. Checks if the database is reachable
2. Makes sure Excel templates exist
3. Starts the website on your computer at `http://127.0.0.1:5000`

### Every line explained

```python
from src.app import app
```
**Meaning:** Import the Flask website object from `app.py`.  
**Why:** `main.py` is tiny on purpose — all the website logic lives in `app.py`. This file just starts it.

```python
from src.db.connection import test_connection
from src.templates_excel.generator import ensure_all_templates
```
**Meaning:** Import two helper functions — one tests the database, one creates Excel templates.

```python
PROJECT_ROOT = Path(__file__).resolve().parents[1]
```
**Meaning:** Find the `Week 3` folder automatically, no matter where you run the command from.  
**Why:** So paths like `excel_templates/` always work correctly.  
**How it works:** `__file__` is `src/main.py` → go up one folder → `Week 3`.

```python
def main() -> None:
    print("Watch Consignment Management — starting local server")
    test_connection()
    ensure_all_templates(PROJECT_ROOT / "excel_templates")
    print("\nOpen your browser at: http://127.0.0.1:5000")
    app.run(debug=True, host="127.0.0.1", port=5000)
```
**Meaning:**
- Print a welcome message
- Test database (prints ✅ or ❌)
- Create/update Excel template files
- Tell you which URL to open
- Start Flask on port 5000, only on your computer (`127.0.0.1` = localhost, not the internet)

**Why `debug=True`?** During development, if code crashes, you see a helpful error page. Turn off for production.

```python
if __name__ == "__main__":
    main()
```
**Meaning:** Only run `main()` when you execute this file directly.  
**Why:** If another file imports from `main.py`, it won't accidentally start the server.

### How to run it

```bash
uv run python -m src.main
```

### What you will see in different situations

| Situation | What happens |
|-----------|--------------|
| Everything works | ✅ Database message, server running, browser works |
| PostgreSQL is off | ❌ Database message, server still starts but uploads fail |
| Wrong password in `.env` | ❌ Database message with error details |
| You press Ctrl+C | Server stops cleanly |

---

# File 2: `app.py` — The Waiter (connects website to Python)

**This is the most important file.** Every button click on the website eventually calls something in here.

### Why Flask?

We need a way for the **browser** (HTML/JavaScript) to talk to **Python**. Flask is a simple, well-documented tool for that. Alternatives exist (Django, FastAPI) but Flask is lightweight and perfect for a local tool.

### Setup section (lines 37–47)

```python
PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = PROJECT_ROOT / "excel_templates"
UPLOAD_DIR = PROJECT_ROOT / "uploads"
MAX_MANUAL_ROWS = 10
```

**Why these folders exist:**
- `excel_templates/` — files employees download
- `uploads/` — temporary storage for uploaded Excel files before processing
- `MAX_MANUAL_ROWS = 10` — business rule: employees can enter at most 10 products manually at once

```python
app = Flask(__name__, template_folder=..., static_folder=...)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
```

**Meaning:** Create the Flask app and tell it where HTML and CSS live.  
**Why 16 MB limit?** Prevents someone accidentally uploading a huge file that crashes the server.

### `_conn()` — Why open a new connection each time?

```python
def _conn():
    return get_connection()
```

**Why not one permanent connection?** Flask handles many requests. Opening/closing per request is simpler and avoids stale connections. For a small local tool with few users, this is fine.

### `@app.before_request` — Runs before EVERY page load

```python
def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(exist_ok=True)
    ensure_all_templates(TEMPLATES_DIR)
```

**Meaning:** Make sure `uploads/` folder exists and Excel templates are ready.  
**Why every request?** So the first employee visit always works, even on a fresh install.

---

## Part A: Page routes (what the employee SEES)

These functions **only show HTML pages**. They do not process data yet.

| URL employee visits | Function | What they see |
|---------------------|----------|---------------|
| `/` | `home()` | Welcome page with 4 big buttons |
| `/templates` | `templates_page()` | 3 download buttons for Excel files |
| `/upload` | `upload_page()` | File picker for product or sales upload |
| `/add-product` | `add_product_page()` | Form to type products manually |
| `/analytics` | `analytics_page()` | Filters + chart buttons |
| `/abbreviations` | `abbreviations_page()` | Table of abbreviation codes |

**Example — employee visits `/templates`:**
1. Browser requests `http://127.0.0.1:5000/templates`
2. Flask calls `templates_page()`
3. That function calls `ensure_all_templates()` to get file names
4. Flask fills in `templates_page.html` with those names
5. Browser shows the page with Download buttons

**Why pass variables to HTML?** So the page can show real file names instead of hardcoded text.

---

## Part B: Download route

```python
@app.route("/download/<template_key>")
def download_template(template_key: str):
```

**Meaning:** When employee clicks Download, browser goes to e.g. `/download/product_catalog`.  
**What happens:** Python finds the matching `.xlsx` file and sends it to the employee's Downloads folder.

**Why `<template_key>`?** One function handles all 3 templates instead of 3 separate functions.

---

## Part C: Upload API (where real work happens)

### Product upload — step by step

**Employee action:** Chooses Excel file, clicks "Upload Products"

```
Browser  →  POST /api/upload/products  (sends file)
app.py   →  saves file to uploads/
app.py   →  calls run_product_upload() in pipeline.py
pipeline →  cleans Excel, inserts into database
app.py   →  sends JSON result back to browser
upload.js → shows "Done! 40 inserted" on screen
```

**Code walkthrough:**

```python
file = request.files["file"]
```
**Meaning:** Get the uploaded file from the browser request.  
**Why check `"file" not in request.files`?** Employee might click Upload without selecting a file.

```python
save_path = UPLOAD_DIR / secure_filename(file.filename)
file.save(save_path)
```
**Meaning:** Save with a safe filename (removes dangerous characters like `../`).  
**Why save to disk first?** pandas reads Excel from a file path — easier than reading from memory.

```python
result = run_product_upload(conn, save_path, sheet_name="Products")
```
**Meaning:** Hand off to the pipeline. Expects sheet named "Products" (matches our template).

**Three possible outcomes returned to browser:**

| Outcome | JSON includes | Employee sees |
|---------|---------------|---------------|
| Success | `insert_summary: {inserted: 40, skipped: 3, conflict: 2}` | Green success box |
| Unknown abbrev | `unknown_abbreviations: [...]` | Popup asking what code means |
| Error | `error: "message"` | Red error box |

### Monthly report upload

Same pattern but calls `run_monthly_report_upload()` instead.  
**Important:** Products and shops must exist in DB first, or sales rows are skipped (foreign key protection).

### Manual product entry

```python
rows = payload.get("products", [])
if len(rows) > MAX_MANUAL_ROWS:
    return jsonify({"error": f"Maximum {MAX_MANUAL_ROWS} products at once"}), 400
```

**Why limit to 10?** Business requirement — for larger batches, use Excel upload instead.

---

## Part D: Abbreviations API

**Why a separate API?** When upload finds unknown code like `"XYZ"`, JavaScript shows a popup. Employee picks meaning → JavaScript calls `POST /api/abbreviations` → saved to database → future uploads auto-expand it.

Three actions:
- **GET** — list all abbreviations (for the Abbreviations page table)
- **POST with action=add** — save new abbreviation
- **POST with action=ignore** — employee says "this is not an abbreviation"

---

## Part E: Analytics API

```python
@app.route("/api/filters")
```
**Returns:** Only shops, months, cities that actually exist in the database.  
**Why?** Employee should not filter by "Shop 9999" if that shop was never uploaded.

```python
@app.route("/api/analytics/<chart_id>")
```
**Returns:** Plotly chart JSON + table rows.  
**Why JSON not HTML?** JavaScript draws the chart in the browser — more interactive.

---

## Full story you can tell your supervisor

> "When an employee uploads an Excel file, the browser sends it to `app.py`. Flask saves the file and calls our cleaning pipeline. The pipeline reads each row, expands abbreviations like BRCLT to BRACELET, validates the data, and saves it to PostgreSQL. Flask sends back a summary — how many inserted, skipped, or conflicted. If unknown abbreviations appear, the website asks the employee to define them on the spot."

---

## Common beginner questions

**Q: Why is `app.py` so long?**  
A: It is the central hub. Every website action goes through it. Other files do the heavy work.

**Q: What is the difference between a page route and an API route?**  
A: Page route → returns HTML (employee sees a page). API route → returns JSON data (JavaScript uses it silently).

**Q: What happens if I change `app.py` while the server is running?**  
A: With `debug=True`, Flask auto-restarts. You will see "Restarting" in the terminal.

**Q: Where do I look if uploads fail?**  
A: First check terminal for error messages. Then read `cleaning/README.md`. Then check database connection in `db/README.md`.

---

## Next steps for learning

1. Read [models/README.md](models/README.md) — understand what a "valid product" means
2. Read [cleaning/README.md](cleaning/README.md) — understand the Excel → database journey
3. Read [db/README.md](db/README.md) — understand how data is stored
4. Run `uv run pytest src/tests/test_all.py -v` — see automated checks pass
