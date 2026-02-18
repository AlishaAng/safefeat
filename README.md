# safefeat
[![PyPI version](https://img.shields.io/pypi/v/safefeat.svg)](https://pypi.org/project/safefeat/)
[![Documentation](https://img.shields.io/badge/docs-online-blue.svg)](https://alishaang.github.io/safefeat/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Leakage-safe, point-in-time feature engineering for event logs.**

`safefeat` builds ML features from event data using only information available *at prediction time* — no future data, no silent leakage, no surprises in production.

---

## The Problem

When you compute features like "total purchases in the last 30 days" without anchoring to a cutoff time, you accidentally include future events. Your model looks great in training — then falls apart in production.

```python
# ❌ Leaky — uses ALL events, including future ones
features = events.groupby("user_id")["amount"].sum()
df = spine.merge(features, on="user_id")

# ✅ Safe — only uses events before each cutoff_time
X = build_features(spine, tables, spec, event_time_cols={"events": "event_time"})
```

---

## Install

```bash
pip install safefeat
```

---

## How It Works

safefeat works with three components:

| Component | Description |
| --------- | ----------- |
| **Spine** | When to make predictions — one row per `(entity_id, cutoff_time)` |
| **Events** | Historical time-series data tied to each entity |
| **Spec** | Declarative definition of what features to compute |

For each row in the spine, safefeat joins only events where `event_time <= cutoff_time`, then computes your features. Future events are excluded.

---

## Quick Start

### Window aggregations

```python
import pandas as pd
from safefeat import build_features, WindowAgg

spine = pd.DataFrame({
    "entity_id":   ["u1", "u2"],
    "cutoff_time": ["2024-01-10", "2024-01-31"],
})

events = pd.DataFrame({
    "entity_id":  ["u1", "u1", "u2", "u2"],
    "event_time": ["2024-01-05", "2024-01-06", "2024-01-10", "2024-01-30"],
    "amount":     [10.0, 20.0, 5.0, 25.0],
    "event_type": ["click", "purchase", "purchase", "click"],
})

spec = [
    WindowAgg(
        table="events",
        windows=["7D", "30D"],
        metrics={
            "*":          ["count"],        # total events
            "amount":     ["sum", "mean"],  # numeric aggregations
            "event_type": ["nunique"],      # distinct event types
        },
    )
]

X = build_features(
    spine=spine,
    tables={"events": events},
    spec=spec,
    event_time_cols={"events": "event_time"},
    allowed_lag="0s",
)
```

Output columns follow the pattern `{table}__{column}__{agg}__{window}`:

```
events__n_events__7d
events__amount__sum__7d
events__amount__mean__30d
events__event_type__nunique__30d
```

### Recency features

Time since the most recent event before each cutoff — useful for churn, fraud, and behavioural modelling:

```python
from safefeat import RecencyBlock

spec = [RecencyBlock(table="events")]

X = build_features(
    spine=spine,
    tables={"events": events},
    spec=spec,
    event_time_cols={"events": "event_time"},
)
# Adds: events__recency (days since last event before cutoff_time)
```

Filter by event type:

```python
spec = [
    RecencyBlock(
        table="events",
        filter_col="event_type",
        filter_value="purchase",
    )
]
# Adds: events__recency__event_type_purchase
```

### Audit report

Verify exactly which events were included and dropped for each prediction point:

```python
X, audit = build_features(
    spine=spine,
    tables={"events": events},
    spec=spec,
    event_time_cols={"events": "event_time"},
    return_report=True,
)

events_audit = audit.tables.get("events")
print(events_audit.total_joined_pairs)    # total event-cutoff pairs considered
print(events_audit.kept_pairs)            # events before cutoff (used)
print(events_audit.dropped_future_pairs)  # events after cutoff (excluded)
```

---

## Development

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
```

---

## Documentation

Full documentation, concepts, and API reference:
👉 **https://alishaang.github.io/safefeat/**