"""Customer records and loyalty points."""

import sqlite3

from sales import discount_rate


def add_customer(conn, name, phone) -> int:
    name, phone = name.strip(), phone.strip()
    if not name or not phone:
        raise ValueError("Name and phone are required")
    try:
        with conn:
            cur = conn.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone))
    except sqlite3.IntegrityError:
        raise ValueError(f"A customer with phone {phone} already exists") from None
    return cur.lastrowid


def find_by_phone(conn, phone):
    return conn.execute("SELECT * FROM customers WHERE phone = ?", (phone.strip(),)).fetchone()


def list_customers(conn):
    """Customers with their current loyalty discount."""
    rows = conn.execute("SELECT * FROM customers ORDER BY points DESC, name").fetchall()
    return [dict(r, discount_pct=int(discount_rate(r["points"]) * 100)) for r in rows]
