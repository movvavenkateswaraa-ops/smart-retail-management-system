"""Product and stock management."""

import sqlite3


def add_product(conn, sku, name, category, price, cost, stock=0, reorder_level=10) -> int:
    """Add a new product and return its id."""
    sku = sku.strip().upper()
    if not sku or not name.strip():
        raise ValueError("SKU and name are required")
    if price < 0 or cost < 0 or stock < 0 or reorder_level < 0:
        raise ValueError("Price, cost, stock and reorder level cannot be negative")
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO products (sku, name, category, price, cost, stock, reorder_level) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (sku, name.strip(), category.strip(), price, cost, stock, reorder_level),
            )
    except sqlite3.IntegrityError:
        raise ValueError(f"Could not add product - SKU '{sku}' already exists") from None
    return cur.lastrowid


def get_product(conn, sku):
    """Return the product row for a SKU, or None."""
    return conn.execute("SELECT * FROM products WHERE sku = ?", (sku.strip().upper(),)).fetchone()


def list_products(conn, category=None):
    if category:
        return conn.execute(
            "SELECT * FROM products WHERE category = ? ORDER BY name", (category,)
        ).fetchall()
    return conn.execute("SELECT * FROM products ORDER BY category, name").fetchall()


def restock(conn, sku, quantity) -> int:
    """Add stock to a product; returns the new stock level."""
    if quantity <= 0:
        raise ValueError("Restock quantity must be greater than zero")
    product = get_product(conn, sku)
    if product is None:
        raise ValueError(f"Unknown SKU '{sku}'")
    with conn:
        conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (quantity, product["id"]))
    return product["stock"] + quantity


def low_stock(conn):
    """Products at or below their reorder level, lowest stock first."""
    return conn.execute(
        "SELECT * FROM products WHERE stock <= reorder_level ORDER BY stock, name"
    ).fetchall()
