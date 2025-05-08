import copy

from activitytracker.object.classes import ChromeSession, ProgramSession

# Deep copy to enable testing of object state before/after this line
# Mutations were ruining test data due to downstream changes affecting spies


def snapshot_obj_for_tests_with_ledger(obj: ProgramSession | ChromeSession):
    """
    The object fed into this helper will retain
    it's present state when a spy looks at it later.

    It lives in the tests/helper folder because it's only used in tests!
    """
    ledger_for_transfer = obj.ledger
    duped_ledger = copy.deepcopy(ledger_for_transfer)
    duplicate = copy.deepcopy(obj)
    duplicate.ledger = duped_ledger
    return duplicate
