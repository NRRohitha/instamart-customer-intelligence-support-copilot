import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import DATA_CLEAN, LAPSE_CUTOFF, OUTPUTS

NUMERIC = [
    "recency",
    "frequency",
    "monetary",
    "avg_discount",
    "cancellation_rate",
    "avg_delivery",
    "age",
    "tenure",
]
CATEGORICAL = ["city", "gender", "favourite_category"]
FEATURES = NUMERIC + CATEGORICAL


def build_cohort(orders, customers, products):
    cutoff = pd.Timestamp(LAPSE_CUTOFF)
    september_end = pd.Timestamp("2025-10-01")
    pre = orders[orders["order_ts"] < cutoff]
    completed_pre = pre[pre["status"] == "completed"]

    base = completed_pre.groupby("customer_id").agg(
        last_order_ts=("order_ts", "max"),
        frequency=("order_id", "nunique"),
        monetary=("order_amount", "sum"),
        avg_discount=("discount_pct", "mean"),
        avg_delivery=("delivery_minutes", "mean"),
    )
    base["recency"] = (cutoff - base["last_order_ts"]).dt.days
    base = base.drop(columns=["last_order_ts"])

    status_counts = (
        pre.groupby("customer_id")["status"]
        .agg(total="size", cancelled=lambda values: (values == "cancelled").sum())
    )
    status_counts["cancellation_rate"] = (
        status_counts["cancelled"] / status_counts["total"]
    )
    base = base.join(status_counts["cancellation_rate"])

    category_counts = (
        completed_pre.merge(products[["product_id", "category"]], on="product_id")
        .groupby(["customer_id", "category"])
        .size()
        .reset_index(name="count")
        .sort_values(["customer_id", "count", "category"], ascending=[True, False, True])
        .drop_duplicates("customer_id")
        .set_index("customer_id")["category"]
    )
    base["favourite_category"] = category_counts

    profile = customers.set_index("customer_id")[["city", "age", "gender", "signup_date"]]
    base = base.join(profile)
    base["tenure"] = (cutoff - base["signup_date"]).dt.days
    base = base.drop(columns=["signup_date"])

    september_customers = set(
        orders.loc[
            (orders["status"] == "completed")
            & (orders["order_ts"] >= cutoff)
            & (orders["order_ts"] < september_end),
            "customer_id",
        ]
    )
    base["lapsed"] = (~base.index.isin(september_customers)).astype(int)
    return base.reset_index()


def build_pipeline(model):
    preprocessor = ColumnTransformer(
        [
            ("num", StandardScaler(), NUMERIC),
            (
                "cat",
                OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False),
                CATEGORICAL,
            ),
        ]
    )
    return Pipeline([("preprocessor", preprocessor), ("model", model)])


def metrics(y_true, predictions):
    return {
        "confusion": confusion_matrix(y_true, predictions, labels=[0, 1]),
        "precision": precision_score(y_true, predictions, zero_division=0),
        "recall": recall_score(y_true, predictions, zero_division=0),
        "f1": f1_score(y_true, predictions, zero_division=0),
    }


def show_metrics(name, values):
    print(f"\n{name}")
    print(f"confusion matrix: {values['confusion'].tolist()}")
    print(f"precision: {values['precision']:.3f}")
    print(f"recall: {values['recall']:.3f}")
    print(f"f1: {values['f1']:.3f}")


def main():
    orders = pd.read_csv(DATA_CLEAN / "orders.csv", parse_dates=["order_ts"])
    customers = pd.read_csv(DATA_CLEAN / "customers.csv", parse_dates=["signup_date"])
    products = pd.read_csv(DATA_CLEAN / "products.csv")

    cohort = build_cohort(orders, customers, products)
    assert len(cohort) == 1156
    assert cohort["lapsed"].sum() == 443
    assert not cohort[FEATURES].isna().any().any()
    print(f"cohort: {len(cohort)}")
    print(f"lapsed: {cohort['lapsed'].sum()} ({cohort['lapsed'].mean() * 100:.2f}%)")

    X = cohort[FEATURES]
    y = cohort["lapsed"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    print(f"train/test: {len(X_train)}/{len(X_test)}")

    baseline = [0] * len(y_test)
    print(f"baseline accuracy: {accuracy_score(y_test, baseline) * 100:.1f}%")
    print(f"baseline lapsed f1: {f1_score(y_test, baseline, zero_division=0):.3f}")

    lr = build_pipeline(LogisticRegression(max_iter=1000))
    lr_grid = GridSearchCV(
        lr,
        {"model__C": [0.01, 0.1, 1, 10, 100]},
        cv=5,
        scoring="f1",
    )
    lr_grid.fit(X_train, y_train)
    best_lr = lr_grid.best_estimator_
    lr_predictions = best_lr.predict(X_test)
    lr_metrics = metrics(y_test, lr_predictions)
    print(f"\nlogistic best params: {lr_grid.best_params_}")
    print(f"logistic best cv f1: {lr_grid.best_score_:.3f}")
    show_metrics("logistic test metrics", lr_metrics)

    rf = build_pipeline(
        RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    )
    rf_grid = GridSearchCV(
        rf,
        {
            "model__max_depth": [3, 5, 8],
            "model__min_samples_leaf": [5, 10, 20],
        },
        cv=5,
        scoring="f1",
    )
    rf_grid.fit(X_train, y_train)
    best_rf = rf_grid.best_estimator_
    rf_predictions = best_rf.predict(X_test)
    rf_metrics = metrics(y_test, rf_predictions)
    print(f"\nrandom forest best params: {rf_grid.best_params_}")
    print(f"random forest best cv f1: {rf_grid.best_score_:.3f}")
    show_metrics("random forest test metrics", rf_metrics)

    selected_name = "random forest" if rf_metrics["f1"] >= lr_metrics["f1"] else "logistic"
    selected = best_rf if selected_name == "random forest" else best_lr
    selected_predictions = selected.predict(X_test)
    print(f"\nselected: {selected_name}")
    assert f1_score(y_test, selected_predictions, zero_division=0) >= 0.55

    scaler = best_lr.named_steps["preprocessor"].named_transformers_["num"]
    frequency_index = NUMERIC.index("frequency")
    print(f"learned train mean frequency: {scaler.mean_[frequency_index]:.3f}")
    print(f"full cohort mean frequency: {X['frequency'].mean():.3f}")

    feature_names = best_rf.named_steps["preprocessor"].get_feature_names_out()
    importances = pd.Series(
        best_rf.named_steps["model"].feature_importances_, index=feature_names
    ).sort_values(ascending=False)
    print("\ntop five random-forest features:")
    print(importances.head(5).round(4).to_string())

    coefficients = pd.Series(
        best_lr.named_steps["model"].coef_[0], index=feature_names
    )
    print("\nselected logistic coefficients:")
    print(coefficients.reindex(coefficients.abs().sort_values(ascending=False).index).head(10).round(4).to_string())
    print("\nthree named logistic coefficients:")
    for feature in ["num__recency", "num__frequency", "num__monetary"]:
        print(f"{feature}: {coefficients[feature]:.4f}")

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    model_path = OUTPUTS / "lapse_model.joblib"
    joblib.dump(selected, model_path)
    reloaded = joblib.load(model_path)
    assert (reloaded.predict(X_test) == selected_predictions).all()
    print("reloaded model predictions identical")

    segments = pd.read_csv(OUTPUTS / "customer_segments.csv")
    premium_ids = set(segments.loc[segments["is_premium"], "customer_id"])
    test_frame = X_test.copy()
    test_frame["customer_id"] = cohort.loc[X_test.index, "customer_id"].to_numpy()
    test_frame["actually_lapsed"] = y_test.to_numpy()
    test_frame["lapse_probability"] = selected.predict_proba(X_test)[:, 1]
    retention = (
        test_frame[test_frame["customer_id"].isin(premium_ids)]
        .sort_values(["lapse_probability", "customer_id"], ascending=[False, True])
        .head(10)[["customer_id", "lapse_probability", "actually_lapsed"]]
    )
    retention.to_csv(OUTPUTS / "retention_list.csv", index=False)
    print(f"\nretention rows: {len(retention)}; truly lapsed: {int(retention['actually_lapsed'].sum())}")
    print(retention.round(4).to_string(index=False))

    lapsed_count = int((y_train == 1).sum())
    non_lapsed_count = int((y_train == 0).sum())
    lapsed_indices = X_train.index[y_train == 1]
    extra_needed = non_lapsed_count - lapsed_count
    extra_indices = pd.Series(lapsed_indices).sample(
        n=extra_needed, replace=True, random_state=42
    )
    balanced_indices = list(X_train.index) + list(extra_indices)
    shuffled = (
        pd.DataFrame(
            {
                "index": balanced_indices,
                "y": [int(value) for value in y_train] + [1] * extra_needed,
            }
        )
        .sample(frac=1, random_state=42)
        .reset_index(drop=True)
    )
    X_balanced = X.loc[shuffled["index"]]
    y_balanced = shuffled["y"].to_numpy()
    print(
        f"balanced training classes: {pd.Series(y_balanced).value_counts().to_dict()}"
    )

    balanced_lr = clone(best_lr)
    balanced_lr.fit(X_balanced, y_balanced)
    balanced_predictions = balanced_lr.predict(X_test)
    balanced_metrics = metrics(y_test, balanced_predictions)
    show_metrics("balanced logistic test metrics", balanced_metrics)

    print("\ncomparison (unbalanced -> balanced):")
    for key in ["precision", "recall", "f1"]:
        print(f"{key}: {lr_metrics[key]:.3f} -> {balanced_metrics[key]:.3f}")


if __name__ == "__main__":
    main()
