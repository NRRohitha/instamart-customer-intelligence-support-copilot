import re
import sqlite3

import pandas as pd

from src.config import DATA_CLEAN, DB_PATH


def main():
    customers = pd.read_csv(DATA_CLEAN / "customers.csv")
    orders = pd.read_csv(DATA_CLEAN / "orders.csv")
    products = pd.read_csv(DATA_CLEAN / "products.csv")

    assert len(customers) == 1200
    assert customers["city"].value_counts().to_dict() == {
        "Pune": 227,
        "Delhi": 210,
        "Bengaluru": 197,
        "Chennai": 191,
        "Hyderabad": 191,
        "Mumbai": 184,
    }
    assert customers["gender"].value_counts().to_dict() == {
        "female": 610,
        "male": 560,
        "unknown": 30,
    }
    assert customers["age"].isna().sum() == 0
    assert customers["age"].min() >= 18 and customers["age"].max() <= 60
    assert len(products) == 40

    assert len(orders) == 12309
    assert orders["order_id"].nunique() == 12309
    status_counts = orders["status"].value_counts().to_dict()
    assert status_counts == {"completed": 11110, "cancelled": 1199}
    assert "pending" not in status_counts
    assert orders["order_amount"].isna().sum() == 0
    completed = orders[orders["status"] == "completed"]
    cancelled = orders[orders["status"] == "cancelled"]
    assert completed["delivery_minutes"].isna().sum() == 0
    assert cancelled["delivery_minutes"].isna().sum() == 1199
    assert abs(completed["order_amount"].sum() - 2998668.80) < 0.01

    with sqlite3.connect(DB_PATH) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert {"customers", "products", "orders"}.issubset(tables)
        assert connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 1200
        assert connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 40
        assert connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 12309
        timestamps = [
            row[0] for row in connection.execute("SELECT order_ts FROM orders LIMIT 500")
        ]
        assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", value) for value in timestamps)
        db_revenue = connection.execute(
            "SELECT SUM(order_amount) FROM orders WHERE status='completed'"
        ).fetchone()[0]
        assert abs(db_revenue - 2998668.80) < 0.01

    print("ALL CHECKPOINTS PASSED")


if __name__ == "__main__":
    main()
