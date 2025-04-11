import copy

# Deep copy to enable testing of object state before/after this line
# Mutations were ruining test data due to downstream changes affecting spies

def snapshot_obj_for_tests(obj):
    """
    The object fed into this helper will retain 
    it's present state when a spy looks at it later.
    """
    return copy.deepcopy(obj)