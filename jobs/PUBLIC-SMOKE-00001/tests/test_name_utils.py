def test_normalize_name():
    from modules.name_utils import normalize_name
    assert normalize_name("  Hello   WORLD ") == "hello world"
