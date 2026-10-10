def test_clamp():
    from modules.bounds import clamp
    assert clamp(12, 0, 10) == 10
