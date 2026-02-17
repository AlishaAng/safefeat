import pandas as pd
from safefeat.core import build_features
from safefeat.spec import FeatureSpec, WindowAgg

def test_build_features_windowagg_count():
    spine = pd.DataFrame({
        "entity_id": ["u1"],
        "cutoff_time": ["2024-01-10"],
    })

    events = pd.DataFrame({
        "entity_id": ["u1", "u1", "u1", "u1"],
        "event_time": ["2024-01-05", "2024-01-06", "2023-01-01", "2024-01-20"],
    })

    spec = FeatureSpec(blocks=[
        WindowAgg(table="events", windows=["30D"], metrics={"*": ["count"]})
    ])

    X = build_features(
        spine=spine,
        tables={"events": events},
        spec=spec,
        event_time_cols={"events": "event_time"},
        allowed_lag="0s"
    )

    assert len(X) == 1 #Checks that the output DataFrame has exactly 1 row
    assert X['events__n_events__30d'].iloc[0] == 2 #Checks that the count of events in the 30-day window is 2, which means there are 2 events in the window