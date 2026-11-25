"""Smart Retail Management System - command-line interface.

Run:  python main.py
(first time, run `python seed_data.py` to load sample products and sales)
"""

import customers
import inventory
import reports
import sales
from db import get_connection
from display import table

MENU = """
===== Smart Retail Management System =====
 1. View products
 2. Add product
 3. Restock product
 4. New sale (billing)
 5. Add customer
 6. View customers
 7. Low-stock alerts
 8. Reports
 0. Exit
"""

REPORT_MENU = """
--- Reports ---
 1. Today's summary
 2. Top selling products
 3. Sales by category
 4. Smart restock suggestions
"""


def ask(prompt: str) -> str:
    return input(prompt).strip()


def ask_int(prompt: str) -> int:
    try:
        return int(ask(prompt))
    except ValueError:
        raise ValueError("Please enter a whole number") from None


def ask_float(prompt: str) -> float:
    try:
        return float(ask(prompt))
    except ValueError:
        raise ValueError("Please enter a number") from None


def view_products(conn):
    rows = [(p["sku"], p["name"], p["category"], f"{p['price']:.2f}", p["stock"]) for p in inventory.list_products(conn)]
    print(table(["SKU", "Name", "Category", "Price", "Stock"], rows))


def add_product(conn):
    inventory.add_product(
        conn,
        sku=ask("SKU: "),
        name=ask("Name: "),
        category=ask("Category: "),
        price=ask_float("Selling price: "),
        cost=ask_float("Cost price: "),
        stock=ask_int("Opening stock: "),
        reorder_level=ask_int("Reorder level: "),
    )
    print("Product added.")


def restock(conn):
    new_stock = inventory.restock(conn, ask("SKU: "), ask_int("Quantity received: "))
    print(f"Stock updated. New stock level: {new_stock}")


def new_sale(conn):
    phone = ask("Customer phone (blank for walk-in): ")
    cart = []
    print("Add items - leave SKU blank to finish.")
    while True:
        sku = ask("  SKU: ")
        if not sku:
            break
        product = inventory.get_product(conn, sku)
        if product is None:
            print("  Unknown SKU, try again.")
            continue
        try:
            qty = ask_int(f"  Quantity of {product['name']}: ")
        except ValueError as err:
            print(f"  {err}")
            continue
        cart.append((sku, qty))
    print(sales.format_receipt(sales.create_sale(conn, cart, customer_phone=phone or None)))


def add_customer(conn):
    customers.add_customer(conn, ask("Name: "), ask("Phone: "))
    print("Customer added.")


def view_customers(conn):
    rows = [(c["name"], c["phone"], c["points"], f"{c['discount_pct']}%") for c in customers.list_customers(conn)]
    print(table(["Name", "Phone", "Points", "Discount"], rows))


def low_stock(conn):
    rows = [(p["sku"], p["name"], p["stock"], p["reorder_level"]) for p in inventory.low_stock(conn)]
    print(table(["SKU", "Name", "Stock", "Reorder level"], rows))


def show_reports(conn):
    print(REPORT_MENU)
    choice = ask("Choose report: ")
    if choice == "1":
        s = reports.daily_summary(conn)
        print(f"Date: {s['day']}\nOrders: {s['orders']}\nRevenue: Rs.{s['revenue']:.2f}\nProfit: Rs.{s['profit']:.2f}")
    elif choice == "2":
        rows = [(r["name"], r["units"], f"{r['revenue']:.2f}") for r in reports.top_products(conn)]
        print(table(["Product", "Units sold", "Revenue"], rows))
    elif choice == "3":
        rows = [(r["category"], r["units"], f"{r['revenue']:.2f}") for r in reports.sales_by_category(conn)]
        print(table(["Category", "Units sold", "Revenue"], rows))
    elif choice == "4":
        rows = [
            (s["sku"], s["name"], s["stock"], s["avg_daily_sales"], s["days_left"] if s["days_left"] is not None else "-", s["suggested_order"])
            for s in reports.restock_suggestions(conn)
        ]
        print(table(["SKU", "Name", "Stock", "Sold/day", "Days left", "Order qty"], rows))
    else:
        print("Invalid report choice.")


ACTIONS = {
    "1": view_products,
    "2": add_product,
    "3": restock,
    "4": new_sale,
    "5": add_customer,
    "6": view_customers,
    "7": low_stock,
    "8": show_reports,
}


def main() -> None:
    conn = get_connection()
    while True:
        print(MENU)
        try:
            choice = ask("Choose an option: ")
        except EOFError:  # input stream closed (e.g. piped input)
            break
        if choice == "0":
            break
        action = ACTIONS.get(choice)
        if action is None:
            print("Invalid option.")
            continue
        try:
            action(conn)
        except ValueError as err:  # includes OutOfStockError
            print(f"Error: {err}")
        except EOFError:
            break
    print("Goodbye!")


if __name__ == "__main__":
    main()
