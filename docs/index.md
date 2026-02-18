
# SafeFeat








<!-- # SafeFeat

**Leakage-safe, point-in-time feature engineering for event logs.**

SafeFeat is a Python library for building machine learning features from event data without data leakage. It ensures that features are computed using only information available *at prediction time*.

## Why SafeFeat?

- **Point-in-time correctness**: Automatically enforces temporal ordering to prevent leakage
- **Audit trails**: Track which events were included, excluded, and why
- **Clean API**: Declarative specs for reproducible feature engineering
- **Fast**: Vectorized pandas operations

## Quick Example

```python
import pandas as pd
from safefeat import build_features, WindowAgg

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

X = build_features(
    spine=spine,
    tables={"events": events},
    spec=spec,
    event_time_cols={"events": "event_time"},
    allowed_lag="0s",  # prevent future leakage
)

print(X)
```
Expected output :

```text
| entity_id | cutoff_time | events__n_events__7d | events__amount__sum__7d | events__amount__mean__7d | events__event_type__nunique__7d | events__n_events__30d | events__amount__sum__30d | events__amount__mean__30d | events__event_type__nunique__30d |
| --------- | ----------- | -------------------- | ----------------------- | ------------------------ | ------------------------------- | --------------------- | ------------------------ | ------------------------- | -------------------------------- |
| u1        | 2024-01-10  | 2                    | 30.0                    | 15.0                     | 2                               | 2                     | 30.0                     | 15.0                      | 2                                |
| u2        | 2024-01-31  | 1                    | 25.0                    | 25.0                     | 1                               | 2                     | 30.0                     | 15.0                      | 2                                |
```

## Key Concepts

- **Spine**: DataFrame with entity IDs and cutoff times (when to look "as of")
- **Events**: Time-series data with entity ID, event time, and attributes
- **WindowAgg**: Count/sum/mean events in rolling time windows
- **RecencyBlock**: Time since last event (optionally filtered)
- **Point-in-Time**: Features only use data before the cutoff time
- **Audit Report**: Tracks joined, kept, and dropped event pairs

## Installation

```bash
pip install safefeat
```
```bash
# With dev tools (pytest, ruff)
pip install safefeat[dev]
```

## Learn More

- [Getting Started](getting-started.md)
- [Concepts](concepts.md)
- [API Reference](api.md) -->
