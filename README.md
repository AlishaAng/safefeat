# safefeat
[![PyPI version](https://img.shields.io/pypi/v/safefeat.svg)](https://pypi.org/project/safefeat/)
[![Documentation](https://img.shields.io/badge/docs-online-blue.svg)](https://alishaang.github.io/safefeat/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Leakage-safe, point-in-time feature engineering for event logs.

`safefeat` builds features for each `(entity_id, cutoff_time)` using only events that occurred at or before the cutoff time (no future data leakage).

## Install

```bash
pip install safefeat
```

## Main Concept:
safefeat works with three components:

1️⃣ Spine : Defines when predictions are made.

| entity_id | cutoff_time |
| --------- | ----------- |
| u1        | 2024-01-10  |

2️⃣ Events : Historical event log.

| entity_id | event_time | amount |
| --------- | ---------- | ------ |
| u1        | 2024-01-05 | 10     |

3️⃣ Feature Specification : Declarative description of what features to compute.


## Example

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
## ⏱ Recency Features (Time Since Last Event)
Recency features are extremely useful in churn, fraud, and behavioural modelling.
Examples:
- Days since last login
- Days since last purchase
- Days since last transaction

```python
#Basic Recency
from safefeat import RecencyBlock

spec = [
    RecencyBlock(table="events")
]

X = build_features(
    spine=spine,
    tables={"events": events},
    spec=spec,
    event_time_cols={"events": "event_time"},
)

print(X)
```
This adds 'events__recency' which represents days since the most recent event before the cutoff.


## 🧪 Development
```bash
pip install -e ".[dev]"
pytest -q
ruff check .
```

## 📚 Documentation
Full documentation:
👉 https://alishaang.github.io/safefeat/