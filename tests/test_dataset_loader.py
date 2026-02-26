from safefeat.datasets import load_customer_demo

def test_demo_dataset_loads():
    events, spine = load_customer_demo()
    assert len(events) > 0
    assert len(spine) > 0
    assert "entity_id" in events.columns
    assert "cutoff_time" in spine.columns

    