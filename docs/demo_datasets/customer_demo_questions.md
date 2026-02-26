# Customer demo: common questions answered with safefeat

This page shows how to answer common product / growth questions using the
synthetic customer dataset shipped with `safefeat`.

### Setup: load the demo data

The synthetic customer dataset ships with `safefeat` and can be loaded directly:

```python
from safefeat.datasets import load_customer_demo

events, spine = load_customer_demo()

print(events.head())
#entity_id | event_time            | session_id | event_type | amount | channel | device | product_category | payment_method
# cust_00001 | 2023-02-22 01:07:37 | s_0000022  | visit      | 0.0    | organic | web    |   books          |  NaN

print(spine.head())
# entity_id | cutoff_time | churned
# cust_0001 | 2024-04-01  | 1
```
---

### Build the feature matrix
```python
import pandas as pd
from safefeat import build_features, WindowAgg, RecencyBlock

spec = [
    WindowAgg(
        table="events",
        windows=["7D", "30D", "90D"],
        metrics={
            "*":               ["count"],           # overall activity
            "amount":          ["sum", "mean"], # spend behaviour
            "event_type":      ["nunique"],          # diversity of actions
            "channel":         ["nunique"],          # marketing breadth
            "device":          ["nunique"],          # device diversity
            "product_category":["nunique"],          # browsing breadth
        },
    ),
    RecencyBlock(table="events"),                    # days since last event
    RecencyBlock(                                    # days since last purchase
        table="events",
        filter_col="event_type",
        filter_value="purchase",
    ),
]

X = build_features(
    spine=spine[["entity_id", "cutoff_time"]],
    tables={"events": events},
    spec=spec,
    event_time_cols={"events": "event_time"},
    allowed_lag="0s",
)

# attach churn label
X = X.merge(
    spine[["entity_id", "cutoff_time", "churned"]],
    on=["entity_id", "cutoff_time"],
    how="left",
)
```
Columns produced:

| Feature group | Columns | What it captures |
|---|---|---|
| Activity | `events__n_events__7d/30d/90d` | Overall engagement level |
| Spend | `events__amount__sum__7d/30d/90d` | Total spend in window |
| Avg spend | `events__amount__mean__7d/30d/90d` | Average transaction size |
| Action diversity | `events__event_type__nunique__7d/30d/90d` | Mix of visits, views, purchases |
| Channel diversity | `events__channel__nunique__7d/30d/90d` | How many channels engaged |
| Device diversity | `events__device__nunique__7d/30d/90d` | Web vs mobile usage |
| Category breadth | `events__product_category__nunique__7d/30d/90d` | Browsing diversity |
| Recency | `events__recency` | Days since any event |
| Purchase recency | `events__recency__event_type_purchase` | Days since last purchase |


---

## Common questions

### Q1: Who are my most active customers in the last 30 days?
```python
top_active = (
    X[["entity_id", "events__n_events__30d"]]
    .sort_values("events__n_events__30d", ascending=False)
    .head(10)
)
print(top_active)
```

---
### Q2: Which customers haven't purchased recently? (early churn signal)
```python
at_risk = (
    X[["entity_id", "events__recency__event_type_purchase", "events__recency"]]
    .dropna(subset=["events__recency__event_type_purchase"])  # exclude customers who never purchased
    .sort_values("events__recency__event_type_purchase", ascending=False)
    .head(10)
)
print(at_risk)
```
> **Note:** `events__recency__event_type_purchase` is `NaN` for customers who
> have never made a purchase before the cutoff.

---

### Q3: Who are my high-spend customers in the last 90 days?
```python
high_spend = (
    X[["entity_id", "events__amount__sum__90d", "events__amount__mean__90d"]]
    .sort_values("events__amount__sum__90d", ascending=False)
    .head(10)
)
print(high_spend)
```

---

### Q4: Do churned customers behave differently before the cutoff?
```python
churn_comparison = (
    X.groupby("churned")[[
        "events__n_events__30d",
        "events__amount__sum__30d",
        "events__recency",
        "events__recency__event_type_purchase",
    ]]
    .mean()
    .round(2)
)
print(churn_comparison)
```

Expected pattern: churned customers will have **lower** event counts and spend,
and **higher** recency values — exactly what point-in-time features capture
without leakage.

---
