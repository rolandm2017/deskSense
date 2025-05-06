import copy

from surveillance.object.classes import ProgramSession, ChromeSession

# Deep copy to enable testing of object state before/after this line
# Mutations were ruining test data due to downstream changes affecting spies


def snapshot_obj_for_tests(obj: ProgramSession | ChromeSession):
    """
    The object fed into this helper will retain 
    it's present state when a spy looks at it later.
    """
    ledger_for_transfer = obj.ledger
    duplicate = copy.deepcopy(obj)
    duplicate.ledger = ledger_for_transfer
    return duplicate
