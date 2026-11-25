# Smart Retail Management System

A simple base project for running a small shop: products and stock, billing,
customers with loyalty rewards, sales reports, and **smart restock suggestions**
that look at how fast each product really sells.

Pure Python 3.10+ with SQLite - **no packages to install**.

## Features

| Area | What it does |
|------|--------------|
| Inventory | add products, restock, low-stock alerts when stock reaches the reorder level |
| Billing | multi-item bills with printed receipts; stock is reduced automatically |
| Safe checkout | each sale is one database transaction - if any item is out of stock, nothing is saved |
| Customers | loyalty points (1 point per Rs.10 spent) and automatic discounts: 5% at 500 points, 10% at 1500 |
| Reports | today's orders / revenue / profit, top sellers, sales by category |
| Smart restock | looks at the last 30 days of sales and suggests how much to order to cover 14 days; flags products that will run out within 7 days even if they are above the reorder level |

## Project structure

```
smart_retail/
├── main.py          # command-line menu (start here)
├── db.py            # SQLite schema and connection
├── inventory.py     # products, stock, low-stock list
├── customers.py     # customer records and loyalty tier
├── sales.py         # billing, discounts, receipts
├── reports.py       # summaries and restock suggestions
├── display.py       # text-table helper
├── seed_data.py     # sample products, customers and 30 days of sales
└── test_retail.py   # unit tests
```

## How to run

```bash
python seed_data.py      # one time: load sample data (creates retail.db)
python main.py           # start the shop menu
python -m unittest -v    # run the tests
```

`python seed_data.py --reset` deletes the database and loads fresh sample data.
Sample customer phones for billing: `9876500001` to `9876500004`.
Sample SKUs: `RICE5`, `TEA250`, `WATER1`, `CHIPS`, `SOAP` ...

## How the smart restock works

For every product: `sold per day = units sold in last 30 days / 30`.

- **Needs restocking** if stock <= reorder level, or `stock / sold per day < 7 days`.
- **Suggested order** = (14 days of sales, or 2x reorder level if larger) minus current stock.

## Ideas for taking it further

- Web interface with Flask or Django, or a desktop UI with Tkinter.
- User logins (cashier / manager roles).
- Suppliers and purchase orders; barcode scanning.
- Returns and refunds; GST/tax on bills.
- Charts and a sales dashboard.
