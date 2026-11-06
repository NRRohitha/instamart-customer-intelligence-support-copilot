-- Q1: WHERE then HAVING. Only completed orders above INR 500 count, and we keep customers whose
-- qualifying total exceeds INR 8000.
SELECT customer_id, SUM(order_amount) AS qualifying_total
FROM orders
WHERE status = 'completed' AND order_amount > 500
GROUP BY customer_id
HAVING SUM(order_amount) > 8000
ORDER BY customer_id;

-- Q2: three-table join. Revenue by city and product category.
SELECT c.city, p.category, SUM(o.order_amount) AS revenue
FROM orders AS o
JOIN customers AS c ON c.customer_id = o.customer_id
JOIN products AS p ON p.product_id = o.product_id
WHERE o.status = 'completed'
GROUP BY c.city, p.category
ORDER BY c.city, p.category;

-- Q3: scalar subquery. Products priced above the catalogue average.
SELECT product_id, product_name, price_inr
FROM products
WHERE price_inr > (SELECT AVG(price_inr) FROM products)
ORDER BY price_inr DESC, product_id;

-- Q4: LEFT JOIN. Customers with no completed order.
SELECT c.customer_id, c.city
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.customer_id AND o.status = 'completed'
WHERE o.order_id IS NULL
ORDER BY c.customer_id;

-- Q5: two CTEs. Customers whose completed spend is above the average of those totals.
WITH spend AS (
    SELECT customer_id, SUM(order_amount) AS total_spend
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
), avg_spend AS (
    SELECT AVG(total_spend) AS average_total
    FROM spend
)
SELECT s.customer_id, s.total_spend
FROM spend AS s
CROSS JOIN avg_spend AS a
WHERE s.total_spend > a.average_total
ORDER BY s.customer_id;

-- Q6: ranking window functions partitioned by city.
WITH spend AS (
    SELECT o.customer_id, c.city, SUM(o.order_amount) AS total_spend
    FROM orders AS o
    JOIN customers AS c ON c.customer_id = o.customer_id
    WHERE o.status = 'completed'
    GROUP BY o.customer_id, c.city
)
SELECT
    customer_id,
    city,
    total_spend,
    RANK() OVER (PARTITION BY city ORDER BY total_spend DESC) AS spend_rank,
    DENSE_RANK() OVER (PARTITION BY city ORDER BY total_spend DESC) AS spend_dense_rank,
    ROW_NUMBER() OVER (PARTITION BY city ORDER BY total_spend DESC) AS spend_row_number
FROM spend
ORDER BY city, total_spend DESC, customer_id;

-- Q7: daily completed revenue with a cumulative running total.
WITH daily AS (
    SELECT substr(order_ts, 1, 10) AS day, SUM(order_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY day
)
SELECT
    day,
    revenue,
    SUM(revenue) OVER (ORDER BY day ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue
FROM daily
ORDER BY day;
