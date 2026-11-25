"""Load sample products, customers and 30 days of sales.

    python seed_data.py            # fill an empty database
    python seed_data.py --reset    # delete retail.db first
"""

import argparse
import random
from datetime import date, datetime, timedelta, time

import customers
import inventory
import sales
from db import DB_PATH, get_connection

PRODUCTS = [
    # sku, name, category, price, cost, stock, reorder_level
    ("RICE5", "Basmati Rice 5kg", "Grocery", 620, 520, 70, 15),
    ("ATTA5", "Wheat Flour 5kg", "Grocery", 240, 200, 80, 15),
    ("DAL1", "Toor Dal 1kg", "Grocery", 165, 135, 90, 20),
    ("OIL1", "Sunflower Oil 1L", "Grocery", 155, 130, 100, 20),
    ("SUGAR1", "Sugar 1kg", "Grocery", 48, 40, 130, 25),
    ("TEA250", "Tea Powder 250g", "Beverages", 130, 105, 110, 20),
    ("COF100", "Instant Coffee 100g", "Beverages", 285, 235, 35, 12),
    ("JUICE1", "Mango Juice 1L", "Beverages", 110, 85, 100, 20),
    ("WATER1", "Mineral Water 1L", "Beverages", 20, 12, 220, 40),
    ("CHIPS", "Potato Chips", "Snacks", 20, 14, 160, 30),
    ("BISC", "Cream Biscuits", "Snacks", 30, 22, 150, 30),
    ("NUTS200", "Mixed Nuts 200g", "Snacks", 260, 200, 30, 10),
    ("SOAP", "Bath Soap", "Personal Care", 42, 30, 120, 25),
    ("SHAM180", "Shampoo 180ml", "Personal Care", 175, 135, 40, 12),
    ("TOOTH150", "Toothpaste 150g", "Personal Care", 95, 70, 90, 20),
    ("DETER1", "Detergent 1kg", "Household", 210, 165, 55, 15),
    ("DISH", "Dishwash Liquid", "Household", 115, 85, 65, 15),
]

CUSTOMERS = [
    ("Anita Sharma", "9876500001"),
    ("Rahul Verma", "9876500002"),
    ("Sneha Reddy", "9876500003"),
    ("Mohammed Khan", "9876500004"),
]


def seed(conn, days=30, seed_value=7) -> int:
    """Fill the database; returns the number of sales created."""
    rng = random.Random(seed_value)
    for p in PRODUCTS:
        inventory.add_product(conn, *p)
    for name, phone in CUSTOMERS:
        customers.add_customer(conn, name, phone)

    skus = [p[0] for p in PRODUCTS]
    count = 0
    for offset in range(days - 1, -1, -1):  # oldest day first, ending today
        day = date.today() - timedelta(days=offset)
        for _ in range(rng.randint(3, 7)):
            cart = []
            for sku in rng.sample(skus, rng.randint(1, 4)):
                qty = rng.randint(1, 3)
                if inventory.get_product(conn, sku)["stock"] >= qty:
                    cart.append((sku, qty))
            if not cart:
                continue
            phone = rng.choice(CUSTOMERS)[1] if rng.random() < 0.4 else None
            moment = datetime.combine(day, time(rng.randint(9, 20), rng.randint(0, 59)))
            sales.create_sale(conn, cart, customer_phone=phone, sold_at=moment.isoformat(timespec="seconds"))
            count += 1
    return count


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="delete the existing database first")
    args = parser.parse_args()

    if args.reset and DB_PATH.exists():
        DB_PATH.unlink()

    connection = get_connection()
    if connection.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
        print("Database already has data. Use --reset to start over.")
    else:
        print(f"Created sample data with {seed(connection)} sales.")
