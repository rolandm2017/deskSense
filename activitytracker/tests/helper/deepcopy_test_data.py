import copy


def deepcopy_test_data(input):
    clones = []
    for x in input:
        duplicate = copy.deepcopy(x)
        clones.append(duplicate)
    return clones
