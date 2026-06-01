"""
db/connection.py
-----------------
Manages the connection between Python and PostgreSQL.

What this file does in plain English:
    - Reads your database credentials from the .env file
    - Opens a connection to PostgreSQL when needed
    - Closes it cleanly when done
    - Provides a single connection object that all other code uses

Why it exists as a separate file:
    If you ever change database (e.g. move to a cloud DB), you only
    change this file. Nothing else in the project needs to change.
"""

import os
import psycopg2                          # the PostgreSQL driver for Python
from psycopg2.extensions import connection as PgConnection
from dotenv import load_dotenv           # reads .env file into os.environ

# Load the .env file so os.environ can see DB_HOST, DB_PORT etc.
load_dotenv()


def get_connection() -> PgConnection:
    """
    Open and return a live connection to PostgreSQL.

    Reads credentials from environment variables set in .env:
        DB_HOST     — where PostgreSQL is running (localhost for your machine)
        DB_PORT     — which port PostgreSQL listens on (default 5432)
        DB_NAME     — the name of your database (consignment)
        DB_USER     — your PostgreSQL username (default: postgres)
        DB_PASSWORD — your PostgreSQL password

    Returns a psycopg2 connection object.
    Raises an exception if the connection fails (wrong password, DB not running etc.)
    """
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 5432)),
        dbname=os.environ.get("DB_NAME", "consignment"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", ""),
    )
    return conn


def test_connection() -> bool:
    """
    Try to open a connection and immediately close it.
    Returns True if successful, False if something is wrong.
    Useful to run at the start of main.py to catch problems early.
    """
    try:
        conn = get_connection()
        conn.close()
        print("✅  Database connection successful.")
        return True
    except Exception as e:
        print(f"❌  Could not connect to the database: {e}")
        print("    Check that PostgreSQL is running and your .env credentials are correct.")
        return False