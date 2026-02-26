# Demo Dataset (Synthetic E-commerce Customers)

Overview
--------

`safefeat` ships with a small synthetic dataset that mimics real e-commerce customer behaviour:
sessions, browsing funnels, purchases, refunds, and support tickets.

This dataset is fully synthetic and contains no real customer information.

Loading the dataset
-------------------

```python
from safefeat.datasets import load_customer_demo

events, spine = load_customer_demo()
```

Dataset structure
-----------------
### customer_events.csv
An event log of customer activity.

Example row:
```python
entity_id   event_time	        session_id	event_type amount  channel	device	product_category payment_method
cust_00001	2023-02-22 01:07:37	s_0000022	visit	    0.0	   organic	 web	   books	          NaN
```

#### Key columns

- entity_id: Customer identifier.
- event_time: Timestamp of the event.
- session_id: Session identifier.
- event_type: One of: visit, view, add_to_cart, purchase, refund, support_ticket.
- amount: Net transaction amount. Positive for purchases, negative for refunds, 0.0 otherwise.
- channel: Acquisition or interaction channel. May be missing.
- device: web, ios, android
- product_category: Product category associated with the event. May be missing.
- payment_method: Present only for purchase events

### customer_spine.csv

The modelling spine defines what is predicted and when.

```python
entity_id	cutoff_time	 churned
cust_00001	2024-01-01	 0
```

Columns

- entity_id: Customer identifier.
- cutoff_time: The prediction time. Features must be computed using only data at or before this timestamp.
- churned: Binary label. See definition below.

Label definition
----------------

At a given cutoff_time, a customer is labelled as churned if they have been inactive
(no events) for more than 90 days prior to the cutoff.

This label is computed using only events with event_time <= cutoff_time.

Multiple cutoffs
----------------

The spine may contain multiple rows per customer, e.g. monthly cutoffs. Each row is a
separate “snapshot”:

“As of this date, using only historical data, what features can we compute and what is the churn label?”

This matches real production usage where customers are scored repeatedly (weekly/monthly).

Point-in-time safety
--------------------
The event log includes activity after some cutoff times.

When computing features with:
```python
allowed_lag="0s"
```
`safefeat` ensures that only events at or before each `cutoff_time`
contribute to feature values.


Example: computing features point-in-time
----------------------------
```python
from safefeat.datasets import load_customer_demo
from safefeat import build_features, WindowAgg, RecencyBlock

events, spine = load_customer_demo()

spec = [
    WindowAgg(
        table="events",
        windows=["7D", "30D", "90D"],
        metrics={
            "*": ["count"],
            "amount": ["sum", "mean"],
        },
    ),
    RecencyBlock(table="events"),
]

X = build_features(
    spine=spine[["entity_id", "cutoff_time"]],
    tables={"events": events},
    spec=spec,
    event_time_cols={"events": "event_time"},
    allowed_lag="0s",
)

X.head()
```

