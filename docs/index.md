# SafeFeat

**Leakage-safe, point-in-time feature engineering for event logs.**

SafeFeat is a Python library for building machine learning features from event data without data leakage. It ensures that features are computed using only information available *at prediction time*.

## Why SafeFeat?

- **Point-in-time correctness**: Automatically enforces temporal ordering to prevent leakage
- **Audit trails**: Track which events were included, excluded, and why
- **Clean API**: Declarative specs for reproducible feature engineering
- **Fast**: Vectorized pandas operations

## Quick Example

```python
from safefeat import build_features, WindowAgg

features, report = build_features(
    spine=spine,
    tables={"events": events},
    spec=[
        WindowAgg(
            table="events",
            windows=["7D", "30D"],
            metrics={
                "*": ["count"],
                "amount": ["sum", "mean"],
            },
        )
    ],
    event_time_cols={"events": "event_time"},
    return_report=True,
)

print(report.tables["events"])
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

# With dev tools (pytest, ruff)
pip install safefeat[dev]
```

## Learn More

- [Getting Started](getting-started.md)
- [Concepts](concepts.md)
- [API Reference](api.md)
