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
    windows=["7D", "30D", "3M", "1Y", None],
    metrics={"*": ["count"], "amount": ["sum", "mean"]}
)
```

For cutoff `2024-02-15`:

- **7D window**: events after `2024-02-08` up to `2024-02-15`
- **30D window**: events after `2024-01-16` up to `2024-02-15`
- **3M window**: events after `2023-11-15` up to `2024-02-15`
- **1Y window**: events after `2023-02-15` up to `2024-02-15`
- **None window**: all events up to `2024-02-15` (no lookback limit)


#### Supported Aggregations

- `"count"` — number of events (on wildcard `"*"` only)
- `"sum"` — total of a numeric column
- `"mean"` — average of a numeric column
- `"nunique"` — count distinct values

#### Window Units

| Unit  | Example | Meaning                              |
|-------|---------|--------------------------------------|
| `D`   | `"30D"` | Exact days                           |
| `H`   | `"24H"` | Exact hours                          |
| `min` | `"90min"`| Exact minutes                       |
| `s`   | `"30s"` | Exact seconds                        |
| `M`   | `"3M"`  | Calendar months (respects month length)|
| `Y`   | `"1Y"`  | Calendar years (respects leap years) |
| `None`| `None`  | All history before cutoff            |

**`M` and `Y` use calendar-aware arithmetic**, meaning they respect actual
month and year lengths rather than assuming fixed days.

The window boundary is computed as:
```
window_start = cutoff - duration
```

Events are included if `window_start < event_time <= cutoff`
(window start is **exclusive**, cutoff is **inclusive**).

> **`"1M"` is not the same as `"30D"`.**
> For cutoff `2024-02-03`:
> - `"1M"` → window_start = `2024-01-03` (31 days back)
> - `"30D"` → window_start = `2024-01-04` (exactly 30 days back)
>
> An event on `2024-01-04` is counted in `"1M"` but **not** in `"30D"`.


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
- **cutoff_time** — the prediction/cut-off moment

When computing features, we:

1. Join events to entity-cutoff pairs by entity
2. Filter to events *up to* the cutoff time
3. Aggregate by entity-cutoff pair

Example:

```
Spine row: user_1, 2024-02-15

All events for user_1:
  2024-01-10: 10  ← excluded (before 30D window start 2024-01-16)
  2024-01-20: 20  ← included
  2024-02-01: 15  ← included
  2024-02-20: 5   ← excluded (after cutoff)

30D window (events after 2024-01-16 up to 2024-02-15):
  Count: 2
  Sum: 35
```

## Output Column Names

Features are named automatically based on the table, metric, aggregation,
and window:

| Pattern | Example |
|---|---|
| `{table}__n_events__{window}` | `events__n_events__30d` |
| `{table}__{col}__{agg}__{window}` | `events__amount__sum__3m` |
| `{table}__n_events__all` | `events__n_events__all` |
| `{table}__recency` | `events__recency` |
| `{table}__recency__{col}_{val}` | `events__recency__event_type_purchase` |

Window suffixes are lowercased: `"30D"` → `30d`, `"3M"` → `3m`, `"1Y"` → `1y`, `None` → `all`.