from .polling_util import count_full_loops


def test_whole_tens():
    a = 10
    b = 40
    c = 90

    assert isinstance(count_full_loops(a), int)

    assert count_full_loops(a) == 1
    assert count_full_loops(b) == 4
    assert count_full_loops(c) == 9


def test_zero():
    a = 0

    assert count_full_loops(a) == 0


def test_uneven_loops():
    a = 33
    b = 99
    c = 14

    assert isinstance(count_full_loops(a), int)

    assert count_full_loops(a) == 3
    assert count_full_loops(b) == 9
    assert count_full_loops(c) == 1
