def test_smoke():
    # ensure build_features can be imported
    from safefeat import build_features
    assert callable(build_features)

