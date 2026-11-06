import pandas as pd

from src.config import DATA_RAW


def load_raw():
    orders = pd.read_csv(DATA_RAW / "orders.csv", dtype=str, keep_default_na=False)
    customers = pd.read_csv(DATA_RAW / "customers.csv", dtype=str, keep_default_na=False)
    products = pd.read_csv(DATA_RAW / "products.csv", dtype=str, keep_default_na=False)
    tickets = pd.read_csv(DATA_RAW / "tickets.csv", dtype=str, keep_default_na=False)
    return orders, customers, products, tickets


def missing_profile(frame):
    rows = []
    for column in frame.columns:
        blank = frame[column].eq("").sum()
        rows.append((column, str(frame[column].dtype), blank, round(blank * 100 / len(frame), 2)))
    return pd.DataFrame(rows, columns=["column", "dtype", "missing", "missing_pct"])


def audit():
    orders, customers, products, tickets = load_raw()
    amounts = pd.to_numeric(orders["order_amount"], errors="coerce")
    delivery = pd.to_numeric(orders["delivery_minutes"], errors="coerce")
    ages = pd.to_numeric(customers["age"], errors="coerce")

    figures = {
        "raw_order_rows": len(orders),
        "exact_duplicate_rows": int(orders.duplicated().sum()),
        "pending_rows": int((orders["status"] == "pending").sum()),
        "distinct_order_ids": int(orders["order_id"].nunique()),
        "non_numeric_amounts": int(amounts.isna().sum()),
        "negative_delivery_minutes": int((delivery < 0).sum()),
        "blank_delivery_minutes": int((orders["delivery_minutes"] == "").sum()),
        "blank_ages": int((customers["age"] == "").sum()),
        "ages_outside_10_100": int(((ages < 10) | (ages > 100)).sum()),
        "raw_city_spellings": int(customers["city"].nunique()),
        "raw_gender_spellings": int(customers.loc[customers["gender"] != "", "gender"].nunique()),
        "blank_genders": int((customers["gender"] == "").sum()),
    }

    for name, frame in {
        "orders": orders,
        "customers": customers,
        "products": products,
        "tickets": tickets,
    }.items():
        print(f"\n=== {name}: shape={frame.shape} ===")
        print(missing_profile(frame).to_string(index=False))

    print("\n=== audit figures ===")
    for key, value in figures.items():
        print(f"{key}: {value}")
    return figures


def main():
    audit()


if __name__ == "__main__":
    main()
