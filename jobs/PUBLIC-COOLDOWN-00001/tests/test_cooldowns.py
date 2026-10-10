from modules.cooldowns import Cooldowns


def test_initial_ready():
    assert Cooldowns().ready("spell", 0)


def test_activation_blocks_until_deadline():
    c = Cooldowns()
    assert c.activate("spell", 10, 5)
    assert not c.activate("spell", 11, 5)
    assert c.remaining("spell", 13) == 2
    assert c.ready("spell", 15)


def test_independent_keys():
    c = Cooldowns()
    assert c.activate("a", 1, 10)
    assert c.activate("b", 1, 2)
    assert c.ready("b", 3)
    assert not c.ready("a", 3)


def test_purge_and_invalid():
    c = Cooldowns()
    c.activate("a", 0, 2)
    assert c.purge(2) == 1
    try:
        c.activate("a", 2, -1)
        assert False
    except ValueError:
        pass
