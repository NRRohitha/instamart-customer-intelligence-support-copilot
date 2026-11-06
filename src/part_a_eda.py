import pandas as pd

from src.config import DATA_CLEAN


def main():
    customers = pd.read_csv(DATA_CLEAN / "customers.csv")
    orders = pd.read_csv(DATA_CLEAN / "orders.csv")
    products = pd.read_csv(DATA_CLEAN / "products.csv")

    completed = orders[orders["status"] == "completed"].merge(
        customers[["customer_id", "city"]], on="customer_id", how="left"
    ).merge(
        products[["product_id", "category"]], on="product_id", how="left"
    )

    pivot = pd.pivot_table(
        completed,
        values="order_amount",
        index="city",
        columns="category",
        aggfunc="sum",
        margins=True,
        margins_name="All",
    )
    print("=== Q2 pivot with margins ===")
    print(pivot.round(2).to_string())
    print(f"pivot grand total: {pivot.loc['All', 'All']:.2f}")

    city_stats = completed.groupby("city")["order_amount"].agg(
        total="sum", average="mean", orders="count"
    )
    print("\n=== city groupby (sum, mean, count) ===")
    print(city_stats.round(2).to_string())

    amounts = completed["order_amount"]
    q1 = amounts.quantile(0.25)
    q3 = amounts.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    print("\n=== completed order_amount distribution ===")
    print(f"mean: {amounts.mean():.2f}")
    print(f"median: {amounts.median():.2f}")
    print(f"skewness: {amounts.skew():.2f}")
    print(f"Q1: {q1:.2f}")
    print(f"Q3: {q3:.2f}")
    print(f"IQR: {iqr:.2f}")
    print(f"lower fence: {lower:.2f}")
    print(f"upper fence: {upper:.2f}")
    print(f"outliers above: {(amounts > upper).sum()}")
    print(f"outliers below: {(amounts < lower).sum()}")

    columns = ["order_amount", "discount_pct", "quantity", "delivery_minutes"]
    correlation = completed[columns].corr()
    print("\n=== correlation matrix ===")
    print(correlation.round(3).to_string())
    masked = correlation.where(~(correlation.index.to_numpy()[:, None] == correlation.columns.to_numpy()[None, :]))
    strongest = masked.abs().stack().idxmax()
    print(f"strongest absolute correlation: {strongest} = {correlation.loc[strongest]:.3f}")


if __name__ == "__main__":
    main()
