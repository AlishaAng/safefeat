# safefeat

Leakage-safe, point-in-time feature engineering for event logs.

`safefeat` builds features for each `(entity_id, cutoff_time)` using only events that occurred at or before the cutoff time (no future data leakage).

## Install

```bash
pip install safefeat

```

## Example
```python
from safefeat import build_features, WindowAgg

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
| entity_id | cutoff_time | events__n_events__7d | events__amount__sum__30d |
| --------- | ----------- | -------------------- | ------------------------ |
| u1        | 2024-01-10  | 2                    | 30                       |
| u2        | 2024-01-10  | 1                    | 5                        |

```
