import pandas as pd
from safefeat.core import build_features
from safefeat.spec import FeatureSpec, WindowAgg

def test_build_features_windowagg_M_and_Y():
    """Test that M and Y windows use calendar-aware arithmetic."""
    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-02-03"],
    })

    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1", "u1", "u1"],
        "event_time": [
            "2024-01-01",  # before window_start (2024-01-03) → excluded
            "2024-01-03",  # equal to window_start → excluded (strict >)
            "2024-01-04",  # just inside 1M window → included
            "2024-01-31",  # inside 1M window → included
            "2024-02-01",  # inside 1M window → included
        ],
    })

    spec = FeatureSpec(blocks=[
        WindowAgg(table="events", windows=["1M"], metrics={"*": ["count"]})
    ])

    X = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
        allowed_lag="0s"
    )

    assert len(X) == 1
    assert X["events__n_events__1m"].iloc[0] == 3  # Jan 4, Jan 31, Feb 1


def test_build_features_windowagg_1M_vs_30D():
    """1M and 30D are not the same — 1M is calendar-aware."""
    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-02-03"],  # 1M → Jan 3, 30D → Jan 4
    })

    # Simpler: use an event that falls between the two window starts
    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1"],
        "event_time": [
            "2024-01-03",  # inside 1M (window_start=Jan 3, excluded), outside 30D → excluded by both
            "2024-01-04",  # inside 1M window (Jan 3 < Jan 4), excluded by 30D (window_start=Jan 4) → only 1M counts it? 
            "2024-01-05",  # included by both
        ],
    })

    spec = FeatureSpec(blocks=[
        WindowAgg(table="events", windows=["1M", "30D"], metrics={"*": ["count"]})
    ])

    X = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
        allowed_lag="0s"
    )

    # 1M: window_start = 2024-01-03 → Jan 4 ✅, Jan 5 ✅ = 2
    # 30D: window_start = 2024-01-04 → Jan 5 ✅ only = 1
    assert X["events__n_events__1m"].iloc[0] == 2
    assert X["events__n_events__30d"].iloc[0] == 1


def test_build_features_windowagg_1Y():
    """Test that 1Y window uses calendar-aware arithmetic."""
    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-02-03"],  # 1Y → window_start = 2023-02-03
    })

    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1", "u1"],
        "event_time": [
            "2023-02-03",  # equal to window_start → excluded (strict >)
            "2023-02-04",  # just inside → included
            "2023-12-31",  # inside → included
            "2022-12-31",  # before window_start → excluded
        ],
    })

    spec = FeatureSpec(blocks=[
        WindowAgg(table="events", windows=["1Y"], metrics={"*": ["count"]})
    ])

    X = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
        allowed_lag="0s"
    )

    assert len(X) == 1
    assert X["events__n_events__1y"].iloc[0] == 2  # Feb 4 2023, Dec 31 2023


def test_build_features_windowagg_none_window():
    """None window returns all events prior to cutoff with no lookback limit."""
    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-01-10"],
    })

    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1", "u1"],
        "event_time": [
            "2020-05-01",  # very old → still included
            "2023-01-01",  # included
            "2024-01-05",  # included
            "2024-01-20",  # future → excluded
        ],
    })

    spec = FeatureSpec(blocks=[
        WindowAgg(table="events", windows=[None], metrics={"*": ["count"]})
    ])

    X = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
        allowed_lag="0s"
    )

    assert len(X) == 1
    assert X["events__n_events__all"].iloc[0] == 3  # all except the future event


def test_build_features_windowagg_mixed_windows_with_none():
    """Mix of D, M, Y, and None windows all work together."""
    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-01-10"],
    })

    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1", "u1"],
        "event_time": [
            "2020-01-01",  # only in None window
            "2023-01-01",  # before 1Y window_start (2023-01-10) → excluded from 1Y
            "2024-01-05",  # in 30D, 1M, 1Y, and None
            "2024-01-20",  # future → excluded from all
        ],
    })

    spec = FeatureSpec(blocks=[
        WindowAgg(table="events", windows=["30D", "1M", "1Y", None], metrics={"*": ["count"]})
    ])

    X = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
        allowed_lag="0s"
    )

    assert len(X) == 1
    assert X["events__n_events__30d"].iloc[0] == 1   # Jan 5 only
    assert X["events__n_events__1m"].iloc[0] == 1    # Jan 5 only (1M window_start = 2023-12-10)
    assert X["events__n_events__1y"].iloc[0] == 1    # Jan 5 only (1Y window_start = 2023-01-10, Jan 1 2023 excluded)
    assert X["events__n_events__all"].iloc[0] == 3   # everything except future