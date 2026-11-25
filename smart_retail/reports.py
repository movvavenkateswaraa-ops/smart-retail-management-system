"""Reports and the 'smart' restock suggestions."""

import math
from datetime import date, timedelta


def daily_summary(conn, day=None) -> dict:
    """Orders, revenue and profit for one day (default: today)."""
    day = day or date.today().isoformat()
    orders, revenue = conn.execute(
        "SELECT COUNT(*), COALESCE(SUM(total), 0) FROM sales WHERE date(sold_at) = ?", (day,)
    ).fetchone()
    cost = conn.execute(
        """SELECT COALESCE(SUM(si.quantity * p.cost), 0)
           FROM sale_items si
           JOIN sales s ON s.id = si.sale_id
           JOIN products p ON p.id = si.product_id
           WHERE date(s.sold_at) = ?""",
        (day,),
    ).fetchone()[0]
    return {
        "day": day,
        "orders": orders,
        "revenue": round(revenue, 2),
        "profit": round(revenue - cost, 2),
    }


def top_products(conn, limit=5):
    """Best sellers by units sold."""
    return conn.execute(
        """SELECT p.name, SUM(si.quantity) AS units, ROUND(SUM(si.quantity * si.unit_price), 2) AS revenue
           FROM sale_items si JOIN products p ON p.id = si.product_id
           GROUP BY p.id ORDER BY units DESC LIMIT ?""",
        (limit,),
    ).fetchall()


def sales_by_category(conn):
    return conn.execute(
        """SELECT p.category, SUM(si.quantity) AS units, ROUND(SUM(si.quantity * si.unit_price), 2) AS revenue
           FROM sale_items si JOIN products p ON p.id = si.product_id
           GROUP BY p.category ORDER BY revenue DESC"""
    ).fetchall()


def restock_suggestions(conn, today=None, lookback_days=30, target_days=14):
    """Suggest what to reorder, based on how fast each product actually sells.

    A product needs restocking if it is at/below its reorder level, OR it will
    run out within 7 days at its recent selling speed. The suggested quantity
    covers `target_days` of sales (never less than 2x the reorder level).
    """
    today = today or date.today()
    since = (today - timedelta(days=lookback_days)).isoformat()
    rows = conn.execute(
        """SELECT p.sku, p.name, p.stock, p.reorder_level,
                  COALESCE(SUM(CASE WHEN s.sold_at >= ? THEN si.quantity END), 0) AS sold
           FROM products p
           LEFT JOIN sale_items si ON si.product_id = p.id
           LEFT JOIN sales s ON s.id = si.sale_id
           GROUP BY p.id""",
        (since,),
    ).fetchall()

    suggestions = []
    for r in rows:
        avg_daily = r["sold"] / lookback_days
        days_left = r["stock"] / avg_daily if avg_daily > 0 else None
        needs = r["stock"] <= r["reorder_level"] or (days_left is not None and days_left < 7)
        target = max(math.ceil(avg_daily * target_days), r["reorder_level"] * 2)
        qty = target - r["stock"]
        if needs and qty > 0:
            suggestions.append(
                {
                    "sku": r["sku"],
                    "name": r["name"],
                    "stock": r["stock"],
                    "avg_daily_sales": round(avg_daily, 2),
                    "days_left": round(days_left, 1) if days_left is not None else None,
                    "suggested_order": qty,
                }
            )
    suggestions.sort(key=lambda s: (s["days_left"] is None, s["days_left"] or 0))
    return suggestions
