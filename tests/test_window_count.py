import pandas as pd
from safefeat.core import count_events_in_window

def test():
    spine = pd.DataFrame(
        {
            "entity_id": ["u1"],
            "cutoff_time": ["2024-01-10"],
        }
    )

    events = pd.DataFrame(
        {
            "entity_id": ["u1", "u1", "u1", "u1"],
            "event_time": ["2024-01-05", "2024-01-06", "2023-01-01", "2024-01-20"],  # first two are in the window, third one is too old,  last is in the future
            "event_type": ["past_event", "past_event", "past_event", "future_event"],
        }
    )

    filtered = count_events_in_window(
        spine=spine,
        events=events,
        entity_col="entity_id",
        cutoff_col="cutoff_time",
        event_time_col="event_time",
        allowed_lag="0s",
        time_window="30D",
    )

    assert len(filtered) == 1 #Checks that the filtered result has exactly 1 row
    assert filtered["event_count_30D"].iloc[0] == 2 #Checks that the event count for the first row is 2, which means there are 2 events in the window