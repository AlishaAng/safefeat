from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Union


@dataclass
class WindowAgg:
    """Specification for aggregating events within a time window.

    Attributes
    ----------
    table:
        Name of the events table to read (key in the `tables` mapping passed
        to :func:`build_features`).
    windows:
        List of window lengths expressed as duration strings (e.g.
        ``"7D"``, ``"30D"``, ``"3M"``, ``"1Y"``). Supported units:

        - ``D`` – days (e.g. ``"30D"`` = last 30 days)
        - ``H`` – hours (e.g. ``"24H"`` = last 24 hours)
        - ``min`` – minutes
        - ``s`` – seconds
        - ``M`` – calendar months (e.g. ``"1M"``, ``"3M"``)
        - ``Y`` – calendar years (e.g. ``"1Y"``, ``"2Y"``)

        For each window a set of features will be produced.

        **How M and Y windows are calculated**

        ``M`` and ``Y`` use calendar-aware arithmetic via ``relativedelta``,
        meaning they respect actual month lengths rather than assuming a fixed
        number of days.

        The window is a **sliding lookback** from the cutoff — it does not
        snap to calendar month or year boundaries.

        Given a cutoff date, the window start is computed as::

            window_start = cutoff - relativedelta(months=n)  # for M
            window_start = cutoff - relativedelta(years=n)   # for Y

        Events are included if ``window_start < event_time <= cutoff``
        (window start is **exclusive**, cutoff is **inclusive**).

        Examples:

        - cutoff = ``2024-02-03``, window = ``"1M"``
          → window_start = ``2024-01-03``
          → Jan 1 ❌, Jan 3 ❌, Jan 4 ✅, Jan 31 ✅, Feb 3 ✅

        - cutoff = ``2024-03-31``, window = ``"1M"``
          → window_start = ``2024-02-29`` (leap year aware)
          → Feb 28 ❌, Feb 29 ✅, Mar 15 ✅

        - cutoff = ``2024-02-03``, window = ``"1Y"``
          → window_start = ``2023-02-03``
          → Feb 3 2023 ❌, Feb 4 2023 ✅, Jan 31 2024 ✅

        .. note::
            ``"1M"`` is not the same as ``"30D"``. A 1-month window from
            ``2024-02-03`` starts on ``2024-01-03`` (31 days back), while
            ``"30D"`` starts on ``2024-01-04`` (exactly 30 days back).

        Use ``None`` in the list to compute features over all history prior
        to the cutoff with no lookback limit (e.g. ``windows=["30D", None]``).
        The resulting column suffix will be ``all`` (e.g.
        ``events__n_events__all``).

    metrics:
        Mapping from a column name to a list of aggregations to compute. Use
        ``"*"`` as a wildcard key to request event counts (only ``["count"]``
        is supported for the wildcard). Example: ``{"*": ["count"],
        "amount": ["sum", "mean"]}``.

    Examples
    --------
    ```python
    import pandas as pd
    from safefeat import build_features, WindowAgg

    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-01-10"],
    })

    events = pd.DataFrame({
        "entity_id": ["u1", "u1"],
        "event_time": ["2024-01-05", "2024-01-08"],
        "amount": [10, 20],
    })

    spec = [
        WindowAgg(
            table="events",
            windows=["7D", "3M", "1Y"],
            metrics={"amount": ["sum"], "*": ["count"]},
        )
    ]

    X = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
    )

    # column names produced:
    [events__n_events__7d
    events__amount__sum__7d
    events__n_events__3m
    events__amount__sum__3m
    events__n_events__1y
    events__amount__sum__1y]
    ```
    """
    table: str
    windows: List[Optional[str]]
    metrics: Dict[str, List[str]]
    
    def __post_init__(self):
        # basic shape/type checks
        if not isinstance(self.metrics, dict):
            raise ValueError("metrics must be a dict")

        # allowed aggregations
        allowed_aggs = {"count", "sum", "mean", "nunique"}

        for dim, aggs in self.metrics.items():
            # each value should be a list of strings
            if not isinstance(aggs, list) or not all(isinstance(a, str) for a in aggs):
                raise ValueError(f"aggregations for '{dim}' must be a list of strings")

            if dim == "*":
                # wildcard only supports a single count
                if aggs != ["count"]:
                    raise ValueError("'*' dimension only supports ['count']")
            else:
                # ensure every aggregation is in allow list
                for a in aggs:
                    if a not in allowed_aggs:
                        raise ValueError(f"unsupported aggregation '{a}' for dimension '{dim}'")


@dataclass
class RecencyBlock:
    """Specification for computing time since the most recent event.

    This block computes the number of days between the cutoff and the most
    recent matching event for each entity-cutoff pair. Optionally the block
    can be restricted to events that match ``filter_col == filter_value``.

    Parameters
    ----------
    table:
        Name of the events table to use.
    filter_col:
        Optional name of a column to filter on (for example ``"event_type"``).
    filter_value:
        Optional value that ``filter_col`` must equal to be considered.

    Examples
    --------
    ```python
    import pandas as pd
    from safefeat import build_features, RecencyBlock

    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-01-10"],
    })

    events = pd.DataFrame({
        "entity_id": ["u1"],
        "event_time": ["2024-01-08"],
    })

    spec = [RecencyBlock(table="events")]

    X = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
    )

    X["events__recency"].iloc[0]
    # 2
    ```
    """
    table: str
    filter_col: Optional[str] = None
    filter_value: Optional[str] = None
    
    def __post_init__(self):
        # both filter_col and filter_value must be provided together or not at all
        if (self.filter_col is None) != (self.filter_value is None):
            raise ValueError("Both filter_col and filter_value must be provided together")


@dataclass
class FeatureSpec:
    """Container for a list of feature specification blocks.

    Instances of this class are passed to :func:`build_features`. Each element
    of ``blocks`` should be either a :class:`WindowAgg` or a :class:`RecencyBlock`.
    """
    blocks: List[Union[WindowAgg, RecencyBlock]]
