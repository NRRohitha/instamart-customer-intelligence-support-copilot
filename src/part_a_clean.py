import sqlite3

import pandas as pd

from src.config import DATA_CLEAN, DATA_RAW, DB_PATH

RAW_ORDER_COLUMNS = [
    "order_id",
    "customer_id",
    "product_id",
    "quantity",
    "order_ts",
    "status",
    "discount_pct",
    "order_amount",
    "delivery_minutes",
]


def clean_customers():
    customers = pd.read_csv(DATA_RAW / "customers.csv", dtype=str, keep_default_na=False)
    customers["city"] = customers["city"].str.strip().str.title()
    gender_map = {
        "male": "male",
        "m": "male",
        "female": "female",
        "f": "female",
        "": "unknown",
    }
    customers["gender"] = (
        customers["gender"].str.strip().str.lower().map(gender_map).fillna("unknown")
    )
    ages = pd.to_numeric(customers["age"], errors="coerce")
    ages = ages.where(ages.between(10, 100))
    customers["age"] = ages.fillna(
        customers.assign(age=ages).groupby("city")["age"].transform("median")
    )
    customers["signup_date"] = pd.to_datetime(customers["signup_date"])
    return customers


def clean_orders(products):
    orders = pd.read_csv(DATA_RAW / "orders.csv")
    orders["order_ts"] = pd.to_datetime(orders["order_ts"])
    orders = orders.drop_duplicates()
    orders = (
        orders.sort_values(["order_id", "order_ts"])
        .drop_duplicates("order_id", keep="last")
        .reset_index(drop=True)
    )
    orders = orders.merge(
        products[["product_id", "price_inr", "category"]],
        on="product_id",
        how="left",
        validate="many_to_one",
    )
    orders["quantity"] = pd.to_numeric(orders["quantity"])
    orders["discount_pct"] = pd.to_numeric(orders["discount_pct"])
    amounts = pd.to_numeric(orders["order_amount"], errors="coerce")
    calculated = (
        orders["price_inr"] * orders["quantity"] * (1 - orders["discount_pct"] / 100)
    ).round(2)
    orders["order_amount"] = amounts.fillna(calculated).round(2)
    delivery = pd.to_numeric(orders["delivery_minutes"], errors="coerce")
    orders["delivery_minutes"] = delivery.where(delivery >= 0)
    completed = orders["status"] == "completed"
    category_median = orders.loc[completed, ["category", "delivery_minutes"]].groupby(
        "category"
    )["delivery_minutes"].transform("median")
    orders.loc[completed, "delivery_minutes"] = orders.loc[
        completed, "delivery_minutes"
    ].fillna(category_median)
    return orders[RAW_ORDER_COLUMNS]


def store(clean_customers_frame, clean_products, clean_orders_frame):
    DATA_CLEAN.mkdir(parents=True, exist_ok=True)
    clean_customers_frame.to_csv(DATA_CLEAN / "customers.csv", index=False)
    clean_products.to_csv(DATA_CLEAN / "products.csv", index=False)
    clean_orders_frame.to_csv(DATA_CLEAN / "orders.csv", index=False)

    db_customers = clean_customers_frame.copy()
    db_customers["signup_date"] = db_customers["signup_date"].dt.strftime("%Y-%m-%d")
    db_orders = clean_orders_frame.copy()
    db_orders["order_ts"] = db_orders["order_ts"].dt.strftime("%Y-%m-%d %H:%M:%S")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        db_customers.to_sql("customers", connection, if_exists="replace", index=False)
        clean_products.to_sql("products", connection, if_exists="replace", index=False)
        db_orders.to_sql("orders", connection, if_exists="replace", index=False)


def main():
    products = pd.read_csv(DATA_RAW / "products.csv")
    customers = clean_customers()
    orders = clean_orders(products)
    store(customers, products, orders)

    completed = orders[orders["status"] == "completed"]
    print(f"customers: {len(customers)}")
    print(customers["city"].value_counts().to_string())
    print(customers["gender"].value_counts().to_string())
    print(f"missing ages: {customers['age'].isna().sum()}")
    print(f"age range: {customers['age'].min()} - {customers['age'].max()}")
    print(f"orders: {len(orders)}")
    print(orders["status"].value_counts().to_string())
    print(f"distinct order ids: {orders['order_id'].nunique()}")
    print(f"missing amounts: {orders['order_amount'].isna().sum()}")
    print(f"missing completed delivery: {completed['delivery_minutes'].isna().sum()}")
    print(
        "missing cancelled delivery: "
        f"{orders.loc[orders['status'] == 'cancelled', 'delivery_minutes'].isna().sum()}"
    )
    print(f"completed revenue: {completed['order_amount'].sum():.2f}")


if __name__ == "__main__":
    main()
