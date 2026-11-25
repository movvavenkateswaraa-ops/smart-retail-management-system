"""Database setup (SQLite - built into Python, nothing to install)."""

import sqlite3
from pathlib import Path

DB_PATH = Path("retail.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sku           TEXT    NOT NULL UNIQUE,
    name          TEXT    NOT NULL,
    category      TEXT    NOT NULL,
    price         REAL    NOT NULL CHECK (price >= 0),
    cost          REAL    NOT NULL CHECK (cost >= 0),
    stock         INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    reorder_level INTEGER NOT NULL DEFAULT 10
);

CREATE TABLE IF NOT EXISTS customers (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT    NOT NULL,
    phone  TEXT    NOT NULL UNIQUE,
    points INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sales (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER REFERENCES customers(id),
    sold_at     TEXT    NOT NULL,
    subtotal    REAL    NOT NULL,
    discount    REAL    NOT NULL DEFAULT 0,
    total       REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS sale_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id    INTEGER NOT NULL REFERENCES sales(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL    NOT NULL
);
"""


def get_connection(path=DB_PATH) -> sqlite3.Connection:
    """Open the database (creating tables on first use).

    Pass ":memory:" as the path for a throw-away in-memory database (used by the tests).
    """
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn
