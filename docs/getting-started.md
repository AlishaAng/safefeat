# Getting Started

## Installation

Install from PyPI:

```bash
pip install safefeat
```

Install (editable, with dev tools):

```bash
pip install -e ".[dev]"
```


## 1. Prepare the spine and events
--------------------------------

The spine defines the prediction scenarios as rows of (entity_id, cutoff_time).
Events contain historical records tied to entities.

```python
import pandas as pd

spine = pd.DataFrame({
    "entity_id": ["u1", "u2"],
    "cutoff_time": ["2024-01-10", "2024-01-31"],
})

events = pd.DataFrame({
    "entity_id": ["u1", "u1", "u2", "u2"],
    "event_time": ["2024-01-05", "2024-01-06", "2024-01-10", "2024-01-30"],
    "amount": [10.0, 20.0, 5.0, 25.0],
    "event_type": ["click", "purchase", "purchase", "click"],
})
```

## 2. Define the Feature Specification
-----------------------
You declare features using WindowAgg.

```python
from safefeat import WindowAgg

spec = [
    WindowAgg(
        table="events",
        windows=["7D", "30D"],
        metrics={
            "*": ["count"],              # total events
            "amount": ["sum", "mean"],   # numeric aggregations
            "event_type": ["nunique"],   # categorical unique counts
        },
    )
]
```

## 3. Build features
------------------

```python
from safefeat import build_features

X = build_features(
    spine=spine,
    tables={"events": events},
    spec=spec,
    event_time_cols={"events": "event_time"},
    allowed_lag="0s",  # prevent future leakage
)

print(X)
```

Expected output (approximate):

```text
| entity_id | cutoff_time | events__n_events__7d | events__amount__sum__7d | events__amount__mean__7d | events__event_type__nunique__7d | events__n_events__30d | events__amount__sum__30d | events__amount__mean__30d | events__event_type__nunique__30d |
|-----------|------------|----------------------|--------------------------|---------------------------|----------------------------------|-----------------------|---------------------------|----------------------------|-----------------------------------|
| u1        | 2024-01-10 | 2                    | 30.0                     | 15.0                      | 2                                | 2                     | 30.0                      | 15.0                       | 2                                 |
| u2        | 2024-01-31 | 1                    | 25.0                     | 25.0                      | 1                                | 2                     | 30.0                      | 15.0                       | 2                                 |
```

### How Leakage Prevention Works
safefeat enforces:
```text
event_time <= cutoff_time
```
This guarantees that no future events are used when building features.

If allowed_lag is set (e.g. "5s"), a small tolerance is allowed to handle timestamp precision issues.


## 4. Inspect the AuditReport
--------------------------

If `return_report=True`, `build_features` returns an `AuditReport` mapping
table names to `TableAudit` objects. The audit shows how many event–cutoff
pairs were joined, how many were kept, how many were dropped for being in the
future, and the largest future delta observed.

```python
events_audit = report.tables.get("events")
print("total joined", events_audit.total_joined_pairs)
print("kept", events_audit.kept_pairs)
print("dropped (future)", events_audit.dropped_future_pairs)
print("max future delta", events_audit.max_future_delta)
```


## Advanced: Recency Features

Recency features represent the time since the most recent event before each cutoff.

Common examples:
- days since last login
- days since last purchase
- hours since last sensor reading

### Days since last event (unfiltered)

```python
from safefeat import build_features, RecencyBlock

spec = [
    RecencyBlock(table="events")
]

X = build_features(
    spine=spine,
    tables={"events": events},
    spec=spec,
    event_time_cols={"events": "event_time"},
)
```
This adds a column:
 - events__recency

### Days since last event of a specific type (filtered)
```python
spec = [
    RecencyBlock(
        table="events",
        filter_col="event_type",
        filter_value="purchase",
    )
]
```
This adds a column:
- events__recency__event_type_purchase


