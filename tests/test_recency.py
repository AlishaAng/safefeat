import pandas as pd
from safefeat.spec import RecencyBlock, FeatureSpec
from safefeat.core import build_features


def test_recency_basic():
    """Test basic recency computation (time since last event)."""
    
    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-01-31"],
    })
    
    # Events at different times
    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1"],
        "event_time": ["2024-01-15", "2024-01-25", "2024-01-28"],
    })
    
    spec = FeatureSpec(
        blocks=[
            RecencyBlock(table="events")
        ]
    )
    
    result = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
    )
    
    # Last event is 2024-01-28, cutoff is 2024-01-31
    # Recency should be 3 days
    assert "events__recency" in result.columns
    assert result["events__recency"].iloc[0] == 3


def test_recency_with_filter():
    """Test recency with filtering on a column."""
    
    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-01-31"],
    })
    
    # Events with different types
    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1", "u1"],
        "event_time": ["2024-01-10", "2024-01-20", "2024-01-25", "2024-01-28"],
        "event_type": ["login", "purchase", "login", "purchase"],
    })
    
    spec = FeatureSpec(
        blocks=[
            RecencyBlock(table="events", filter_col="event_type", filter_value="purchase")
        ]
    )
    
    result = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
    )
    
    # Last purchase is 2024-01-28, cutoff is 2024-01-31
    # Recency should be 3 days
    assert "events__recency__event_type_purchase" in result.columns
    assert result["events__recency__event_type_purchase"].iloc[0] == 3


def test_recency_no_events():
    """Test recency when entity has no events."""
    
    spine = pd.DataFrame({
        "entity_id": ["u1", "u2"],
        "cutoff_time": ["2024-01-31", "2024-01-31"],
    })
    
    # Events only for u1
    events = pd.DataFrame({
        "entity_id": ["u1", "u1"],
        "event_time": ["2024-01-25", "2024-01-28"],
    })
    
    spec = FeatureSpec(
        blocks=[
            RecencyBlock(table="events")
        ]
    )
    
    result = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
    )
    
    # u1 has events
    assert result.loc[result["entity_id"] == "u1", "events__recency"].iloc[0] == 3
    
    # u2 has no events (should be NaN or null)
    assert pd.isna(result.loc[result["entity_id"] == "u2", "events__recency"].iloc[0])


def test_recency_multiple_cutoffs():
    """Test recency with multiple entities and cutoffs."""
    
    spine = pd.DataFrame({
        "entity_id": ["u1", "u1", "u2"],
        "cutoff_time": ["2024-01-15", "2024-01-31", "2024-01-31"],
    })
    
    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1", "u2", "u2"],
        "event_time": ["2024-01-05", "2024-01-10", "2024-01-25", "2024-01-28", "2024-01-30"],
    })
    
    spec = FeatureSpec(
        blocks=[
            RecencyBlock(table="events")
        ]
    )
    
    result = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
    )
    
    # u1, cutoff 2024-01-15: last event is 2024-01-10, recency = 5 days
    assert result.loc[(result["entity_id"] == "u1") & (result["cutoff_time"] == "2024-01-15"), "events__recency"].iloc[0] == 5
    
    # u1, cutoff 2024-01-31: last event is 2024-01-25, recency = 6 days
    assert result.loc[(result["entity_id"] == "u1") & (result["cutoff_time"] == "2024-01-31"), "events__recency"].iloc[0] == 6
    
    # u2, cutoff 2024-01-31: last event is 2024-01-30, recency = 1 day
    assert result.loc[result["entity_id"] == "u2", "events__recency"].iloc[0] == 1
