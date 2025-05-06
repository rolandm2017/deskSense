from activitytracker.util.add_util import add, subtract


def test_add():
    v = add(1, 2)
    assert v == 3


def test_subtract():
    k = subtract(10, 2)
    assert k == 8
