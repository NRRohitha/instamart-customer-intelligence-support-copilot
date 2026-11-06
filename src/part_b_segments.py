import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.config import DATA_CLEAN, OUTPUTS, SNAPSHOT

RFM_COLUMNS = ["recency", "frequency", "monetary"]


def build_rfm(orders):
    completed = orders[orders["status"] == "completed"]
    snapshot = pd.Timestamp(SNAPSHOT)
    rfm = completed.groupby("customer_id").agg(
        last_order_ts=("order_ts", "max"),
        frequency=("order_id", "nunique"),
        monetary=("order_amount", "sum"),
    )
    rfm["recency"] = (snapshot - rfm["last_order_ts"]).dt.days
    return rfm[RFM_COLUMNS].reset_index()


def evaluate_k(scaled):
    rows = []
    for k in range(2, 9):
        model = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = model.fit_predict(scaled)
        rows.append(
            {
                "k": k,
                "inertia": model.inertia_,
                "silhouette": silhouette_score(scaled, labels),
            }
        )
    return pd.DataFrame(rows)


def name_segments(profile):
    profile = profile.copy()
    premium_id = profile["monetary"].idxmax()
    remaining = [index for index in profile.index if index != premium_id]
    frequent_id = profile.loc[remaining, "frequency"].idxmax()
    remaining = [index for index in remaining if index != frequent_id]
    at_risk_id = profile.loc[remaining, "recency"].idxmax()
    remaining = [index for index in remaining if index != at_risk_id]
    occasional_id = remaining[0]
    return {
        int(premium_id): ("Premium", "Protect with loyalty perks and early access"),
        int(frequent_id): ("Frequent Loyalists", "Reward frequency with bundled offers"),
        int(at_risk_id): ("At-Risk", "Win back with a time-limited discount"),
        int(occasional_id): ("Occasional Shoppers", "Nudge with category-led reminders"),
    }


def main():
    orders = pd.read_csv(DATA_CLEAN / "orders.csv", parse_dates=["order_ts"])
    rfm = build_rfm(orders)
    assert len(rfm) == 1175

    scaler = StandardScaler()
    scaled = scaler.fit_transform(rfm[RFM_COLUMNS])
    k_table = evaluate_k(scaled)
    print("=== K-means evaluation ===")
    print(k_table.round(3).to_string(index=False))

    chosen_k = 4
    model = KMeans(n_clusters=chosen_k, n_init=10, random_state=42)
    rfm["segment_id"] = model.fit_predict(scaled)

    profile = rfm.groupby("segment_id")[RFM_COLUMNS].mean()
    profile["size"] = rfm.groupby("segment_id").size()
    names = name_segments(profile)
    rfm["segment_name"] = rfm["segment_id"].map(lambda value: names[int(value)][0])
    premium_id = profile["monetary"].idxmax()
    rfm["is_premium"] = rfm["segment_id"].eq(premium_id)

    print("\n=== segment profile ===")
    print(profile.round(2).to_string())
    print("\n=== segment names ===")
    for segment_id, (name, action) in sorted(names.items()):
        print(f"{segment_id}: {name} | action: {action}")

    pca = PCA(n_components=2)
    pca.fit(scaled)
    print("\n=== PCA explained variance ===")
    print(pca.explained_variance_ratio_.round(3).tolist())
    print(f"total: {pca.explained_variance_ratio_.sum():.3f}")

    rfm["segment_id"] = rfm["segment_id"].astype(int)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    output_columns = [
        "customer_id",
        "recency",
        "frequency",
        "monetary",
        "segment_id",
        "segment_name",
        "is_premium",
    ]
    rfm[output_columns].to_csv(OUTPUTS / "customer_segments.csv", index=False)
    print(f"\nwrote {OUTPUTS / 'customer_segments.csv'} with {len(rfm)} rows")
    print(f"segment sizes: {rfm['segment_id'].value_counts().sort_index().to_dict()}")
    print(f"premium segment: {premium_id} / {names[premium_id][0]}")


if __name__ == "__main__":
    main()
