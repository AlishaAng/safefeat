# API Reference

This page documents the public API of `safefeat`.

## Example

### 1) Basic window features (count, sum, mean)

```python
import pandas as pd
from safefeat import build_features, WindowAgg

spine = pd.DataFrame({
    "entity_id": ["u1"],
    "cutoff_time": ["2024-01-10"],
})

events = pd.DataFrame({
    "entity_id": ["u1", "u1", "u1", "u1"],
    "event_time": ["2024-01-05", "2024-01-06", "2023-01-01", "2024-01-20"],
    "amount": [10.0, 20.0, 999.0, 999.0],
})

X = build_features(
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
)

print(X)

```

Expected output :

```text

| entity_id | cutoff_time | events__n_events__7d | events__amount__sum__7d | events__amount__mean__7d | events__n_events__30d | events__amount__sum__30d | events__amount__mean__30d |
| --------- | ----------- | -------------------- | ----------------------- | ------------------------ | --------------------- | ------------------------ | ------------------------- |
| u1        | 2024-01-10  | 2                    | 30.0                    | 15.0                     | 2                     | 30.0                     | 15.0                      |

```


---

## build_features

::: safefeat.core.build_features
    options:
      show_source: true
      show_root_heading: true
      show_signature: true


---

## Feature Specification

### WindowAgg

::: safefeat.spec.WindowAgg
    options:
      show_source: true
      show_root_heading: true
      show_signature: true

---

### RecencyBlock

::: safefeat.spec.RecencyBlock
    options:
      show_source: true
      show_root_heading: true
      show_signature: true

---
