"""
main.py
-------
Entry point to start the local web server.

Usage:
    uv run python -m src.main
"""

from src.app import app
from src.db.connection import test_connection
from src.templates_excel.generator import ensure_all_templates
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    print("Watch Consignment Management — starting local server")
    print("=" * 50)
    test_connection()
    ensure_all_templates(PROJECT_ROOT / "excel_templates")
    print("\nOpen your browser at: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server.\n")
    app.run(debug=True, host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
