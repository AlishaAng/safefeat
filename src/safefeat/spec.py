from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Union


@dataclass
class WindowAgg:
    """Specification for aggregating events within a time window."""
    table: str # e.g. "events"
    windows: List[str] # e.g. ["30D", "60D"]
    metrics: Dict[str, List[str]] # e.g. {"*": ["count"]} or {"event_type": ["nunique"], "amount": ["sum", "mean"]}
    
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
    """Specification for computing time since last event."""
    table: str # e.g. "events"
    filter_col: Optional[str] = None # optional: e.g. "event_type" to filter before computing recency
    filter_value: Optional[str] = None # optional: e.g. "purchase" to match against filter_col
    
    def __post_init__(self):
        # both filter_col and filter_value must be provided together or not at all
        if (self.filter_col is None) != (self.filter_value is None):
            raise ValueError("Both filter_col and filter_value must be provided together")


@dataclass
class FeatureSpec:
    """Specification for building features.
    It's the full specification passed to build_features()
    """
    blocks: List[Union[WindowAgg, RecencyBlock]] # e.g. [WindowAgg(...), RecencyBlock(...)]
