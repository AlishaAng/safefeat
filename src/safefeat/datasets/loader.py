from importlib.resources import files
import pandas as pd


def load_customer_demo():
    base = files("safefeat.datasets.data")
    events = pd.read_csv(base / "customer_events.csv", parse_dates=["event_time"])
    spine = pd.read_csv(base / "customer_spine.csv", parse_dates=["cutoff_time"])
    return events, spine

