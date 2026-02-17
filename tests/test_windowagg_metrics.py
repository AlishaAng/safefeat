import pandas as pd
from safefeat.spec import WindowAgg, FeatureSpec
from safefeat.core import build_features


def test_windowagg_sum():
    """Test sum aggregation on a named column within a time window."""
    
    # spine with one cutoff
    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-01-31"],
    })
    
    # events with two in-window amounts and one out-of-window amount
    # In-window: 2024-01-30 (amount=10) and 2024-01-31 (amount=20)
    # Out-of-window: 2023-01-01 (amount=5)
    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1"],
        "event_time": ["2023-01-01", "2024-01-30", "2024-01-31"],
        "amount": [5, 10, 20],
    })
    
    # spec requests sum of amount in 30D window
    spec = FeatureSpec(
        blocks=[
            WindowAgg(
                table="events",
                windows=["30D"],
                metrics={"*": ["count"], "amount": ["sum", "mean"]},
            )
        ]
    )

    # run build_features
    result = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
    )
    
    # assert output column exists
    assert "events__amount__sum__30d" in result.columns
    
    # assert value equals 30 (10 + 20, excluding 5 which is outside the 30D window)
    assert result["events__amount__sum__30d"].iloc[0] == 30

def test_windowagg_mean():
    """Test mean aggregation on a named column within a time window."""
    
    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-01-31"],
    })
    
    # In-window: amounts 10 and 20 (mean = 15)
    # Out-of-window: amount 5
    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1"],
        "event_time": ["2023-01-01", "2024-01-30", "2024-01-31"],
        "amount": [5, 10, 20],
    })
    
    spec = FeatureSpec(
        blocks=[
            WindowAgg(
                table="events",
                windows=["30D"],
                metrics={"*": ["count"], "amount": ["mean"]},
            )
        ]
    )
    
    result = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
    )
    
    assert "events__amount__mean__30d" in result.columns
    assert result["events__amount__mean__30d"].iloc[0] == 15.0


def test_windowagg_nunique():
    """Test nunique aggregation on a named column within a time window."""
    
    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-01-31"],
    })
    
    # In-window: 3 distinct event_types ("a", "b", "a")
    # Out-of-window: 1 event_type ("c")
    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1", "u1"],
        "event_time": ["2023-01-01", "2024-01-30", "2024-01-30", "2024-01-31"],
        "event_type": ["c", "a", "b", "a"],
    })
    
    spec = FeatureSpec(
        blocks=[
            WindowAgg(
                table="events",
                windows=["30D"],
                metrics={"*": ["count"], "event_type": ["nunique"]},
            )
        ]
    )
    
    result = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
    )
    
    assert "events__event_type__nunique__30d" in result.columns
    # nunique of ["a", "b", "a"] = 2
    assert result["events__event_type__nunique__30d"].iloc[0] == 2


def test_windowagg_multiple_windows():
    """Test multiple windows in a single spec block."""
    
    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-01-31"],
    })
    
    # Events spread across different dates
    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1"],
        "event_time": ["2024-01-01", "2024-01-20", "2024-01-31"],
        "amount": [10, 20, 30],
    })
    
    spec = FeatureSpec(
        blocks=[
            WindowAgg(
                table="events",
                windows=["7D", "60D"],
                metrics={"*": ["count"], "amount": ["sum"]},
            )
        ]
    )
    
    result = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
    )
    
    # 7D window (2024-01-24 to 2024-01-31): only 2024-01-31 event (amount=30)
    assert "events__n_events__7d" in result.columns
    assert result["events__n_events__7d"].iloc[0] == 1
    assert "events__amount__sum__7d" in result.columns
    assert result["events__amount__sum__7d"].iloc[0] == 30
    
    # 60D window (2023-12-02 to 2024-01-31): all 3 events (amount=10+20+30=60)
    assert "events__n_events__60d" in result.columns
    assert result["events__n_events__60d"].iloc[0] == 3
    assert "events__amount__sum__60d" in result.columns
    assert result["events__amount__sum__60d"].iloc[0] == 60


def test_windowagg_multiple_entities_cutoffs():
    """Test multiple entities and cutoffs in one spec."""
    
    spine = pd.DataFrame({
        "entity_id": ["u1", "u1", "u2"],
        "cutoff_time": ["2024-01-15", "2024-01-31", "2024-01-31"],
    })
    
    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1", "u2", "u2"],
        "event_time": ["2024-01-10", "2024-01-12", "2024-01-20", "2024-01-28", "2024-01-31"],
        "amount": [5, 10, 15, 20, 25],
    })
    
    spec = FeatureSpec(
        blocks=[
            WindowAgg(
                table="events",
                windows=["30D"],
                metrics={"*": ["count"], "amount": ["sum"]},
            )
        ]
    )
    
    result = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
    )
    
    # u1, cutoff 2024-01-15: events on 2024-01-10 (5) and 2024-01-12 (10)
    assert result.loc[(result["entity_id"] == "u1") & (result["cutoff_time"] == "2024-01-15"), "events__n_events__30d"].iloc[0] == 2
    assert result.loc[(result["entity_id"] == "u1") & (result["cutoff_time"] == "2024-01-15"), "events__amount__sum__30d"].iloc[0] == 15
    
    # u1, cutoff 2024-01-31: all 3 u1 events (5 + 10 + 15)
    assert result.loc[(result["entity_id"] == "u1") & (result["cutoff_time"] == "2024-01-31"), "events__n_events__30d"].iloc[0] == 3
    assert result.loc[(result["entity_id"] == "u1") & (result["cutoff_time"] == "2024-01-31"), "events__amount__sum__30d"].iloc[0] == 30
    
    # u2, cutoff 2024-01-31: both u2 events (20 + 25)
    assert result.loc[result["entity_id"] == "u2", "events__n_events__30d"].iloc[0] == 2
    assert result.loc[result["entity_id"] == "u2", "events__amount__sum__30d"].iloc[0] == 45