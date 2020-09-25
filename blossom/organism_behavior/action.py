import random


def move_only(organism, population_dict, world, position_hash_table=None):
    """
    Only move.
    """
    return 'move'


def move_and_reproduce(organism, population_dict, world, position_hash_table=None):
    """
    Move and reproduce. Reproduction occurs with probability 1/8.
    """
    choice = random.randrange(0, 8)
    if choice == 0:
        return 'reproduce'
    else:
        return 'move'


def move_and_drink(organism, population_dict, world, position_hash_table=None):
    """
    Move and drink. Each occurs with probability 1/2.
    """
    choice = random.randrange(0, 8)
    if choice < 4:
        return 'drink'
    else:
        return 'move'


def move_reproduce_drink(organism, population_dict, world, position_hash_table=None):
    """
    Move, drink, and reproduce. Reproduction occurs with probability 1/8.
    Drinks with probability 3/8, and moves with probability 1/2.
    """
    choice = random.randrange(0, 8)
    if choice == 0:
        return 'reproduce'
    elif choice < 4:
        return 'drink'
    else:
        return 'move'
