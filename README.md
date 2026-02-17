# safefeat

Leakage-safe, point-in-time feature engineering for event logs.

`safefeat` builds features for each `(entity_id, cutoff_time)` using only events that occurred at or before the cutoff time (no future data leakage).

## Install

```bash
pip install safefeat

```

## Core idea

You provide:

- Spine: the prediction moments (one row per entity and cutoff time)

- Events: event history (one row per event and timestamp)

- Spec: what features to compute (windows + aggregations)

safefeat guarantees features are point-in-time correct.


