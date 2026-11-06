import sqlite3

import pandas as pd

from src.config import DB_PATH, SQL_DIR


def load_queries():
    text = (SQL_DIR / "queries.sql").read_text(encoding="utf-8")
    return [statement.strip() for statement in text.split(";") if statement.strip()]


def main():
    queries = load_queries()
    assert len(queries) == 7, f"expected 7 queries, found {len(queries)}"

    with sqlite3.connect(DB_PATH) as connection:
        q1 = pd.read_sql_query(queries[0], connection)
        q2 = pd.read_sql_query(queries[1], connection)
        q3 = pd.read_sql_query(queries[2], connection)
        q4 = pd.read_sql_query(queries[3], connection)
        q5 = pd.read_sql_query(queries[4], connection)
        q6 = pd.read_sql_query(queries[5], connection)
        q7 = pd.read_sql_query(queries[6], connection)

        average_spend = connection.execute(
            """
            SELECT AVG(total_spend)
            FROM (
                SELECT SUM(order_amount) AS total_spend
                FROM orders
                WHERE status = 'completed'
                GROUP BY customer_id
            )
            """
        ).fetchone()[0]

    print(f"Q1 customers: {len(q1)}")
    print(f"Q2 rows: {len(q2)}")
    print(f"Q2 revenue total: {q2['revenue'].sum():.2f}")
    largest = q2.loc[q2["revenue"].idxmax()]
    print(f"Q2 largest cell: {largest['city']} / {largest['category']} = {largest['revenue']:.2f}")
    print(f"Q3 products: {len(q3)}")
    print(f"Q4 customers: {len(q4)}")
    print(f"Q5 customers: {len(q5)}")
    print(f"Q5 average customer spend: {average_spend:.2f}")
    rank_gap = (
        q6["spend_rank"] != q6["spend_row_number"]
    ).sum()
    print(f"Q6 rows where RANK != ROW_NUMBER: {rank_gap}")
    for city, group in q6.groupby("city", sort=True):
        top = group.iloc[0]
        print(f"Q6 top {city}: {top['customer_id']} {top['total_spend']:.2f}")
    print(f"Q7 daily rows: {len(q7)}")
    print(f"Q7 final cumulative revenue: {q7['cumulative_revenue'].iloc[-1]:.2f}")


if __name__ == "__main__":
    main()
