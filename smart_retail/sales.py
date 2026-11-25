"""Billing: create sales, update stock, apply loyalty discounts."""

from datetime import datetime

# Loyalty rules
POINTS_PER_RUPEES = 10  # 1 point for every Rs.10 spent
DISCOUNT_TIERS = [(1500, 0.10), (500, 0.05)]  # (points needed, discount rate)


class OutOfStockError(ValueError):
    """Raised when a sale asks for more units than are in stock."""


def discount_rate(points: int) -> float:
    for needed, rate in DISCOUNT_TIERS:
        if points >= needed:
            return rate
    return 0.0


def create_sale(conn, items, customer_phone=None, sold_at=None) -> dict:
    """Record a sale.

    items          - list of (sku, quantity) pairs
    customer_phone - optional, links the sale to a customer (earns/uses loyalty)
    sold_at        - optional ISO timestamp (used by the seed script)

    Everything happens in ONE transaction: if anything fails (e.g. not enough
    stock for the 3rd item) nothing is saved and stock is untouched.
    Returns a receipt dictionary.
    """
    if not items:
        raise ValueError("The cart is empty")

    # Merge duplicate SKUs and validate quantities
    cart: dict[str, int] = {}
    for sku, qty in items:
        if not isinstance(qty, int) or qty <= 0:
            raise ValueError(f"Invalid quantity for {sku}: must be a whole number above zero")
        key = sku.strip().upper()
        cart[key] = cart.get(key, 0) + qty

    sold_at = sold_at or datetime.now().isoformat(timespec="seconds")

    with conn:  # commit on success, roll back on any exception
        customer = None
        if customer_phone:
            customer = conn.execute("SELECT * FROM customers WHERE phone = ?", (customer_phone.strip(),)).fetchone()
            if customer is None:
                raise ValueError(f"No customer with phone {customer_phone}")

        lines = []
        for sku, qty in cart.items():
            product = conn.execute("SELECT * FROM products WHERE sku = ?", (sku,)).fetchone()
            if product is None:
                raise ValueError(f"Unknown SKU '{sku}'")
            if product["stock"] < qty:
                raise OutOfStockError(f"Only {product['stock']} of '{product['name']}' in stock (wanted {qty})")
            lines.append(
                {
                    "product_id": product["id"],
                    "sku": sku,
                    "name": product["name"],
                    "qty": qty,
                    "unit_price": product["price"],
                    "line_total": round(product["price"] * qty, 2),
                }
            )

        subtotal = round(sum(line["line_total"] for line in lines), 2)
        rate = discount_rate(customer["points"]) if customer else 0.0
        discount = round(subtotal * rate, 2)
        total = round(subtotal - discount, 2)

        cur = conn.execute(
            "INSERT INTO sales (customer_id, sold_at, subtotal, discount, total) VALUES (?, ?, ?, ?, ?)",
            (customer["id"] if customer else None, sold_at, subtotal, discount, total),
        )
        sale_id = cur.lastrowid

        for line in lines:
            conn.execute(
                "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (sale_id, line["product_id"], line["qty"], line["unit_price"]),
            )
            conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (line["qty"], line["product_id"]))

        points_earned = int(total // POINTS_PER_RUPEES) if customer else 0
        if customer:
            conn.execute("UPDATE customers SET points = points + ? WHERE id = ?", (points_earned, customer["id"]))

    return {
        "sale_id": sale_id,
        "sold_at": sold_at,
        "customer": customer["name"] if customer else None,
        "lines": lines,
        "subtotal": subtotal,
        "discount_rate": rate,
        "discount": discount,
        "total": total,
        "points_earned": points_earned,
    }


def format_receipt(r: dict) -> str:
    """Printable text receipt."""
    out = [
        "-" * 44,
        f"  SMART RETAIL   Receipt #{r['sale_id']}",
        f"  {r['sold_at']}",
        f"  Customer: {r['customer'] or 'Walk-in'}",
        "-" * 44,
    ]
    for line in r["lines"]:
        out.append(f"  {line['name'][:22]:<22} {line['qty']:>2} x {line['unit_price']:>7.2f} = {line['line_total']:>8.2f}")
    out.append("-" * 44)
    out.append(f"  {'Subtotal':<30}{r['subtotal']:>12.2f}")
    if r["discount"]:
        out.append(f"  {'Loyalty discount (' + str(int(r['discount_rate'] * 100)) + '%)':<30}{-r['discount']:>12.2f}")
    out.append(f"  {'TOTAL (Rs.)':<30}{r['total']:>12.2f}")
    if r["customer"]:
        out.append(f"  Points earned: {r['points_earned']}")
    out.append("-" * 44)
    return "\n".join(out)
