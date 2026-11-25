"""Unit tests - run with:  python -m unittest -v"""

import unittest
from datetime import date, timedelta

import customers
import inventory
import reports
import sales
from db import get_connection


class RetailTests(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        inventory.add_product(self.conn, "A1", "Rice", "Grocery", price=100, cost=80, stock=10, reorder_level=5)
        inventory.add_product(self.conn, "B1", "Soap", "Care", price=50, cost=30, stock=3, reorder_level=5)
        customers.add_customer(self.conn, "Test Customer", "111")

    def test_sale_reduces_stock_and_totals(self):
        receipt = sales.create_sale(self.conn, [("a1", 2), ("B1", 1)])
        self.assertEqual(receipt["total"], 250)
        self.assertEqual(inventory.get_product(self.conn, "A1")["stock"], 8)
        self.assertEqual(inventory.get_product(self.conn, "B1")["stock"], 2)

    def test_out_of_stock_changes_nothing(self):
        with self.assertRaises(sales.OutOfStockError):
            sales.create_sale(self.conn, [("A1", 2), ("B1", 99)])  # 2nd item fails
        self.assertEqual(inventory.get_product(self.conn, "A1")["stock"], 10)  # rolled back
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0], 0)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            sales.create_sale(self.conn, [])
        with self.assertRaises(ValueError):
            sales.create_sale(self.conn, [("A1", 0)])
        with self.assertRaises(ValueError):
            sales.create_sale(self.conn, [("NOPE", 1)])
        with self.assertRaises(ValueError):
            inventory.add_product(self.conn, "A1", "Dup", "Grocery", 1, 1)

    def test_loyalty_points_and_discount(self):
        first = sales.create_sale(self.conn, [("A1", 2)], customer_phone="111")  # Rs.200 -> 20 points
        self.assertEqual(first["points_earned"], 20)
        self.assertEqual(first["discount"], 0)
        self.conn.execute("UPDATE customers SET points = 500")  # reach the 5% tier
        second = sales.create_sale(self.conn, [("A1", 1)], customer_phone="111")
        self.assertEqual(second["discount"], 5.0)
        self.assertEqual(second["total"], 95.0)

    def test_restock_and_low_stock(self):
        self.assertEqual([p["sku"] for p in inventory.low_stock(self.conn)], ["B1"])
        self.assertEqual(inventory.restock(self.conn, "B1", 20), 23)
        self.assertEqual(inventory.low_stock(self.conn), [])

    def test_daily_summary_profit(self):
        sales.create_sale(self.conn, [("A1", 2)])  # revenue 200, cost 160
        summary = reports.daily_summary(self.conn)
        self.assertEqual((summary["orders"], summary["revenue"], summary["profit"]), (1, 200, 40))

    def test_restock_suggestion_uses_sales_speed(self):
        inventory.restock(self.conn, "A1", 90)  # stock 100
        for _ in range(9):
            sales.create_sale(self.conn, [("A1", 10)])  # 90 sold -> stock 10 (above reorder level 5)
        suggestions = {s["sku"]: s for s in reports.restock_suggestions(self.conn)}
        # 90 units / 30 days = 3 per day -> only ~3 days of stock left, so it is flagged
        self.assertEqual(suggestions["A1"]["avg_daily_sales"], 3.0)
        self.assertEqual(suggestions["A1"]["days_left"], 3.3)
        self.assertEqual(suggestions["A1"]["suggested_order"], 32)  # 14 days * 3/day = 42, minus 10 in stock
        self.assertIn("B1", suggestions)  # B1 is below its reorder level

    def test_old_sales_ignored_by_suggestions(self):
        inventory.restock(self.conn, "A1", 90)  # stock 100
        old = (date.today() - timedelta(days=60)).isoformat() + "T10:00:00"
        sales.create_sale(self.conn, [("A1", 20)], sold_at=old)  # outside the 30-day window
        suggestions = {s["sku"]: s for s in reports.restock_suggestions(self.conn)}
        self.assertNotIn("A1", suggestions)  # 80 in stock and no recent sales


if __name__ == "__main__":
    unittest.main()
