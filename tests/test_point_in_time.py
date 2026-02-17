import pandas as pd
from safefeat.core import filter_events_point_in_time


def test_single_cutoff_drops_future_events():
    spine = pd.DataFrame(
        {
            "entity_id": ["u1"],
            "cutoff_time": ["2024-01-10"],
        }
    )

    events = pd.DataFrame(
        {
            "entity_id": ["u1", "u1"],
            "event_time": ["2024-01-05", "2024-01-20"],  # second is in the future
            "event_type": ["past_event", "future_event"],
        }
    )

    filtered = filter_events_point_in_time(
        spine=spine,
        events=events,
        entity_col="entity_id",
        cutoff_col="cutoff_time",
        event_time_col="event_time",
        allowed_lag="0s",
    )

    # Only the past event should remain
    assert len(filtered) == 1 #Checks that the filtered result has exactly 1 row
    assert filtered["event_type"].iloc[0] == "past_event" #Checks that the first event's type is "past_event"


def test_two_cutoffs_keep_event_only_for_later_cutoff():
    spine = pd.DataFrame(
        {
            "entity_id": ["u1", "u1"],
            "cutoff_time": ["2024-01-10", "2024-02-10"],
        }
    )

    events = pd.DataFrame(
        {
            "entity_id": ["u1"],
            "event_time": ["2024-01-15"],  # between the two cutoffs
            "event_type": ["mid_event"],
        }
    )

    filtered = filter_events_point_in_time(
        spine=spine,
        events=events,
        entity_col="entity_id",
        cutoff_col="cutoff_time",
        event_time_col="event_time",
        allowed_lag="0s",
    )

    # The event should match ONLY the later cutoff (Feb 10), not Jan 10
    assert len(filtered) == 1 
    assert filtered["cutoff_time"].iloc[0] == pd.Timestamp("2024-02-10")
    assert filtered["event_time"].iloc[0] == pd.Timestamp("2024-01-15")
    assert filtered["event_type"].iloc[0] == "mid_event"
