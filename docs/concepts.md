# Concepts

## Point-in-Time

The core principle of SafeFeat is **point-in-time correctness**: when computing features for a prediction at cutoff time $t$, only use information available *before* time $t$.

Example: If you predict churn on 2024-02-15, don't use events from 2024-02-16.

### Spine

The spine defines your prediction scenarios:

```
entity_id | cutoff_time
----------|------------
user_1    | 2024-01-31
user_1    | 2024-02-15
user_2    | 2024-02-15
```

Each row is an "as-of" moment: compute features for that entity looking back from that date.

## Aggregations

### WindowAgg

Count or summarize events in a rolling time window *before* the cutoff.

```python
WindowAgg(
    table="events",
    windows=["7D", "30D"],
    metrics={"*": ["count"], "amount": ["sum", "mean"]}
)
```

For cutoff 2024-02-15:
- **7D window**: 2024-02-08 to 2024-02-15
- **30D window**: 2024-01-16 to 2024-02-15

Only events falling in these windows before the cutoff are included.

#### Supported Aggregations

- `"count"` — number of events (on wildcard `"*"` only)
- `"sum"` — total of a numeric column
- `"mean"` — average of a numeric column
- `"nunique"` — count distinct values

### RecencyBlock

Time since the last event:

```python
RecencyBlock(
    table="events",
    filter_col="event_type",
    filter_value="purchase"
)
```

Returns the number of *days* between the cutoff and the most recent matching event.

Useful for:
- Churn modeling (days since purchase)
- Fraud detection (days since login)
- Activity recency

## Data Quality & Leakage

### Future Events

Events that occur *after* the cutoff are automatically excluded. This prevents leakage.

```python
allowed_lag = "0s"  # Default: strict point-in-time
# or
allowed_lag = "24h"  # Allow events up to 24h after cutoff
```

Use `allowed_lag` if your event data has slight delays in ingestion.

### Audit Report

The report tracks data quality by table:

```python
features, report = build_features(..., return_report=True)
audit = report.tables["events"]
```

Available metrics:
- `total_joined_pairs` — events matched to entities/cutoffs
- `kept_pairs` — events within cutoff
- `dropped_future_pairs` — events after cutoff (leakage risk)
- `max_future_delta` — largest lateness of dropped events

High `dropped_future_pairs` may indicate:
- Ingestion delays
- Timezone issues
- Data quality problems

## Entity-Cutoff Pairs

Each row in the spine creates an entity-cutoff pair. Events are grouped by:
- **entity_id** — which user/customer/entity
- **cutoff_time** — the prediction moment

When computing features, we:

1. Join events to entity-cutoff pairs by entity
2. Filter to events *up to* the cutoff time
3. Aggregate by entity-cutoff pair

Example:

```
Spine row: user_1, 2024-02-15

Join events for user_1:
  2024-01-10: 10 ← included
  2024-01-20: 20 ← included
  2024-02-01: 15 ← included
  2024-02-20: 5  ← excluded (after cutoff)

30D window (back to 2024-01-16):
  Count: 3
  Sum: 45
```
