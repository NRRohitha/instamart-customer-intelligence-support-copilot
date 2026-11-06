PART_A_AUDIT = {
    "raw_order_rows": 13084,
    "exact_duplicate_rows": 119,
    "pending_rows": 656,
    "distinct_order_ids": 12309,
    "non_numeric_amounts": 120,
    "negative_delivery_minutes": 106,
    "blank_delivery_minutes": 2541,
    "blank_ages": 61,
    "ages_outside_10_100": 6,
    "raw_city_spellings": 24,
    "raw_gender_spellings": 10,
    "blank_genders": 30,
}

PART_A_CUSTOMERS = {
    "city_counts": {
        "Pune": 227,
        "Delhi": 210,
        "Bengaluru": 197,
        "Chennai": 191,
        "Hyderabad": 191,
        "Mumbai": 184,
    },
    "gender_counts": {"female": 610, "male": 560, "unknown": 30},
    "missing_ages": 0,
    "age_min": 18,
    "age_max": 60,
}

PART_A_ORDERS = {
    "clean_rows": 12309,
    "completed": 11110,
    "cancelled": 1199,
    "missing_amounts": 0,
    "missing_completed_delivery": 0,
    "missing_cancelled_delivery": 1199,
    "completed_revenue_inr": 2998668.80,
}

PART_A_SQL = {
    "q1_customers": 30,
    "q2_rows": 30,
    "q2_total_inr": 2998668.80,
    "q2_max_cell_inr": 233909.45,
    "q3_products": 11,
    "q4_customers": 25,
    "q5_customers": 550,
    "q5_average_inr": 2552.06,
    "q6_rank_row_number_differences": 8,
    "q6_top_per_city": {
        "Bengaluru": ("C0082", 12856.20),
        "Chennai": ("C0930", 10151.40),
        "Delhi": ("C0291", 13742.60),
        "Hyderabad": ("C0743", 12730.05),
        "Mumbai": ("C0693", 14766.55),
        "Pune": ("C0426", 10377.10),
    },
    "q7_daily_rows": 183,
    "q7_final_cumulative_inr": 2998668.80,
}

PART_A_EDA = {
    "bengaluru": {"sum": 523643.40, "mean": 276.47, "count": 1894},
    "mumbai": {"sum": 479058.50, "mean": 297.00, "count": 1613},
    "mean": 269.91,
    "median": 135.00,
    "skewness": 4.61,
    "q1": 64.80,
    "q3": 297.00,
    "upper_fence": 645.30,
    "outliers_above": 897,
    "outliers_below": 0,
    "strongest_correlation": {"pair": ("order_amount", "discount_pct"), "value": -0.095},
}

PART_B_RFM = {
    "customers": 1175,
    "recency_median": 19,
    "recency_min": 0,
    "recency_max": 180,
    "frequency_mean": 9.46,
    "frequency_max": 33,
    "monetary_mean_inr": 2552.06,
    "monetary_max_inr": 14766.55,
}

PART_B_KMEANS = {
    2: {"inertia": 1820.8, "silhouette": 0.465},
    3: {"inertia": 1268.2, "silhouette": 0.445},
    4: {"inertia": 743.1, "silhouette": 0.526},
    5: {"inertia": 617.4, "silhouette": 0.481},
    6: {"inertia": 503.2, "silhouette": 0.482},
    7: {"inertia": 408.5, "silhouette": 0.416},
    8: {"inertia": 366.5, "silhouette": 0.412},
}

PART_B_PCA = {"pc1": 0.634, "pc2": 0.218, "total": 0.852, "tolerance": 0.02}

PART_B_LAPSE = {
    "cohort": 1156,
    "lapsed": 443,
    "lapsed_rate_pct": 38.32,
    "train_rows": 924,
    "test_rows": 232,
    "baseline_accuracy_pct": 61.6,
    "baseline_lapsed_f1": 0.0,
    "minimum_selected_test_f1": 0.55,
    "balanced_class_count": 570,
}

PART_C = {
    "empty_tickets": 4,
    "long_tickets": 4,
    "long_ticket_tokens": 734,
    "eligible_tickets": 156,
    "redactions": {"email": 55, "phone": 91, "order_id": 132, "total": 278, "remaining": 0},
    "transient_errors": 19,
    "statuses": {"classified_json": 135, "classified_keyword": 12, "flagged_invalid_output": 9},
    "classified": 147,
    "zero_shot_accuracy_pct": 85.7,
    "few_shot_accuracy_pct": 100.0,
    "final_rows": 164,
}

PART_D = {
    "chunks": {"refund_policy.txt": 4, "delivery_policy.txt": 3, "escalation_policy.txt": 3,
                "payment_policy.txt": 3, "privacy_policy.txt": 2, "total": 15},
    "grounding_overlap_10": {"doc": 12, "fact": 12, "fallback": 2},
    "scenarios": {
        "S1": {"status": "REFUND", "refund_inr": 128.25, "model_calls": 5},
        "S2": {"status": "REFUND", "refund_inr": 135.00},
        "S3": {"status": "ESCALATE", "refund_inr": 1999.00},
        "S4": {"status": "DENIED", "refund_inr": 0.0},
        "S5": {"status": "DENIED", "refund_inr": 0.0},
        "S6": {"status": "NOT_FOUND", "refund_inr": 0.0},
        "S7": {"status": "FALLBACK_MAX_ITERATIONS", "refund_inr": 0.0},
    },
    "stop_demos": {"S1_token_limit_200": "FALLBACK_TOKEN_LIMIT", "time_limit_0": "FALLBACK_TIMEOUT"},
    "resume_tools": ["get_order", "search_policy", "calculate_refund", "issue_refund"],
    "resume_final": {"status": "REFUND", "refund_inr": 128.25},
}
