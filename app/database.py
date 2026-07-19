import os
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("DATABASE_PATH", ROOT_DIR / "data" / "business.db"))


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    order_date TEXT NOT NULL,
    region TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS refunds (
    refund_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    refund_date TEXT NOT NULL,
    refund_amount REAL NOT NULL,
    reason TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
"""


def connect(read_only: bool = False) -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if read_only:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    conn = connect()
    conn.executescript(SCHEMA_SQL)
    existing = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    if existing:
        conn.close()
        return

    products = [
        (1, "轻羽降噪耳机", "数码", 699.0),
        (2, "星云机械键盘", "数码", 459.0),
        (3, "云感护颈枕", "家居", 199.0),
        (4, "极简双肩包", "箱包", 329.0),
        (5, "恒温保温杯", "家居", 159.0),
        (6, "跃动智能手环", "数码", 299.0),
    ]
    conn.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)

    rng = random.Random(2026)
    regions = ["华东", "华南", "华北", "西南"]
    statuses = ["completed", "completed", "completed", "refunded"]
    start = date(2026, 1, 1)
    refund_id = 1
    item_id = 1

    for order_id in range(1001, 1121):
        order_date = start + timedelta(days=rng.randrange(180))
        region = rng.choice(regions)
        status = rng.choice(statuses)
        conn.execute(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
            (order_id, order_date.isoformat(), region, f"客户{order_id - 1000:03d}", status),
        )

        product = rng.choice(products)
        quantity = rng.randint(1, 4)
        conn.execute(
            "INSERT INTO order_items VALUES (?, ?, ?, ?, ?)",
            (item_id, order_id, product[0], quantity, product[3]),
        )
        item_id += 1

        if status == "refunded":
            conn.execute(
                "INSERT INTO refunds VALUES (?, ?, ?, ?, ?)",
                (
                    refund_id,
                    order_id,
                    (order_date + timedelta(days=rng.randint(1, 10))).isoformat(),
                    product[3] * quantity,
                    rng.choice(["质量问题", "不喜欢", "尺寸不合适", "物流延迟"]),
                ),
            )
            refund_id += 1

    conn.commit()
    conn.close()


def schema_description() -> dict:
    return {
        "database": "SQLite 电商经营示例库",
        "tables": {
            "products": "商品表：product_id, product_name, category, unit_price",
            "orders": "订单表：order_id, order_date(YYYY-MM-DD), region, customer_name, status",
            "order_items": "订单明细表：item_id, order_id, product_id, quantity, unit_price",
            "refunds": "退款表：refund_id, order_id, refund_date, refund_amount, reason",
        },
        "relationships": [
            "orders.order_id = order_items.order_id",
            "products.product_id = order_items.product_id",
            "orders.order_id = refunds.order_id",
        ],
        "metrics": {
            "sales_amount": "SUM(order_items.quantity * order_items.unit_price)，默认仅统计 status='completed'",
            "order_count": "COUNT(DISTINCT orders.order_id)",
            "refund_rate": "退款订单数 / 总订单数；分母口径必须在回答中说明",
        },
    }

