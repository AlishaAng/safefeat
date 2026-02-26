# Synthetic Customer Demo Dataset

This dataset simulates a retail e-commerce environment with sessions,
funnel behaviour, purchases, refunds, and support tickets.

⚠️ This dataset is fully synthetic and contains no real customer data.

## Tables

### customer_events.csv

| Column | Description |
|--------|------------|
| entity_id | Customer identifier |
| event_time | Timestamp of event |
| session_id | Session identifier |
| event_type | visit, view, add_to_cart, purchase, refund, support_ticket |
| amount | Net amount (positive for purchase, negative for refund, else 0) |
| channel | Marketing / acquisition channel |
| device | web / ios / android |
| product_category | Product category |
| payment_method | Present only for purchase events |

### customer_spine.csv

| Column | Description |
|--------|------------|
| entity_id | Customer identifier |
| cutoff_time | Prediction time |
| churned | 1 if inactive > 90 days before cutoff |

## Churn Definition

A customer is labelled as churned at cutoff_time if:

    (cutoff_time - last_event_time) > 90 days